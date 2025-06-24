from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from toir_app.core.db import get_async_session
from toir_app.crud.stats import (add_statement_after_loading_csv_file,
                                 get_stats_for_organization)
from toir_app.models import Organization
from toir_app.schemas.service_work_stats import ServiceStatusStatsBase

router = APIRouter()


@router.get(
    '/fix_stats',
    name='Фиксация статистики'
)
async def fix_stats(session: AsyncSession = Depends(get_async_session)):
    await add_statement_after_loading_csv_file(session=session)


@router.get(
    '/get_stats',
    response_model=list[ServiceStatusStatsBase],
    name='Получение статистики по цеху'
)
async def get_stats(
    organization_id: Annotated[int, Organization.id] = Query(...),
    session: AsyncSession = Depends(get_async_session)
):
    return await get_stats_for_organization(
        organization_id=organization_id,
        session=session
    )
