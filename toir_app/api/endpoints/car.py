from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from toir_app.models import Car
from toir_app.core.db import get_async_session
from toir_app.crud.car import (
    get_car_by_full_grz,
    get_cars_with_request_status
)
from toir_app.crud.service_work import (
    get_last_request_reading_by_car
)
from toir_app.crud.service_status import (
    check_service_status_by_param
)
from toir_app.schemas.car import CarBase


router = APIRouter()


@router.get(
    '/with_status_in_organization',
    response_model=list[CarBase],
    name='Срез списка машин',
    description=('Получение среза списка машин цеха Х со статусом Y.'),
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
    response_model=CarBase,
    name='Поиск машины по ГРЗ и возврат информации о ней.',
)
async def get_car_in_db_by_grz(
    grz: str,
    session: AsyncSession = Depends(get_async_session)
):
    car: Car = await get_car_by_full_grz(grz, session)
    car.indicators = await get_last_request_reading_by_car(car.id, session)
    return car
