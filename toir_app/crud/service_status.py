from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from toir_app.models.service_status import ServiceStatus


async def get_service_status_by_name(name: str, session: AsyncSession):
    return await session.scalar(
        select(ServiceStatus)
        .where(ServiceStatus.name == name)
    )


async def get_service_status_by_id(id: int, session: AsyncSession):
    return await session.get(ServiceStatus, id)
    # return await session.scalar(
    #     select(ServiceStatus)
    #     .where(ServiceStatus.id == id)
    # )


async def check_exist_service_status_by_id(
        id: int, session: AsyncSession
) -> Optional[int]:
    """Проверяет существование service_status по ID."""
    return await session.scalar(
        select(ServiceStatus.id)
        .where(ServiceStatus.id == id)
        .exists()
        .select()
    )
