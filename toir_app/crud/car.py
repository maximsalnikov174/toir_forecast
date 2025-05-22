import re
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from toir_app.constants import pattern_grz_input_user
from toir_app.models import Car, ServiceWork


async def get_car_by_personal_id(
        personal_id: int,
        session: AsyncSession
) -> Optional[Car]:
    """Получаем запись о Car по OeBS personal_id."""
    return await session.scalar(
        select(Car).where(Car.personal_id == personal_id)
    )


async def get_car_by_full_grz(
        grz: str,
        session: AsyncSession
) -> Car:
    """
    Получаем запись о Car по ГРЗ (без учета пробелов).

    Прогоняем ГРЗ по паттерну А 123 АВ или АВ 1234 74/174/774, после чего
    получаем запись.
    """
    match = re.match(pattern_grz_input_user, grz.upper())
    if not match:
        raise HTTPException(
            status_code=404,
            detail='Проверьте формат ГРЗ!'
        )
    groups_grz = match.groups()
    clear_grz = ' '.join(filter(None, groups_grz))  # убрали None из groups

    car = await session.scalar(
        select(Car)
        .where(
            # Car.grz.startswith(grz),  # ГРЗ начинается с ...
            Car.grz == clear_grz,
            Car.in_archive.is_(False))
    )
    if not car:
        raise HTTPException(
            status_code=404,
            detail='ТС не найдено!'
        )
    return car


async def get_cars_with_request_status(
    request_status_id: int,
    organization_id: int,
    session: AsyncSession
) -> list[Optional[Car]]:
    """
    Возврат УНИКАЛЬНЫХ машин c выбранным Присвоенным статусом.
    """
    cars = await session.execute(
        select(Car, ServiceWork)
        .join(ServiceWork, Car.id == ServiceWork.car_id)
        .where(
            ServiceWork.request_status_id == request_status_id,
            Car.organization_id == organization_id,
            Car.in_archive.is_(False)
        ).distinct()  # distinct - дедупликация.
        .order_by(Car.grz)
    )
    return list(cars.scalars().all())
