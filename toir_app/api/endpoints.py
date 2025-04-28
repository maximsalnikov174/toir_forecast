from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from toir_app.core.db import get_async_session
from toir_app.crud.toir_app_crud import (
    check_service_status_by_param,
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
    request_status_param: int,
    session: AsyncSession = Depends(get_async_session)
):
    """Возвращает список видов ТехОбслуж с выбранным Присвоенным Статусом."""
    # Проверяем существование выбранного присвоенного статуса в БД:
    check_request_status_id = await check_service_status_by_param(
        session, request_status_param
    )
    # если совпадений нет - выбрасываем исключение:
    if not check_request_status_id:
        raise HTTPException(
            status_code=404,
            detail=(
                f'Экземпляр ServiceName с параметром {request_status_param} '
                'в БД не найден.'
            )
        )

    return await get_service_name_with_request_status(
        check_request_status_id, session
    )
