# ----------ФУНКЦИИ, ВЫПОЛНЯЮЩИЕ НАПОЛНЕНИЕ ДАННЫМИ НЕ ИЗ CSV-ФАЙЛА----------
# -------------Понадобятся только на старте создания приложения-------------

from typing import List, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from toir_app.convert_csv_to_py.convertation import UsersServiceName
from toir_app.core.db import Base as db
from toir_app.models import (ServiceName,
                             ServiceStatus,
                             SpecialStatus,
                             SpecialStatusForCar,
                             Status,
                             Role,
                             UserRole)


# Все что нужно загрузить при СОЗДАНИИ базы:
need_to_upload_datas = [
    (SpecialStatusForCar, SpecialStatus),  # к выбытию, на ВР
    (Status, ServiceStatus),  # подошло, превышение
    (UsersServiceName, ServiceName),  # ТО-2, замена масла ДВС
    (UserRole, Role),  # админ, только чтение
    # ...
]


async def upload_all_users_data_in_db(
    data_and_model_pair: List[Tuple],
    session: AsyncSession
):
    """
    Дружно загружаем все данные в базу.
    """
    for enum_class, need_model in data_and_model_pair:
        enum_values = [_.value for _ in enum_class]
        for enum_value in enum_values:
            await upload_users_data_in_db(
                element=enum_value,
                apps_model=need_model,
                session=session
            )
    await session.commit()


async def upload_users_data_in_db(
    element: str,
    apps_model: type[db],
    session: AsyncSession
):
    """Асинхронно наполняет БД статичными данными."""
    # Получаем значение (работает и для Enum, и для обычных строк)
    value = element.value if hasattr(element, 'value') else element

    # Проверяем существование записи
    stmt = select(apps_model).where(apps_model.name == value)
    result = await session.execute(stmt)
    existing = result.scalar_one_or_none()

    if not existing:
        new_instance = apps_model(name=value)
        session.add(new_instance)
