import asyncio

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  # Импорт CORS middleware

from api.routers import main_router
from core.config import settings
from logger.logger import logger

toir_app = FastAPI(title=settings.app_title)

# Подключаем роутер к приложению:
toir_app.include_router(main_router)

# Если нужен фронтенд:
if settings.cors_on_frontend:
    # ... и если локальная разработка, то доступно всем:
    allow_origins = (
        '*' if settings.for_local else 'http://toir.atu.mmk.ru:8811'
    )
    # ... тогда добавляем CORS middleware:
    toir_app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,  # От кого разрешаем подключения
        allow_credentials=True,
        allow_methods=["*"],  # Разрешаем все методы
        allow_headers=["*"],  # Разрешаем все заголовки
        expose_headers=["Content-Disposition"]
    )


async def main():
    """Основная асинхронная функция инициализации"""
    # Настраиваем конфигуратор:
    config = uvicorn.Config(
        'main:toir_app',
        reload=True
    )
    # 3. Запускаем FastAPI сервер:
    server = uvicorn.Server(config)
    # непонятно для чего, не ведаю, что творю)
    await server.serve()


if __name__ == '__main__':
    logger.info('Поехали!')
    asyncio.run(main())  # Запускаем асинхронный main()
