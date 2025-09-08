from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    # CallbackQuery,
    Message,
)

from bot_command import BotCommand
from services.gateway import backend_gateway

router = Router()


@router.message(F.text.startswith(f'/start {BotCommand.CAR.value}'))
async def get_service_works_in_archive_by_car(message: Message):
    """Получение инфы о архивных работах ТС."""
    async with backend_gateway as connector:
        if message.text:
            car_id = message.text.split(BotCommand.CAR.value)[1]
        if car_id.isdigit():
            data = await connector.get_car_info(path=int(car_id))
        if len(data):
            stmt = []
            for el in data:
                stmt.append(el.get('zvr_number', 'нет данных'))
            await message.answer(', '.join(stmt))
        else:
            await message.answer('пока ничего нет')


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
