from datetime import datetime as dt

from pydantic import BaseModel, Field


class ServiceWorkBase(BaseModel):
    car_id: int = Field(
        ...,
        title='pk из таблицы Car'
    )
    last_service_id: int = Field(
        ...,
        title='pk из таблицы ServiceName'
    )
    next_service_id: int = Field(
        ...,
        title='pk из таблицы ServiceName'
    )
    last_service_date: dt
    last_service_reading: float
    request_date: dt
    request_reading: float
    base_interval: int
    daily_distance: float


class ServiceWorkWithRequestStatus(ServiceWorkBase):
    request_status_id: int
