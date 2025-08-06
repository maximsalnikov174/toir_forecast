from http import HTTPStatus
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_async_session
from core.user import current_user, current_superuser
from crud.special_status import (
    create_association_special_statuses_and_role,
    get_all_special_status,
)
from models import Role, SpecialStatus, User
from schemas.special_status import (
    FullSpecialStatusSchemas,
)

router = APIRouter()


@router.get(
    '/all',
    response_model=list[FullSpecialStatusSchemas],
    dependencies=[Depends(current_user)],
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
    user: User = Depends(current_user),
):
    """Получение списка специальных статусов, доступных пользователю."""
    return await get_all_special_status(
        session=session,
        role_id=user.role_id
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
