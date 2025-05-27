from typing import Optional
from pydantic import BaseModel, Field


class OrganizationBase(BaseModel):
    """Базовая (только name) схема Подразделения (цеха)."""
    name: str = Field(
        ...,
        title='Объект в OeBS',
        description='Название подразделения в формате Юхх',
        pattern=r'^Ю\d{2}$',
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
        pattern=r'^\d-\w{1,3}$',
        examples=['2-МГ', '4-УСТ', '3-Л']
    )
