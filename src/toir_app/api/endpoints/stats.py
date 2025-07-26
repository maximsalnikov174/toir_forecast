import csv
import re
from array import array
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile,
)
from sqlalchemy.ext.asyncio import AsyncSession
from tqdm import tqdm

from constants import ENCODING_DEFAULT, PATTERN_FOR_DATE_IN_CSV
from convert_csv_to_py.parse_data import (
    convert_csv_to_list,
    upload_filedata_in_db,
)
from core.db import AsyncSessionLocal, get_async_session
from crud.car import push_cars_in_archive
from crud.service_work import (
    add_service_works_in_archive,
    get_active_service_work_list_by_car,
)
from crud.special_status import (
    deactivate_list_of_special_status_for_car,
)
from crud.stats import (
    add_statement_after_loading_csv_file,
    get_stats_for_organization,
)
from exception import BadNameInUploadFileException
from logger.logger import logger
from models import Organization
from schemas.service_work_stats import ServiceStatusStatsBase

router = APIRouter()


@router.post('/uploadfile')
async def upload_file(file: UploadFile = File(...)):
    """Обработка файла csv и загрузка данных в БД."""
    try:
        # 1. проверим корректность имени файла CSV и заберём `datetime`:
        update_date = re.match(PATTERN_FOR_DATE_IN_CSV, file.filename)
        update_date = update_date.groups()[0] if update_date else None
        if update_date is None:
            raise BadNameInUploadFileException

        # 2. Разбираем файл на строки, загоняем каждую из них в нужный словарь:
        content = (await file.read()).decode(ENCODING_DEFAULT)
        csv_data = csv.reader(content.splitlines())
        stmt = await convert_csv_to_list(csv_data)

        # 3. Выполняем загрузку и обновление строк в БД:
        async with AsyncSessionLocal() as download_session:
            # Создаём пустое множество ТС:
            car_list = array('H')

            # TODO
            # Следующие строчки - место для БОЛЬШОГО рефакторинга:
            # Можно (читать-НУЖНО!) проверять, чтобы не было в сессии и в базе

            # 3.1 Собираем список всех ТС из файла RMT-321:
            for element in tqdm(stmt):
                car_list.append(
                    await upload_filedata_in_db(element, download_session)
                )
            logger.info(
                f'Завершена загрузка данных за {update_date} из CSV-файла.'
            )

            # 3.2* шаг не связан с загружаемым файлом
            await deactivate_list_of_special_status_for_car(download_session)

            # 3.3 Переносим все непереданные (читай-выбывшие) ТС в архив:
            archive_car_ids = await push_cars_in_archive(
                cars_in_file=car_list,
                session=download_session
            )
            # 3.4 (опциональный) и связанных с ними ТO:
            if archive_car_ids:  # только если есть выбывшие ТС
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
                logger.info('Архивирования ТС не было, все в строю.')

            # 3.5 Обновляем статистику по всем подразделениям
            logger.info('Начало обновления статистики:')
            await add_statement_after_loading_csv_file(
                file_date=update_date, session=download_session
            )

            # 3.6 Общий коммит сессии:
            await download_session.commit()

    except BadNameInUploadFileException:
        raise HTTPException(
            status_code=400,
            detail='Проверьте имя файла'
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f'Ошибка при загрузке файла: {str(e)}'
        )


@router.get(
    '/get_stats',
    response_model=list[ServiceStatusStatsBase],
    name='Получение статистики по цеху'
)
async def get_stats(
    organization_id: Annotated[int, Organization.id] = Query(...),
    session: AsyncSession = Depends(get_async_session)
):
    return await get_stats_for_organization(
        organization_id=organization_id,
        session=session
    )
