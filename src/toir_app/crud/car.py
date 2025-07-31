import re
from datetime import date, timedelta
from http import HTTPStatus
from typing import Annotated, Any, Optional

from fastapi import HTTPException
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from constants import MAX_SPECIAL_STATUS_VALID, pattern_grz_input_user
from logger.logger import logger
from models import (
    Car,
    ServiceWork,
    SpecialStatus,
    SpecialStatusForCar,
    User,
)
from schemas.car import CarToDownloadInDB
from schemas.car_model import CarModelID
from schemas.organization import OrganizationID


async def get_car_by_personal_id(
        personal_id: int,
        session: AsyncSession
) -> Optional[Car]:
    """Получаем запись о Car по OeBS personal_id."""
    return await session.scalar(
        select(Car).where(Car.personal_id == personal_id)
    )


async def get_car_by_pk(
        car_id: int,
        session: AsyncSession,
        check_car_in_archive: bool = True,
        expand_data: bool = False
) -> Optional[Car]:
    """Получаем запись о Car по PK.

    ### Args:
    - check_car_in_archive: проверяет ТС, переведенные в архив;
    - expand_data: получение связанных данных(специальные статусы ТС).

    ### Returns:
        - объект модели Car

    ### Exceptions:
        - 404 если ТС не найдено
        - 400 если ТС находится в архиве
    """
    if expand_data:
        car = await session.scalar(
            select(Car)
            .options(selectinload(Car.status_associations))
            .where(Car.id == car_id)
        )
    else:
        car = await session.get(Car, car_id)

    if not car:
        raise HTTPException(HTTPStatus.NOT_FOUND, 'ТС не найдено')

    elif check_car_in_archive and car.in_archive:
        raise HTTPException(
            HTTPStatus.BAD_REQUEST,
            'ТС находится в архиве, действие невозможно'
        )

    return car


async def get_all_active_car_list(
        session: AsyncSession
) -> list[Car.id]:
    """Получаем список ID всех активных Car (со статусом «не в архиве»)."""
    result = await session.scalars(
        select(Car.id)
        .where(Car.in_archive.is_(False))
    )
    return list(result)


async def push_cars_in_archive(
        cars_in_file: set[int],
        session: AsyncSession
) -> set[int]:
    """Сбор всех непереданных в отчёте RMT321 ТС и перевод их в архив."""
    car_list_in_db = await get_all_active_car_list(session=session)
    cars_list_in_archive = set(car_list_in_db) - set(cars_in_file)

    if cars_list_in_archive:
        logger.info(f'Начало архивирования {len(cars_list_in_archive)} ТС:')

        for car_id in cars_list_in_archive:
            await add_car_in_archive(car_id=car_id, session=session)

        logger.info(
            f'Архивирование {len(cars_list_in_archive)} ТС завершено.'
        )

    # await session.commit()
    return cars_list_in_archive


async def add_car_in_archive(
        car_id: int,
        session: AsyncSession
) -> None:
    """Архивирование (без коммита) Car."""
    car: Optional[Car] = await get_car_by_pk(car_id=car_id, session=session)
    if car:
        car.in_archive = True
        session.add(car)
        logger.info(f'🫡 🚚 ТС «{car.grz}» перенесено в архив.')


async def get_car_by_full_grz(
        grz: str,
        session: AsyncSession
) -> Car:
    """
    Получаем запись о Car по ГРЗ (без учета пробелов).

    Прогоняем ГРЗ по паттерну А 123 АВ или АВ 1234 74/174/774, после чего
    получаем запись.

    Exceptions:
        - 404 если указанный ГРЗ не соответствует базовым паттернам ГРЗ.
        - 404 если ТС с указанным валидным ГРЗ не найден.
    """
    match = re.match(pattern_grz_input_user, grz.upper())
    if not match:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Проверьте формат ГРЗ!'
        )
    groups_grz = match.groups()
    clear_grz = ' '.join(filter(None, groups_grz))  # убрали None из groups

    car = await session.scalar(
        select(Car)
        .where(
            # Car.grz.startswith(grz),  # ГРЗ начинается с ...
            Car.grz == clear_grz,
            Car.in_archive.is_(False)
        ).options(
            joinedload(Car.organization),
            joinedload(Car.car_model),
            joinedload(Car.status_associations)
        )
    )
    if not car:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='ТС не найдено!'
        )
    return car


async def get_cars_with_request_and_special_status(
    request_status_id: int,
    special_status_ids: list[Optional[int]],
    organization_id: int,
    session: AsyncSession,
    hide_service_work_with_zvr: bool = False
) -> list[Optional[Car]]:
    """
    Возврат УНИКАЛЬНЫХ машин c учётом выбранных пользователем фильтров.

    Filters:
        - расчётный статус (он и строже)
        - все ТС без статусов (FIXME пока обязательно)
        - список специальных статусов (опционально)
    """
    stmt = (
        select(Car)
        .options(
            selectinload(Car.car_model),
            selectinload(Car.status_associations),
            selectinload(Car.service_works)
        )
        .join(Car.service_works)  # Явное соед. с service_works
        .outerjoin(Car.status_associations)  # OUTER JOIN: статусы могут отс.
        .where(
            ServiceWork.request_status_id <= request_status_id,
            Car.organization_id == organization_id,
            Car.in_archive.is_(False),
            or_(
                SpecialStatusForCar.id.is_(None),
                SpecialStatusForCar.special_status_id.in_(special_status_ids)
            )
        ).distinct()  # distinct - дедупликация (FIXME не уверен, что так)
        .order_by(Car.grz)
    )

    # Скрыть записи о сервисном обслуживании, если для них уже создан ЗВР:
    if hide_service_work_with_zvr:
        stmt = stmt.where(ServiceWork.zvr_number.is_(None))

    cars = await session.execute(stmt)

    return list(cars.unique().scalars().all())  # получение уникальных cars


async def add_special_status_to_car(
        special_status_id: int,
        car_id: int,
        user: User,
        date_from_user: date,
        session: AsyncSession,
        comment: Optional[str] = None
) -> Optional[Car]:
    """Устанавливает специальный статус для ТС.

    Returns:
        - объект модели Car.
        - None.

    Exceptions:
        - 400 если выбранный статус и так равен текущему.
        - 403 если у пользователя недостаточно прав.
        - 404 если ID выбранного статуса нет в списке статусов.
        - 500 если случились прочие проблемы.
    """
    if date_from_user <= date.today():
        raise HTTPException(HTTPStatus.BAD_REQUEST, 'Укажите дату в будущем!')
    elif date_from_user >= date.today() + timedelta(MAX_SPECIAL_STATUS_VALID):
        raise HTTPException(
            HTTPStatus.BAD_REQUEST,
            'Давайте так: специальный статус для ТС действует '
            f'не больше {MAX_SPECIAL_STATUS_VALID} дней!'
        )

    # Проверяем, существует ли car и special_status:
    if not await session.get(SpecialStatus, special_status_id):
        raise HTTPException(HTTPStatus.NOT_FOUND, 'Статус не найден')

    car = await get_car_by_pk(car_id, session, expand_data=True)

    if car:

        if (
            car.organization_id != user.organization_id
            and not user.is_superuser
        ):
            raise HTTPException(
                HTTPStatus.FORBIDDEN,
                'Только пользователь подразделения или суперпользователь'
            )

        active_status_car = {
            elem.special_status_id: elem.date_left
            for elem in car.status_associations
            if elem.is_active
        }

        if special_status_id in active_status_car.keys():
            raise HTTPException(
                HTTPStatus.BAD_REQUEST,
                'Выбранный статус ТС уже назначен '
                f'и действует до {active_status_car[special_status_id]}'
            )

        try:
            element = SpecialStatusForCar()
            element.car_id = car_id
            element.special_status_id = special_status_id
            element.assigned_by_user_id = user.id
            element.comment = comment
            element.date_left = date_from_user
            element.is_active = True
            session.add(element)
            await session.commit()

            # Обновляем объект из БД
            await session.refresh(car)
        except Exception as e:
            await session.rollback()
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail=f'Ошибка при обновлении статуса ТС: {str(e)}'
            )

        # car = await get_car_by_pk(car.id, session, expand_data=True)
        return car

    return None


async def get_car_history(
        car_id: Annotated[int, Car.id],
        session: AsyncSession
):
    """Получение истории по выполненным сервисным обслуживаниям для ТС."""
    await get_car_by_pk(car_id=car_id, session=session)

    return await session.scalars(
        select(ServiceWork)
        .join(ServiceWork.car)
        .where(
            Car.id == car_id,
            ServiceWork.in_archive.is_(True)
        ).order_by(
            ServiceWork.request_reading,
            ServiceWork.last_service_id  # чтоб всегда был один порядок
        )
    )


async def get_or_create_car_and_return_id(
    session: AsyncSession,
    personal_id: int,
    grz: str,
    car_model: CarModelID,
    organization: OrganizationID
) -> tuple[int, str]:
    """Получает экземпляр модели Car или создает его (автомобиль)."""
    car_in_db = await get_car_by_personal_id(personal_id, session)

    if not car_in_db:
        # загоняем в pydantic-схему:
        validated_car = CarToDownloadInDB(
            personal_id=personal_id,
            grz=grz,
            car_model_id=car_model.id,
            organization_id=organization.id
        )
        new_car: dict[str, Any] = validated_car.model_dump()

        # создаем экземпляр модели Car и добавляем в сессию:
        car: Car = Car(**new_car)
        session.add(car)
        await session.commit()
        await session.refresh(car)
        logger.info(f'🚚 «{car.grz}» создано.')
        return car.id, car.grz

    else:
        # Проверяем прописку ТС в подразделении:
        if car_in_db.organization_id != organization.id:
            car_in_db.organization_id = organization.id
            logger.info(f'ТС {grz} изменило прописку на {organization}')
            session.add(car_in_db)

    return car_in_db.id, car_in_db.grz
