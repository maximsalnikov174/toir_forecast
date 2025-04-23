from pydantic import BaseModel, Field

from toir_app.constants import SERVICE_STATUS_NAME_LEN


class ServiceNameBase(BaseModel):
    """Базовая модель Видов технического обслуживания (ТО-1, ЗМ ДВС и тд)."""
    id: int = Field(..., title='ID вида работ')
    name: str = Field(
        title='Вид работ',
        description='Сконвертированный вид работ',
        max_length=SERVICE_STATUS_NAME_LEN
    )
