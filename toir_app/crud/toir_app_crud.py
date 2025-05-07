from typing import Optional, Union
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from toir_app.crud.service_status import check_exist_service_status_by_id
from toir_app.models.car import Car
from toir_app.models.service_name import ServiceName
from toir_app.models.service_work import ServiceWork
from toir_app.models.static_model import Status


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
        .order_by(ServiceName.id)
    )
    return list(service_names.scalars().all())


async def get_cars_with_request_status(
    request_status_id: int,
    session: AsyncSession
) -> list[Optional[Car]]:
    """
    Возврат УНИКАЛЬНЫХ машин c выбранным Присвоенным статусом.
    """
    cars = await session.execute(
        select(Car)
        .join(ServiceWork, Car.id == ServiceWork.car_id)
        .where(ServiceWork.request_status_id == request_status_id)
        .distinct()  # distinct - дедупликация.
        .order_by(Car.grz)
    )
    return list(cars.scalars().all())


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
