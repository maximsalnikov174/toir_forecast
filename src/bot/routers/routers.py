from aiogram import Dispatcher

from handlers.admin import router as admin_router

main_dp = Dispatcher()


# РОУТЕРЫ: подключаем к диспетчеру роутеры из handlers:
main_dp.include_router(admin_router)
# main_dp.include_router(admin_router)
