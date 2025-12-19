import csv
import re
from array import array
from datetime import date, datetime, time
from typing import Annotated

import pandas as pd
from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile,
)
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from tqdm import tqdm

from api.endpoints.bot import bot_schedular
from constants import ENCODING_DEFAULT, PATTERN_FOR_DATE_IN_CSV
from convert_csv_to_py.upload_data import (
    need_to_upload_datas,
    upload_all_users_data_in_db,
)
from convert_csv_to_py.parse_data import (
    collect_unique_service_names,
    convert_csv_to_list,
    upload_filedata_in_db,
)
from core.db import AsyncSessionLocal, get_async_session
from core.init_db import create_first_superuser
from core.user import current_user
from crud.car import push_cars_in_archive
from crud.organization import get_organization_by_name
from crud.role import get_superuser_role
from crud.service_name import dao_service_name
from crud.service_work import (
    add_service_works_in_archive,
    get_active_service_work_list_by_car,
)
from crud.special_status import (
    deactivate_list_of_special_status_for_car,
)
from crud.stats import (
    add_statement_after_loading_csv_file,
    get_completed_service_works_stats,
    get_stats_for_organization,
)
from exception import (
    BadNameInUploadFileException,
    NoPermissionForSuperUser,
    ServiceNameNotFoundException,
    StaticDataInDBNotFoundException,
)
from function import convert_pandas_table_to_xlsx
from logger.logger import logger
from models import Organization, StaticOrganization, User
from schemas.service_work_stats import ServiceStats, ServiceStatusStatsBase

router = APIRouter()


@router.post(
        '/uploadfile',
        # dependencies=[Depends(current_user)],
)
async def upload_file(
    file: UploadFile = File(...),
    user: User = Depends(current_user),
):
    """Обработка файла csv и загрузка данных в БД."""
    try:
        # 1. проверим корректность имени файла CSV и заберём `datetime`:
        update_date = re.match(PATTERN_FOR_DATE_IN_CSV, file.filename)
        if update_date is None:
            raise BadNameInUploadFileException
        update_date = update_date.group(1)

        # 2. Разбираем файл на строки, загоняем каждую из них в нужный словарь:
        content = (await file.read()).decode(ENCODING_DEFAULT)
        csv_data = csv.reader(content.splitlines())
        stmt = await convert_csv_to_list(csv_data)

        # Собираем коллекцию видов работ, чтобы проверить их наличие в БД:
        service_name_set = collect_unique_service_names(stmt)

        # 3. Выполняем загрузку и обновление строк в БД:
        async with AsyncSessionLocal() as download_session:

            # Проверяем наполнение БД статическими данными:
            await get_organization_by_name(
                name=StaticOrganization.ORG_UPR.value,
                session=download_session
            )

            if not user.is_superuser:
                raise NoPermissionForSuperUser

            # Проверяем существование видов работ в БД:
            await dao_service_name.notificate_unknown_objects(
                obj_list=service_name_set,
                bot=bot_schedular,
                session=download_session
            )

            # Создаём пустое множество ТС:
            car_list = array('H')

            # TODO
            # Следующие строчки - место для БОЛЬШОГО рефакторинга:
            # Можно (читать-НУЖНО!) проверять, чтобы не было в сессии и в базе

            await bot_schedular.send_notification_for_admin(
                msg='⚠️ Началось обновление базы данных',
            )

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

            await bot_schedular.send_notification_for_admin(
                msg=f'Файл {update_date} загружен',
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

    except BadNameInUploadFileException:
        raise HTTPException(
            status_code=400,
            detail='Проверьте имя файла'
        )
    except ServiceNameNotFoundException as e:
        raise HTTPException(
            status_code=400,
            detail=f'Найдены неизвестные виды работ {e.reason}'
        )
    except NoPermissionForSuperUser:
        raise HTTPException(
            status_code=400,
            detail='У пользователя недостаточно прав для загрузки файла'
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


@router.get(
    '/all_service_works_completed',
    name='Получение статистики по всем завершенным работам.',
)
async def get_service_works_stats(
    start_day: date,
    end_day: date,
    completed_only: bool = True,
    organization_id: Annotated[int, Organization.id] = Query(...),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Получение статистики по подразделению за указанный период для отчета в СМТ.

    :param start_day: Начальная дата (с 0:00)
    :type start_day: date
    :param end_day: Дата окончания (до 23:59)
    :type end_day: date
    :param completed_only: Только завершенные в КИС (`True` по умолчанию)
    :type completed_only: bool
    :param organization_id: Идентификатор Подразделения
    """
    # Задаём временные границы от и до:
    start_time, end_time = time(0, 0, 0), time(23, 59, 59)
    start_dt = datetime.combine(start_day, start_time)
    end_dt = datetime.combine(end_day, end_time)

    result = await get_completed_service_works_stats(
        start_day=start_dt,
        end_day=end_dt,
        organization_id=organization_id,
        completed_only=completed_only,
        session=session
    )
    # Все элементы из списка моделей SQLAlchemy валидируем pydantic-схемой:
    new_result = (
        [ServiceStats.model_validate(el).model_dump() for el in result]
    )
    # И загоняем в (отсортированную и очищенную таблицу) pandas:
    pandas_table = (
        pd.DataFrame(new_result)
        .sort_values(by=['service_name', 'service_work_completed'])
        .drop(columns=[
            'id', 'station_id', 'last_service_reading', 'daily_distance'
        ])
    )

    # Переименовываем столбцы:
    pandas_table = pandas_table.rename(columns={
        'service_name': 'Вид работ',
        'car_grz': 'ГРЗ',
        'zvr_number': '№ ЗВР',
        'base_interval': 'Базовый интервал, км',
        'request_reading': 'На пробеге, км',
        'service_work_completed': 'Дата закрытия',
        'in_archive': 'В архиве',
        'request_status': 'Расчётный статус',
        'divergence': 'Отклонение, км'
    })

    return StreamingResponse(
        convert_pandas_table_to_xlsx(pandas_table),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={'Content-Disposition': 'attachment; filename="service_works_report"'}
    )
