# ----------ФУНКЦИИ, ВЫПОЛНЯЮЩИЕ НАПОЛНЕНИЕ ДАННЫМИ ИЗ CSV-ФАЙЛА----------

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from toir_app.core.db import Base as db
from toir_app.crud.service_status import get_service_status
from toir_app.crud.service_work import get_last_service_with_current_service_id
from toir_app.models.car import Car
from toir_app.models.service_work import ServiceWork
from toir_app.schemas.car import CarBase
from toir_app.schemas.car_model import CarModelID
from toir_app.schemas.organization import OrganizationID
from toir_app.schemas.service_work import ServiceWorkBase


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

        # TODO здесь нет валидации pydantic-схемами

        new_instance = apps_model(name=value)
        session.add(new_instance)

    await session.commit()


async def get_or_create_car(
    session: AsyncSession,
    personal_id: int,
    grz: str,
    car_model: CarModelID,
    organization: OrganizationID
) -> Car:
    """Получает экземпляр модели Car или создает его (автомобиль)."""
    car_in_db = await session.scalar(
        select(Car).where(Car.personal_id == personal_id)
    )

    if not car_in_db:
        # загоняем в pydantic-схему:
        validated_car = CarBase(
            personal_id=personal_id,
            grz=grz,
            car_model_id=car_model.id,
            organization_id=organization.id
        )
        new_car: dict[str, Any] = validated_car.model_dump()

        # создаем экземпляр модели Car и добавляем в сессию:
        car: Car = Car(**new_car)
        car_in_db = await session.merge(car)

    await session.flush()
    return car_in_db


async def create_service_work(
    session: AsyncSession,
    car_id: int,
    element_dict: dict,
    last_service_id: int,
    next_service_id: int
) -> None:
    """
    Создает запись обработки строки из csv для объекта обслуживания.

    Проверяем существующую запись. Должны совпасть:
    - id ТС,
    - вид последнего обслуживания

    Дальше смотрим показания последнего обслуживания

    Если нет изменений - просто пропускаем.
    """
    # Ищем в БД самую свежую запись для данного ТС с тем же видом обслуживания:
    service = await get_last_service_with_current_service_id(
        car_id=car_id,
        last_service_id=last_service_id,
        session=session
    )

    # Когда сервис в БД совпадает с полученным (в т.ч. пробег последнего
    # сервиса), но при этом изменился общий пробег - ОБНОВЛЕНИЕ ЗАПИСИ по сути:
    if (
        service
        and service.last_service_reading == (
            element_dict['last_service_reading']
        )
        and service.request_reading != element_dict['reading_now']
    ):
        # Переписываем суточный пробег, пробег в момент запроса и тек.дату:
        service.daily_distance = element_dict['daily_distance']
        service.request_reading = element_dict['reading_now']
        service.request_date = element_dict['dt_now']

        old_status = service.request_status.name  # запомнили старый статус
        upd_status = service.calculated_status  # и пересчиталие его

        # Если отличаются - идём в базу:
        if old_status != upd_status:
            upd_status_in_db = await get_service_status(
                upd_status.value, session
            )
            # ... и перезаписываем для записи поля «статус» и «id статуса»:
            if upd_status_in_db:
                service.request_status = upd_status_in_db
                service.request_status_id = upd_status_in_db.id
        return

    if not service:
        # Валидация pydentic-схемой:
        # request_status_id=оставляем пока пустым
        validated_service_work = ServiceWorkBase(
            car_id=car_id,
            last_service_id=last_service_id,
            next_service_id=next_service_id,
            last_service_date=element_dict['last_service_date'],
            last_service_reading=element_dict['last_service_reading'],
            request_date=element_dict['dt_now'],
            request_reading=element_dict['reading_now'],
            base_interval=element_dict['base_interval'],
            daily_distance=element_dict['daily_distance']
        )
        new_service_work: dict[str, Any] = validated_service_work.model_dump()
        service = ServiceWork(**new_service_work)

        # Рассчитываем и получаем глобальный статус для авто:
        service_status = await get_service_status(
            name=service.calculated_status.value, session=session
        )
        service.request_status_id = service_status.id
        session.add(service)
