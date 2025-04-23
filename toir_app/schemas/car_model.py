from pydantic import BaseModel, Field

from toir_app.constants import CAR_MODEL_NAME_LEN


class CarModelBase(BaseModel):
    """Базовая модель Моделей Автомобилей (из справочника)."""
    id: int = Field(..., title='ID марки')
    name: str = Field(
        title='Марка Автомобиля',
        description='Марка Автомобиля, указанная в OeBS',
        max_length=CAR_MODEL_NAME_LEN
    )
