from datetime import datetime as dt
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from toir_app.constants import (CAR_MODEL_NAME_LEN,
                                PERSON_FULL_NAME_LEN,
                                SERVICE_STATUS_NAME_LEN)
from toir_app.convert_csv_to_py.convertation import normalize_service_name


# -------------------------------ПЕРЕЧИСЛЕНИЯ-------------------------------

class Status(str, Enum):
    """
    Расчётные статусы (для вида обслуживания) записи из OeBS.
    """
    DANGER = '⚡ Превышение'
    TIME_HAS_COME = '⏰ Подошло'
    WAIT_MOMENT = '🎲 Ожидается в текущем периоде'
    NO_NEED = '❌ Нет необходимости'
    BAD_REQUEST = 'Не был расчитан'


class SpecialStatusForCar(str, Enum):
    """
    Глобальные статусы, устанавливающие особое состояние для ТС (для админа).

    Примеры статусов (доступно расширение):
    - к выбытию
    - на реализации
    - после ВР
    - ...
    """
    DISPOSAL = 'К выбытию'
    ON_SALE = 'На реализации'
    REMEDIAL_REPAIR = 'На восстановительном ремонте'


class UserRole(str, Enum):
    """Полномочия Пользователей (read_only, can_edit, admin)."""
    READ_ONLY = 'Только чтение'
    CAN_EDIT = 'Редактирует свой цех'
    ADMIN = 'Полный доступ'


# ----------------------------------МИКСИНЫ----------------------------------

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


# ------------------------СХЕМЫ КОНВЕРТАЦИИ RMT-321------------------------
class BaseCarData(BaseModel):
    """Базовая схема с общими полями для всех автомобильных данных"""
    base_interval: int
    dt_now: dt
    daily_distance: float
    reading_now: float
    last_service_reading: float  # не уверен, но будто он всегда должен быть

    @field_validator('dt_now', mode='before')
    @classmethod
    def validate_dt_now(cls, value: str) -> dt:
        """Валидатор для dt_now"""
        if not value or not isinstance(value, str):
            raise ValueError("Неверный формат даты")
        return dt.strptime(value, "%d.%m.%Y %H:%M:%S")


class CarDataPoint(BaseCarData):
    """Расширенная схема с дополнительными полями"""
    personal_id: int
    grz: str
    car_model: str
    organization: str
    last_service_date: Optional[dt] = None
    last_service_view: Optional[str] = None
    next_service_view: Optional[str] = None

    @field_validator('last_service_date', mode='before')
    @classmethod
    def validate_last_service_date(cls, value: str) -> Optional[dt]:
        """Валидатор для last_service_date"""
        if not value or not isinstance(value, str):
            return None
        try:
            return dt.strptime(value, "%d.%m.%Y %H:%M:%S")
        except ValueError:
            return None

    @field_validator('last_service_view', 'next_service_view', mode='before')
    @classmethod
    def normalize_service_fields(cls, value: str) -> Optional[str]:
        """Валидатор для сервисных полей"""
        if not value or not isinstance(value, str):
            return None
        return normalize_service_name(value)


# ------------------------------ОСНОВНЫЕ СХЕМЫ------------------------------
class OrganizationBase(BaseModel):
    """Базовая модель Подразделения (цеха)."""
    name: str = Field(
        ...,
        title='Объект в OeBS',
        description='Название подразделения в формате Юхх',
        pattern=r'^Ю\d{2}$',
        examples=['Ю51']
    )


class OrganizationResponse(OrganizationBase):
    """Модель Подразделения (цеха) для ответа API."""
    id: int = Field(..., title='ID подразделения')
    normal_name: str = Field(
        ...,
        title='Номер цеха',
        description='Номер цеха перевозок (привычный)',
        pattern=r'^\d-\w{1,3}$',
        examples=['2-МГ', '4-УСТ', '3-Л']
    )


class UserBase(BaseModelWithTimestamps):
    """Базовая модель Пользователя системы."""
    surname: str = Field(
        title='Фамилия',
        max_length=PERSON_FULL_NAME_LEN
    )
    name: str = Field(
        title='Имя',
        max_length=PERSON_FULL_NAME_LEN
    )
    patronymic: str = Field(
        title='Отчество',
        max_length=PERSON_FULL_NAME_LEN
    )
    organization: OrganizationResponse = Field(
        title='Сотрудник цеха'
    )
    role: UserRole = Field(
        UserRole.READ_ONLY,
        title='Полномочия (из спр.)'
    )


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


class CarModelBase(BaseModel):
    """Базовая модель Моделей Автомобилей (из справочника)."""
    id: int = Field(..., title='ID марки')
    name: str = Field(
        title='Марка Автомобиля',
        description='Марка Автомобиля, указанная в OeBS',
        max_length=CAR_MODEL_NAME_LEN
    )


class ServiceNameBase(BaseModel):
    """Базовая модель Видов технического обслуживания (ТО-1, ЗМ ДВС и тд)."""
    id: int = Field(..., title='ID вида работ')
    name: str = Field(
        title='Вид работ',
        description='Сконвертированный вид работ',
        max_length=SERVICE_STATUS_NAME_LEN
    )


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
