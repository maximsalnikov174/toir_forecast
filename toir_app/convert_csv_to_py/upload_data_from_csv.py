# ----------ФУНКЦИИ, ВЫПОЛНЯЮЩИЕ НАПОЛНЕНИЕ ДАННЫМИ ИЗ CSV-ФАЙЛА----------

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from toir_app.core.db import Base as db
from toir_app.models.car import Car
from toir_app.models.car_model import CarModel
from toir_app.models.organization import Organization
from toir_app.models.service_work import ServiceWork


async def upload_users_data_in_db(
    element: str,
    apps_model: type[db],
    session: AsyncSession
):
    """Асинхронно наполняет БД статичными данными."""
    # Получаем значение (работает и для Enum, и для обычных строк)
    value = element.value if hasattr(element, 'value') else element

    # Проверяем существование записи
    stmt = select(apps_model).where(apps_model.name == value)
    result = await session.execute(stmt)
    existing = result.scalar_one_or_none()

    if not existing:
        new_instance = apps_model(name=value)
        session.add(new_instance)

    await session.commit()


async def get_or_create_car(
    session: AsyncSession,
    personal_id: int,
    grz: str,
    car_model: Optional[CarModel],
    organization: Optional[Organization]
) -> Car:
    """Получает или создает автомобиль"""
    car = await session.scalar(
        select(Car).where(Car.personal_id == personal_id)
    )
    if not car:
        new_car = Car(
            personal_id=personal_id,
            grz=grz,
            car_model=car_model,
            organization=organization
        )
        car = await session.merge(new_car)
    await session.flush()
    return car


async def create_service_work(
    session: AsyncSession,
    car_id: int,
    element_dict: dict,
    last_service_id: Optional[int],
    next_service_id: Optional[int]
) -> None:
    """
    Создает запись обработки строки из csv для объекта обслуживания.

    Проверяем существующую запись. Должны совпасть:
    - id,
    - текущие показания пробега,
    - вид последнего обслуживания,
    - (на всякий случай) показания последнего обслуживания

    Если нет изменений - просто пропускаем.
    """
    service = await session.scalar(
        select(ServiceWork)
        .where(
            ServiceWork.car_id == car_id,
            ServiceWork.request_reading == element_dict['reading_now'],
            ServiceWork.last_service_id == last_service_id,
            ServiceWork.last_service_reading == (
                element_dict['last_service_reading']
            )
        )
    )

    if not service:
        service = ServiceWork(
            car_id=car_id,
            last_service_id=last_service_id,
            next_service_id=next_service_id,
            last_service_date=element_dict['last_service_date'],
            last_service_reading=element_dict['last_service_reading'],
            request_date=element_dict['dt_now'],
            request_reading=element_dict['reading_now'],
            base_interval=element_dict['base_interval'],
            daily_distance=element_dict['daily_distance'],
            # request_status_id=оставляем пока пустым
        )

        session.add(service)  # добавляем в сессию запись из csv
        # синхронизирует состояние в сессии без коммита
        # необходим для получения "service"
        await session.flush()
        await service.update_request_status(session)  # обновляем статус
        await session.flush()  # необходим для добавления request_status
