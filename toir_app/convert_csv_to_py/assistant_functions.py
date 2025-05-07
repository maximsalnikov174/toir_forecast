from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from toir_app.convert_csv_to_py.convertation import normalize_service_name
from toir_app.function import convert_date
from toir_app.schemas.convertation import CarDataPoint


def find_element_position(
    row: List, elem: str, mapping_name: List, type='str'
):
    """
    Возвращает элемент (в обработанном виде) из поданной строки.

    Args:
    - row : список элементов из строки данных csv
    - elem : наименование столбца в файле csv
    - mapping_name : список заголовков (1-ая строка файла csv)
    - type : способ преобразования [str, int, float, complex]
    """
    if type == 'str':
        return row[mapping_name.index(elem)]
    elif type == 'int':
        return int(row[mapping_name.index(elem)])
    elif type == 'float':
        return float(row[mapping_name.index(elem)].replace(',', '.'))
    elif type == 'complex':
        return row[mapping_name.index(elem)].strip()
    # else:
    #     неизвестные данные


# Как по состоянию на 25/04/2025 выглядят поля rmt321:
# all_value = {
#     'dt_now': 'TEK_DATE',  # 0
#     'organization': 'ORGANIZATION_CODE',  # 1
#     'car_model': 'GR',  # 3
#     'personal_id': 'INSTANCE_ID',  # 4
#     'grz': 'INSTANCE_NUMBER',  # 5
#     'last_service_date': 'LAST_SERVICE_END_DATE',  # 7
#     'last_service_view': 'LAST_OPER',  # 8
#     'base_interval': 'RUNTIME_INTERVAL',  # 9
#     'daily_distance': 'NORMA',  # 10
#     'last_service_reading': 'LAST_SERVICE_READING',  # 11
#     'reading_now': 'CUR_READING',  # 15
#     'next_service_view': 'NEXT_OPER',  # 16
# }


def create_data_point(
    row: List[str], mapping_name
) -> Optional[CarDataPoint]:
    """
    Создает схему CarDataPoint из входящей строки данных.
    """
    try:
        return CarDataPoint(
            # Описание ТС:
            personal_id=find_element_position(
                row, 'INSTANCE_ID', mapping_name, 'int'
            ),
            grz=find_element_position(
                row, 'INSTANCE_NUMBER', mapping_name),
            car_model=find_element_position(row, 'GR', mapping_name),
            organization=find_element_position(
                row, 'ORGANIZATION_CODE', mapping_name),

            # Базовая настройка:
            base_interval=find_element_position(
                row, 'RUNTIME_INTERVAL', mapping_name, 'int'
            ),

            # Динамические данные:
            dt_now=convert_date(find_element_position(
                row, 'TEK_DATE', mapping_name)),
            daily_distance=find_element_position(
                row, 'NORMA', mapping_name, 'float'),
            reading_now=find_element_position(
                row, 'CUR_READING', mapping_name, 'float'),

            # История:
            last_service_date=(
                convert_date(
                    find_element_position(
                        row, 'LAST_SERVICE_END_DATE', mapping_name)
                ) if find_element_position(
                    row, 'LAST_SERVICE_END_DATE', mapping_name, 'complex'
                ) else None
            ),
            last_service_view=normalize_service_name(
                find_element_position(row, 'LAST_OPER', mapping_name)
            ),
            last_service_reading=find_element_position(
                row, 'LAST_SERVICE_READING', mapping_name, 'float'
            ),

            # Прогноз:
            next_service_view=normalize_service_name(
                find_element_position(row, 'NEXT_OPER', mapping_name)
            )
        )
    except (ValueError, IndexError) as e:
        print(f'Ошибка создания точки данных: {e}')
        raise


async def base_update_model(
    session: AsyncSession,
    model,
    check_field: str,
    element,
    data_field=None
):
    """
    Универсальная функция для создания/проверки объектов моделей.

    Args:
        session: SQLAlchemy сессия
        model: Класс модели SQLAlchemy
        check_field: Поле модели для фильтрации
        element: Данные (dict, str или Enum)
        data_field: Ключ в element (если element - dict)

    Returns:
        Существующий или новый объект модели
    """
    try:
        # Получаем значение:
        if hasattr(element, 'value'):  # обработка класса Enum
            value = element.value
        else:
            value = element.dict().get(data_field) if data_field else element
        #
        # Формируем и выполняем запрос
        stmt = select(model).where(getattr(model, check_field) == value)
        #
        # Правильный способ выполнения асинхронного запроса
        result = await session.execute(stmt)
        existing_in_db = result.scalars().first()
        #
        if not existing_in_db:
            #
            new_instance = model(**{check_field: value})
            session.add(new_instance)
            # возможно дальше коммит не нужен!!!
            # его надо вынести в parse_data.update_db
            #
            await session.commit()
            return new_instance  # скорее всего возвращает модель, проверить!
        return existing_in_db  # скорее всего возвращает модель, проверить!
        #
    except AttributeError as e:
        raise ValueError(
            f'Поле {check_field} не существует в модели {model.__name__}'
        ) from e
    except KeyError as e:
        raise ValueError(f'Ключ {e} не найден в element') from e
