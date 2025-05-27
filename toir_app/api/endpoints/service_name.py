from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from toir_app.core.db import get_async_session
from toir_app.crud.service_name import (
    get_service_name_with_request_status
)
from toir_app.crud.service_status import (
    check_service_status_by_param
)
from toir_app.schemas.service_name import ServiceNameBase


router = APIRouter()


# TODO ПРОВЕРИТЬ как работает фильтрация на простых примерах!!!
@router.post(
    '/all_service_names',
    response_model=list[ServiceNameBase],
    name='Срез видов ТО',
    description='Получение среза видов ТО для заполнения шапки таблицы.',
    status_code=200,
)
async def get_all_service_names_with_selected_request_status(
    *,
    request_status_param: int,
    special_status_ids: list[Optional[int]],
    organization_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    """Возвращает список видов ТО с выбранным Присвоенным Статусом.

    Args:
        request_status_param (int): id выбранного юзером расчётного статуса.
        special_status_ids (list(int)): список ids специальных статусов.
        organization_id (int): id выбранного юзером подразделения.
        session: сессия.
    """
    # Проверяем существование выбранного присвоенного статуса в БД:
    await check_service_status_by_param(session, request_status_param)

    return await get_service_name_with_request_status(
        request_status_id=request_status_param,
        special_status_ids=special_status_ids,
        organization_id=organization_id,
        session=session
    )
