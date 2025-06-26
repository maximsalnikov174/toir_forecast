from enum import Enum


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
