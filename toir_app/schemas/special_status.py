from typing import Optional

from pydantic import Field, BaseModel

from toir_app.models.static_model import SpecialStatusForCar
from toir_app.schemas.mixins import TimestampMixin
from toir_app.schemas.user import UserBase


class SpecialStatusWithTimestamp(TimestampMixin):
    """
    Модель статуса Автомобиля с меткой времени и информацией о Пользователе.

    Примеры статусов:
    - к выбытию
    - на реализации
    - после ВР
    """
    status: Optional[SpecialStatusForCar] = Field(
        None,
        title='Текущий статус'
    )
    from_user: Optional[UserBase] = Field(
        None,
        title='Пользователь, присвоивший статус'
    )


class FullSpecialStatusSchemas(BaseModel):
    id: int
    name: str
