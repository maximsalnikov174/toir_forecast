# ----------ФУНКЦИИ, ВЫПОЛНЯЮЩИЕ НАПОЛНЕНИЕ ДАННЫМИ ИЗ CSV-ФАЙЛА----------

import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from toir_app.core.db import Base as db
from toir_app.crud.car import get_car_by_personal_id
from toir_app.crud.service_status import get_service_status_by_name
from toir_app.crud.service_work import get_last_service_with_current_service_id
from toir_app.models import Car, ServiceWork
from toir_app.schemas.car import (
    CarToDownloadInDB
)
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


async def get_or_create_car_and_return_id(
    session: AsyncSession,
    personal_id: int,
    grz: str,
    car_model: CarModelID,
    organization: OrganizationID
) -> tuple[int, str]:
    """Получает экземпляр модели Car или создает его (автомобиль)."""
    # Можно бы было ВЫШЕ получить все проиндексированные personal_id одним
    # запросом и искать среди них:
    car_in_db = await get_car_by_personal_id(personal_id, session)

    # TODO перевод ТС в статус "в архиве" после того, как из rmt по нему
    # не пришло данных

    if not car_in_db:
        # загоняем в pydantic-схему:
        validated_car = CarToDownloadInDB(
            personal_id=personal_id,
            grz=grz,
            car_model_id=car_model.id,
            organization_id=organization.id
        )
        new_car: dict[str, Any] = validated_car.model_dump()

        # создаем экземпляр модели Car и добавляем в сессию:
        car: Car = Car(**new_car)
        session.add(car)
        await session.commit()
        await session.refresh(car)
        logging.info(f'🚚 «{car.grz}» создано.')
        return car.id, car.grz

    return car_in_db.id, car_in_db.grz


async def create_service_work(
    session: AsyncSession,
    car_id: int,
    element_dict: dict,
    last_service_id: int,
    next_service_id: int,
    **kwargs
) -> None:
    """
    Создает или обновляет запись обслуживания для автомобиля.

    Параметры:
        session: Асинхронная сессия SQLAlchemy
        car_id: ID автомобиля
        element_dict: Словарь с данными из CSV
        last_service_id: ID последнего выполненного обслуживания
        next_service_id: ID следующего запланированного обслуживания

    Логика:
    1. Если запись существует и данные совпадают - проверяем только статус;
    2. Если запись существует, но данные изменились - обновляем;
    3. Если записи нет - создаем новую запись.
    """
    # Ищем в БД самую свежую запись для данного ТС с тем же или
    # сгруппированным (пример ТО-1, ТО-2, ТО-3 и тд) видом обслуживания:
    service = await get_last_service_with_current_service_id(
        car_id=car_id,
        last_service_id=last_service_id,
        session=session
    )
    # Валидация pydentic-схемой:
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

    old_request_status_id = None  # Переменная для старого статуса
    need_to_update = False  # Переменная для срабатывания обновления

    # Если сервис в БД совпадает с полученным (в т.ч. пробег посл. сервиса):
    if (
        service
        and service.last_service_reading == (
            validated_service_work.last_service_reading
        )
    ):
        # ... но при этом изменился общий пробег - ОБНОВЛЕНИЕ ЗАПИСИ по сути
        if service.request_reading != validated_service_work.request_reading:
            need_to_update = True
            # Обновляем суточный и общий пробег:
            service.daily_distance = validated_service_work.daily_distance
            service.request_reading = validated_service_work.request_reading
            logging.info(f'🏃‍➡️ «{kwargs["car_grz"]}» : обновился пробег.')

        # Записываем дату обновления (нужно для пересчёта статуса):
        service.request_date = validated_service_work.request_date
        # и дополнительно фиксируем старый статус экземпляра:
        old_request_status_id = service.request_status_id

        # Создаём переменную, с которой будем работать далее:
        processing_service = service

    else:
        # Перевод старой записи в архив:
        if service:
            service.in_archive = True
            service.service_work_completed = True

            # Логирование записи о ТО, перешедшей в архив
            logging.info(
                f'🏁 «{kwargs["car_grz"]}». '
                f'🛠️#{service.next_service_id} закрыт '
                f'{validated_service_work.request_date.date()} '
                f'на пробеге {service.request_reading}.'
            )

        # Если инфы о ТС нет или появилась новая запись о сервисе:
        new_service_work: dict[str, Any] = validated_service_work.model_dump()

        # Создание нового экземпляра (с которым будем работать далее):
        processing_service = ServiceWork(**new_service_work)

    # Рассчитываем и получаем глобальный статус для авто:
    # Должно гарантированно рассчитываться!
    upd_status = processing_service.calculated_status
    upd_status = (
        await get_service_status_by_name(upd_status.value, session)
    )
    processing_service.request_status_id = upd_status.id

    # Если глоб. статус изменился - для
    # * обновляемой записи - откат или прогресс
    # * новой записи - в любом случае должна быть разница
    # или глоб. статус - прежний, но поменялись (малозначимые) данные,
    # к примеру, общий пробег - тем самым обновив need_to_update=True:
    if old_request_status_id != upd_status.id or need_to_update:
        session.add(processing_service)

        # Логгирование:
        if not need_to_update:
            message = f'«{kwargs["car_grz"]}». 🛠️#{next_service_id}'
            if not old_request_status_id:
                logging.info(
                    f'✅ {message}. Присвоен глобальный статус: '
                    f'{upd_status.id}.'
                )
            else:
                logging.info(
                    f'🔄 {message}. Изменен глобальный статус: '
                    f'({old_request_status_id}) -> {upd_status.id}.'
                )
