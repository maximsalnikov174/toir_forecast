from typing import Optional

from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery


async def get_button_text_from_state(
    state: FSMContext,
    storage_key: str,
    callback: Optional[CallbackQuery] = None
) -> Optional[str]:
    """
    Извлекает текст кнопки из состояния FSM по callback data.

    Args:
        state: Контекст состояния FSM
        callback: CallbackQuery объект
        storage_key: Ключ в состоянии, где хранится mapping кнопок

    Returns:
        Текст кнопки или None если не найден
    """
    data = await state.get_data()
    button_mapping = data.get(storage_key, {})

    if callback:
        return button_mapping.get(callback.data)

    return button_mapping
