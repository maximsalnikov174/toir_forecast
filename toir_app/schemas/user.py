from pydantic import Field

from toir_app.constants import PERSON_FULL_NAME_LEN
from toir_app.models.static_model import UserRole
from toir_app.schemas.mixins import BaseModelWithTimestamps
from toir_app.schemas.organization import OrganizationResponse


class UserBase(BaseModelWithTimestamps):
    """Базовая модель Пользователя системы."""
    surname: str = Field(
        title='Фамилия',
        max_length=PERSON_FULL_NAME_LEN
    )
    name: str = Field(
        title='Имя',
        max_length=PERSON_FULL_NAME_LEN
    )
    patronymic: str = Field(
        title='Отчество',
        max_length=PERSON_FULL_NAME_LEN
    )
    organization: OrganizationResponse = Field(
        title='Сотрудник цеха'
    )
    role: UserRole = Field(
        UserRole.READ_ONLY,
        title='Полномочия (из спр.)'
    )
