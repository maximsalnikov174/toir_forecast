import re
from typing import Optional

from pydantic import Field, field_validator, BaseModel

from toir_app.constants import pattern_grz
# from toir_app.schemas.car_model import CarModelBase
# from toir_app.schemas.organization import OrganizationID
from toir_app.schemas.car_model import CarModelWithID
from toir_app.schemas.organization import OrganizationResponse
from toir_app.schemas.service_work import CarAtributesInServiceWork
from toir_app.schemas.special_status import SpecialStatusWithTimestamp


class CarBase(BaseModel):
    """
    Базовая схема модели Автомобиля.

    Используемые поля:
    - ID из OeBS
    - ГРЗ
    - ID специального статуса
    """
    personal_id: int = Field(..., title='Уникальный ID из OeBS')
    grz: str = Field(..., title='ГРЗ')
    special_status_id: Optional[int] = None

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
            raise ValueError('Не удалось обработать ГРЗ по шаблону')
        else:
            return clear_grz.group()


class CarWithCarModelAndOrganizationIDs(CarBase):
    """
    Расширенная схема модели Автомобиля.

    Используемые поля:
    - ID из OeBS
    - ГРЗ
    - ID марки ТС
    - ID подразделения
    - ID специального статуса
    """
    car_model_id: int = Field(..., title='ID модели ТС')
    organization_id: int = Field(..., title='ID подразделения')


class CarWithCarModelAndOrganizationFields(CarBase):
    """
    Расширенная схема модели Автомобиля.

    Используемые поля:
    - ID из OeBS
    - ГРЗ
    - Поля марки ТС
    - Поля подразделения
    - ID специального статуса
    """
    car_model: CarModelWithID
    organization: OrganizationResponse


class CarExpandWithIndicators(CarWithCarModelAndOrganizationFields):
    """
    Расширенная схема модели Автомобиля.

    Используемые поля:
    - ID из OeBS
    - ГРЗ
    - Поля марки ТС
    - Поля подразделения
    - ID специального статуса
    - Общий пробег
    - Среднесуточный пробег
    """
    indicators: Optional[CarAtributesInServiceWork]


class CarBaseWithSpecialStatusAndTimestamp(
    CarBase, SpecialStatusWithTimestamp
):
    """Базовая модель Автомобиля расширяется статусами и временем."""
