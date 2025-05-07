from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from toir_app.models.service_status import ServiceStatus


async def get_service_status(name: str, session: AsyncSession):
    return await session.scalar(
        select(ServiceStatus)
        .where(
            ServiceStatus.name == name
        )
    )
