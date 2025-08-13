import logging

from aiohttp import ClientSession
from fastapi import HTTPException

from core.config import settings
from models import ServiceWork


class TgSchedular:
    """Отправка уведомлений через Telegram API.

    ## Args:
    - `chat_id`: родительская группа в Telegram (где есть threads)
    """

    chat_id = settings.chat_id

    def __init__(self, obj: ServiceWork):
        self.obj = obj

    def convert_model_to_text(self) -> str:
        """Обрабатывает поля модели `ServiceWork` в человекочитаемый текст."""
        return (
            f'Готово!\n🚚 {self.obj.car.grz}\n🔧 {self.obj.next_service.name}'
            f'🧰 {self.obj.station.name}.'
        )

    def get_thread_by_organization(self) -> int:
        """Определяет `thread_id` с учётом подразделения ТС.

        ## Warning
        Костыль с `+ 1` под конкретно созданную ТГ-группу.
        """
        return self.obj.car.organization_id + 1

    async def send_notification(self):
        """Функция отправки уведомления в Telegram"""
        try:
            async with ClientSession() as session:
                url = (
                    'https://api.telegram.org/'
                    f'bot{settings.tg_bot_token}/sendMessage'
                )
                payload = {
                    'chat_id': self.chat_id,
                    'message_thread_id': self.get_thread_by_organization(),
                    'text': self.convert_model_to_text()
                }
                async with session.post(url, json=payload) as resp:
                    if resp.status != 200:
                        raise HTTPException(
                            status_code=500,
                            detail='Ошибка отправки сообщения')

        except Exception as e:
            logging.error(f'Ошибка: {str(e)}')
            raise HTTPException(status_code=500, detail=str(e))

    # async def mass_sending_notification(self, chat_ids: list[int], text: str):
    #     """Функция рассылки уведомлений в Telegram группе контактов."""
    #     for chat_id in chat_ids:
    #         await self.send_notification(chat_id, text)
