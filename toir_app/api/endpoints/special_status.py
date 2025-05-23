from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from toir_app.core.db import get_async_session
from toir_app.crud.special_status import (
    get_all_special_status
)
from toir_app.schemas.special_status import (
    FullSpecialStatusSchemas
)


router = APIRouter()


@router.get(
    '/all',
    response_model=list[FullSpecialStatusSchemas],
    name='Получение всех специальных статусов',
    description=(
        '''
        С помощью списка из данных статусов пользователь сможет выбрать и
        присвоить для машины особое состояние.
        '''
    )
)
async def get_all_special_status_for_car(
    session: AsyncSession = Depends(get_async_session)
):
    """Получение списка специальных статусов."""
    return await get_all_special_status(session)
