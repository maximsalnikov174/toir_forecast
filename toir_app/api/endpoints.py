from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from toir_app.core.db import get_async_session
from toir_app.crud.car import get_car_by_full_grz
from toir_app.crud.toir_app_crud import (
    check_service_status_by_param,
    get_cars_with_request_status,
    get_service_name_with_request_status
)
from toir_app.schemas.car import CarBase, CarWithServiceWorkAtributes
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
    """Возвращает список видов ТО с выбранным Присвоенным Статусом."""
    # Проверяем существование выбранного присвоенного статуса в БД:
    await check_service_status_by_param(session, request_status_param)
    return await get_service_name_with_request_status(
        request_status_param, session
    )


@router.get(
    '/cars_with_status_in_organization',
    response_model=list[CarBase],
    name='Срез списка машин',
    description=(
        'Получение среза списка машин цеха Х со статусом Y.'
    ),
    tags=['cars'],
    status_code=200,
)
async def get_all_cars_with_selected_request_status(
    request_status_param: int,
    organization_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    """Возвращает список ТС с выбранным Присвоенным Статусом."""
    # Проверяем существование выбранного присвоенного статуса в БД:
    await check_service_status_by_param(session, request_status_param)
    return await get_cars_with_request_status(
        request_status_param, organization_id, session
    )


@router.get(
    '/current_car/{grz}',
    response_model=list[CarBase],
    name='Поиск машины по ГРЗ',
    tags=['cars'],
    status_code=200
)
async def get_car_in_db_by_grz(
    grz: str,
    session: AsyncSession = Depends(get_async_session)
):
    return await get_car_by_full_grz(grz, session)
