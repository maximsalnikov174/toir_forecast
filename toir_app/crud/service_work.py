from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from toir_app.models.service_work import ServiceWork


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
    await session.scalar(
        select(ServiceWork).where(
            ServiceWork.car_id == car_id,
            ServiceWork.last_service_id == last_service_id,
        ).order_by(
            ServiceWork.last_service_reading.desc()
        ).limit(1)
    )
