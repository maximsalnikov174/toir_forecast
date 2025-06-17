# ----------ФУНКЦИИ, ВЫПОЛНЯЮЩИЕ НАПОЛНЕНИЕ ДАННЫМИ ИЗ CSV-ФАЙЛА----------

import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from toir_app.core.db import Base as db
from toir_app.crud.service_status import get_service_status_by_name
from toir_app.crud.service_work import (
    add_service_works_in_archive, get_last_service_with_current_service_id,
    update_reading_and_daily_distance)
from toir_app.models import ServiceWork
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

    if service:
        # Если пробег последнего сервиса в db отличается от входящих данных ...
        if service.last_service_reading > (
            validated_service_work.last_service_reading
        ):
            logging.warning(
                f'⛔ На ТС «{kwargs["car_grz"]}» пробег ниже предыдущего.'
            )

        elif service.last_service_reading < (
            validated_service_work.last_service_reading
        ):
            # ... закрываем старую запись:
            await add_service_works_in_archive(
                service_work_list=[service],
                session=session,
                car_grz=kwargs['car_grz'],
                validated_service_work=validated_service_work
            )
            need_to_update = True  # ставим флаг на обновление.

        else:
            # Проверяем запись (при необходимости обновляем сут/общ пробеги):
            update_reading_and_daily_distance(
                car_grz=kwargs['car_grz'],
                service_work=service,
                incoming_data=validated_service_work,
                session=session
            )

            # Фиксируем текущий статус экземпляра ...
            old_request_status_id = service.request_status_id
            # ... и записываем дату обновления (нужно для пересчёта статуса)
            service.request_date = validated_service_work.request_date

            # Создаём переменную, с которой будем работать далее:
            processing_service = service

    # Если инфы нет вообще или появилась новая запись о сервисе -
    # создаём новый экземпляр (с которым будем работать далее):
    if not service or need_to_update:
        new_service_work: dict[str, Any] = validated_service_work.model_dump()
        processing_service = ServiceWork(**new_service_work)

    # Рассчитываем и получаем глобальный статус для авто:
    upd_status = processing_service.calculated_status
    upd_status = await get_service_status_by_name(upd_status.value, session)
    processing_service.request_status_id = upd_status.id

    # Если глоб. статус изменился - для
    # * обновляемой записи - откат или прогресс
    # * новой записи - в любом случае должна быть разница
    if old_request_status_id != upd_status.id:
        session.add(processing_service)

        # Логгирование:
        message = f'«{kwargs["car_grz"]}». 🛠️#{next_service_id}'
        if old_request_status_id:
            logging.info(
                f'🔄 {message}. Изменен глобальный статус: '
                f'({old_request_status_id}) -> {upd_status.id}.'
            )
        else:
            logging.info(
                f'✅ {message}. Присвоен глобальный статус: {upd_status.id}.'
            )
