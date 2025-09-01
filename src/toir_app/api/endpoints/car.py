from datetime import date
from http import HTTPStatus
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_async_session
from core.user import current_user
from crud.car import (
    add_special_status_to_car, get_car_by_full_grz,
    get_car_history,
    get_cars_with_request_and_special_status,
)
from crud.service_status import dao_service_status
from crud.service_work import get_last_request_reading_by_car
from models import Car, User
from schemas.car import (
    CarExpandWithIndicators,
    CarWithCarModelAndOrganizationIDs,
)
from schemas.service_work import ServiceWorkWithInArchive

router = APIRouter()


@router.post(
    '/with_many_statuses',
    response_model=list[CarExpandWithIndicators],
    name='Срез списка машин цеха Х (доступно всем)',
    description=(
        'Получение среза списка машин цеха Х.\nУчитываются:\n'
        '- расчётный статус (учитывается он и всё что строже)\n'
        '- выбранные статусы ТС (ТС без статуса учитываются всегда)'
    ),
    response_model_exclude_none=True
)
async def get_all_cars_with_selected_request_status(
    request_status_param: int,
    special_status_ids: list[Optional[int]],
    organization_id: int,
    hide_service_work_with_zvr: bool = False,
    session: AsyncSession = Depends(get_async_session)
):
    """Возвращает список ТС с выбранным Присвоенным Статусом."""
    # Проверяем существование выбранного присвоенного статуса в БД:
    await dao_service_status.check_exists(
        id=request_status_param,
        session=session,
    )

    # TODO Проверяем существование выбранных статусов для ТС (на ВР и тд):
    # FIXME Попробовать здесь реализовать отбор без None
    pass

    cars = await get_cars_with_request_and_special_status(
        request_status_id=request_status_param,
        special_status_ids=special_status_ids,
        organization_id=organization_id,
        session=session,
        hide_service_work_with_zvr=hide_service_work_with_zvr,
    )
    for car in cars:
        car.indicators = await get_last_request_reading_by_car(car.id, session)

    return cars


@router.post(
    '/with_many_statuses_for_master',
    response_model=list[CarExpandWithIndicators],
    name='Срез списка машин (доступно мастерским)',
    description=(
        'Получение среза списка машин с ЗВР и незавершенными работами'
    ),
    response_model_exclude_none=True
)
async def get_all_cars_with_open_zvr(
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Возвращает список ТС с открытыми ЗВР."""
    cars = await get_cars_with_request_and_special_status(
        session=session,
        for_masters=True,
        organization_id=user.users_organization.station_id,
        user=user,
    )
    for car in cars:
        car.indicators = await get_last_request_reading_by_car(car.id, session)

    return cars


@router.get(
    '/about_car',
    response_model=CarExpandWithIndicators,
    name='Поиск машины по ГРЗ и возврат информации о ней (доступно всем).',
    response_model_exclude_none=True
)
async def get_car_in_db_by_grz(
    grz: str,
    session: AsyncSession = Depends(get_async_session)
):
    car: Car = await get_car_by_full_grz(grz, session)
    car.indicators = await get_last_request_reading_by_car(car.id, session)
    return car


@router.patch(
    '/{car_id}/add_special_status',
    response_model=CarWithCarModelAndOrganizationIDs,
    dependencies=[Depends(current_user)],
    name='Добавление специального статуса ТС (только сотрудник цеха).',
    description=(
        'ТС устанавливается специальный статус, предназначенный для помощи '
        '(в дальнейшем) сотрудникам с определением состояния ТС (примеры '
        'статусов: на ВР, к выбытию/списанию, на реализации и т.д.)\n'
        'Ограничения:\n - ТС не должно быть в архиве.'
    ),
    status_code=HTTPStatus.CREATED
)
async def link_special_status_and_car(
    car_id: int,
    special_status_id: int,
    date_from_user: date = Query(..., example='2025-09-01'),
    comment: Optional[str] = None,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Установка специального статуса для ТС."""
    return await add_special_status_to_car(
        special_status_id=special_status_id,
        car_id=car_id,
        user=user,
        session=session,
        date_from_user=date_from_user,
        comment=comment
    )


@router.get(
    '/get_history',
    response_model=List[ServiceWorkWithInArchive],
    name='Отображение истории по выполнению сервисных обслуживаний для ТС.',
    description='Позже допишу',
    status_code=HTTPStatus.OK
)
async def get_history_for_current_car(
    car_id: int = Query(None, ge=0, description='ID ТС'),
    session: AsyncSession = Depends(get_async_session)
):
    return await get_car_history(car_id=car_id, session=session)
