# ----------ФУНКЦИИ, ВЫПОЛНЯЮЩИЕ НАПОЛНЕНИЕ ДАННЫМИ НЕ ИЗ CSV-ФАЙЛА----------
# -------------Понадобятся только на старте создания приложения-------------

from typing import Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from convert_csv_to_py.convertation import UsersServiceName
from core.db import Base as db
from models import (
    Organization,
    Role,
    ServiceName,
    ServiceStatus,
    SpecialStatus,
    SpecialStatusForCarBase,
    StaticOrganization,
    Station,
    StationDefault,
    Status,
    UserRole,
)
from models.static_model import (
    convert_oebs_name_to_1c_normal_name,
    ServiceWorkData,
)

# Все что нужно загрузить при СОЗДАНИИ базы:
need_to_upload_datas = [
    (SpecialStatusForCarBase, SpecialStatus),  # к выбытию, на ВР
    (Status, ServiceStatus),  # подошло, превышение
    (UsersServiceName, ServiceName),  # ТО-2, замена масла ДВС
    (UserRole, Role),  # админ, только чтение
    (StaticOrganization, Organization),  # Ю51, Ю52, Ю53, Ю54, УПР
    (StationDefault, Station),  # УРГА, УРЛА, Сторона
    # ...
]


async def upload_all_users_data_in_db(
    data_and_model_pair: list[Tuple],
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
        if (
            apps_model.__name__ == 'ServiceName'
            and hasattr(apps_model, 'group')
        ):
            setattr(new_instance, 'group', ServiceWorkData.get(value))
        elif (
            apps_model.__name__ == 'Organization'
            and hasattr(apps_model, 'normal_name')
        ):
            setattr(
                new_instance,
                'normal_name',
                convert_oebs_name_to_1c_normal_name.get(value))

        session.add(new_instance)
