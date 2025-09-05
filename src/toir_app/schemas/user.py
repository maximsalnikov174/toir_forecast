import re
from http import HTTPStatus
from typing import Optional

from fastapi import HTTPException
from fastapi_users import schemas
from pydantic import BaseModel, Field, computed_field, field_validator

from constants import COMPANY_DOMAIN, PERSON_FULL_NAME_LEN
from schemas.organization import OrganizationResponse


class UserFullnameRead(BaseModel):
    """Схема с одним полем «полное имя пользователя» (Фамилия И.)."""
    name: str = Field(
        title='Имя',
        max_length=PERSON_FULL_NAME_LEN,
        exclude=True,
    )
    surname: str = Field(
        title='Фамилия',
        max_length=PERSON_FULL_NAME_LEN,
        exclude=True,
    )

    @computed_field
    def full_name(self) -> str:
        """Полное имя пользователя вида «Иванов И.»."""
        if self.name is not None and self.surname is not None:
            return f'{self.surname.capitalize()} {self.name.capitalize()[0]}.'


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
    role_id: int = Field(
        ..., title='ID из таблицы ролей в системе.'
    )
    users_organization: OrganizationResponse


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
    organization_id: int = Field(
        ..., title='ID из таблицы подразделений.'
    )
    role_id: int = Field(
        ..., title='ID из таблицы ролей в системе.'
    )

    @field_validator('email', mode='before')
    @classmethod
    def validate_email(cls, value: str) -> str:
        """Валидатор электронного ящика при регистрации пользователя."""
        if not re.search(COMPANY_DOMAIN, value):
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail={
                    'code': HTTPStatus.BAD_REQUEST,
                    'reason': (
                        'Емэйл должен быть вида '
                        'ivanov.ii@atu.mmk.ru или petrov@mmk.ru'
                    )
                }
            )
        return value


class UserUpdate(schemas.BaseUserUpdate):
    """Схема обновления данных пользователя.

    Можно изменить подразделение и/или роль(маловероятно)."""
    organization_id: Optional[int]
    role_id: Optional[int]
