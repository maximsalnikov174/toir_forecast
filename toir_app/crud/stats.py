from datetime import datetime as dt
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from toir_app.constants import LIST_ORGANIZATIONS
from toir_app.crud.organization import get_organization_by_name
from toir_app.crud.service_work import (
    get_active_service_work_count_for_all_service_status)
from toir_app.models import ServiceWorkState, ServiceStatusStats, Status

# FIXME Уточнить, когда будут созданы все необходимые статусы:
SPECIAL_STATUS_LIST_FOR_GET_STATS: List[int] = [2, 3]


async def add_statement_after_loading_csv_file(session: AsyncSession):
    date: dt = dt(2025, 5, 28, 0, 0, 0)
    for organization_name in LIST_ORGANIZATIONS:
        organization = await get_organization_by_name(
            name=organization_name,
            session=session
        )
        if organization:
            stats = await get_active_service_work_count_for_all_service_status(
                organization_id=organization.id,
                special_status_list=SPECIAL_STATUS_LIST_FOR_GET_STATS,
                session=session
            )

            danger_slice = stats.get(Status.DANGER.value)
            ds_state = ServiceWorkState(**danger_slice)
            session.add(ds_state)
            await session.commit()
            await session.refresh(ds_state)  # Опционально

            time_has_come_slice = stats.get(Status.TIME_HAS_COME.value)
            thc_state = ServiceWorkState(**time_has_come_slice)
            session.add(thc_state)
            await session.commit()
            await session.refresh(thc_state)  # Опционально

            wait_moment_slice = stats.get(Status.WAIT_MOMENT.value)
            wm_state = ServiceWorkState(**wait_moment_slice)
            session.add(wm_state)
            await session.commit()
            await session.refresh(wm_state)  # Опционально

            no_need_slice = stats.get(Status.NO_NEED.value)
            nn_state = ServiceWorkState(**no_need_slice)
            session.add(nn_state)
            await session.commit()
            await session.refresh(nn_state)  # Опционально

            bad_reqiest_slice = stats.get(Status.BAD_REQUEST.value)
            br_state = ServiceWorkState(**bad_reqiest_slice)
            session.add(br_state)
            await session.commit()
            await session.refresh(br_state)  # Опционально

            ss_stats = ServiceStatusStats()
            ss_stats.stats_date = date
            ss_stats.organization_id = organization.id
            ss_stats.danger_slice_id = ds_state.id
            ss_stats.time_has_come_slice_id = thc_state.id
            ss_stats.wait_moment_slice_id = wm_state.id
            ss_stats.no_need_slice_id = nn_state.id
            ss_stats.bad_reqiest_slice_id = br_state.id
            session.add(ss_stats)
            await session.commit()
