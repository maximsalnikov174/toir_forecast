from enum import Enum


class BaseCommand(Enum):
    """Абстракция."""

    def __repr__(self) -> str:
        return self.value

    def __str__(self) -> str:
        return self.value


class CommonKeyboardCommand(BaseCommand):
    """Общие команды для клавиатур."""

    BACK = '⬅️ К списку работ'
    DONE = '✅ Завершаем эту работу!'
    BOM = '📦 Посмотреть запчасти'


class CommonAnswer(BaseCommand):
    """Общие команды для ответов."""

    NO_DATA = 'Заявленных работ по сервисным обслуживаниям пока нет'
    NO_PERMISSION = '🥹 Кто ты, воин?'
    TO_LATE = '🌵🤠 на Диком Западе есть кто-то быстрее тебя'
    ACTIVE_WORKS = 'Активные работы для объекта '  # ...
