from pydantic import Field

from toir_app.schemas.car_model import CarModelBase
from toir_app.schemas.organization import OrganizationResponse
from toir_app.schemas.special_status import SpecialStatusWithTimestamp


class CarBase(SpecialStatusWithTimestamp):
    """Базовая модель Автомобиля."""
    personal_id: int = Field(
        ...,
        title='Уникальный ID из OeBS'
    )
    grz: str = Field(
        ...,
        title='ГРЗ'
        # TODO Добавить проверку по шаблону re
    )
    car_model: CarModelBase = Field(
        ...,
        title='Марка Автомобиля (из спр.)'
    )
    organization: OrganizationResponse = Field(
        ...,
        title='Находится в ЦП (из спр.)'
    )
