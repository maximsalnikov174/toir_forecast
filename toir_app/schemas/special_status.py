from typing import Optional

from pydantic import Field, BaseModel

from toir_app.models.static_model import SpecialStatusForCarBase
from toir_app.schemas.mixins import TimestampMixin
# from toir_app.schemas.user import UserRead


class SpecialStatusWithTimestamp(TimestampMixin):
    """
    Модель статуса Автомобиля с меткой времени и информацией о Пользователе.

    Примеры статусов:
    - к выбытию
    - на реализации
    - после ВР
    """
    status: Optional[SpecialStatusForCarBase] = Field(
        None,
        title='Текущий статус'
    )
    # from_user: Optional[UserRead] = Field(
    #     None,
    #     title='Пользователь, присвоивший статус'
    # )


class FullSpecialStatusSchemas(BaseModel):
    id: int
    name: str
