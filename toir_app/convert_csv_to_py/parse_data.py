import csv
# from pprint import pprint
from typing import List, Optional

from toir_app.convert_csv_to_py.convertation import normalize_service_name
from toir_app.core.db import Base as db
from toir_app.function import convert_date
from toir_app.models.models import (ServiceWork,
                                    Car,
                                    CarModel,
                                    Organization,
                                    ServiceName)
from toir_app.schemas.schemas import (CarDataPoint,)


# Тестировал обработку строки:
# pprint(convert_csv_to_list('database_test/rmt321.csv')[20])


# ------------------------ПОДГОТОВИТЕЛЬНЫЕ ФУНКЦИИ:------------------------
# TODO добавить аннотацию типов:
def base_update_model(
    model,
    check_value,
    element,
    data_field=None
):
    """
    Универсальная функция для создания/проверки объектов моделей

    Args:
        model: Класс модели SQLAlchemy
        check_field: Поле модели для фильтрации
        element: Данные (dict или str)
        data_field: Ключ в element (если element - dict)

    Returns:
        Новый объект модели (+ добавляется в базу) или уже существует объект.
    """
    try:
        value = element[data_field] if data_field else element
        filter_condition = {check_value: value}
        existing_in_db = model.query.filter_by(**filter_condition).first()

        if not existing_in_db:
            new_instance = model(**{check_value: value})
            db.session.add(new_instance)
            return new_instance
        return existing_in_db
    except KeyError as e:
        raise ValueError(f'Ключ {e} не найден в element') from e
    except AttributeError as e:
        raise ValueError(
            f'Поле {check_value} не существует в модели {model.__name__}'
        ) from e


def create_data_point(row: List[str]) -> Optional[CarDataPoint]:
    """Создает объект CarDataPoint из строки данных."""
    try:
        return CarDataPoint(
            # Описание ТС:
            personal_id=int(row[4]),
            grz=row[5],
            car_model=row[3],
            organization=row[1],

            # Базовая настройка:
            base_interval=int(row[9]),

            # Динамические данные:
            dt_now=convert_date(row[0]),
            daily_distance=float(row[10].replace(',', '.')),
            reading_now=float(row[15].replace(',', '.')),

            # История:
            last_service_date=convert_date(row[7]) if row[7].strip() else None,
            last_service_view=normalize_service_name(row[8]),
            last_service_reading=float(row[11].replace(',', '.')),

            # Прогноз:
            next_service_view=normalize_service_name(row[16])
        )
    except (ValueError, IndexError) as e:
        print(f'Ошибка создания точки данных: {e}')
        raise


# ------------------------ФУНКЦИИ-КОНВЕРТЕРЫ:------------------------
def convert_csv_to_list(filename: str) -> List[CarDataPoint]:
    """
    Конвертирует CSV файл в список словарей с записями по обслуживанию.

    Выполняет подготовку для последующего выполнения update_db()

    Args:
        filename: Путь к CSV файлу

    Returns:
        List[CarDataPoint]: Список объектов с данными автомобилей
    """
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
                        data_point = create_data_point(rows)
                        if data_point:
                            total_list.append(data_point)
                    except ValueError as e:
                        print(f'Ошибка обработки данных: {e}')
                        continue

                except Exception as e:
                    print(f'Ошибка разбора строки: {row}, {str(e)}')
                    continue

        return total_list


# -------------------------СОЗДАТЕЛИ ОБЪЕКТОВ БД:-------------------------
# FIXME ЗДЕСЬ ЕЩЕ НАДО КОВЫРЯТЬСЯ, ПОТОМУ ЧТО ВЫГЛЯДИТ НЕ ОЧЕНЬ

def update_db(filename):
    """
    Проверяет (и вносит) каждую строку из файла csv в базу данных.

    Сначала каждый из elements надо провалидировать через pydantic
    """

    # Обработка данных из файла csv:
    elements = convert_csv_to_list(filename=filename)

    for element in elements:

        # Проверяем Цех (маловероятно для повторных обработок):
        organization = base_update_model(
            Organization, 'name', element, 'organization'
        )

        # Проверяем Модель ТС (понадобится, когда появятся новые марки ТС):
        model = base_update_model(
            CarModel, 'name', element, 'car_model'
        )

        # Проверяем вид работ (понадобится, когда появятся новые вид работ):
        for key in ['last_service_view', 'next_service_view']:
            base_update_model(
                ServiceName, 'name', element, key
            )

        # TODO Это можно тоже затолкать в base_update_model:
        # Проверяем ТС (понадобится, когда появятся новые ТС в цехе):
        car = Car.query.filter_by(personal_id=element['personal_id']).first()
        if not car:
            car = Car(
                personal_id=element['personal_id'],
                grz=element['grz'],
                car_model=model,
                organization=organization
            )
            db.session.add(car)

        # TODO ВСЁ ЭТО НАДО ТЕСТИРОВАТЬ НА МАЛЕНЬКОМ ДИАПАЗОНЕ:
        # TODO Надо подумать, как удалить старую запись (или закинуть в архив)

        # Создаём запись, если подобной нет:
        # Получаем объекты ServiceName для прошлого и следующего обслуживания
        last_service = ServiceName.query.filter_by(
            name=element['last_service_view']
        ).first() if element.get('last_service_view') else None

        next_service = ServiceName.query.filter_by(
            name=element['next_service_view']
        ).first() if element.get('next_service_view') else None

        # Проверяем записи о прошлых обслуживаниях и создаём новые:
        service = ServiceWork.query.filter_by(
            car_id=car.id,
            next_service_id=element['next_service_view'],
            request_reading=element['reading_now']
        ).first()

        if not service:
            # Создаем новую запись ServiceWork
            service = ServiceWork(
                car_id=car.id,
                last_service_date=element['last_service_date'],
                last_service_reading=element['last_service_reading'],
                request_date=element['dt_now'],
                request_reading=element['reading_now'],
                base_interval=element['base_interval'],
                daily_distance=element['daily_distance'],
                last_service_id=last_service.id if last_service else None,
                next_service_id=next_service.id if next_service else None
            )
            db.session.add(service)

            # Вычисляем и устанавливаем статус
            service.update_request_status()

            # Логируем создание новой записи
            # print(
            #     'Создана новая запись обслуживания для '
            #     f'{car.grz} от {element["dt_now"]}'
            # )
        else:
            # FIXME Обновляем существующую запись (если нужно, а нужно ли?!)
            service.last_service_date = element['last_service_date']
            service.last_service_reading = element['last_service_reading']
            service.base_interval = element['base_interval']
            service.daily_distance = element['daily_distance']
            service.last_service_id = last_service.id if last_service else None
            service.next_service_id = next_service.id if next_service else None
            service.update_request_status()

            # print(
            #     'Обновлена запись обслуживания для '
            #     f'{car.grz} от {element["dt_now"]}'
            # )

    db.session.commit()  # Применение всех изменений
