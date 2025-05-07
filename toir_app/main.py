import asyncio
import os

import uvicorn
from fastapi import FastAPI
from dotenv import load_dotenv

from toir_app.api.endpoints import router
from toir_app.core.config import settings
from toir_app.convert_csv_to_py.parse_data import (
    convert_csv_to_list, upload_filedata_in_db
)
from toir_app.convert_csv_to_py.upload_data import (
    upload_all_users_data_in_db,
    need_to_upload_datas
)

load_dotenv()  # подгружаем переменные из env

toir_app = FastAPI(title=settings.app_title)

# Подключаем роутер к приложению:
toir_app.include_router(router)
script_dir = os.path.dirname(os.path.abspath(__file__))
file_path = f'{script_dir}/dataset_from_oebs/rmt321_full_new_part3.csv'


async def main():
    """Основная асинхронная функция инициализации"""
    if os.environ['UPLOAD_STATIC_DATA_FROM_CSV'].lower() == 'true':
        # 1. Загружаем enum-значения в БД
        await upload_all_users_data_in_db(need_to_upload_datas)

    if os.environ['UPLOAD_DATA_FROM_CSV'].lower() == 'true':
        # 2. Конвертируем CSV и обновляем БД
        lst = await convert_csv_to_list(file_path)
        for element in lst:
            await upload_filedata_in_db(element)

    # 3. Запускаем FastAPI сервер
    config = uvicorn.Config(
        'toir_app.main:toir_app',
        reload=True
    )
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == '__main__':
    # Запускаем асинхронный main()
    asyncio.run(main())


# При запуске приложения через python main.py, работа с env-файлом строится
# иначе — нужно указать полный или относительный путь до env-файла либо
# указать его в параметрах метода uvicorn.run()
