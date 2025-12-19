import json

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_users.authentication import AuthenticationBackend
from sqlalchemy.ext.asyncio import AsyncSession

from constants import (
    ENDPOINT_URL_FOR_AUTH,
    ENDPOINT_URL_FOR_REGISTRATION,
)
from core.db import get_async_session
from core.user import auth_backend, fastapi_users
from crud.user import user_dao
from schemas.user import UserCreate, UserRead, UserReadBase, UserUpdate

router = APIRouter()

# Аутентификационный роутер предоставляет доступ к эндпоинтам:
# /login (для аутентификации)
# /logout (для завершения сессии) для выбранного бэкенда аутентификации;
router.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix=ENDPOINT_URL_FOR_AUTH,
    tags=['user_auth'],
)


@router.get(
    '/user/secret/get_token_for_use_in_telegram/{user_tg_account}',
    tags=['telegram']
)
async def get_user_info_and_token_for_use_in_tg(
    user_tg_account: int,
    session: AsyncSession = Depends(get_async_session),
    auth_backend: AuthenticationBackend = Depends(lambda: auth_backend)
):
    """Получение инфы о пользователе и его токена для tg-запросов."""
    user = await user_dao.get_by_tg_account(user_tg_account, session)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Пользователь не найден.',
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Пользователь не в списке активных пользователей.',
        )
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Пользователь не валидирован администратором.',
        )

    token_data = await auth_backend.login(auth_backend.get_strategy(), user)

    return {
        'token': json.loads(token_data.body),
        'user': user,
    }

# Регистрационный роутер предоставляет доступ к эндпоинту:
# /register (для регистрации нового пользователя)
router.include_router(
    fastapi_users.get_register_router(
        user_schema=UserReadBase,
        user_create_schema=UserCreate
    ),
    prefix=ENDPOINT_URL_FOR_REGISTRATION,
    tags=['user_registration'],
)

# Роутер пользователей предоставляет доступ к эндпоинтам:
# управления пользователями (чтение из БД, удаление, обновление и тд).
# 1. Сохраняем роутер в переменную.
users_router = fastapi_users.get_users_router(UserRead, UserUpdate)
# 2. Из списка эндпоинтов роутера исключаем ручки delete и patch.
users_router.routes = [
    rout for rout in users_router.routes
    if rout.name not in ['users:delete_user', 'users:patch_current_user']
]
# 3. Подключаем изменённый роутер по старому адресу.
router.include_router(
    users_router,
    prefix='/users',
    tags=['user_about'],
)
