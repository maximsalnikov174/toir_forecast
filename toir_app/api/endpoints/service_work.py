from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import Field
from sqlalchemy.ext.asyncio import AsyncSession

from toir_app.core.db import get_async_session
from toir_app.crud.service_work import check_zvr_unique, get_service_work
from toir_app.schemas.service_work import (
    ServiceWorkWithZVRNumber
)

router = APIRouter()


@router.post(
    '/add_zvr',
    response_model=ServiceWorkWithZVRNumber,
    name='Добавление ЗВР к конкретному service_work',
    response_model_exclude_none=True,
    status_code=201
)
async def add_zvr_to_service_work(
    service_work_id: int,
    zvr_number: Annotated[int, Field(ge=1_000_000, lt=10_000_000)],
    session: AsyncSession = Depends(get_async_session)
):
    """Добавление 7-значного ЗВР к service_work."""
    service_work = await get_service_work(service_work_id, session)

    if not service_work:
        raise HTTPException(
            status_code=404,
            detail='Указанная работа не найдена.'
        )
    if service_work.zvr_number:
        raise HTTPException(
            status_code=422,
            detail='У данной работы ЗВР уже существует.'
        )
    if await check_zvr_unique(zvr_number, session):
        raise HTTPException(
            status_code=422,
            detail=f'Указанный ЗВР #{zvr_number} не уникален, сверьте данные.'
        )

    try:
        service_work.zvr_number = zvr_number
        await session.commit()
        await session.refresh(service_work)  # Опционально
        return service_work
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            500,
            detail=f'Ошибка при сохранении ЗВР: {str(e)}'
        )
