from datetime import datetime as dt

from pydantic import BaseModel, Field


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
