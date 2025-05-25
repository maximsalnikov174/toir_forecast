from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from toir_app.core.db import get_async_session
from toir_app.crud.organization import (
    get_organization_list
)
from toir_app.schemas.organization import OrganizationResponse


router = APIRouter()


@router.get(
    '/all',
    response_model=list[OrganizationResponse],
    name='Список подразделений',
    description='Получение списка всех подразделений для отбора по цеху.',
    status_code=200,
)
async def get_all_organization(
    session: AsyncSession = Depends(get_async_session)
):
    """Возвращает список видов ТО с выбранным Присвоенным Статусом."""
    # Проверяем существование выбранного присвоенного статуса в БД:
    return await get_organization_list(session)
