from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from toir_app.convert_csv_to_py.convertation import normalize_service_name
from toir_app.function import convert_date
from toir_app.schemas.convertation import CarDataPoint


async def create_data_point(row: List[str]) -> Optional[CarDataPoint]:
    """
    Создает схему CarDataPoint из входящей строки данных.
    """
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


async def base_update_model(
    session: Session,
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
        # Получаем значение (в т.ч. обрабатывается Enum)
        if hasattr(element, 'value'):
            value = element.value
        else:
            value = element.dict().get(data_field) if data_field else element

        # Формируем и выполняем запрос
        stmt = select(model).where(getattr(model, check_field) == value)
        
        # Правильный способ выполнения асинхронного запроса
        result = await session.execute(stmt)
        existing_in_db = result.scalars().first()  # Теперь это работает

        if not existing_in_db:
            new_instance = model(**{check_field: value})
            session.add(new_instance)
            # возможно дальше коммит не нужен!!!
            # его надо вынести в parse_data.update_db

            await session.commit()  # или коммитить отдельно после всех операций
            return new_instance  # скорее всего возвращает модель, проверить!
        return existing_in_db  # скорее всего возвращает модель, проверить!

    except AttributeError as e:
        raise ValueError(
            f'Поле {check_field} не существует в модели {model.__name__}'
        ) from e
    except KeyError as e:
        raise ValueError(f'Ключ {e} не найден в element') from e
