import asyncio

from aiogram import Bot, Dispatcher

from core.config import settings
from routers.routers import main_dp as dp

bot = Bot(token=settings.tg_bot_token)


async def start_bot(dispatcher: Dispatcher) -> None:
    """Запуск бота."""
    await dispatcher.start_polling(bot)


# Если запускается этот файл:
if __name__ == '__main__':
    asyncio.run(start_bot(dispatcher=dp))
