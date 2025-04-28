from pydantic import BaseModel, Field

from toir_app.constants import SERVICE_STATUS_NAME_LEN


class ServiceNameID(BaseModel):
    """
    Схема видов Технического Обслуживания (только ID видов ТО).
    """

    id: int = Field(..., title='ID вида работ')


class ServiceNameBase(ServiceNameID):
    """Схема Видов технического обслуживания (ТО-1, ЗМ ДВС и тд) с ID."""
    name: str = Field(
        title='Вид работ',
        description='Сконвертированный вид работ',
        max_length=SERVICE_STATUS_NAME_LEN
    )
