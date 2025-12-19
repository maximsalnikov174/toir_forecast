from typing import Union

from aiogram.filters import Filter
from aiogram.types import CallbackQuery

from bot_command import BotCommand


class ServiceWorkFilter(Filter):
    """Фильтр для поиска service_work."""

    def __init__(self, command: BotCommand):
        self.command = command.value

    async def __call__(self, callback: CallbackQuery) -> Union[dict, bool]:
        if callback.data is None or not callback.data.startswith(self.command):
            return False

        id_part = callback.data[len(self.command):]
        if not id_part or not id_part.isdigit():
            return False

        return {'service_work_id': int(id_part)}
