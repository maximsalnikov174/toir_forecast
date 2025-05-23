from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from toir_app.models import ServiceWork
from toir_app.schemas.service_work import CarAtributesInServiceWork


async def get_service_work(
        service_work_id: int,
        session: AsyncSession
) -> Optional[ServiceWork]:
    return await session.get(ServiceWork, service_work_id)


async def get_last_service_with_current_service_id(
        car_id: int,
        last_service_id: int,
        session: AsyncSession
):
    """
    Возвращает последнюю (свежую) запись сервисного обслуживания.

    Args:
    - car_id : ID выбранного ТС
    - last_service_id : ID вида обслуживания, для которого выполняется поиск

    Returns:
    - оbj(ServiceWork)
    """
    return await session.scalar(
        select(ServiceWork).where(
            ServiceWork.car_id == car_id,
            ServiceWork.last_service_id == last_service_id,
        ).order_by(
            ServiceWork.last_service_reading.desc()
        ).limit(1)
    )


async def get_last_request_reading_by_car(
        car_id: int,
        session: AsyncSession
):
    """Данные о машине (общий и суточный пробеги)."""
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
) -> bool:
    """Проверяет ЗВР на уникальный номер."""
    result = await session.scalar(
        select(ServiceWork)
        .where(ServiceWork.zvr_number == zvr_number)
    )
    return True if result else False
