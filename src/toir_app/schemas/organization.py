from typing import Optional
from pydantic import BaseModel, Field

from constants import (
    ORGANIZATION_NORMAL_NAME_PATTERN,
    ORGANIZATION_BASE_NAME_PATTERN,
)


class OrganizationBase(BaseModel):
    """Базовая (только name) схема Подразделения (цеха)."""
    name: str = Field(
        ...,
        title='Объект в OeBS',
        description='Название подразделения в формате Юхх',
        pattern=ORGANIZATION_BASE_NAME_PATTERN,
        examples=['Ю51']
    )


class OrganizationID(BaseModel):
    """Базовая (только ID) схема Подразделения (цеха)."""
    id: int = Field(..., title='ID подразделения')


class OrganizationResponse(OrganizationID, OrganizationBase):
    """Схема Подразделения (цеха) для ответа API."""
    normal_name: Optional[str] = Field(
        None,
        title='Номер цеха',
        description='Номер цеха перевозок (привычный)',
        pattern=ORGANIZATION_NORMAL_NAME_PATTERN,
        examples=['2-МГ', '4-УСТ', '3-Л', 'УРЛА', 'УРГА']
    )
    station_id: Optional[int]

    class Config:
        from_attributes = True
