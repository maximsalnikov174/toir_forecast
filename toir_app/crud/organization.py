from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from toir_app.models import Organization


async def get_organization_list(session: AsyncSession) -> list[Organization]:
    """Возврат списка подразделений."""
    organization_list = await session.scalars(
        select(Organization)
        # .where(ServiceWork.request_status_id == request_status_id)
        .order_by(Organization.name)  # сортировка по Юхх
    )
    return organization_list.all()
