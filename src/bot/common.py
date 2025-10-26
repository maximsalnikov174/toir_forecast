from typing import Optional

from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from constants import BOM_DESCRIPTION_LEN
from services.gateway import BackendApiGateway


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


async def organize_service_work_bom_list(
    service_work_id: int,
    session: BackendApiGateway,
) -> list[str]:
    """Формирует ответ со списком использованных в ЗВР материалов."""
    result: list[str] = []
    total_materials = (
        await session.get_bom_for_service_work(service_work_id)
    )
    if docs := total_materials.get('docs_in_service_work'):
        # Перебираем все документы:
        for doc in docs:
            components = doc.get('components')

            # Перебираем все элементы внутри каждого документа:
            for elem in components:
                data = (
                    f"{elem['material_name'][:BOM_DESCRIPTION_LEN]} "
                    f"({elem['material_count']} ед.)"
                )
                result.append('✔️ ' + data + '\n')
    return result
