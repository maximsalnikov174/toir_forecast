from datetime import datetime as dt

from pydantic import BaseModel, Field, field_validator, ValidationInfo


class ServiceWorkBase(BaseModel):
    """
    Базовая схема записи о Сервисном Обслуживании.

    Есть все поля, кроме расчётного состояния (статуса) на текущий момент.
    """
    car_id: int = Field(
        ...,
        title='pk из таблицы Car'
    )
    last_service_id: int = Field(
        ...,
        title='pk из таблицы ServiceName'
    )
    next_service_id: int = Field(
        ...,
        title='pk из таблицы ServiceName'
    )
    request_date: dt
    request_reading: float
    last_service_date: dt
    last_service_reading: float
    base_interval: int
    daily_distance: float

    @field_validator('last_service_date')
    def last_service_date_must_be_in_past(
        cls, value: dt, info: ValidationInfo
    ) -> dt:
        """
        Проверка, что дата последнего сервиса - в прошлом.

        Связано с тем, что в OeBS могут сделать ошибку завершить ЗВР в будущем.
        """
        if value > info.data['request_date']:
            # ЧТО-ТО С ЭТИМ В ИТОГЕ НАДО СДЕЛАТЬ, ЧТОБ НЕ ПАДАЛ ТЕСТ
            car_id = info.data['car_id']
            last_service_id = info.data['last_service_id']
            date = value.date().isoformat()
            # МОЖЕТ ЗДЕСЬ ВМЕСТО RAISE ДОЛЖНО БЫТЬ ЛОГИРОВАНИЕ И ВРЕМЕННАЯ ЗАПИСЬ ДЕФОЛТНОГО ЗНАЧЕНИЯ
            raise ValueError(
                f'Прошлое ТО id#{last_service_id} для ТС id#{car_id} '
                f'«выполнено» в будущем ({date}). Исправьте в OeBS!'
            )
        return value


class ServiceWorksRequestStatus(BaseModel):
    """
    Схема записи о Сервисном Обслуживании (только ID вычисляемого статуса).
    """
    request_status_id: int


class ServiceWorkWithRequestStatus(
    ServiceWorkBase, ServiceWorksRequestStatus
):
    """Полная базовая схема записи о Сервисном Обслуживании."""
