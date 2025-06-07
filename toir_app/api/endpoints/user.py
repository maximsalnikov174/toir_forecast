from fastapi import APIRouter

from toir_app.constants import ENDPOINT_URL_FOR_AUTH
from toir_app.core.user import auth_backend, fastapi_users
from toir_app.schemas.user import UserCreate, UserRead, UserUpdate


router = APIRouter()

# Аутентификационный роутер предоставляет доступ к эндпоинтам:
# /login (для аутентификации)
# /logout (для завершения сессии) для выбранного бэкенда аутентификации;
router.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix=ENDPOINT_URL_FOR_AUTH,
    tags=['auth'],
)

# Регистрационный роутер предоставляет доступ к эндпоинту:
# /register (для регистрации нового пользователя)
router.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix='/auth',
    tags=['auth'],
)

# Роутер пользователей предоставляет доступ к эндпоинтам:
# управления пользователями (чтение из БД, удаление, обновление и тд).

# Сохраняем роутер в переменную.
users_router = fastapi_users.get_users_router(UserRead, UserUpdate)
# Из списка эндпоинтов роутера исключаем ручку delete_user.
users_router.routes = [
    rout for rout in users_router.routes if rout.name != 'users:delete_user'
]
# Подключаем изменённый роутер по старому адресу.
router.include_router(
    users_router,
    prefix='/users',
    tags=['users'],
)
