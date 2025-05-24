from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from toir_app.models import ServiceName, ServiceWork


async def get_service_name_with_request_status(
    request_status_id: int,
    session: AsyncSession
) -> list[Optional[ServiceName]]:
    """
    Возврат УНИКАЛЬНЫХ видов ТО c выбранным Присвоенным статусом.
    """
    service_names = await session.execute(
        select(ServiceName)
        .join(ServiceWork, ServiceName.id == ServiceWork.next_service_id)
        .where(ServiceWork.request_status_id == request_status_id)
        .distinct()  # distinct - дедупликация
        .order_by(ServiceName.id)  # сортировка по ID вида работ
    )
    return list(service_names.scalars().all())
