# Создание суперпользователя при инициализации базы данных (лайфхак):

import contextlib

from fastapi_users.exceptions import UserAlreadyExists
from pydantic import EmailStr

from core.config import settings
from core.db import get_async_session
from core.user import get_user_db, get_user_manager
from schemas.user import UserCreate

# Превращаем асинхронные генераторы в асинхронные менеджеры контекста.
get_async_session_context = contextlib.asynccontextmanager(get_async_session)
get_user_db_context = contextlib.asynccontextmanager(get_user_db)
get_user_manager_context = contextlib.asynccontextmanager(get_user_manager)


# Корутина, создающая юзера с переданным email и паролем.
# Возможно создание суперюзера при передаче аргумента is_superuser=True.
async def create_user(
        email: EmailStr,
        password: str,
        name: str,
        surname: str,
        organization_id: int,
        role_id: int,
        is_superuser: bool = False
):
    try:
        # Получение объекта асинхронной сессии.
        async with get_async_session_context() as session:
            # Получение объекта класса SQLAlchemyUserDatabase.
            async with get_user_db_context(session) as user_db:
                # Получение объекта класса UserManager.
                async with get_user_manager_context(user_db) as user_manager:
                    # Создание пользователя.
                    await user_manager.create(
                        UserCreate(
                            email=email,
                            password=password,
                            is_superuser=is_superuser,
                            name=name,
                            surname=surname,
                            organization_id=organization_id,
                            role_id=role_id
                        )
                    )
    # В случае, если такой пользователь уже есть, ничего не предпринимать.
    except UserAlreadyExists:
        pass


# Корутина, проверяющая, указаны ли в настройках данные для суперюзера.
# Если да, то вызывается корутина create_user для создания суперпользователя.
async def create_first_superuser(role_id: int, organization_id: int):
    if (
        settings.first_superuser_email is not None
        and settings.first_superuser_password is not None
        and settings.superuser_name is not None
        and settings.superuser_surname is not None
    ):
        await create_user(
            email=settings.first_superuser_email,
            password=settings.first_superuser_password,
            is_superuser=True,
            name=settings.superuser_name,
            surname=settings.superuser_surname,
            organization_id=organization_id,
            role_id=role_id
        )
