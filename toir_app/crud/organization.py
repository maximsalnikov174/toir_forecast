from http import HTTPStatus
from typing import Annotated, Optional, Sequence

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from toir_app.exception import StaticDataInDBNotFoundException
from toir_app.models import Organization


async def get_organization_list(
        session: AsyncSession
) -> Sequence[Organization]:
    """Возврат списка подразделений."""
    organization_list = await session.scalars(
        select(Organization)
        .order_by(Organization.name)  # сортировка по Юхх
    )
    return organization_list.all()


async def get_current_organization(
        organization_id: Annotated[int, Organization.id],
        session: AsyncSession
) -> Optional[Organization]:
    """Возврат выбранного подразделения."""
    organization = await session.scalar(
        select(Organization)
        .where(Organization.id == organization_id)
    )
    if not organization:
        raise HTTPException(
            HTTPStatus.NOT_FOUND,
            detail=f'Подразделение с ID={organization_id} не найдено'
        )
    return organization


# get_current_organization_dep = Annotated[
#     Organization, Depends(get_current_organization)
# ]


async def get_organization_by_name(
        name: Annotated[str, Organization.name],
        session: AsyncSession
) -> Optional[Organization]:
    organization = (await session.execute(
        select(Organization)
        .where(Organization.name == name)
    )).scalar_one_or_none()
    if organization:
        return organization
    raise StaticDataInDBNotFoundException(
        HTTPStatus.NOT_FOUND,
        detail=f'Подразделение {name} не найдено'
    )
