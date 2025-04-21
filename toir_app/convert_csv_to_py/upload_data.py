from typing import List, Tuple

from toir_app.convert_csv_to_py.parse_data import base_update_model
from toir_app.core.db import Base as db
from toir_app.models.models import (ServiceStatus,
                                    SpecialStatus,
                                    ServiceName,
                                    Role)
from toir_app.schemas.schemas import (SpecialStatusForCar,
                                      Status,
                                      UserRole,
                                      UsersServiceName)


# ----------ФУНКЦИИ, ВЫПОЛНЯЮЩИЕ НАПОЛНЕНИЕ ДАННЫМИ НЕ ИЗ CSV-ФАЙЛА----------
# -------------Понадобятся только на старте создания приложения-------------

def upload_users_data_in_db(elements, apps_model):
    """Добавляет сервисные статусы из заранее подготовленного списка."""
    for element in elements:
        base_update_model(apps_model, 'name', element)
    db.session.commit()


# Все что нужно загрузить при СОЗДАНИИ базы:
need_to_upload_datas = [
    (SpecialStatusForCar, SpecialStatus),  # к выбытию, на ВР
    (Status, ServiceStatus),  # подошло, превышение
    (UserRole, Role),  # админ, только чтение
    (UsersServiceName, ServiceName),  # ТО-2, замена масла ДВС
    # может что-то еще
]


def upload_all_users_data_in_db(data_and_model_pair: List[Tuple]):
    """Дружно загружаем все данные в базу."""
    for values, need_model in data_and_model_pair:
        upload_users_data_in_db(elements=values.value, apps_model=need_model)
