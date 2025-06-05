from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from toir_app.core.db import get_async_session
from toir_app.crud.organization import (
    get_organization_list,
    get_current_organization
)
from toir_app.schemas.organization import OrganizationResponse


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
    organization = await get_current_organization(organization_id, session)
    if not organization:
        raise HTTPException(
            HTTPStatus.NOT_FOUND,
            detail=f'Подразделение с ID={organization_id} не найдено'
        )
    return organization
