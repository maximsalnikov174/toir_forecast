import csv
import logging
import os
from typing import List, Optional, Type, TypedDict, Union

from sqlalchemy.ext.asyncio import AsyncSession

from toir_app.constants import TOTAL_VALUES_IN_RAW_RMT_321
from toir_app.convert_csv_to_py.assistant_functions import (
    base_update_model,
    create_data_point
)
from toir_app.convert_csv_to_py.upload_data_from_csv import (
    create_service_work,
    get_or_create_car_and_return_id
)
# from toir_app.core.db import get_async_session
from toir_app.models import CarModel, Organization, ServiceName
from toir_app.schemas.convertation import CarDataPoint


class ModelMapping(TypedDict):
    """Модель аннотации типов."""
    model: Type[Union[Organization, CarModel, ServiceName]]
    field: str


# Наполнение простыми таблицами:
MODEL_MAPPING: dict[str, ModelMapping] = {
    'organization': {
        'model': Organization,
        'field': 'organization'
    },
    'car_model': {
        'model': CarModel,
        'field': 'car_model'
    },
    'last_service_name_view': {
        'model': ServiceName,
        'field': 'last_service_view'
    },
    'next_service_name_view': {
        'model': ServiceName,
        'field': 'next_service_view'
    }
}


# ------------------------ФУНКЦИЯ-КОНВЕРТЕР:------------------------

async def convert_csv_to_list(filename: str) -> List[CarDataPoint]:
    """
    Конвертирует CSV файл в список словарей с записями по обслуживанию.

    Выполняет подготовку для последующего выполнения update_db()

    Args:
        filename: Путь к CSV файлу

    Returns:
        List[CarDataPoint]: Список объектов с данными автомобилей
    """

    if not os.path.exists(filename):
        logging.critical(f'Файл не найден: {filename}')

    if os.path.isdir(filename):
        logging.error(
            f'Указанный путь ведет к директории: {filename}, а не к файлу.'
        )

    # Заготовка для общего списка данных из файла rmt-321:
    total_list: List[CarDataPoint] = []

    with open(filename, mode='r', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile, quotechar='"')

        for row in reader:
            # Первая строчка - заголовки:
            if (
                len(row) == TOTAL_VALUES_IN_RAW_RMT_321
                and reader.line_num == 1
            ):
                mapping_name = list(row)

            # Стандартная ситуация:
            elif len(row) == TOTAL_VALUES_IN_RAW_RMT_321:
                try:
                    data_point = create_data_point(row, mapping_name)
                    if data_point:
                        total_list.append(data_point)
                    # else:
                        # ERROR здесь!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                        # logging.info(f'Строчка из другого цеха {data_point}')
                except ValueError as e:
                    logging.error(f'Ошибка обработки данных: {e}')
                    continue

            # Кривые данные:
            elif len(row) == 1:  # все остальные строчки
                try:
                    # Поскольку в исходной строке csv есть запятые внутри
                    # элемента - пришлось хардкодить и собирать список заново:
                    first_row, other_row = row[0].split(',"', 1)
                    rows = other_row.split('","')
                    rows.insert(0, first_row)

                    # Когда в строке кривое количество элементов
                    # (последняя строка файла):
                    if len(rows) < TOTAL_VALUES_IN_RAW_RMT_321:
                        logging.error(
                            f'Cтрока {row[0]} не соответствует нужной длине'
                        )
                        continue

                    # Только гении в элемент csv заталкивают «,»:
                    # n = 1 if len(row) == 22 else 0

                    # Валидация и преобразование данных
                    try:
                        data_point = create_data_point(rows, mapping_name)

                        if data_point:
                            total_list.append(data_point)
                        else:
                            logging.error(f'И тут разобраться {data_point}')
                    except ValueError as e:
                        logging.error(f'Ошибка обработки данных: {e}')
                        continue

                except Exception as e:
                    logging.error(f'Ошибка разбора строки: {row}, {str(e)}')
                    continue

    logging.info(f'Общее количество строк - {len(total_list)}')
    return total_list


async def upd_light_model_in_db(
    element: CarDataPoint,
    some_model: Union[Organization, ServiceName, CarModel],  # аннотация треш
    data_field,
    session: AsyncSession
):
    """Загрузка простых (понятных) моделей в БД."""
    return await base_update_model(
        session=session,
        model=some_model,
        check_field='name',
        element=element,
        data_field=data_field
    )


# -------------------------СОЗДАТЕЛИ ОБЪЕКТОВ БД:-------------------------

async def upload_filedata_in_db(
        element: CarDataPoint,
        session: AsyncSession
) -> None:
    """
    Проверяет (и вносит) каждую строку из файла csv в базу данных.

    Сначала каждый из elements надо провалидировать через pydantic
    """
    try:
        element_dict = element.model_dump()

        # Проверяем Цех, модель ТС и виды работ (предыдущую и следующую)
        # TODO Можно накапливать в одной сессии
        updated_fields = {}
        for field_name, model_data in MODEL_MAPPING.items():
            updated_value = await upd_light_model_in_db(
                element=element,
                some_model=model_data['model'],
                data_field=model_data['field'],
                session=session
            )
            updated_fields[field_name] = updated_value

        # Получаем объекты ServiceName для прошлого/следующего обслуживания
        last_service = get_id_from_service(
            'last',
            updated_fields=updated_fields,
            element_dict=element_dict
        )
        next_service = get_id_from_service(
            'next',
            updated_fields=updated_fields,
            element_dict=element_dict
        )

    # Проверяем автомобиль (понадобится, когда появятся новые ТС в цехе):
        car_id, car_grz = await get_or_create_car_and_return_id(
            session=session,
            personal_id=element_dict['personal_id'],
            grz=element_dict['grz'],
            car_model=updated_fields['car_model'],
            organization=updated_fields['organization']
        )

        # Машина уже должна быть сохранена!
        # Проверяем записи о прошлых обслуживаниях и создаём новые:
        if last_service and next_service:
            # TODO может ли быть такое, что last и next не будет?
            # например у нового ТС должно ли быть только last?
            await create_service_work(
                session=session,
                car_id=car_id,
                element_dict=element_dict,
                last_service_id=last_service,
                next_service_id=next_service,
                car_grz=car_grz
            )

        # Закидываем всю строчку в коммит
        await session.commit()

    except Exception as e:
        await session.rollback()
        raise ValueError(f'Ошибка обновления БД: {str(e)}') from e


# переделать в метод класса ServiceName
def get_id_from_service(in_time: str, **kwargs) -> Optional[int]:
    return (
        kwargs['updated_fields'][in_time + '_service_name_view'].id
        if kwargs['element_dict'].get(in_time + '_service_view')
        else None
    )
