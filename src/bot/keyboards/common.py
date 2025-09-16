from asyncio import create_task, sleep

from aiogram.types import Message

from constants import KEYBOARD_DELETE_FROM_SECONDS


async def delete_message(message: Message, delay: int) -> None:  # noqa: E501 FIXME -> return type
    """Удаляет сообщение после указанного в секундах времени."""
    await sleep(delay)
    await message.delete()


async def fast_remove_keyboard(message: Message) -> None:
    """Мгновенно удаляет клавиатуру после нажатия кнопки юзером."""
    await message.edit_reply_markup(reply_markup=None)


async def create_task_for_delete_message_after_delay(
        message: Message,
        delay: int = KEYBOARD_DELETE_FROM_SECONDS,
) -> None:
    """Создает задачу для удаления сообщения (в т.ч. с клавиатурой).

    Args:
        delay: задержка (в секундах), после которой сообщение удаляется.
    """
    create_task(delete_message(message, delay))
    return None
