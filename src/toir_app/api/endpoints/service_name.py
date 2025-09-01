from http import HTTPStatus
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_async_session
from core.user import current_user
from crud.service_name import (
    get_service_name_with_request_status,
    get_service_name_for_master,
)
from crud.service_status import dao_service_status
from models import User
from schemas.service_name import ServiceNameBase

router = APIRouter()


# TODO ПРОВЕРИТЬ как работает фильтрация на простых примерах!!!
@router.post(
    '/all_service_names',
    response_model=list[ServiceNameBase],
    name='Срез видов ТО (доступно всем)',
    description='Получение среза видов ТО для заполнения шапки таблицы.',
    status_code=HTTPStatus.OK,
)
async def get_all_service_names_with_selected_request_status(
    *,
    request_status_param: int,
    special_status_ids: list[Optional[int]],
    organization_id: int,
    session: AsyncSession = Depends(get_async_session),
    hide_service_work_with_zvr: bool = False
):
    """Возвращает список видов ТО с выбранным Присвоенным Статусом.

    Args:
        request_status_param (int): id выбранного юзером расчётного статуса.
        special_status_ids (list(int)): список ids специальных статусов.
        organization_id (int): id выбранного юзером подразделения.
        session: сессия.
    """
    # Проверяем существование выбранного присвоенного статуса в БД:
    await dao_service_status.check_exists(request_status_param, session)

    return await get_service_name_with_request_status(
        request_status_id=request_status_param,
        special_status_ids=special_status_ids,
        organization_id=organization_id,
        session=session,
        need_range=True,
        hide_service_work_with_zvr=hide_service_work_with_zvr
    )


@router.post(
    '/all_service_names_for_master',
    response_model=list[ServiceNameBase],
    name='Срез видов ТО (доступно мастерским)',
    description='Получение среза видов ТО для заполнения шапки таблицы.',
    status_code=HTTPStatus.OK,
)
async def get_all_service_names_for_master(
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_async_session),
):
    return await get_service_name_for_master(
        station_id=user.users_organization.station_id,
        user=user,
        session=session
    )
