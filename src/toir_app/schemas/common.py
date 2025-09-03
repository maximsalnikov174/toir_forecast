from typing import Optional, Union

from pydantic import BaseModel, field_validator

from schemas.car import CarWithCarModelFields
from schemas.common_func import convert_value_with_discharge
from schemas.organization import OrganizationID


class CarsOrganization(BaseModel):
    """Только подразделение машины."""
    organization: OrganizationID


class CarAtributesInServiceWork(BaseModel):
    """
    Схема ServiceWork с полями, необходимыми для Car.

    Дополнительно - округление поля daily_distance до .1 знака.
    """

    # используется в индикаторах (нужны только 2 этих поля)
    request_reading: Union[float, str]
    daily_distance: float

    class Config:
        from_attributes = True

    @field_validator('daily_distance')
    def split_value(cls, value):
        """Округление суточного пробега до 1 знака после запятой."""
        return round(value, 1)


class CarAtributesInServiceWorkSplitDischarge(CarAtributesInServiceWork):
    """Схема ServiceWork с полями, необходимыми для представления Car."""

    request_reading: str

    @field_validator('request_reading', mode='before')
    def split_request_reading_value(cls, value):
        """Разделение общего пробега по разрядам."""
        return convert_value_with_discharge(value)


class CarExpandWithIndicators(CarWithCarModelFields):
    """
    Расширенная схема модели Автомобиля.

    Используемые поля:
    - PK aka ID
    - ID из OeBS
    - ГРЗ
    - ID специального статуса
    - Поля марки ТС
    - (new) Общий пробег
    - (new) Среднесуточный пробег
    """

    indicators: Optional[CarAtributesInServiceWorkSplitDischarge]
    id: Optional[int]
