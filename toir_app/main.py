import asyncio
import logging
import os
from array import array

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from tqdm import tqdm

from toir_app.api.routers import main_router
from toir_app.constants import UPLOAD_FILE_DIR
from toir_app.convert_csv_to_py.parse_data import (convert_csv_to_list,
                                                   upload_filedata_in_db)
from toir_app.convert_csv_to_py.upload_data import (
    need_to_upload_datas, upload_all_users_data_in_db)
from toir_app.core.config import settings
from toir_app.core.db import AsyncSessionLocal
from toir_app.core.init_db import create_first_superuser
from toir_app.crud.car import push_cars_in_archive
from toir_app.crud.organization import get_organization_by_name
from toir_app.crud.role import get_superuser_role
from toir_app.crud.service_work import (add_service_works_in_archive,
                                        get_active_service_work_list_by_car)
from toir_app.crud.stats import add_statement_after_loading_csv_file
from toir_app.logging.logger import configure_logging

load_dotenv()  # подгружаем переменные из env

toir_app = FastAPI(title=settings.app_title)

# Подключаем роутер к приложению:
toir_app.include_router(main_router)

# Находим файл для загрузки данных:
script_dir = os.path.dirname(os.path.abspath(__file__))
date_in_data: str = os.environ['DATE_IN_DATA']
file_path = f'{script_dir}{UPLOAD_FILE_DIR}{date_in_data}.csv'
logging.debug(f'Dataset filename: {UPLOAD_FILE_DIR}{date_in_data}.csv')


async def main():
    """Основная асинхронная функция инициализации"""
    async with AsyncSessionLocal() as download_session:
        try:
            await get_organization_by_name(
                name='Ю80', session=download_session
            )
        except HTTPException:
            logging.info('Началась загрузка статических данных.')
            # 1. Загружаем enum-значения в БД (по итогу - коммит, он нужен)
            await upload_all_users_data_in_db(
                need_to_upload_datas, download_session
            )
            logging.info('Завершилась загрузка статических данных.')

            logging.info('Начало создания первого суперпользователя.')
            organization = await get_organization_by_name(
                name='Ю80', session=download_session
            )
            role_id = await get_superuser_role(session=download_session)
            await create_first_superuser(
                role_id=role_id,
                organization_id=organization.id
            )
            logging.info('Суперпользователь создан.')
            await download_session.commit()

        if os.environ['UPLOAD_DATA_FROM_CSV'].lower() == 'true':
            logging.info('Началась загрузка данных из CSV-файла.')
            # 2. Конвертируем CSV и обновляем БД
            lst = await convert_csv_to_list(file_path)  # нужно ли здесь async?

            # Создаём множество ТС в CSV-файле:
            car_list = array('H')

            # TODO
            # Следующие 2 строчки - место для БОЛЬШОГО рефакторинга:
            # Можно (читать-НУЖНО!) проверять, чтобы не было в сессии и в базе
            for element in tqdm(lst):

                # Собираем список всех ТС из файла RMT-321:
                car_list.append(
                    await upload_filedata_in_db(element, download_session)
                )
            logging.info('Завершена загрузка данных из CSV-файла.')

            # АРХИВИРОВАНИЕ в рамках одного коммита:
            # Переносим все непереданные (читай-выбывшие) ТС в архив:
            archive_car_ids = await push_cars_in_archive(
                cars_in_file=car_list,
                session=download_session
            )
            # и связанных с ними ТO:
            if archive_car_ids:
                for car_id in archive_car_ids:
                    service_work_list = (
                        await get_active_service_work_list_by_car(
                            car_id=car_id,
                            session=download_session
                        )
                    )
                    await add_service_works_in_archive(
                        service_work_list=service_work_list,
                        session=download_session
                    )
            else:
                logging.info('Архивирования ТС не было.')

            logging.info('Начало обновления статистики:')
            await add_statement_after_loading_csv_file(
                session=download_session
            )
            await download_session.commit()

    # Настраиваем конфигуратор:
    config = uvicorn.Config(
        'toir_app.main:toir_app',
        reload=True
    )
    # 3. Запускаем FastAPI сервер:
    server = uvicorn.Server(config)
    # непонятно для чего, не ведаю, что творю)
    await server.serve()


if __name__ == '__main__':
    # Сборка и конфигурирование логгера:
    configure_logging()
    logging.info('Поехали!')

    # Запускаем асинхронный main()
    asyncio.run(main())

# При запуске приложения через python main.py, работа с env-файлом строится
# иначе — нужно указать полный или относительный путь до env-файла либо
# указать его в параметрах метода uvicorn.run()
