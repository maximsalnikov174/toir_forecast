from typing import Optional
from fastapi_users import schemas
from pydantic import Field

from toir_app.constants import PERSON_FULL_NAME_LEN


class UserRead(schemas.BaseUser[int]):
    """Схема с базовыми полями модели пользователя."""
    name: str = Field(
        title='Имя',
        max_length=PERSON_FULL_NAME_LEN
    )
    surname: str = Field(
        title='Фамилия',
        max_length=PERSON_FULL_NAME_LEN
    )
    organization_id = Field(
        ..., title='ID из таблицы подразделений.'
    )
    role_id = Field(
        ..., title='ID из таблицы ролей в системе.'
    )


class UserCreate(schemas.BaseUserCreate):
    """Схема создания нового пользователя."""
    name: str = Field(
        title='Имя',
        max_length=PERSON_FULL_NAME_LEN
    )
    surname: str = Field(
        title='Фамилия',
        max_length=PERSON_FULL_NAME_LEN
    )
    organization_id = Field(
        ..., title='ID из таблицы подразделений.'
    )
    role_id = Field(
        ..., title='ID из таблицы ролей в системе.'
    )


class UserUpdate(schemas.BaseUserUpdate):
    """Схема обновления данных пользователя.

    Можно изменить подразделение и/или роль(маловероятно)."""
    organization_id = Optional[int]
    role_id = Optional[int]
