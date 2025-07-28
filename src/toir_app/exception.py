from http import HTTPStatus
from typing import Any

from fastapi_users.exceptions import FastAPIUsersException


class InvalidEmailException(FastAPIUsersException):
    """Емэйл, указанный пользователем не прошел валидацию."""
    def __init__(self, reason: Any) -> None:
        self.reason = reason


class StaticDataInDBNotFoundException(Exception):
    """Если в базе данных нет статических данных, необходимых для запуска."""
    def __init__(self, status: HTTPStatus, detail: Any) -> None:
        self.status = status
        self.detail = detail


class BadNameInUploadFileException(Exception):
    """Если файл для загрузки имеет неправильное имя."""
