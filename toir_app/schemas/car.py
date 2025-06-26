import logging
import re
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from toir_app.constants import pattern_grz
# from toir_app.schemas.car_model import CarModelBase
# from toir_app.schemas.organization import OrganizationID
from toir_app.schemas.car_model import CarModelWithID
from toir_app.schemas.organization import OrganizationResponse
from toir_app.schemas.service_work import CarAtributesInServiceWork
from toir_app.schemas.special_status import SpecialStatusWithTimestamp


class CarOnlyIDs(BaseModel):
    """Перечень pk ТС (используется при построении строк главной таблицы)."""
    id: int = Field(..., serialization_alias='car_id', description='PK aka ID')


class CarStartParse(BaseModel):
    """
    Базовая схема модели Автомобиля.

    Используемые поля:
    - PK aka ID
    - (new) ID из OeBS *
    - (new) ГРЗ *
    """
    personal_id: int = Field(
        ..., title='Уникальный ID из OeBS (не путать с PK)'
    )
    grz: str = Field(..., title='ГРЗ')

    class Config:
        from_attributes = True

    @field_validator('grz')
    @classmethod
    def extract_and_validate_grz(cls, value: str) -> str:
        """
        Выполняется валидация ГРЗ по шаблонам:
        - А 123 АВ 74/174/774
        - АВ 1234 74/174/774

        и отсекается всё лишнее.
        """
        if not value or not isinstance(value, str):
            raise ValueError('Неверный формат ГРЗ')
        clear_grz = re.search(pattern_grz, value, flags=re.IGNORECASE)
        if not clear_grz:
            logging.warning(f'Не удалось обработать ГРЗ {value}')
            raise ValueError('Не удалось обработать ГРЗ по шаблону')
        else:
            return clear_grz.group()


class CarToDownloadInDB(CarStartParse):
    """Схема для загрузки данных из CSV-файла (не трогать!)."""
    car_model_id: int = Field(..., title='ID модели ТС')
    organization_id: int = Field(..., title='ID подразделения')


class CarBase(CarStartParse):
    """
    Базовая схема #2 модели Автомобиля.

    Используемые поля:
    - PK aka ID
    - ID из OeBS
    - ГРЗ
    - (new) ID специального статуса
    """
    special_status_id: Optional[int] = None


class CarBaseWithSpecialStatusAndTimestamp(
    CarBase, SpecialStatusWithTimestamp
):
    """(не используется) Схема Автомобиля расширяется статусами и временем."""


class CarWithCarModelAndOrganizationIDs(CarBase):
    """
    Расширенная схема модели Автомобиля.

    Используемые поля:
    - PK aka ID
    - ID из OeBS
    - ГРЗ
    - ID специального статуса
    - (new) ID марки ТС
    - (new) ID подразделения
    """
    car_model_id: int = Field(..., title='ID модели ТС')
    organization_id: int = Field(..., title='ID подразделения')


class CarWithCarModelFields(CarBase):
    """
    Расширенная схема модели Автомобиля.

    Используемые поля:
    - PK aka ID
    - ID из OeBS
    - ГРЗ
    - ID специального статуса
    - (new) Поля марки ТС
    """
    car_model: CarModelWithID


class CarWithCarModelAndOrganizationFields(CarWithCarModelFields):
    """
    Расширенная схема модели Автомобиля.

    Используемые поля:
    - PK aka ID
    - ID из OeBS
    - ГРЗ
    - ID специального статуса
    - Поля марки ТС
    - (new) Поля подразделения
    """
    organization: OrganizationResponse


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
    indicators: Optional[CarAtributesInServiceWork]
