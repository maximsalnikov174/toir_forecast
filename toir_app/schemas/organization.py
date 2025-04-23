from pydantic import BaseModel, Field


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
