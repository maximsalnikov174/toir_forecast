from enum import Enum
from typing import Annotated, Optional

from toir_app.convert_csv_to_py.convertation import UsersServiceName as USN


class Status(str, Enum):
    """
    Расчётные статусы (для вида обслуживания) записи из OeBS.
    """
    DANGER = '⚡ Превышение'
    TIME_HAS_COME = '⏰ Подошло'
    WAIT_MOMENT = '🎲 Ожидается в текущем периоде'
    NO_NEED = '❌ Нет необходимости'
    BAD_REQUEST = 'Не был расчитан'


class SpecialStatusForCarBase(str, Enum):
    """
    Глобальные статусы, устанавливающие особое состояние для ТС (для админа).

    Примеры статусов (доступно расширение):
    - к выбытию
    - на реализации
    - после ВР
    - ...
    """
    DISPOSAL = 'К выбытию'
    ON_SALE = 'На реализации'
    REMEDIAL_REPAIR = 'На восстановительном ремонте'


class UserRole(str, Enum):
    """Полномочия Пользователей (read_only, can_edit, admin)."""
    READ_ONLY = 'Только чтение'
    CAN_EDIT = 'Редактирует свой цех'
    ADMIN = 'Полный доступ'


class StaticOrganization(str, Enum):
    """Действующие огранизации из OeBS (Ю51, Ю52, Ю53, Ю54)."""
    ORG_TWO = 'Ю51'
    ORG_THREE = 'Ю52'
    ORG_FOUR = 'Ю53'
    ORG_FIVE = 'Ю54'


convert_oebs_name_to_1c_normal_name: dict[str, str] = {
    'Ю51': '2-МГ',
    'Ю52': '3-АЛ',
    'Ю53': '4-НТ',
    'Ю54': '5-НТ',
    'Ю80': 'УПР'
}


# Связываем ServiceName с группой взаимосвязанных работ:
ServiceWorkData: dict[Annotated[USN, str], Optional[int]] = {
    USN.TO_4.value: 1,
    USN.TO_2.value: 1,
    USN.TO_1.value: 1,
    USN.TO.value: None,
    USN.TO_2000.value: 2,
    USN.TO_1000.value: 2,
    USN.TO_250.value: 2,
    USN.TO_GAZ.value: None,
    USN.ENGINE.value: None,
    USN.GEARBOX.value: None,
    USN.ANTIFREEZE.value: None,
    USN.HYDRO.value: None,
    USN.DRIVE_AXLE.value: None,
    USN.STEERING_WHEEL.value: None,
    USN.BRAKE_FLUID.value: None,
    USN.ON_BOARD_TRANSMISSION.value: None
}
