import re
from typing import Optional, Union

from fastapi import Depends, Request
from fastapi_users import (
    BaseUserManager, FastAPIUsers, IntegerIDMixin, InvalidPasswordException
)
from fastapi_users.authentication import (
    AuthenticationBackend, BearerTransport, JWTStrategy
)
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from toir_app.constants import (
    ENDPOINT_URL_FOR_GET_TOKEN,
    LIFETIME_TOKEN_IN_SECONDS,
    MIN_PASSWORD_LEN,
    WORDS_AND_DIGITS
)
from toir_app.core.config import settings
from toir_app.core.db import get_async_session
from toir_app.models import User
from toir_app.schemas.user import UserCreate


# Асинхронный генератор обеспечивает доступ к БД через SQLAlchemy
# и в дальнейшем будет использоваться в качестве dependency
# для объекта класса UserManager:
async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, User)

# Определяем транспорт: передавать токен будем
# через заголовок HTTP-запроса Authorization: Bearer
bearer_transport = BearerTransport(tokenUrl=ENDPOINT_URL_FOR_GET_TOKEN)


# Определяем стратегию: хранение токена в виде JWT.
def get_jwt_strategy() -> JWTStrategy:
    # В специальный класс из настроек приложения
    # передаётся секретное слово, используемое для генерации токена.
    # Вторым аргументом передаём срок действия токена в секундах.
    return JWTStrategy(
        secret=settings.secret, lifetime_seconds=LIFETIME_TOKEN_IN_SECONDS
    )


# Создаём объект бэкенда аутентификации с выбранными параметрами.
auth_backend = AuthenticationBackend(
    name='jwt',  # Произвольное имя бэкенда (должно быть уникальным).
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)


class UserManager(IntegerIDMixin, BaseUserManager[User, int]):

    async def validate_password(
        self,
        password: str,
        user: Union[UserCreate, User],
    ) -> None:
        """Условия валидации пароля.

        Returns:
        - При успешной валидации - ничего.
        - При ошибке валидации - вызван спецкласс InvalidPasswordException.
        """
        if not re.search(WORDS_AND_DIGITS, password):
            raise InvalidPasswordException(
                reason=(
                    'В пароле должны быть буквы (A-Z, a-z) и цифры. Это важно!'
                )
            )
        if len(password) < MIN_PASSWORD_LEN:
            raise InvalidPasswordException(
                reason=(
                    'Одумайтесь, пароль должен содержать'
                    f' не менее {MIN_PASSWORD_LEN} символов'
                )
            )

    async def on_after_register(
        self,
        user: User,
        request: Optional[Request] = None
    ):
        """Действие после успешной регистрации пользователя."""
        # Вместо print здесь можно было бы настроить отправку письма.
        print(f'Пользователь {user.email} зарегистрирован.')


async def get_user_manager(user_db=Depends(get_user_db)):
    """Корутина, возвращающая объект класса UserManager."""
    yield UserManager(user_db)


# Создаём центральный объект класса FastAPIUsers —
# объект, связывающий объект класса UserManager и бэкенд аутентификации.
fastapi_users = FastAPIUsers[User, int](
    get_user_manager,
    [auth_backend],
)

# Методы FastAPIUsers, которые будут использоваться в системе DI для:
# получения текущего пользователя при выполнении запросов
current_user = fastapi_users.current_user(active=True)

# разграничения прав для эндпоинтов, доступных только суперпользователю
current_superuser = fastapi_users.current_user(active=True, superuser=True)
