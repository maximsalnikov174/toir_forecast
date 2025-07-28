# ----------ФУНКЦИИ, ВЫПОЛНЯЮЩИЕ НАПОЛНЕНИЕ ДАННЫМИ ИЗ CSV-ФАЙЛА----------

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from crud.service_status import get_service_status_by_name
from crud.service_work import (
    add_service_works_in_archive, get_last_service_with_current_service_id,
    update_reading_and_daily_distance,
)
from models import ServiceWork
from schemas.service_work import ServiceWorkBase
from logger.logger import logger


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
        base_interval=element_dict['base_interval'],
        session=session
    )
    # Попробовать передавать еще и базовый интервал

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
        # Если пробег последнего сервиса в db ниже входящих данных:
        if service.last_service_reading < (
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

        elif service.last_service_reading == (
            validated_service_work.last_service_reading
        ):
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

        # Если пробег последнего сервиса в db вдруг стал выше входящих данных:
        elif (
            service.last_service_reading > (
                validated_service_work.last_service_reading
            )
            and service.base_interval == validated_service_work.base_interval
        ):
            logger.warning(
                f'⛔ На ТС «{kwargs["car_grz"]}» показатель пробега последнего '
                f'обслуживания ({validated_service_work.last_service_reading})'
                f' стал ниже предыдущего ({service.last_service_reading})! '
                'Странно, да?!'
            )
            # TODO Происходит подмена данных о последнем обслуживании, странно
            # что такая ситуация возможна:
            processing_service = service
            processing_service.last_service_reading = (
                validated_service_work.last_service_reading
            )

    # Если инфы нет вообще или появилась новая запись о сервисе -
    # создаём новый экземпляр (с которым будем работать далее):
    if not service or need_to_update:
        new_service_work: dict[str, Any] = validated_service_work.model_dump(
            context='create_update_mode'
        )
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
            logger.info(
                f'🔄 {message}. Изменен глобальный статус: '
                f'({old_request_status_id}) -> {upd_status.id}.'
            )
        else:
            logger.info(
                f'✅ {message}. Присвоен глобальный статус: {upd_status.id}.'
            )
