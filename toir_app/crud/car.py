import re
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from toir_app.constants import pattern_grz_input_user
from toir_app.models import Car


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
) -> list[Car]:
    """
    Получаем запись о Car по ГРЗ (без учета пробелов).

    Прогоняем ГРЗ по паттерну А 123 АВ или АВ 1234 74/174/774, после чего
    получаем запись.
    """
    match = re.match(pattern_grz_input_user, grz)
    if not match:
        raise HTTPException(
            status_code=404,
            detail='Проверьте формат ГРЗ!'
        )
    groups_grz = match.groups()
    clear_grz = ' '.join(filter(None, groups_grz))  # убрали None из groups

    cars = await session.scalars(
        select(Car)
        .where(
            # Car.grz.startswith(grz),  # ГРЗ начинается с ...
            Car.grz == clear_grz,
            Car.in_archive.is_(False))
    )
    cars_list = list(cars.all())
    if not cars_list:
        raise HTTPException(
            status_code=404,
            detail='ТС не найдено!'
        )
    return cars_list
