import re
from typing import Optional, TYPE_CHECKING

from pydantic import BaseModel, Field, field_validator

from constants import pattern_grz
from logger.logger import logger
# from schemas.car_model import CarModelBase
# from schemas.organization import OrganizationID
from schemas.car_model import CarModelWithID
from schemas.organization import OrganizationResponse, OrganizationID
from schemas.special_status import (
    SpecialStatusForCarSchema,
    SpecialStatusWithTimestamp,
)

if TYPE_CHECKING:
    from schemas.service_work import CarAtributesInServiceWorkSplitDischarge


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
            logger.warning(f'Не удалось обработать ГРЗ {value}')
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
    status_associations: Optional[list[SpecialStatusForCarSchema]]


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


class CarsOrganization(BaseModel):
    """Только подразделение машины."""

    organization: OrganizationID


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

    indicators: Optional['CarAtributesInServiceWorkSplitDischarge']
    id: Optional[int]
