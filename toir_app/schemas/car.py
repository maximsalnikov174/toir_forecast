import re

from pydantic import Field, field_validator, BaseModel

from toir_app.constants import pattern_grz
from toir_app.schemas.car_model import CarModelID
from toir_app.schemas.organization import OrganizationID
from toir_app.schemas.special_status import SpecialStatusWithTimestamp


class CarBase(BaseModel):
    """
    Базовая схема модели Автомобиля (ID из OeBS, ГРЗ, модель ТС, цех)

    Выполняется валидация ГРЗ по шаблонам:
    - А 123 АВ 74/174/774
    - АВ 1234 74/174/774

    и отсекается всё лишнее.
    """
    personal_id: int = Field(
        ...,
        title='Уникальный ID из OeBS'
    )
    grz: str = Field(
        ...,
        title='ГРЗ'
    )
    car_model: CarModelID
    organization: OrganizationID

    @field_validator('grz')
    @classmethod
    def extract_and_validate_grz(cls, value: str) -> str:
        """Валидатор для grz"""
        if not value or not isinstance(value, str):
            raise ValueError('Неверный формат даты')
        clear_grz = re.search(pattern_grz, value, flags=re.IGNORECASE)
        if not clear_grz:
            raise ValueError('Не удалось обработать ГРЗ по шаблону')
        else:
            return clear_grz.group()


class CarBaseWithSpecialStatusAndTimestamp(
    CarBase, SpecialStatusWithTimestamp
):
    """Базовая модель Автомобиля расширяется статусами и временем."""
