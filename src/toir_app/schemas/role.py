from pydantic import BaseModel, Field

from constants import MIN_ROLE_LEN, MAX_ROLE_LEN


class RoleCreate(BaseModel):
    """Базовая схема ролей пользователей."""

    name: str = Field(
        title='Название роли',
        description=(
            'Название роли (например, «только чтение», «Мастер (станции)»)'
        ),
        min_length=MIN_ROLE_LEN,
        max_length=MAX_ROLE_LEN,
    )

    class Config:
        from_attributes = True


class RoleBase(RoleCreate):
    """Схема ролей пользователей."""

    id: int
