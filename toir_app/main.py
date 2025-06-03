import asyncio
import os

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  # Импортируем CORS middleware
from dotenv import load_dotenv

from toir_app.core.db import AsyncSessionLocal
from toir_app.api.routers import main_router
from toir_app.core.config import settings
from toir_app.convert_csv_to_py.parse_data import (
    convert_csv_to_list,
    upload_filedata_in_db
)
from toir_app.convert_csv_to_py.upload_data import (
    upload_all_users_data_in_db,
    need_to_upload_datas
)

load_dotenv()  # подгружаем переменные из env

toir_app = FastAPI(title=settings.app_title)

# Добавляем CORS middleware
toir_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешаем запросы от всех доменов
    allow_credentials=True,
    allow_methods=["*"],  # Разрешаем все методы
    allow_headers=["*"],  # Разрешаем все заголовки
)

# Подключаем роутер к приложению:
toir_app.include_router(main_router)

# Находим файл для загрузки данных:
script_dir = os.path.dirname(os.path.abspath(__file__))
file_path = f'{script_dir}/dataset_from_oebs/rmt321_ATU_full.csv'


async def main():
    """Основная асинхронная функция инициализации"""
    async with AsyncSessionLocal() as download_session:
        if os.environ['UPLOAD_STATIC_DATA_FROM_CSV'].lower() == 'true':
            # 1. Загружаем enum-значения в БД (по итогу - коммит, он нужен)
            await upload_all_users_data_in_db(
                need_to_upload_datas, download_session
            )

        if os.environ['UPLOAD_DATA_FROM_CSV'].lower() == 'true':
            # 2. Конвертируем CSV и обновляем БД
            lst = await convert_csv_to_list(file_path)  # нужно ли здесь async?

            # TODO
            # Следующие 2 строчки - место для БОЛЬШОГО рефакторинга:
            # Можно (читать-НУЖНО!) проверять, чтобы не было в сессии и в базе
            for element in lst:
                await upload_filedata_in_db(element, download_session)

    # 3. Запускаем FastAPI сервер
    # (не понятно, как тут дальше начнет работать сессия)
    config = uvicorn.Config(
        'toir_app.main:toir_app',
        reload=True
    )
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == '__main__':
    # Запускаем асинхронный main()
    asyncio.run(main())