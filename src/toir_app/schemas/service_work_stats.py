from datetime import datetime as dt
from typing import Any, Optional

from pydantic import BaseModel, Field, computed_field, field_serializer

from schemas.service_work import ServiceWorkEntrypointForMasterSchema
from models import ServiceStatus


class ServiceWorkStateBase(BaseModel):
    """Схема сбора статистики по состоянию ЗВР."""
    with_open_zvr: int = Field(..., title='С открытыми ЗВР')
    de_facto_completed: int = Field(..., title='Фактически завершены')
    without_zvr: int = Field(..., title='Пустые (без ЗВР)')

    class Config:
        from_attributes = True


class ServiceStatusStatsBase(BaseModel):
    """Схема сбора статистики по расчётным статусам для видов работ."""
    stats_date: dt = Field(..., title='Дата')
    danger_slice: ServiceWorkStateBase = Field(..., title='Превышение')
    time_has_come_slice: ServiceWorkStateBase = Field(..., title='В интервале')
    wait_moment_slice: ServiceWorkStateBase = Field(..., title='Подойдёт')
    no_need_slice: ServiceWorkStateBase = Field(..., title='Не нужно')
    bad_request_slice: ServiceWorkStateBase = Field(
        ..., title='Ошибка в расчёте'
    )

    class Config:
        from_attributes = True


class ServiceStats(ServiceWorkEntrypointForMasterSchema):
    """Получение данных для сбора статистики выполненных работ."""

    base_interval: int           # базовый интервал
    request_reading: float       # пробег на момент запроса
    last_service_reading: float  # пробег последнего ТО
    daily_distance: float        # среднесуточный пробег
    service_work_completed: dt   # дата закрытия ЗВР
    in_archive: bool             # статус нахождения в архиве
    request_status: Any          # расчётный статус

    @field_serializer('request_status')
    def serialize_request_status(
        self, request_status: ServiceStatus, _info: Any
    ):
        """Выпрямляет модель `ServiceStatus` в его поле `name`."""
        return request_status.name

    @computed_field
    def divergence(self) -> Optional[float]:
        """Отклонение фактического пробега от норматива (1 знак после «,»).

        Returns:
        - если значение (-) превышение;
        - если значение (+) недопробег.
        """
        if (
            self.request_reading
            and self.last_service_reading is not None
            and self.base_interval
        ):
            return round(
                (
                    self.last_service_reading
                    + self.base_interval
                    - self.request_reading
                ),
                1
            )
        return None

    @field_serializer('service_work_completed')
    def serialize_service_work_completed(
        self, service_work_completed: dt, _info: Any
    ) -> str:
        """Выпрямляет модель `ServiceName` в его поле `name`."""
        return service_work_completed.strftime('%d.%m.%Y')
