from typing import Optional, Union

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import ServiceStatus, Status


async def get_multi_service_status(session: AsyncSession):
    """Получение всех расчётных статусов для сервисного обслуживания."""
    result = await session.scalars(select(ServiceStatus))
    return result.all()


async def get_service_status_by_name(name: str, session: AsyncSession):
    return await session.scalar(
        select(ServiceStatus)
        .where(ServiceStatus.name == name)
    )


async def check_service_status_by_param(
    session: AsyncSession,
    request_status_param: Union[int, Status]
) -> bool:
    """
    Проверяем существование присвоенного Статуса с выбранным ID (параметром).

    Results:
    - если существует - Возврат True;
    - если не существует - Выбросит исключение.
    """
    if isinstance(request_status_param, int):
        exists = await check_exist_service_status_by_id(
            id=request_status_param,
            session=session
        )

    # TODO - сделать это!!!
    # elif isinstance(request_status_param, Status):
    #     service_name_id = await session.execute(
    #         select(ServiceName.id)
    #         .where(ServiceName.name == request_status_param)
    #     )
        if not exists:
            raise HTTPException(
                status_code=404,
                detail=(
                    'Экземпляр ServiceName с параметром '
                    f'{request_status_param} в БД не найден.'
                )
            )
    return True


async def check_exist_service_status_by_id(
        id: int, session: AsyncSession
) -> Optional[int]:
    """Проверяет существование service_status по ID."""
    return await session.scalar(
        select(ServiceStatus.id)
        .where(ServiceStatus.id == id)
        .exists()
        .select()
    )
