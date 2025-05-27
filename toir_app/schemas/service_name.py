from pydantic import BaseModel, Field

from toir_app.constants import SERVICE_STATUS_NAME_LEN


class ServiceNameID(BaseModel):
    """
    Базовая схема видов Сервисного Обслуживания (только ID видов ТО).
    """

    id: int = Field(
        ...,
        title='ID вида работ',
        serialization_alias='service_name_id')


class ServiceNameBase(ServiceNameID):
    """Схема Видов сервисного обслуживания (ТО-1, ЗМ ДВС и тд) с ID.

    (используется при построении шапки главной таблицы).
    """
    name: str = Field(
        title='Вид работ',
        description='Сконвертированный вид работ',
        max_length=SERVICE_STATUS_NAME_LEN
    )
