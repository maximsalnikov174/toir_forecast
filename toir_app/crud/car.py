import re
from typing import Optional
from http import HTTPStatus

from fastapi import HTTPException
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, contains_eager

from toir_app.constants import pattern_grz_input_user
from toir_app.models import Car, ServiceWork, SpecialStatus, User


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
        session: AsyncSession
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
    elif car.in_archive is True:
        raise HTTPException(
            HTTPStatus.BAD_REQUEST,
            'ТС находится в архиве, действие невозможно'
        )

    return car


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
            car.special_status_id = special_status_id
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
