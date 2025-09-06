class NoConnectToBackendException(Exception):
    """Модуль с ботом не смог подключиться к бэкенду."""


class NoParseDataFromButtonException(Exception):
    """Не удалось извлечь данные из нажатой пользователем кнопки."""


class NoCallbackDataException(Exception):
    """В полученном ответе не оказалось данных из callback."""
