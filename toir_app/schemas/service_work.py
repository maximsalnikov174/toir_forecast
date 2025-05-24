from datetime import datetime as dt
from typing import Optional

from pydantic import (
    BaseModel,
    Field,
    computed_field,
    field_validator,
    ValidationInfo
)


class ServiceWorksRequestStatus(BaseModel):
    """
    Схема записи о Сервисном Обслуживании (только ID вычисляемого статуса).
    """
    request_status_id: int


class CarAtributesInServiceWork(BaseModel):
    """
    Схема ServiceWork с полями, необходимыми для Car.

    Дополнительно - округление поля daily_distance до .1 знака.
    """
    # используется в индикаторах (нужны только 2 этих поля)
    request_reading: float
    daily_distance: float

    class Config:
        from_attributes = True

    @field_validator('daily_distance')
    def split_value(cls, value):
        """Округление суточного пробега до 1 знака после запятой."""
        return round(value, 1)


class ServiceWorkBase(CarAtributesInServiceWork):
    """
    Базовая схема записи о Сервисном Обслуживании.
    Дополнительное сравнение даты последнего сервиса и now()
    """
    car_id: int = Field(..., title='pk из таблицы Car')
    last_service_id: int = Field(..., title='pk из таблицы ServiceName')
    next_service_id: int = Field(..., title='pk из таблицы ServiceName')
    request_date: dt
    last_service_date: dt
    last_service_reading: float
    base_interval: int

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


class ServiceWorkWithZVRNumber(ServiceWorkBase):
    """
    Схема записи о Сервисном Обслуживании с номером ЗВР.
    """
    zvr_number: Optional[int]
    zvr_create_date: Optional[dt]
    service_work_completed: Optional[bool]

    @computed_field
    def delta_between_service_work_completed_and_now(self) -> Optional[int]:
        """Разница между сегодня и датой фактического завершения работ.

        Returns:
        - some days
        """
        if self.zvr_create_date:
            return (dt.now()-self.zvr_create_date).days
        return None
