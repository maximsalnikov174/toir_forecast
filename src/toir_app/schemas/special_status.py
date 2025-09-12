from datetime import date
from typing import Optional

from pydantic import BaseModel, Field

from models.static_model import SpecialStatusForCarBase
from schemas.mixins import TimestampMixin
# from schemas.user import UserRead


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


class SpecialStatusForCarSchema(BaseModel):
    special_status_id: int
    comment: Optional[str] = None
    date_left: date
    is_active: bool
    assigned_by_user_id: int
    id: int
