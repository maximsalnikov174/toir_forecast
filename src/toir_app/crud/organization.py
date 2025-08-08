from http import HTTPStatus
from typing import Annotated, Optional, Sequence

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from constants import VEHICLE_ORGANOZATIONS
from exception import StaticDataInDBNotFoundException
from models import Organization


async def get_organization_list(
        session: AsyncSession,
        vehicle_only: bool = False,
) -> Sequence[Organization]:
    """Возврат списка подразделений.

    # Args:
    - `vehicle_only=True` - если нужны ТОЛЬКО подразделения с транспортом.
    """
    query = (
        select(Organization)
        .order_by(Organization.name)  # сортировка по Юхх
    )

    # FIXME Костыль: поиск цеха выполняется, пока УЭ - только Ю5х
    if vehicle_only:
        query = query.where(Organization.name.contains(VEHICLE_ORGANOZATIONS))

    organization_list = await session.scalars(query)
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
