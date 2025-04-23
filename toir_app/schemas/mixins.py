from datetime import datetime as dt
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class TimestampMixin(BaseModel):
    """
    Миксин для добавления временных меток создания и обновления.

    Добавляет временные метки:
    - created_at - фиксация создания
    - updated_at - фиксация изменения
    """
    created_at: dt = Field(
        default_factory=dt.now,
        title='Дата создания',
        frozen=True
    )
    updated_at: Optional[dt] = Field(
        None,
        title='Дата последнего обновления'
    )


class ArchiveMixin(BaseModel):
    """
    Миксин для архивных записей.

    Переводит запись в архив параметром:
    - in_archive=True
    """
    in_archive: bool = Field(
        False,
        title='В архиве?',
        description='Флаг, указывающий находится ли запись в архиве'
    )


class BaseModelWithTimestamps(TimestampMixin, ArchiveMixin):
    """Базовая модель с временными метками и архивным статусом."""
    model_config = ConfigDict(from_attributes=True)  # Для работы с ORM ЧИХУА?
