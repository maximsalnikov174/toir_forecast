from pydantic import BaseModel, Field

from constants import CAR_MODEL_NAME_LEN


class CarModelBase(BaseModel):
    """Базовая схема Моделей Автомобилей (name из OeBS)."""
    name: str = Field(
        title='Марка Автомобиля',
        description='Марка Автомобиля, указанная в OeBS',
        max_length=CAR_MODEL_NAME_LEN
    )


class CarModelID(BaseModel):
    """Базовая схема Моделей Автомобилей (только PK)."""
    id: int = Field(..., title='ID марки')


class CarModelWithID(CarModelBase, CarModelID):
    """Объедененная схема Моделей Автомобилей (PK + name)."""
