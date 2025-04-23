from datetime import datetime as dt
from typing import Optional

from pydantic import BaseModel, field_validator
from toir_app.convert_csv_to_py.convertation import normalize_service_name


class BaseCarData(BaseModel):
    """Базовая схема с общими полями для всех автомобильных данных"""
    base_interval: int
    dt_now: dt
    daily_distance: float
    reading_now: float
    last_service_reading: float  # не уверен, но будто он всегда должен быть

    # @field_validator('dt_now', mode='before')
    # @classmethod
    # def validate_dt_now(cls, value: str) -> dt:
    #     """Валидатор для dt_now"""
    #     if not value or not isinstance(value, str):
    #         raise ValueError("Неверный формат даты")
    #     return dt.strptime(value, "%d.%m.%Y %H:%M:%S")


class CarDataPoint(BaseCarData):
    """Расширенная схема с дополнительными полями"""
    personal_id: int
    grz: str
    car_model: str
    organization: str
    last_service_date: Optional[dt] = None
    last_service_view: Optional[str] = None
    next_service_view: Optional[str] = None

    # @field_validator('last_service_date', mode='before')
    # @classmethod
    # def validate_last_service_date(cls, value: str) -> Optional[dt]:
    #     """Валидатор для last_service_date"""
    #     if not value or not isinstance(value, str):
    #         return None
    #     try:
    #         return dt.strptime(value, "%d.%m.%Y %H:%M:%S")
    #     except ValueError:
    #         return None

    # @field_validator('last_service_view', 'next_service_view', mode='before')
    # @classmethod
    # def normalize_service_fields(cls, value: str) -> Optional[str]:
    #     """Валидатор для сервисных полей"""
    #     if not value or not isinstance(value, str):
    #         return None
    #     return normalize_service_name(value)
