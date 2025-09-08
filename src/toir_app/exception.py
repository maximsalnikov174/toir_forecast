from http import HTTPStatus
from typing import Any

from fastapi_users.exceptions import FastAPIUsersException


class BaseException(Exception):
    """Метакласс исключюения с `reason` (причиной)."""

    def __init__(self, reason: Any) -> None:
        self.reason = reason


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


class BadTypeUploadFileException(Exception):
    """Если файл для загрузки имеет неправильный тип."""


class ServiceNameBadDataException(Exception):
    """Если в файле для загрузки вид работ пришел некорректным."""


class ServiceNameNotFoundException(BaseException):
    """Если в файле для загрузки есть вид работ с необработанным названием."""


class NoPermissionForSuperUser(Exception):
    """У пользователя нет прав суперпользователя."""


class NoPermissionForActionException(Exception):
    """Пользователь не обладает необходимыми правами."""


class AlreadyAssignedException(Exception):
    """Сигнал о попытке повторного назначения."""


class NotFoundError(BaseException):
    """Данные не были найдены."""


class CarNotFoundException(NotFoundError):
    """Сигнал, что ТС по id не найдено."""


class CarInArchiveException(Exception):
    """Сигнал, что ТС находится (было переведено) в архив."""


class ObjectIsExistException(Exception):
    """Объект уже существует."""


class ObjectNotFoundException(Exception):
    """Объект в БД не найден."""


class InsufficientDataError(Exception):
    """Указание на отсутствие полноты данных в таблице."""


class BarcodeInAreaNotFoundException(Exception):
    """Штрих-код не найден в указанной области."""


class BarcodeNotValidException(Exception):
    """Штрих-код не соответствует шаблону."""


class NotAllFilesSuccessfullyUpload(BaseException):
    """Не все файлы были успешно обработаны и загружены."""
