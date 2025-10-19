from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from handlers.master import router as master_router

# from middleware.db import DatabaseMiddlware
# from src.backend.core.db import get_async_session

# Инициализируем хранилище:
storage = MemoryStorage()

main_dp = Dispatcher(storage=storage)

# РОУТЕРЫ: подключаем к диспетчеру роутеры из handlers:
main_dp.include_router(master_router)
# main_dp.include_router(admin_router)
