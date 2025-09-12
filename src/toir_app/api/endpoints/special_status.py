from datetime import date
from http import HTTPStatus
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_async_session
from core.user import current_user, current_superuser
from crud.special_status import (
    create_association_special_statuses_and_role,
    dao_special_status_for_car,
    get_all_special_status,
)
from models import Role, SpecialStatus, User
from schemas.special_status import (
    FullSpecialStatusSchemas,
    SpecialStatusForCarMoveSchema,
    SpecialStatusForCarSchema,
)

router = APIRouter()


@router.get(
    '/all',
    response_model=list[FullSpecialStatusSchemas],
    name='Получение всех специальных статусов (доступно всем).',
    description=(
        '''
        С помощью списка из данных статусов пользователь сможет выбрать и
        присвоить для машины особое состояние.
        '''
    )
)
async def get_all_special_status_for_car(
    session: AsyncSession = Depends(get_async_session),
):
    """Получение списка специальных статусов, доступных пользователю."""
    return await get_all_special_status(session=session)


@router.get(
    '/all_for_users_role',
    response_model=list[FullSpecialStatusSchemas],
    dependencies=[Depends(current_user)],
    name='Получение специальных статусов для роли (доступно авторизованным).',
    description=(
        '''
        С помощью ограниченного списка из данных статусов пользователь сможет
        выбрать и присвоить для машины своего цеха особое состояние.
        '''
    )
)
async def get_all_special_status_for_car_and_role(
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_user),
):
    """Получение списка специальных статусов, доступных пользователю."""
    return await get_all_special_status(
        session=session,
        role_id=user.role_id,
    )


@router.post(
    '/add_role_permission',
    dependencies=[Depends(current_superuser)],
    name=(
        'Назначение полномочий на установку специальных статусов'
        '(доступно только админу)'
    ),
    status_code=HTTPStatus.CREATED
)
async def add_special_status_permissions_for_role(
    role_id: Annotated[int, Role.id],
    special_status_ids: list[Annotated[int, SpecialStatus.id]] = Query(
        description='Список специальных статусов, доступных данной роли'
    ),
    session: AsyncSession = Depends(get_async_session)
):
    """Выставление связи специальных статусов для роли пользователя."""
    try:
        await create_association_special_statuses_and_role(
            special_status_ids=special_status_ids,
            role_id=role_id,
            session=session
        )

        return {'detail': 'Успешно'}

    # FIXME почему-то без try-except не работает :(
    except Exception as e:
        raise HTTPException(HTTPStatus.BAD_REQUEST, detail=str(e))


@router.patch(
    '/{special_status_id}/deactivate',
    response_model=SpecialStatusForCarSchema,
    dependencies=[Depends(current_user)],
    name='Перевод специального статуса в архив раньше времени.',
    status_code=HTTPStatus.OK,
)
async def move_special_status_in_archive(
    special_status_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    special_status = await dao_special_status_for_car.get(
        obj_id=special_status_id,
        session=session,
    )

    # FIXME получить ТС, к которому статус был привязан и сравнить его подразд
    # с подразделением юзера

    if not special_status:
        raise HTTPException(
            HTTPStatus.BAD_REQUEST,
            f'Статус #{special_status_id} не найден',
        )

    if not special_status.is_active:
        raise HTTPException(HTTPStatus.BAD_REQUEST, 'Статус уже в архиве')

    upd_data = SpecialStatusForCarMoveSchema(
        id=special_status_id,
        is_active=False,
        date_left=date.today()
    )
    return await dao_special_status_for_car.update(
        db_obj=special_status,
        obj_in=upd_data,
        session=session,
    )
