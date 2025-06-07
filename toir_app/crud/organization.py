from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from toir_app.models import Organization


async def create_superuser_organization(session: AsyncSession) -> int:
    """Создание организации для суперпользователя.

    Returns:
    - Organization.id
    """
    admin_organization_data = {'name': 'Ю80'}
    admin_organization = Organization(**admin_organization_data)
    session.add(admin_organization)
    await session.commit()
    await session.refresh(admin_organization)
    return admin_organization.id


async def get_organization_list(session: AsyncSession) -> list[Organization]:
    """Возврат списка подразделений."""
    organization_list = await session.scalars(
        select(Organization)
        .order_by(Organization.name)  # сортировка по Юхх
    )
    return organization_list.all()


async def get_current_organization(
        organization_id: int,
        session: AsyncSession
) -> Organization:
    """Возврат выбранного подразделения."""
    organization = await session.scalars(
        select(Organization)
        .where(Organization.id == organization_id)
        .order_by(Organization.name)  # сортировка по Юхх
    )
    return organization.first()
