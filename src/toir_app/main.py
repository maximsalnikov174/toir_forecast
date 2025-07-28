import asyncio

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  # Импортируем CORS middleware

from api.routers import main_router
from core.config import settings
from logger.logger import logger

toir_app = FastAPI(title=settings.app_title)

# Подключаем роутер к приложению:
toir_app.include_router(main_router)

# Добавляем CORS middleware
toir_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешаем запросы от всех доменов
    allow_credentials=True,
    allow_methods=["*"],  # Разрешаем все методы
    allow_headers=["*"],  # Разрешаем все заголовки
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

# При запуске приложения через python main.py, работа с env-файлом строится
# иначе — нужно указать полный или относительный путь до env-файла либо
# указать его в параметрах метода uvicorn.run()
