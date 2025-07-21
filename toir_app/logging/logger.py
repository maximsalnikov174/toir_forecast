import logging
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from zoneinfo import ZoneInfo

from constants import (BACKUP_COUNT, CUSTOM_TIME_FORMAT, LOG_DIR, LOG_FILE,
                       LOGGER_FORMAT, MAX_BYTES_FOR_LOG_FILE, TIMEZONE_AE)


class TimezoneFormatter(logging.Formatter):
    """Форматтер, задающий время в нужной часовой зоне."""
    def __init__(self, fmt=None, datefmt=None, tz=None):
        super().__init__(fmt, datefmt)
        self.tz = ZoneInfo(TIMEZONE_AE)

    def converter(self, timestamp):
        """Конвертирует timestamp в формат timezone-aware datetime."""
        return (
            datetime.fromtimestamp(timestamp, timezone.utc).astimezone(self.tz)
        )

    def formatTime(self, record, datefmt=None):
        """Форматирует время в нужной таймзоне."""
        dt = self.converter(record.created)
        if datefmt:
            return dt.strftime(datefmt)
        return dt.isoformat()


def configure_logging():
    LOG_DIR.mkdir(exist_ok=True)

    rotating_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=MAX_BYTES_FOR_LOG_FILE,
        backupCount=BACKUP_COUNT,
        encoding='utf-8'
    )

    # Создаем кастомный форматтер с часовой зоной
    formatter = TimezoneFormatter(
        fmt=LOGGER_FORMAT,
        datefmt=CUSTOM_TIME_FORMAT,
    )
    rotating_handler.setFormatter(formatter)

    # Получаем корневые логгеры:
    root_logger = logging.getLogger()

    # Удаляем все существующие обработчики
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        handler.close()  # Важно для корректного закрытия

    # Добавляем наш обработчик
    root_logger.addHandler(rotating_handler)
    root_logger.setLevel(logging.INFO)
    print('Текущие обработчики:', root_logger.handlers)

    # Отключаем propagate для всех дочерних логгеров:
    root_logger.propagate = False

    # Тестовый лог с проверкой временной зоны
    test_time = datetime.now(ZoneInfo(TIMEZONE_AE))
    test_time_now = test_time.strftime(CUSTOM_TIME_FORMAT)
    logging.info(
        f'Проверка часовой зоны - текущее время {test_time_now} '
        f'(часовая зона: {TIMEZONE_AE})'
    )
