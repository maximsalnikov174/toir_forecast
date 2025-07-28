import asyncio

import uvicorn
from fastapi import FastAPI

from api.routers import main_router
from convert_csv_to_py.upload_data import (
    need_to_upload_datas,
    upload_all_users_data_in_db,
)
from core.config import settings
from core.db import AsyncSessionLocal
from core.init_db import create_first_superuser
from crud.organization import get_organization_by_name
from fastapi.middleware.cors import CORSMiddleware  # Импортируем CORS middleware
from crud.role import get_superuser_role
from exception import StaticDataInDBNotFoundException
from logger.logger import logger
from models import StaticOrganization

toir_app = FastAPI(title=settings.app_title)

# Подключаем роутер к приложению:
toir_app.include_router(main_router)

# Добавляем CORS middleware
toir_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешаем запросы от всех доменов
    allow_credentials=True,
    allow_methods=["POST", "DELET", "GET", "PATCH"],  # Разрешаем все методы
    allow_headers=["*"],  # Разрешаем все заголовки
)

async def main():
    """Основная асинхронная функция инициализации"""
    async with AsyncSessionLocal() as download_session:
        try:
            # Проверяем наполнение БД статическими данными:
            await get_organization_by_name(
                name=StaticOrganization.ORG_UPR.value,
                session=download_session
            )
        except StaticDataInDBNotFoundException:
            logger.info('Началась загрузка статических данных.')
            # 1. Загружаем enum-значения в БД (по итогу - коммит, он нужен)
            await upload_all_users_data_in_db(
                need_to_upload_datas, download_session
            )
            await download_session.commit()
            logger.info('Завершилась загрузка статических данных.')

            logger.info('Начало создания первого суперпользователя.')
            organization = await get_organization_by_name(
                name=StaticOrganization.ORG_UPR.value,
                session=download_session
            )
            role_id = await get_superuser_role(session=download_session)
            await create_first_superuser(
                role_id=role_id,
                organization_id=organization.id
            )
            logger.info('Суперпользователь создан.')
            await download_session.commit()

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
