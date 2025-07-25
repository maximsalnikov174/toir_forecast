from datetime import date, timedelta

from sqlalchemy import ScalarResult, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from logger.logger import logger
from models import SpecialStatus, SpecialStatusForCar


async def get_all_special_status(session: AsyncSession):
    return await session.scalars(select(SpecialStatus))


async def deactivate_special_status_for_car(
        special_status_for_car: SpecialStatusForCar,
        session: AsyncSession
) -> None:
    """Деактивирует специальный статус для карточки (без commit)."""
    special_status_for_car.is_active = False
    session.add(special_status_for_car)


async def get_special_status_for_car_list_where_left_yesterday(
        session: AsyncSession
) -> ScalarResult[SpecialStatusForCar]:
    """Получение карточек специальных статусов с истекшим сроком действия."""
    return await session.scalars(
        select(SpecialStatusForCar)
        .options(
            joinedload(SpecialStatusForCar.car),
            joinedload(SpecialStatusForCar.special_status)
        ).where(
            SpecialStatusForCar.date_left <= date.today() - timedelta(1),
            SpecialStatusForCar.is_active.is_(True)
        )
    )


async def deactivate_list_of_special_status_for_car(
        session: AsyncSession
) -> None:
    """Деактивирует список карточек специальных статусов для ТС.

    ## Detail:
    - Карточки имеют истекший срок действия.
    - Выполняется commit внутри функции.
    """
    cards = (await get_special_status_for_car_list_where_left_yesterday(
        session)).all()
    for card in cards:
        await deactivate_special_status_for_car(
            special_status_for_car=card,
            session=session
        )
        logger.info(
            f'Закрыт статус «{card.special_status.name}» для «{card.car.grz}».'
        )

    await session.commit()
