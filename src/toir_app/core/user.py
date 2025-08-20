import re
from typing import Optional, Union

from fastapi import Depends, Request
from fastapi_users import (
    BaseUserManager,
    exceptions,
    FastAPIUsers,
    IntegerIDMixin,
    InvalidPasswordException,
)
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.endpoints.bot import bot_schedular
from constants import (
    COMPANY_DOMAIN,
    ENDPOINT_URL_FOR_GET_TOKEN,
    LIFETIME_TOKEN_IN_SECONDS,
    MIN_PASSWORD_LEN,
    WORDS_AND_DIGITS,
)
from core.config import settings
from core.db import get_async_session
from exception import InvalidEmailException
from logger.logger import logger
from models import User
from schemas.user import UserCreate


class ExpandUserDatabase(SQLAlchemyUserDatabase):
    async def get(self, id):
        """Получение модели User вместе с relationships."""
        statement = select(self.user_table).options(
            selectinload(self.user_table.users_role),
            selectinload(self.user_table.users_organization)
            # когда появятся еще какие-то связи:
            # ...
        ).where(
            self.user_table.id == id
        )
        return await super()._get_user(statement)


# Асинхронный генератор обеспечивает доступ к БД через SQLAlchemy
# и в дальнейшем будет использоваться в качестве dependency
# для объекта класса UserManager:
async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield ExpandUserDatabase(session, User)

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

    async def get_by_email(self, user_email):
        """Получение пользователя с валидацией его email по шаблону ММК."""
        if not re.search(COMPANY_DOMAIN, user_email):
            raise InvalidEmailException(
                reason=(
                    'Емэйл должен быть вида '
                    'ivanov.ii@atu.mmk.ru или petrov@mmk.ru'
                )
            )
        return await super().get_by_email(user_email)

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

    async def authenticate(self, credentials):
        """Аутентификация пользователя.

        ## CHECKING:
        - неправильный email;
        - неправильный пароль;

        ## RETURNS:
        - уведомление в админ-чат Telegram (независимо от результата);
        - передача пользователя дальше в `/login` или `None + Exception`.
        """
        try:
            result = await super().authenticate(credentials)
            if not result:
                await bot_schedular.send_notification_for_admin(
                    f'🤦‍♂️ {credentials.username} не прошел аутентификацию.\n'
                    'Проблемы с паролем.'
                )
            else:
                await bot_schedular.send_notification_for_admin(
                    f'👋 {credentials.username} вошёл в систему.'
                )
                return result

        except InvalidEmailException:
            await bot_schedular.send_notification_for_admin(
                f'🤦‍♂️ {credentials.username} неверно указал свой email.'
            )

    async def on_after_register(
        self,
        user: User,
        request: Optional[Request] = None
    ):
        """Действие после успешной регистрации пользователя."""
        # Вместо print здесь можно было бы настроить отправку письма.
        logger.info(f'Пользователь {user.email} зарегистрирован.')
        msg = (
            f'👤 Новый пользователь: {user.name} {user.surname}\n'
            f'e-mail: {user.email}\n'
            f'подразделение #{user.organization_id}\n'
            f'роль #{user.role_id}'
        )
        await bot_schedular.send_notification_for_admin(msg=msg)


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
