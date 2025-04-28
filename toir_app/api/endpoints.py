from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from toir_app.core.db import get_async_session
from toir_app.crud.toir_app_crud import (
    check_service_name_by_id,
    get_service_name_with_request_status
)
from toir_app.schemas.service_name import ServiceNameBase

# Создаём объект роутера.
router = APIRouter()


@router.get(
    '/all_service_names',
    response_model=list[ServiceNameBase],
    name='Срез видов ТО',
    description='Получение среза видов ТО для заполнения шапки таблицы.',
    tags=['service_name'],
    status_code=200,
)
async def get_all_service_names_with_selected_request_status(
    request_status_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    """Возвращает список видов ТехОбслуж с выбранным Присвоенным Статусом."""
    # Проверяем существование выбранного присвоенного статуса в бд:
    check_request_status_id = await check_service_name_by_id(
        request_status_id, session
    )
    # если совпадений нет - выбрасываем исключение:
    if check_request_status_id is None:
        raise HTTPException(
            status_code=404,
            detail=f'ID#{request_status_id} в БД не найден.'
        )

    return await get_service_name_with_request_status(
        request_status_id, session
    )
