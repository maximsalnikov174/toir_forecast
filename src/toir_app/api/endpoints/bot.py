import logging
from typing import Optional

from aiohttp import ClientSession
from fastapi import HTTPException

from core.config import settings
from models import EventForBot, ServiceWork, SpecialStatusForCar


class TgSchedular:
    """Отправка уведомлений через Telegram API.

    ## Args:
    - `chat_id`: родительская группа в Telegram (где есть threads)
    """

    chat_id = settings.chat_id

    def convert_model_to_text(self, obj, event: str) -> str:
        """Обрабатывает поля модели `ServiceWork` в человекочитаемый текст."""

        if event == EventForBot.DONE:
            msg = ('Выполнено', f'\n📍 {obj.station.name}')
        elif event == EventForBot.CLOSE:
            msg = ('Карточка успешно закрыта', '')
        elif event == EventForBot.END_FOR_STATUS:
            msg = ('⏳ Истёк статус ТС', '')

        if isinstance(obj, ServiceWork):
            elem = f'🔧 {obj.next_service.name}'
        elif isinstance(obj, SpecialStatusForCar):
            elem = f'🏷️ {obj.special_status.name}'

        return (
            f'{msg[0]}\n\n'
            f'🚚 {obj.car.grz}\n'
            f'{elem}'
            f'{msg[1]}'
        )

    def _get_thread_by_organization(self, obj) -> int:
        """Определяет `thread_id` с учётом подразделения ТС.

        ## Warning
        Костыль с `+ 1` под конкретно созданную ТГ-группу.
        """
        return obj.car.organization_id + 1

    async def _send_notification(self, message, thread: Optional[int] = None):
        """Функция отправки уведомления в Telegram."""
        try:
            async with ClientSession() as session:
                url = (
                    'https://api.telegram.org/'
                    f'bot{settings.tg_bot_token}/sendMessage'
                )
                payload = {
                    'chat_id': self.chat_id,
                    'message_thread_id': thread,
                    'text': message
                }
                async with session.post(url, json=payload) as resp:
                    if resp.status != 200:
                        raise HTTPException(
                            status_code=500,
                            detail='Ошибка отправки сообщения')

        except Exception as e:
            logging.error(f'Ошибка: {str(e)}')
            raise HTTPException(status_code=500, detail=str(e))

    async def send_notification(self, obj, event: str):
        """Функция отправки уведомления в Telegram в группу цеха."""
        return await self._send_notification(
            thread=self._get_thread_by_organization(obj=obj),
            message=self.convert_model_to_text(obj=obj, event=event),
        )

    async def send_notification_for_admin(self, msg: str):
        """Функция отправки уведомления в группу Админа."""
        return await self._send_notification(message=msg)

    # async def mass_sending_notification(self, chat_ids: list[int], text: str):
    #     """Функция рассылки уведомлений в Telegram группе контактов."""
    #     for chat_id in chat_ids:
    #         await self.send_notification(chat_id, text)


bot_schedular = TgSchedular()
