from typing import Any

from fastapi_users.exceptions import FastAPIUsersException


class InvalidEmailException(FastAPIUsersException):
    """Емэйл, указанный пользователем не прошел валидацию."""
    def __init__(self, reason: Any) -> None:
        self.reason = reason
