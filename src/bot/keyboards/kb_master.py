from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from lexicon import CommonKeyboardCommand
from bot_command import BotCommand
from schemas.service_work import ActiveServiceWorksSchema


async def build_zvr_list_buttons(
    cards: list[ActiveServiceWorksSchema],
    state: FSMContext,
) -> InlineKeyboardBuilder:
    """Создает клавиатуру с кнопками «Вид работ + № ЗВР» по одной в ряд."""
    builder = InlineKeyboardBuilder()

    # Фиксируем текущее состояние FSM:
    current_data = await state.get_data()
    button_mapping = current_data.setdefault('button_mapping', {})
    station_info = {}  # шаблон для сопоставления service_work_id и station_id

    for card in cards:
        data = f"{BotCommand.SERVICE_WORK.value}{str(card['id'])}"
        msg = f"{card['service_name']}  |  {card['zvr_number']}"

        # Фиксируем в FCM `callback` и `описание работ`:
        button_mapping[data] = msg
        station_info[card['id']] = card['station_id']

        builder.button(text=msg, callback_data=data)

    # Обновляем состояние FSM:
    await state.update_data(
        button_mapping=button_mapping,
        station_info=station_info,
    )

    builder.adjust(1)  # <-- по одной в ряд
    return builder


async def build_done_button(state: FSMContext) -> InlineKeyboardBuilder:
    """Создает клавиатуру с кнопками `завершить работу` и `назад к списку`."""
    builder = InlineKeyboardBuilder()

    # Кнопка с переходом к списку использованных материалов,
    # когда вложен (в FSM) хоть один материал:
    if len(await state.get_value('total_bom')):
        builder.button(
            text=CommonKeyboardCommand.BOM,
            callback_data=BotCommand.MATERIALS,
        )
    # Кнопка с подтверждением выполнения работы:
    builder.button(
        text=CommonKeyboardCommand.DONE,
        callback_data=BotCommand.SERVICE_WORK_DONE,
    )
    # Кнопка с возвратом к предыдущему состоянию:
    builder.button(
        text=CommonKeyboardCommand.BACK,
        callback_data=BotCommand.SERVICE_WORK_BACK,
    )

    builder.adjust(1)  # <-- по одной в ряд
    return builder


async def build_back_button(
        state: FSMContext, in_works: bool = True,
) -> InlineKeyboardBuilder:
    """Создает клавиатуру с кнопкой `назад к списку`."""
    builder = InlineKeyboardBuilder()
    # По умолчанию возвращаемся к списку всех активных работ:
    if in_works:
        msg = CommonKeyboardCommand.BACK
        cb_data = BotCommand.SERVICE_WORK_BACK
    else:  # ... а если нет - то формируем callback для конкретной работы:
        msg = CommonKeyboardCommand.BACK_TO_WORK
        service_work_id = await state.get_value('service_work_id')
        cb_data = f'{BotCommand.SERVICE_WORK.value}{service_work_id}'

    builder.button(text=msg, callback_data=cb_data)
    builder.adjust(1)  # <-- по одной в ряд
    return builder
