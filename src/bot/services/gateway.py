from __future__ import annotations

import asyncio
from http import HTTPStatus
from types import TracebackType
from typing import Any, Type

from aiohttp import ClientError, ClientSession, ClientTimeout

from constants import (
    MAX_ATTEMPT_FOR_CONNECT,
    SECONDS_FOR_SESSION_CONNECT,
    SECONDS_FOR_SESSION_READ_DATA,
    SECONDS_SLEEP_TIME,
)
from core.config import settings
from exceptions import NoConnectToBackendException


class BackendApiGateway():
    """Подключение к бэкенду."""

    root_url = settings.backend_api_url
    session_timeout: ClientTimeout = ClientTimeout(
        connect=SECONDS_FOR_SESSION_CONNECT,  # время на подключение
        sock_read=SECONDS_FOR_SESSION_READ_DATA,  # время на чтение данных
    )

    def __init__(self) -> None:
        """Создание экземпляра (пока без сессии)."""
        self._session: ClientSession | None = None

    async def __aenter__(self) -> BackendApiGateway:
        """Создаёт сессию при входе в контекст."""
        self._session = ClientSession(timeout=self.session_timeout)
        return self

    async def __aexit__(
            self,
            exc_type: Type[BaseException] | None,
            exc_val: BaseException | None,
            exc_tb: TracebackType | None,
    ) -> None:
        """Закрывает сессию при выходе из контекста."""
        if self._session:
            await self._session.close()
            self._session = None

    @property
    def session(self) -> ClientSession:
        """Возвращает текущую сессию или выдаёт ошибку."""
        if self._session is None:
            raise RuntimeError('Сессия не была создана.')
        return self._session

    async def _wait_for_retry(
            self,
            attempt: int,
            handicap: int = (
                SECONDS_FOR_SESSION_CONNECT + SECONDS_FOR_SESSION_READ_DATA
            ),
    ) -> None:
        """Берёт паузу, чтобы дать еще попытку подключиться к бэкенду.

        ## Args:
        - attempt: номер попытки;
        - handicap: дополнительный запас по времени.
        """
        await asyncio.sleep(
            handicap + SECONDS_SLEEP_TIME * 2 ** attempt,
        )

    async def _request(
            self,
            method: str,
            path: str,
            **kwargs: Any,
    ) -> dict:
        """Выполняет запрос к бэкенду указанным методом.

        ## Args:
        - method: имя метода;
        - path: фрагмент пути (без корневой директории).

        ## Returns:
        словарь с данными из БД.
        """
        url = f'{self.root_url}/{path.lstrip("/")}'
        async with self.session.request(method, url, **kwargs) as resp:
            if resp.status in (HTTPStatus.OK, HTTPStatus.CREATED):
                data = await resp.json()
                return data
            if resp.status >= HTTPStatus.BAD_REQUEST:
                body = await resp.text()
                raise RuntimeError(f'Backend replied {resp.status}: {body}')
            # Если обрабатывать другие статусы:
            return {'data': '...'}  # заглушка

    async def _fetch_api_data(
            self,
            method: str,
            rel_path: str,
            **kwargs: Any,
    ) -> dict:
        """Получение данных для бота через API бэкенда.

        ## Args:
        - rel_path: часть url, конкретизирующая получаемые данные.

        ## Constants:
        - MAX_ATTEMPT_FOR_CONNECT: количество попыток подключения;
        - SECONDS_SLEEP_TIME: интервал между попытками.

        ## Exceptions:
        - NoConnectToBackendException: если бэкенд не отвечает.
        """
        last_error = None

        # Создаём несколько попыток:
        for attempt in range(MAX_ATTEMPT_FOR_CONNECT):
            try:
                return await self._request(
                    method=method, path=rel_path, **kwargs,
                )

            except TimeoutError:
                await self._wait_for_retry(attempt, 0)
                # logging.error(
                #     'Подключиться к бэкенду удалось, однако данные '
                #     f'не успели поступить (по таймауту). Причина: {e}',
                # )
            except ClientError:
                await self._wait_for_retry(attempt)
                # logging.error(
                #     'Из-за проблем с подключением к бэкэнду бот '
                #     f'встал на паузу в {round(SECONDS_SLEEP_TIME, 1)} сек. '
                #     f'Причина: {e}.'
                # )
            except RuntimeError:
                ...
                # logging.error(
                #     f'Что-то не так в коде, стоит проверить. Причина: {e}.'
                # )
            except Exception:
                ...
                # logging.error(
                #     'Бот не смог получить данные и встал на паузу'
                #     f' в {round(SECONDS_SLEEP_TIME, 1)} сек. '
                #     f'Причина: {e}.'
                # )

        # Если дошёл - значит бэк не отвечает:
        raise NoConnectToBackendException(last_error)
