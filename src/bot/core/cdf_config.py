# CallbackDataFactory configuration

from aiogram.filters.callback_data import CallbackData


class ServiceWorkFactory(CallbackData, prefix='complete_service_work'):
    """Фабрика коллбэков для действий с `service_work` при выполнении работ."""

    car_tag: str  # Идентификатор ТС (например, рандомная комбинация)
    # car_grz: str  # Уникальный ГРЗ ТС (пока не используется)
    service_work_id: int  # Идентификатор сервисной работы
