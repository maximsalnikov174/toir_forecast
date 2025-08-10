from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    Message,
)

from constants import ADMIN_TG_ID

# from exception import (
#     NoCallbackDataException,
#     NoConnectToBackendException,
#     NoParseDataFromButtonException,
# )
# from handlers.common import (
#     check_users,
#     create_keyboard_and_sent_anwser,
#     create_message,
#     create_ticket_from_bot,
#     give_anwser,
#     parse_data,
# )
# from lexicon.lexicon import LEXICON_RU as LEX
# from lexicon.lexicon import CommandForBot
# from keyboards.functions import create_first_button
# from state_form import QuestionForm
# from url_path import (
#     PATTERN_FOR_FIND_PAGI,
#     PATTERN_FOR_FIND_QUESTION_VALUE,
#     PATTERN_FOR_FIND_SECTOR_VALUE,
#     SECTOR_PATH,
#     QUESTION_PATH,
# )

router = Router()


@router.message(CommandStart())
async def command_get_data_handler(
    message: Message,
    # state: FSMContext,
) -> None:
    """Обработка команды начала взаимодействия с ботом."""
    try:
        # await state.clear()  # сбрасываем состояние FSM

        # Проверка прав доступа к чату:
        if message.chat.id != ADMIN_TG_ID:
            await message.answer('Пока не хватает прав')

        else:
            await message.answer('Буду направлять уведомления')
            #     text=(
            #         f'{LEX[CommandForBot.START]}'
            #         f'{message.chat.first_name}!\n'
            #         f'{LEX[CommandForBot.WELCOME]}'
            #     ),
            #     reply_markup=create_first_button().as_markup(),
            # )

    except Exception:
        print('Не сработало что-то')
