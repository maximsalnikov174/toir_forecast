from pydantic import Field, BaseModel

from toir_app.models.static_model import Status


class ServiceStatusSchema(BaseModel):
    """
    Схема для модели ServiceStatus для карточки вида сервисного обслуживания.

    Примеры статусов:
    - Превышение
    - Входит в 10%
    - Подойдет в этом месяце
    - Не требуется

    Поля:
    - ID
    - Имя статуса
    """
    id: int
    name: Status = Field(
        ..., title='Расчётный статус', serialization_alias='status_name'
    )
