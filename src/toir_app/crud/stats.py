from datetime import datetime as dt
from typing import Annotated, Dict

from sqlalchemy import select
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from constants import (
    LIST_ORGANIZATIONS,
    SPECIAL_STATUS_LIST_FOR_GET_STATS,
)
from crud.organization import get_organization_by_name
from crud.service_work import (
    get_active_service_work_count_for_all_service_status,
)
from logger.logger import logger
from models import (
    Organization,
    ServiceStatusStats,
    ServiceWorkState,
    Status,
)


async def add_statement_after_loading_csv_file(
        file_date: str, session: AsyncSession,
):
    """Оценка состояния service_works в подразделении с заполнением БД."""
    stmt_date = file_date.replace('_', '-')

    for organization_name in LIST_ORGANIZATIONS:
        organization = await get_organization_by_name(
            name=organization_name,
            session=session
        )
        if organization:
            service_status_stats = ServiceStatusStats()

            stats = await get_active_service_work_count_for_all_service_status(
                organization_id=organization.id,
                special_status_list=SPECIAL_STATUS_LIST_FOR_GET_STATS,
                session=session
            )

            total_dump: Dict[str, Annotated[int, ServiceWorkState.id]] = {}

            for status in Status:
                status_slice = stats.get(status.value)
                if status_slice:
                    elem = ServiceWorkState(**status_slice)
                    session.add(elem)
                    await session.commit()
                    await session.refresh(elem)
                    total_dump[f'{status.name.lower()}_slice_id'] = elem.id

            service_status_stats.stats_date = dt.fromisoformat(stmt_date)
            service_status_stats.organization_id = organization.id

            for key, value in total_dump.items():
                setattr(service_status_stats, key, value)
            session.add(service_status_stats)
            logger.info(
                f'📈 Статистика по {organization_name} за {stmt_date} '
                'загружена в БД.')
    await session.commit()


async def get_stats_for_organization(
        organization_id: Annotated[int, Organization.id],
        session: AsyncSession
):
    """Получение статистики по подразделению с загрузкой доп.моделей."""
    return await session.scalars(
        select(ServiceStatusStats)
        .where(ServiceStatusStats.organization_id == organization_id)
        .options(
            joinedload(ServiceStatusStats.organization),
            joinedload(ServiceStatusStats.danger_slice),
            joinedload(ServiceStatusStats.time_has_come_slice),
            joinedload(ServiceStatusStats.wait_moment_slice),
            joinedload(ServiceStatusStats.no_need_slice),
            joinedload(ServiceStatusStats.bad_request_slice)
        )
    )
