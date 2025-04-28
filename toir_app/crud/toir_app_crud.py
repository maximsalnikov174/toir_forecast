from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from toir_app.models.service_name import ServiceName
from toir_app.models.service_work import ServiceWork


async def get_service_name_with_request_status(
    request_status_id: int,
    session: AsyncSession
) -> list[Optional[ServiceName]]:
    """
    Возврат УНИКАЛЬНЫХ видов ТО c выбранным Присвоенным статусом.
    """
    service_names = await session.execute(
        select(ServiceName)
        .join(ServiceWork, ServiceName.id == ServiceWork.next_service_id)
        .where(ServiceWork.request_status_id == request_status_id)
        .distinct()  # distinct - дедупликация
    )
    return list(service_names.scalars().all())


async def check_service_name_by_id(
    request_status_id: int,
    session: AsyncSession
) -> Optional[int]:
    """
    Проверяем существование присвоенного Статуса с выбранным ID.

    Results:
    - если существует - Возврат его ID;
    - если не существует - Возврат None.
    """
    service_name_id = await session.execute(
        select(ServiceName.id).where(ServiceName.id == request_status_id)
    )
    service_name_id = service_name_id.scalars().first()
    return service_name_id
