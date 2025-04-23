import csv
import os
from typing import List, Optional

from sqlalchemy import select

from toir_app.convert_csv_to_py.assistant_functions import (
    base_update_model, create_data_point
)
from toir_app.core.db import AsyncSessionLocal, Base as db
from toir_app.models.car import Car
from toir_app.models.car_model import CarModel
from toir_app.models.organization import Organization
from toir_app.models.service_name import ServiceName
from toir_app.models.service_work import ServiceWork
from toir_app.schemas.convertation import CarDataPoint


MODEL_MAPPING = {
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
        print(f"Файл не найден: {filename}")

    if os.path.isdir(filename):
        print(f"Указанный путь ведет к директории: {filename}")

    # Заготовка для общего списка данных из файла rmt-321:
    total_list: List[CarDataPoint] = []

    with open(filename, mode='r', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile, quotechar='"')

        for row in reader:
            if len(row) == 1:
                try:
                    # Поскольку в исходной строке csv есть запятые внутри
                    # элемента - пришлось хардкодить и собирать список заново:
                    first_row, other_row = row[0].split(',"', 1)
                    rows = other_row.split('","')
                    rows.insert(0, first_row)

                    # Когда в строке кривое количество элементов
                    # (последняя строка файла):
                    if len(rows) < 22:
                        print(f'Cтрока {row[0]} не соответствует нужной длине')
                        # logger.warning(f'{row[0]} не соответствует длине.')
                        continue

                    # Только гении в элемент csv заталкивают «,»:
                    # n = 1 if len(row) == 22 else 0

                    # Валидация и преобразование данных
                    try:
                        data_point = await create_data_point(rows)

                        if data_point:
                            total_list.append(data_point)
                        else:
                            print(data_point)
                    except ValueError as e:
                        print(f'Ошибка обработки данных: {e}')
                        continue

                except Exception as e:
                    print(f'Ошибка разбора строки: {row}, {str(e)}')
                    continue

    return total_list


async def upd_model_in_db(
    element,
    some_model,
    data_field
):
    async with AsyncSessionLocal() as session:
        return await base_update_model(
            session=session,
            model=some_model,
            check_field='name',
            element=element,
            data_field=data_field
        )


# -------------------------СОЗДАТЕЛИ ОБЪЕКТОВ БД:-------------------------

async def update_db(element):
    """
    Проверяет (и вносит) каждую строку из файла csv в базу данных.

    Сначала каждый из elements надо провалидировать через pydantic
    """
    async with AsyncSessionLocal() as session:
        try:
            element_dict = element.dict()

            # Проверяем Цех, модель ТС и виды работ (пред и след)
            updated_fields = {}
            for field_name, model_data in MODEL_MAPPING.items():
                updated_value = await upd_model_in_db(
                    element=element,
                    some_model=model_data['model'],
                    data_field=model_data['field']
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
            car = await session.execute(
                select(Car)
                .where(Car.personal_id == element_dict['personal_id'])
            )
            car = car.scalars().first()
            if not car:
                car = Car(
                    personal_id=element_dict['personal_id'],
                    grz=element_dict['grz'],
                    car_model=updated_fields['car_model'],
                    organization=updated_fields['organization']
                )
                session.add(car)
                await session.flush()

        # Машина уже должна быть сохранена!
        # Проверяем записи о прошлых обслуживаниях и создаём новые:
            service = await session.execute(
                select(ServiceWork).where(
                    ServiceWork.car_id == car.id,  # это пока не работает
                    ServiceWork.next_service_id == next_service,
                    ServiceWork.request_reading == element_dict['reading_now']
                )
            )
            service = service.scalars().first()
            if not service:
                # Создаем новую запись ServiceWork
                service = ServiceWork(
                    car_id=car.id,
                    last_service_date=element_dict['last_service_date'],
                    last_service_reading=element_dict['last_service_reading'],
                    request_date=element_dict['dt_now'],
                    request_reading=element_dict['reading_now'],
                    base_interval=element_dict['base_interval'],
                    daily_distance=element_dict['daily_distance'],
                    # В этих не уверен (когда вернется None):
                    last_service_id=last_service,
                    next_service_id=next_service
                )
                # Логируем создание новой записи
                # print(
                #     'Создана новая запись обслуживания для '
                #     f'{car.grz} от {element["dt_now"]}'
                # )

        # TODO как удалить старую запись (или закинуть в архив)?

            # FIXME Обновляем существующую запись (если нужно, а нужно ли?)
            service.last_service_date = element_dict['last_service_date']
            service.last_service_reading = element_dict['last_service_reading']
            service.base_interval = element_dict['base_interval']
            service.daily_distance = element_dict['daily_distance']
            # # За это подумать:
            # service.last_service_id = last_service
            # service.next_service_id = next_service

            await service.update_request_status(session=session)

            session.add(service)  # Добавляем все что сделали в сессию
            # print(
            #     'Обновлена запись обслуживания для '
            #     f'{car.grz} от {element["dt_now"]}'
            # )
            await session.commit()  # Применение всех изменений

        except Exception as e:
            await session.rollback()
            raise ValueError(f"Ошибка обновления БД: {str(e)}") from e


# переделать в метод класса ServiceName
def get_id_from_service(in_time: str, **kwargs) -> Optional[int]:
    return (
        kwargs['updated_fields'][in_time + '_service_name_view'].id
        if kwargs['element_dict'].get(in_time + '_service_view')
        else None
    )
