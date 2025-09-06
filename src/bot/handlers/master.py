from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    # CallbackQuery,
    Message,
)

router = Router()


@router.message(CommandStart())
async def command_get_data_handler(
    message: Message,
    state: FSMContext,
) -> None:
    """Обработка команды начала взаимодействия с ботом."""
    try:
        await state.clear()  # сбрасываем состояние FSM

        # # Проверка прав доступа к чату:
        # if not await check_users(id=message.chat.id):
        #     await message.answer(LEX[CommandForBot.NOT_ACCESS])

        await message.answer('Привет')

    except Exception:
        await message.answer('Sorry')
        print('Sorry, bro')
