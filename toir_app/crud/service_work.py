import logging
from collections.abc import Sequence
from http import HTTPStatus
from typing import Annotated, Optional

from fastapi import HTTPException
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from toir_app.crud.car import (get_car_by_pk,
                               get_cars_with_request_and_special_status)
from toir_app.crud.service_name import (get_service_name_group,
                                        get_service_name_with_request_status)
from toir_app.crud.service_status import get_multi_service_status
from toir_app.models import Car, ServiceName, ServiceWork, User, UserRole
from toir_app.schemas.service_work import (CarAtributesInServiceWork,
                                           ServiceWorkBase)


async def get_service_work(
        service_work_id: int,
        session: AsyncSession,
        check_active: bool = True
) -> Optional[ServiceWork]:
    """Получение объекта модели ServiceWork по ID."""
    stmt = (
        select(ServiceWork)
        .options(selectinload(ServiceWork.car))  # Явно загружаем связь с Car
        .where(ServiceWork.id == service_work_id)
    )
    result = await session.scalar(stmt)
    if not result:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Указанная работа не найдена.'
        )
    if check_active and result.in_archive:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail='Указанная работа находится в архиве.'
        )
    return result


async def get_last_service_with_current_service_id(
        car_id: int,
        last_service_id: int,
        base_interval: int,
        session: AsyncSession
):
    """
    Возвращает последнюю (свежую) запись сервисного обслуживания.

    Применяется для поиска последней записи в базе данных с целью перевода
    её в архив.

    Args:
        - car_id : ID выбранного ТС
        - last_service_id : ID вида сервисного обслуживания, для которого
        выполняется поиск

    Returns:
        - оbj(ServiceWork)
    """

    service_name_group = await get_service_name_group(last_service_id, session)

    stmt = select(
        ServiceWork
    ).join(
        ServiceName, ServiceName.id == ServiceWork.last_service_id
    ).where(
        ServiceWork.car_id == car_id,
        or_(
            and_(
                ServiceName.group.is_not(None),
                ServiceName.group == service_name_group
            ),
            and_(
                ServiceWork.last_service_id == last_service_id,
                ServiceWork.base_interval == base_interval
            )
        )
    ).order_by(
        ServiceWork.last_service_reading.desc()
    ).limit(1)

    return await session.scalar(stmt)


async def get_last_request_reading_by_car(
        car_id: int,
        session: AsyncSession
):
    """Для передачи данных о машине (общий и суточный пробеги)."""
    result = await session.scalar(
        select(ServiceWork)
        .where(ServiceWork.car_id == car_id)
        .order_by(ServiceWork.request_date.desc())
        .limit(1)
    )
    return CarAtributesInServiceWork.model_validate(result)


async def check_zvr_unique(
        zvr_number: int,
        session: AsyncSession
) -> None:
    """Проверяет ЗВР на уникальный номер."""
    result = await session.scalar(
        select(ServiceWork)
        .where(ServiceWork.zvr_number == zvr_number)
    )
    if result:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail=f'Указанный ЗВР #{zvr_number} не уникален, сверьте данные.'
        )


async def get_active_service_work_list_by_car(
        car_id: int,
        session: AsyncSession,
        *,
        request_status_id: Optional[int] = None,
) -> Sequence[ServiceWork]:
    """Получение списка (неархивных) сервисных обслуживаний для ТС.

    ### Filters(optional):
         для всех расчётных статусов (request_status_id), строже выбранного.

    ### Order_by:
        - по возрастанию ID service_name (идентично шапке в итоговой таблице).
    """
    await get_car_by_pk(car_id, session, check_car_in_archive=False)

    stmt = select(
            ServiceWork
        ).where(
            ServiceWork.car_id == car_id,
            ServiceWork.in_archive.is_(False)
        ).order_by(
            ServiceWork.next_service_id  # сортировка по ID вида работ
        )
    if request_status_id is not None:
        stmt = stmt.where(ServiceWork.request_status_id <= request_status_id)

    result = await session.scalars(stmt)
    return result.all()


def update_reading_and_daily_distance(
        car_grz: Annotated[str, Car.grz],
        service_work: ServiceWork,
        incoming_data: ServiceWorkBase,
        session: AsyncSession
) -> None:
    """Сравнение поступивших данных с БД и их обновление при необходимости.

    ## Дополнительно:
        - Добавление в сессию без коммита.
    """
    if service_work.request_reading == incoming_data.request_reading:
        logging.info(f'⏸️ «{car_grz}» : за сутки не пошевелился.')
    else:
        service_work.daily_distance = incoming_data.daily_distance
        service_work.request_reading = incoming_data.request_reading
        logging.info(f'🏃‍➡️ «{car_grz}» : обновился пробег.')
        session.add(service_work)


async def add_service_works_in_archive(
        service_work_list: Sequence[ServiceWork],
        session: AsyncSession,
        **kwargs
):
    """Архивирование (без коммита) записей о ServiceWork."""
    for service_work in service_work_list:
        service_work.in_archive = True
        service_work.service_work_completed = True
        # TODO Подумать, нужно ли перезаписывать пробег для старой записи
        # Скорее всего НЕТ, поскольку с момента закрытия ЗВР по документам до
        # момента включения в отчет - пройдет некоторое время (и пробег).

        if kwargs:
            logging.info(
                f'🏁 «{kwargs["car_grz"]}». '
                f'🛠️#{service_work.next_service_id} закрыт '
                f'{kwargs["validated_service_work"].request_date.date()} '
                'на пробеге '
                f'{kwargs["validated_service_work"].last_service_reading}'
            )
        else:
            logging.info(f'🫡 🛠️ ТО id#{service_work.id} перенесено в архив.')

        session.add(service_work)


async def _get_active_service_work_with_service_status(
        *,
        organization_id: int,
        service_status_id: int,
        session: AsyncSession,
        need_stats: bool = False
):
    """
    Получение активных сервисных работ в подразделении с расчётным статусом.

    ## Args:
    - need_stats: если указать True - переключается на сбор статистики по
    видам: «пустые», «с открытым ЗВР», «с незакрытым ЗВР» с получением кол-ва.
    """
    stmt = select(
        ServiceWork
    ).join(
        Car
    ).where(
        ServiceWork.request_status_id == service_status_id,
        ServiceWork.in_archive.is_(False),
        Car.organization_id == organization_id,
        Car.in_archive.is_(False)
    )
    total_result = (await session.scalars(stmt)).all()

    # Переключение на сбор данных по группам:
    if need_stats:
        de_facto_completed_stmt = stmt.where(
            ServiceWork.service_work_completed.is_(True)
        )
        zvr_create_stmt = stmt.where(
            ServiceWork.zvr_number,
            ServiceWork.service_work_completed.is_(False)
        )
        de_facto_completed_result = (
            await session.scalars(de_facto_completed_stmt)
        ).all()
        zvr_create_result = (await session.scalars(zvr_create_stmt)).all()

        return {
            'without_zvr':
            len(total_result) - len(de_facto_completed_result)
            - len(zvr_create_result),
            'with_open_zvr': len(zvr_create_result),
            'de_facto_completed': len(de_facto_completed_result)
        }

    return total_result


async def get_active_service_work_count_for_all_service_status(
        organization_id: int,
        session: AsyncSession
) -> dict[str, dict[str, int]]:
    """Получение сводных данных о количестве активных работ по статусам."""
    # Получение списка сервисных статусов:
    service_statuses = await get_multi_service_status(session=session)

    # Подготовка пустого словаря:
    summary_data = {}

    # Перебор и наполнение:
    for service_status in service_statuses:
        value = await _get_active_service_work_with_service_status(
            organization_id=organization_id,
            service_status_id=service_status.id,
            session=session,
            need_stats=True
        )
        summary_data[service_status.name] = value

    return summary_data


async def get_all_active_service_work_with_open_zvr(
        organization_id: int,
        session: AsyncSession
):
    """Получение «зависших» активных сервисных работ."""
    result = await session.scalars(
        select(ServiceWork)
        .join(Car)
        .where(
            Car.organization_id == organization_id,
            ServiceWork.service_work_completed.is_(True),
            ServiceWork.in_archive.is_(False)
        )
    )
    return result.all()


async def _get_service_work_for_car_and_service_name(
        car_id: int,
        service_name_id: int,
        request_status_id: int,
        special_status_ids: list[Optional[int]],
        session: AsyncSession,
        hide_service_work_with_zvr: bool = False
) -> Optional[int]:
    """Получение ID записи ServiceWork если оно соответствует условиям.

    Опция:
        - hide_service_work_with_zvr=True (если нужно скрыть записи с ЗВР)
    """

    # TODO Если ТС в архиве - должен сработать pass

    stmt = select(ServiceWork).join(Car).where(
        Car.id == car_id,
        or_(
            Car.special_status_id.in_(special_status_ids),
            Car.special_status_id.is_(None),
        ),
        ServiceWork.request_status_id <= request_status_id,
        ServiceWork.in_archive.is_(False),
        ServiceWork.next_service_id == service_name_id,
    )

    # Скрыть записи о сервисном обслуживании, если для них уже создан ЗВР:
    if hide_service_work_with_zvr:
        stmt = stmt.where(ServiceWork.zvr_number.is_(None))

    return result if (result := await session.scalar(stmt)) else None


async def create_main_table(
        request_status_id: int,
        special_status_ids: list[Optional[int]],
        organization_id: int,
        session: AsyncSession,
        hide_service_work_with_zvr: bool = False
):
    """Наполнение содержимым главной таблицы."""
    total_data = []
    # Получение списка всех названий сервисных операций:
    # Выстраиваем шапку
    all_service_name = await get_service_name_with_request_status(
        request_status_id=request_status_id,
        special_status_ids=special_status_ids,
        organization_id=organization_id,
        session=session,
        need_range=True
    )

    # Получение списка ТС (выстраиваем строки):
    all_cars = await get_cars_with_request_and_special_status(
        request_status_id=request_status_id,
        special_status_ids=special_status_ids,
        organization_id=organization_id,
        session=session
    )

    for car in all_cars:
        one_row = []
        for service_name in all_service_name:
            if car and service_name:
                one_row.append(
                    await _get_service_work_for_car_and_service_name(
                        car_id=car.id,
                        service_name_id=service_name.id,
                        request_status_id=request_status_id,
                        special_status_ids=special_status_ids,
                        session=session,
                        hide_service_work_with_zvr=hide_service_work_with_zvr
                    )
                )
        total_data.append(one_row)

    return total_data


async def check_users_can_edit_service_work(
        user: User,
        service_work: ServiceWork
) -> None:
    """Проверка полномочий пользователя для внесения изменений.

    Если пользователь имеет права «Только чтение» или он является сотрудником
    другого подразделения - действия невозможны.
    """
    if (
        user.users_role.name == UserRole.READ_ONLY.value
        or service_work.car.organization_id != user.organization_id
    ):
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN,
            detail='Недостаточно прав!'
        )
