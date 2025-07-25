from typing import Optional
from sqlalchemy import and_, or_, select
# from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from models import Car, ServiceName, ServiceWork, SpecialStatusForCar


async def get_service_name_with_request_status(
    request_status_id: int,
    special_status_ids: list[Optional[int]],
    organization_id: int,
    session: AsyncSession,
    need_range: bool = False,
    hide_service_work_with_zvr: bool = False
) -> list[Optional[ServiceName]]:
    """Возврат УНИКАЛЬНЫХ видов сервисного обслуживания.

    Args:
        - need_range - чтобы указать, что нужен диапазон.

    Users filters:
        - расчётный статус.
        - список специальных статусов ТС (FIXME без статуса -> всегда).
        - подразделение.

    Default filters:
        - запись о сервисном обслуживании не в архиве.
        - ТС не в архиве.
        - дедупликация объектов ServiceName (вроде).

    Order by:
        - asc IDs ServiceName.
    """
    stmt = (
        select(ServiceName)
        .join(ServiceWork, ServiceName.id == ServiceWork.next_service_id)
        .join(Car)
        .outerjoin(Car.status_associations)
        # .options(
        #     joinedload(ServiceWork.car),
        # )
        .where(
            and_(
                ServiceWork.in_archive.is_(False),
                (
                    # выбираем точное == или диапазон до цели и все что строже
                    ServiceWork.request_status_id <= request_status_id
                    if need_range
                    else ServiceWork.request_status_id == request_status_id
                ),
                Car.organization_id == organization_id,
                Car.in_archive.is_(False),
                or_(
                    Car.status_associations == None,
                    SpecialStatusForCar.special_status_id.in_(
                        special_status_ids
                    )
                )
            )
        ).distinct()  # distinct - дедупликация
        .order_by(ServiceName.id)  # сортировка по ID вида работ
    )

    if hide_service_work_with_zvr:
        stmt = stmt.where(ServiceWork.zvr_number.is_(None))

    service_names = await session.execute(stmt)

    return list(service_names.scalars().all())


async def get_service_name_group(
    service_name_id: int,
    session: AsyncSession,
) -> Optional[int]:
    """Возврат номера группы вида сервисного обслуживания."""
    return await session.scalar(
        select(ServiceName.group).where(ServiceName.id == service_name_id)
    )
