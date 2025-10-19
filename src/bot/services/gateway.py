from __future__ import annotations

import asyncio
from http import HTTPStatus
from types import TracebackType
from typing import Any, Optional, Type

from aiohttp import ClientError, ClientSession, ClientTimeout

from constants import (
    MAX_ATTEMPT_FOR_CONNECT,
    SECONDS_FOR_SESSION_CONNECT,
    SECONDS_FOR_SESSION_READ_DATA,
    SECONDS_SLEEP_TIME,
)
from core.config import settings
from exception import NoConnectToBackendException
from backend_path import CAR_PATH, SERVICE_WORK_PATH, USER_PATH
from schemas.service_work import ActiveServiceWorksSchema


class BackendApiGateway():
    """Подключение к бэкенду."""

    root_url = settings.backend_api_url
    session_timeout: ClientTimeout = ClientTimeout(
        connect=SECONDS_FOR_SESSION_CONNECT,  # время на подключение
        sock_read=SECONDS_FOR_SESSION_READ_DATA,  # время на чтение данных
    )

    def __init__(self, token: Optional[str] = None) -> None:
        """Создание экземпляра (пока без сессии)."""
        self._session: ClientSession | None = None
        self._token: Optional[str] = token  # Приватное поле для токена

    @property
    def token(self) -> Optional[str]:
        """Геттер для токена."""
        return self._token

    @token.setter
    def token(self, value: str) -> None:
        """Сеттер для токена."""
        self._token = value

    def _get_headers(self) -> dict[str, str]:
        "Формирование словаря для передачи токена пользователя."
        return {
            'accept': 'application/json',
            'Authorization': f'Bearer {self._token}'
        }

    async def get_user_token(self, telegram_id: int) -> Optional[str]:
        """Entrypoint для получения user-токена по telegram_id."""
        result = await self._fetch_api_data(
            method='get',
            rel_path=(
                f'{USER_PATH}/secret/'
                f'get_token_for_use_in_telegram/{telegram_id}'
            )
        )
        self._token = result.get('access_token')
        return self._token

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

        Args
        ---------
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

        Args
        ---------
        - method: имя метода;
        - path: фрагмент пути (без корневой директории).

        Returns
        ---------
        словарь с данными из БД.
        """
        url = f'{self.root_url}/{path.lstrip("/")}'
        async with self.session.request(method, url, **kwargs) as resp:
            data = await resp.json()

            if resp.status in (HTTPStatus.OK, HTTPStatus.CREATED):
                return data
            if resp.status in (HTTPStatus.BAD_REQUEST, HTTPStatus.NOT_FOUND):
                return {'result': data['detail'], 'status': resp.status}
            else:
                # FIXME (пока не знаю, как работает)
                raise RuntimeError(f'Backend replied {resp.status}: {data}')

    async def _fetch_api_data(
            self,
            method: str,
            rel_path: str,
            **kwargs: Any,
    ) -> dict:
        """Получение данных для бота через API бэкенда.

        Args
        ----------
        - rel_path: часть url, конкретизирующая получаемые данные.

        Constants
        ----------
        - MAX_ATTEMPT_FOR_CONNECT: количество попыток подключения;
        - SECONDS_SLEEP_TIME: интервал между попытками.

        Exceptions
        ----------
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

    async def get_car_info(self, path: str) -> dict:
        """Получение архива `service_work` по `tg_UUID` выбранного ТС."""
        return await self._fetch_api_data(
            method='get',
            rel_path=f'{CAR_PATH}/by_tg_uuid/{path}',
        )

    async def get_service_work_for_current_car(
            self, car_attr: str, station_id: Optional[int] = None,
    ) -> list[ActiveServiceWorksSchema]:
        """Получение списка активных работ (с ЗВР) для клавиатуры мастера.

        ## Params:
            - Мастер видит только работы своей мастерской!
        """
        params = {}
        if station_id is not None:
            params['station_id'] = station_id

        return await self._fetch_api_data(
            method='get',
            rel_path=f'{CAR_PATH}/{car_attr}/service_work',
            params=params,
        )

    async def get_bom_for_service_work(
            self,
            service_work_id: int,
    ):
        """Получение списка уже вложенных в работу материалов."""
        try:
            result = await self._fetch_api_data(
                method='GET',
                rel_path=(
                    f'{SERVICE_WORK_PATH}/{service_work_id}/unit_of_bom'
                ),
            )
            return result
        except Exception as e:
            print(e)

    async def completed_real_service_work(
            self,
            service_work_id: int,
    ):
        """Фиксация факта фактического завершения выбранной работы."""
        try:
            result = await self._fetch_api_data(
                method='PATCH',
                rel_path=(
                    f'{SERVICE_WORK_PATH}/de_facto_completed/'
                    f'?service_work_id={service_work_id}'
                ),
                headers=self._get_headers(),
            )
            return result
        except Exception as e:
            print(e)

    async def get_token(
            self,
            chat_user_id: int,
    ):
        """Получение токена для выполнения запросов, требующих полномочий."""
        return await self._fetch_api_data(
            method='get',
            rel_path=(
                f'{USER_PATH}/secret/get_token_for_use_in_telegram/'
                f'{chat_user_id}'
            )
        )


backend_gateway = BackendApiGateway()


async def get_connector():
    """Создание подключения к бэкенду через точку входа."""
    async with backend_gateway as gateway:
        yield gateway
