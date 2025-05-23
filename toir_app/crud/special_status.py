from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from toir_app.models import SpecialStatus


async def get_all_special_status(session: AsyncSession):
    return await session.scalars(select(SpecialStatus))
