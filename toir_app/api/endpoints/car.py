from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from toir_app.models import Car
from toir_app.core.db import get_async_session
from toir_app.crud.car import (
    get_car_by_full_grz,
    get_cars_with_request_status,
    add_special_status_to_car
)
from toir_app.crud.service_work import (
    get_last_request_reading_by_car
)
from toir_app.crud.service_status import (
    check_service_status_by_param
)
from toir_app.schemas.car import CarWithCarModelAndOrganizationIDs


router = APIRouter()


@router.get(
    '/with_status_in_organization',
    response_model=list[CarWithCarModelAndOrganizationIDs],
    name='Срез списка машин',
    description=(
        'Получение среза списка машин цеха Х с расчётным статусом Y.'
    ),
    response_model_exclude_none=True
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
    '/about_car',
    response_model=CarWithCarModelAndOrganizationIDs,
    name='Поиск машины по ГРЗ и возврат информации о ней.',
    response_model_exclude_none=True
)
async def get_car_in_db_by_grz(
    grz: str,
    session: AsyncSession = Depends(get_async_session)
):
    car: Car = await get_car_by_full_grz(grz, session)
    car.indicators = await get_last_request_reading_by_car(car.id, session)
    return car


@router.post(
    '/{car_id}/add_special_status',
    response_model=CarWithCarModelAndOrganizationIDs,
    name='Добавление специального статуса машине.'
)
async def link_special_status_and_car(
    car_id: int,
    special_status_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    """Установка специального статуса для ТС."""
    return await add_special_status_to_car(
        special_status_id,
        car_id,
        session
    )
