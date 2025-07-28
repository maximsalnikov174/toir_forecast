from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_async_session
from crud.service_status import (
    get_multi_service_status,
)
from schemas.service_status import ServiceStatusSchema

router = APIRouter()


@router.get(
    '/all',
    response_model=list[ServiceStatusSchema],
    name=('Список расчётных статусов (доступно всем)'),
    description=(
        'Получение списка всех расчётных статусов для сервисного'
        ' обслуживания.'
    ),
    status_code=200,
)
async def get_all_service_status(
    session: AsyncSession = Depends(get_async_session)
):
    """Возвращает список всех подразделений."""
    return await get_multi_service_status(session)
