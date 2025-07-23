from pydantic import BaseModel, Field


class StationBase(BaseModel):
    """Базовая схема Сервисных Организаций."""
    id: int
    name: str = Field(
        title='Сервисная организация',
        description='Название сервисной организации (например, УРЛА, УРГА)',
    )

    class Config:
        from_attributes = True
