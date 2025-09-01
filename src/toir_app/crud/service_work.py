from collections.abc import Sequence
from datetime import datetime as dt
from http import HTTPStatus
from typing import Annotated, List, Optional

from fastapi import HTTPException
from sqlalchemy import and_, or_, select
from sqlalchemy.sql.expression import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.endpoints.bot import bot_schedular
from constants import PATTERN_DATE_OEBS
from crud.base import DAOBase
from crud.car import (
    get_car_by_pk,
    get_cars_with_request_and_special_status,
)
from crud.service_name import (
    get_service_name_group,
    get_service_name_with_request_status,
    get_service_name_for_master
)
from crud.service_status import dao_service_status
from logger.logger import logger
from models import (
    Car,
    EventForBot,
    Organization,
    ServiceName,
    ServiceStatus,
    ServiceWork,
    SpecialStatus,
    SpecialStatusForCar,
    User,
    UserRole,
)
from schemas.service_work import (
    CarAtributesInServiceWork,
    ServiceWorkBase,
)


class DAOServiceWork(DAOBase[ServiceWork]):
    """DAO для работы с моделью карточек работ."""

    # async def get_with_docs(
    #         self,
    #         obj_id: int,
    #         session: AsyncSession,
    # ) -> Optional[ServiceWork]:
    #     """Получение карточки работы с документами по идентификатору."""
    #     stmt = (
    #         select(self.model)
    #         .options(selectinload(self.model.docs_in_service_work))
    #         .where(self.model.id == obj_id)
    #     )
    #     return await session.scalar(stmt)
    async def get_service_work(
            self,
            obj_id: int,
            session: AsyncSession,
            check_active: bool = True
    ):
        stmt = (
            select(self.model)
            .options(
                selectinload(self.model.car).joinedload(Car.organization),
                selectinload(self.model.station),
                selectinload(self.model.next_service),
            )
            .where(self.model.id == obj_id)
            .limit(1)
        )

        result = await session.scalar(stmt)

        if not result:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=f'Карточка работы #{obj_id} не найдена',
            )

        if check_active and result.in_archive:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail='Указанная работа находится в архиве.'
            )
        return result


dao_service_work = DAOServiceWork(ServiceWork)


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

    stmt = (
        select(ServiceWork)
        .options(
            selectinload(ServiceWork.next_service),
            selectinload(ServiceWork.car),
        )
        .join(ServiceName, ServiceName.id == ServiceWork.last_service_id)
        .where(
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
        ).order_by(ServiceWork.last_service_reading.desc())
        .limit(1)
    )
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
        zvr_number: str,
        session: AsyncSession
) -> None:
    """Проверяет ЗВР на уникальный номер."""
    result = await session.scalar(
        select(ServiceWork)
        .where(ServiceWork.zvr_number.contains(zvr_number))
    )
    if result is not None:
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

    stmt = (
        select(ServiceWork)
        .where(
            ServiceWork.car_id == car_id,
            ServiceWork.in_archive.is_(False)
        ).order_by(
            ServiceWork.next_service_id  # сортировка по ID вида работ
        )
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
        logger.info(f'⏸️ «{car_grz}» : за сутки не пошевелился.')
    else:
        service_work.daily_distance = incoming_data.daily_distance
        service_work.request_reading = incoming_data.request_reading
        logger.info(f'🏃‍➡️ «{car_grz}» : обновился пробег.')
        session.add(service_work)


async def add_service_works_in_archive(
        service_work_list: Sequence[ServiceWork],
        session: AsyncSession,
        **kwargs
):
    """Архивирование (без коммита) записей о ServiceWork."""
    for service_work in service_work_list:
        service_work.in_archive = True
        service_work.service_work_completed = dt.now()
        # TODO Подумать, нужно ли перезаписывать пробег для старой записи
        # Скорее всего НЕТ, поскольку с момента закрытия ЗВР по документам до
        # момента включения в отчет - пройдет некоторое время (и пробег).

        if kwargs:
            # Отправка сообщения в тред цеха телеги:
            await bot_schedular.send_notification(
                obj=service_work,
                event=EventForBot.CLOSE,
            )

            logger.info(
                f'🏁 «{kwargs["car_grz"]}». '
                f'🛠️ {service_work.next_service.name} закрыт '
                f'{kwargs["validated_service_work"].request_date.date()} '
                'на пробеге '
                f'{kwargs["validated_service_work"].last_service_reading}'
            )
        else:
            logger.info(f'🫡 🛠️ ТО id#{service_work.id} перенесено в архив.')

        session.add(service_work)


async def _get_active_service_work_with_service_status(
        *,
        organization_id: Annotated[int, Organization.id],
        service_status_id: Annotated[int, ServiceStatus.id],
        special_status_list: List[Annotated[int, SpecialStatus.id]],
        session: AsyncSession,
        need_stats: bool = False
):
    """
    Получение активных сервисных работ в подразделении с расчётным статусом.

    ## Args:
    - special_status_list: если нужно к ТС без статусов добавить, например,
    находящиеся на ВР ТС;
    - need_stats: если указать True - переключается на сбор статистики по
    видам: «пустые», «с открытым ЗВР», «с незакрытым ЗВР» с получением кол-ва.
    """
    stmt = (
        select(ServiceWork)
        .join(ServiceWork.car)
        .outerjoin(Car.status_associations)
        .where(
            ServiceWork.request_status_id == service_status_id,
            ServiceWork.in_archive.is_(False),
            Car.organization_id == organization_id,
            Car.in_archive.is_(False),
            or_(
                Car.status_associations == None,
                SpecialStatusForCar.special_status_id.in_(special_status_list)
            )
        )
    )
    total_result = (await session.scalars(stmt)).all()

    # Переключение на сбор данных по группам:
    if need_stats:
        de_facto_completed_stmt = stmt.where(
            ServiceWork.service_work_completed.is_not(None)
        )
        zvr_create_stmt = stmt.where(
            ServiceWork.zvr_number.is_not(None),
            ServiceWork.service_work_completed.is_(None)
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
        organization_id: Annotated[int, Organization.id],
        special_status_list: List[Annotated[int, SpecialStatus.id]],
        session: AsyncSession
) -> dict[str, dict[str, int]]:
    """Получение сводных данных о количестве активных работ по статусам."""
    # Получение списка сервисных статусов:
    service_statuses = await dao_service_status.get_multi(
        session=session,
        sorted_param='id',
    )

    # Подготовка пустого словаря:
    summary_data = {}

    # Перебор и наполнение:
    for service_status in service_statuses:
        value = await _get_active_service_work_with_service_status(
            organization_id=organization_id,
            service_status_id=service_status.id,
            special_status_list=special_status_list,
            session=session,
            need_stats=True
        )
        summary_data[service_status.name] = value

    return summary_data


async def get_all_active_service_work_with_open_zvr(
        organization_id: Annotated[int, Organization.id],
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
        car_id: Annotated[int, Car.id],
        service_name_id: Annotated[int, ServiceName.id],
        session: AsyncSession,
        user: Optional[User] = None,
        station_id: Optional[int] = None,
        hide_service_work_with_zvr: bool = False,
        request_status_id: Optional[Annotated[int, ServiceStatus.id]] = None,
        special_status_ids: Optional[
            list[Optional[Annotated[int, SpecialStatus.id]]]
        ] = None,
) -> Optional[ServiceWork]:
    """Получение ID записи ServiceWork если оно соответствует условиям.

    ## Args:
    - `station_id`: если нужно собрать `service_work` для конкретного СТО;
    - `hide_service_work_with_zvr = True`: если нужно скрыть запись с ЗВР;
    - `request_status_id`: когда нужно получить `service_work` строже
        определенного статуса;
    - `special_status_ids`: когда нужно учесть установленные для ТС
        специальные статусы.
    """

    # TODO Если ТС в архиве - должен сработать pass

    stmt = (
        select(ServiceWork)
        .options(
            selectinload(ServiceWork.station)
        )
        .join(ServiceWork.car)
        .where(
            ServiceWork.in_archive.is_(False),
            ServiceWork.next_service_id == service_name_id,
            Car.id == car_id,
        )
    )

    # Собираем для мастерской:
    if station_id and user:
        stmt = stmt.where(ServiceWork.station_id == station_id)

        if user.users_role.name == UserRole.MASTER.value:
            # - поле «работа завершена фактически» не заполнено
            stmt = stmt.where(ServiceWork.service_work_completed.is_(None))

        elif user.users_role.name == UserRole.OPERATOR.value:
            # - поле «работа завершена фактически» не пустое
            stmt = stmt.where(ServiceWork.service_work_completed.is_not(None))

    # Собираем для цеха перевозки:
    else:
        stmt = (
            stmt
            .outerjoin(Car.status_associations)
            .where(
                ServiceWork.request_status_id <= request_status_id,
                or_(
                    Car.status_associations == None,  # может .is_(None)?
                    SpecialStatusForCar.special_status_id.in_(
                        special_status_ids
                    )
                )
            )
        )

        # Скрыть записи о сервисном обслуживании, если для них уже создан ЗВР:
        if hide_service_work_with_zvr:
            stmt = stmt.where(ServiceWork.zvr_number.is_(None))

    return result if (result := await session.scalar(stmt)) else None


async def create_main_table_for_master(
        user: User,
        session: AsyncSession,
):
    """Наполнение содержимым главной таблицы для мастерских."""
    users_station = user.users_organization.station_id
    total_data = []
    # Получение списка всех названий сервисных операций:
    # Выстраиваем шапку
    all_service_name = await get_service_name_for_master(
        station_id=users_station,
        user=user,
        session=session,
    )

    # Получение списка ТС (выстраиваем строки):
    all_cars = await get_cars_with_request_and_special_status(
        for_masters=True,
        organization_id=users_station,
        session=session,
        user=user,
    )

    for car in all_cars:
        one_row = []
        for service_name in all_service_name:
            if car and service_name:
                one_row.append(
                    await _get_service_work_for_car_and_service_name(
                        car_id=car.id,
                        service_name_id=service_name.id,
                        station_id=users_station,
                        session=session,
                        user=user,
                    )
                )
        total_data.append(one_row)

    return total_data


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
        need_range=True,
        hide_service_work_with_zvr=hide_service_work_with_zvr
    )

    # Получение списка ТС (выстраиваем строки):
    all_cars = await get_cars_with_request_and_special_status(
        request_status_id=request_status_id,
        special_status_ids=special_status_ids,
        organization_id=organization_id,
        session=session,
        hide_service_work_with_zvr=hide_service_work_with_zvr
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


def check_users_can_edit_service_work(
        user: User,
        service_work: ServiceWork,
        *,
        for_station: bool = False,
        operator_leniency: bool = False
):
    """Проверка полномочий юзера для редактирования карточки `ServiceWork`.

    Args:
    -----
    - `for_station` если у пользователя нужно проверить связь с мастерской при
    наступлении события, когда ранее выбранная механиком в карточке
    `servise_work` `station_id` сверяется с `station_id` связанной
    с `organization_id` пользователя;
    - `operator_leniency` понижение уровня проверки для оператора.

    ## Важно:
    - ЛЮБОЙ `user` должен быть валидирован админом (`is_verified=True`).
    - Если `user` имеет права `READ_ONLY` или он является сотрудником
    другого `organization` (подразделения) - действия невозможны.
    """
    if not user.is_verified:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN,
            detail=(
                'Требуется подтверждение аккаунта пользователя '
                'администратором!'
            )
        )

    # Проверка роли "только чтение" (кроме суперюзеров)
    if (
        user.users_role.name == UserRole.READ_ONLY.value
        and not user.is_superuser
    ):
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN,
            detail='Недостаточно прав!'
        )

    # Проверка принадлежности к подразделению (кроме суперюзеров)
    if not user.is_superuser:

        if for_station:
            # Ограничиваем доступ к редактированию операторам:
            if (
                user.users_role.name == UserRole.OPERATOR.value
                and not operator_leniency  # ПРОВЕРИТЬ РАБОТУ!!!
            ):
                raise HTTPException(
                    status_code=HTTPStatus.FORBIDDEN,
                    detail='Недостаточно прав! Оператор только получает данные'
                )

            # Для мастера: проверка станции
            if (
                service_work.station_id and user.users_organization and
                service_work.station_id != user.users_organization.station_id
            ):
                raise HTTPException(
                    status_code=HTTPStatus.FORBIDDEN,
                    detail='Недостаточно прав! Нужна «Мастерская»'
                )
        else:
            # Для обычного пользователя: проверка организации
            if (
                service_work.car and service_work.car.organization_id and
                service_work.car.organization_id != user.organization_id
            ):
                raise HTTPException(
                    status_code=HTTPStatus.FORBIDDEN,
                    detail='Недостаточно прав! Нужен «перевозчик»!'
                )


def check_user_can_add_docs_in_service_work(user: User):
    """Проверка полномочий юзера для добавления материалов в «накладной»."""
    if (
        user.users_role.name != UserRole.MASTER.value
        and not user.is_superuser
    ):
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN,
            detail='Недостаточно прав! Накладную может вложить «мастер»!'
        )


async def get_db_status(session: AsyncSession) -> dict[str, str]:
    """Получение состояния об актуальности данных по ServiceWork."""
    max_date = await session.scalar(select(func.max(ServiceWork.request_date)))
    return {
        'current_db_status': (
            f'Актуально на {max_date.strftime(PATTERN_DATE_OEBS)}'
        )
    }


async def zvr_delete(
        service_work_id: Annotated[int, ServiceWork.id],
        user: User,
        session: AsyncSession
) -> Optional[ServiceWork]:
    """Удаление ЗВР из `service_work`.

    PERMISSION
    ----------
    - Верифицированный сотрудник подразделения-перевозчика или суперюзер.

    DETAIL
    ------
    Очищаются следующие поля:
    - zvr_number;
    - zvr_create_date;
    - station_id;
    - service_work_completed.
    """
    service_work = (
        await dao_service_work.get_service_work(service_work_id, session)
    )

    if service_work:
        check_users_can_edit_service_work(
            user=user,
            service_work=service_work,
        )
        if not service_work.zvr_number:
            raise HTTPException(
                status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                detail='ЗВР для данной работы нет.'
            )

    try:
        service_work.zvr_number = None
        service_work.zvr_create_date = None
        service_work.station_id = None
        service_work.service_work_completed = None

        await session.commit()
        await session.refresh(service_work)
        return service_work

    except Exception as e:
        await session.rollback()
        raise HTTPException(
            HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=(
                f'Непредвиденная ошибка случилась: {str(e)}'
            )
        )


async def update_completed_real_service_work(
        add_date: bool,
        service_work_id: Annotated[int, ServiceWork.id],
        user: User,
        session: AsyncSession
):
    """Обновление `service_work_completed` (фактического завершения работ)

    Для `service_work`, которые были фактически сделаны (только мастерская).

    ARGS
    ----
    - `add_date=True` чтобы зафиксировать текущее (на момент запроса) время.
    """
    service_work = (
        await dao_service_work.get_service_work(service_work_id, session)
    )

    if service_work:
        check_users_can_edit_service_work(
            user=user,
            service_work=service_work,
            for_station=True
        )
        if not service_work.zvr_number:
            raise HTTPException(
                status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                detail='Сначала необходимо добавить ЗВР.'
            )

    try:
        value = dt.now() if add_date else None
        service_work.service_work_completed = value
        await session.commit()
        await session.refresh(service_work)  # Опционально

    except Exception as e:
        await session.rollback()
        raise HTTPException(
            HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=(
                'Ошибка при указании информации'
                f'о фактическом завершении работ: {str(e)}'
            )
        )
    return service_work
