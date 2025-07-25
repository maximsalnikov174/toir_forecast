from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_async_session
from crud.station import get_multi
from schemas.station import StationBase

router = APIRouter()


@router.get(
    '',
    response_model=list[StationBase],
    name='Получение списка сервисных мастерских.'
)
async def get_all_cars_with_selected_request_status(
    session: AsyncSession = Depends(get_async_session)
):
    return await get_multi(session=session)
