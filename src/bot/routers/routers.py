from aiogram import Dispatcher

from handlers.master import router as master_router

# from middleware.db import DatabaseMiddlware
# from src.backend.core.db import get_async_session

main_dp = Dispatcher()

# РОУТЕРЫ: подключаем к диспетчеру роутеры из handlers:
main_dp.include_router(master_router)
# main_dp.include_router(admin_router)
