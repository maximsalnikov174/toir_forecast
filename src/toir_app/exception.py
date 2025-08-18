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


class NoPermissionForSuperUser(Exception):
    """У пользователя нет прав суперпользователя."""


class NoPermissionForActionException(Exception):
    """Пользователь не обладает необходимыми правами."""


class AlreadyAssignedException(Exception):
    """Сигнал о попытке повторного назначения."""


class NotFoundError(Exception):
    """Данные не были найдены."""
    def __init__(self, reason: Any) -> None:
        self.reason = reason


class CarNotFoundException(NotFoundError):
    """Сигнал, что ТС по id не найдено."""


class CarInArchiveException(Exception):
    """Сигнал, что ТС находится (было переведено) в архив."""


class ObjectIsExistException(Exception):
    """Объект уже существует."""


class ObjectNotFoundException(Exception):
    """Объект в БД не найден."""
