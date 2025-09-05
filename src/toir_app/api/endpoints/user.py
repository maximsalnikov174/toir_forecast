from fastapi import APIRouter

from constants import (
    ENDPOINT_URL_FOR_AUTH,
    ENDPOINT_URL_FOR_REGISTRATION,
)
from core.user import auth_backend, fastapi_users
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
