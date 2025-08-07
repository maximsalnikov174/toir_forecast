from http import HTTPStatus

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_async_session
from crud.organization import (
    get_current_organization,
    get_organization_list,
)
from schemas.organization import OrganizationResponse

router = APIRouter()


@router.get(
    '/all',
    response_model=list[OrganizationResponse],
    name='Получение списка подразделений (на выбор пользователю)',
    description='Получение списка всех подразделений для отбора по цеху.',
    status_code=HTTPStatus.OK,
)
async def get_all_organization(
    session: AsyncSession = Depends(get_async_session)
):
    """Возвращает список всех подразделений."""
    return await get_organization_list(session)


@router.get(
    '/with_vehicles',
    response_model=list[OrganizationResponse],
    name='Получение списка подразделений (на выбор пользователю)',
    description='Получение списка всех подразделений для отбора по цеху.',
    status_code=HTTPStatus.OK,
)
async def get_all_vehicles_organization(
    session: AsyncSession = Depends(get_async_session)
):
    """Возвращает список всех подразделений."""
    return await get_organization_list(session, vehicle_only=True)


@router.get(
    '/{organization_id}',
    response_model=OrganizationResponse,
    name='Получение информации о выбранном пользователем подразделении',
    description='Получение подразделения для отбора по цеху.',
    status_code=HTTPStatus.OK,
)
async def get_organization(
    organization_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    """Возвращает выбранное пользователем подразделение."""
    return await get_current_organization(organization_id, session)
