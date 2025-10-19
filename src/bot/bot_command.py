from enum import Enum


class BotCommand(Enum):
    """Общие комманды для бота."""

    CAR = 'car_'
    SERVICE_WORK = 'service_work_'
    MATERIALS = 'materials'
    SERVICE_WORK_DONE = 'work_done'
    SERVICE_WORK_BACK = 'work_back'
