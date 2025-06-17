import logging
import re
from http import HTTPStatus
from typing import Annotated, Any, Optional

from fastapi import HTTPException
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import contains_eager, joinedload

from toir_app.constants import pattern_grz_input_user
from toir_app.models import Car, ServiceWork, SpecialStatus, User
from toir_app.schemas.car import CarToDownloadInDB
from toir_app.schemas.car_model import CarModelID
from toir_app.schemas.organization import OrganizationID


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
        check_car_in_archive: bool = True
) -> Optional[Car]:
    """Получаем запись о Car по PK.

    Returns:
        - объект модели Car

    Exceptions:
        - 404 если ТС не найдено
        - 400 если ТС находится в архиве
    """
    car = await session.get(Car, car_id)

    if not car:
        raise HTTPException(HTTPStatus.NOT_FOUND, 'ТС не найдено')

    # FIXME сравнить результаты car.in_archive is True и car.in_archive
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
        select(Car.id).where(Car.in_archive.is_(False))
    )
    return list(result)


async def push_cars_in_archive(
        cars_in_file: set[int],
        session: AsyncSession
) -> set[int]:
    """Сбор всех непереданных в отчёте RMT321 ТС и перевод их в архив."""
    car_list_in_db = await get_all_active_car_list(session=session)
    cars_list_in_archive = set(car_list_in_db) - set(cars_in_file)

    for car_id in cars_list_in_archive:
        await add_car_in_archive(car_id=car_id, session=session)

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
        logging.info(f'🫡 🚚 ТС «{car.grz}» перенесено в архив.')


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
            joinedload(Car.car_model)
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
    session: AsyncSession
    # ) -> list[Optional[CarExpandWithIndicators]]:
) -> list[Optional[Car]]:
    """
    Возврат УНИКАЛЬНЫХ машин c учётом выбранных пользователем фильтров.

    Filters:
        - расчётный статус (он и строже)
        - все ТС без статусов (FIXME пока обязательно)
        - список специальных статусов (опционально)
    """
    cars = await session.execute(
        select(Car)
        .join(ServiceWork, Car.id == ServiceWork.car_id)
        .options(contains_eager(Car.service_works))  # жадный подгруз ServWork
        .where(
            ServiceWork.request_status_id <= request_status_id,
            Car.organization_id == organization_id,
            Car.in_archive.is_(False),
            or_(
                Car.special_status_id.is_(None),
                Car.special_status_id.in_(special_status_ids)
            )
        ).distinct()  # distinct - дедупликация (FIXME не уверен, что так)
        .order_by(Car.grz)
    )
    return list(cars.unique().scalars().all())  # получение уникальных cars


async def add_special_status_to_car(
        special_status_id: int,
        car_id: int,
        user: User,
        session: AsyncSession
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
    # Проверяем, существует ли car и special_status:
    if not await session.get(SpecialStatus, special_status_id):
        raise HTTPException(HTTPStatus.NOT_FOUND, 'Статус не найден')

    car = await get_car_by_pk(car_id, session)

    if car:

        if (
            car.organization_id != user.organization_id
            and not user.is_superuser
        ):
            raise HTTPException(
                HTTPStatus.FORBIDDEN,
                'Только пользователь подразделения или суперпользователь'
            )

        if special_status_id == car.special_status_id:
            raise HTTPException(
                HTTPStatus.BAD_REQUEST, 'Выбранный статус и так равен текущему'
            )

        try:
            # Устанавливаем статус
            car['special_status_id'] = special_status_id
            await session.commit()

            # Обновляем объект из БД
            await session.refresh(car)
        except Exception as e:
            await session.rollback()
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail=f'Ошибка при обновлении статуса ТС: {str(e)}'
            )

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
        .join(Car)
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
        logging.info(f'🚚 «{car.grz}» создано.')
        return car.id, car.grz

    return car_in_db.id, car_in_db.grz
