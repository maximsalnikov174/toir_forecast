from asyncio import create_task, sleep
from typing import Union

from aiogram.types import Message
from aiogram.exceptions import TelegramBadRequest

from constants import KEYBOARD_BASE_ALIVE_IN_SECONDS


async def delete_message(message: Message, delay: Union[int, float]) -> None:  # noqa: E501 FIXME -> return type
    """Удаляет сообщение после указанного в секундах времени.

    Exception
    ---------
        `TelegramBadRequest`: если сообщение уже удалено - просто пропускаем.
    """
    await sleep(delay)

    try:
        await message.delete()
    except TelegramBadRequest:
        pass


async def fast_remove_keyboard(message: Message) -> None:
    """Мгновенно удаляет клавиатуру после нажатия кнопки юзером."""
    await message.edit_reply_markup(reply_markup=None)


async def create_task_for_delete_message_after_delay(
        message: Message,
        delay: Union[int, float] = KEYBOARD_BASE_ALIVE_IN_SECONDS,
) -> None:
    """Создает задачу для удаления сообщения (в т.ч. с клавиатурой).

    Args:
        delay: задержка (в секундах), после которой сообщение удаляется.
    """
    create_task(delete_message(message, delay))
    return None
