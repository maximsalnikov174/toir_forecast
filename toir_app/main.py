import uvicorn
from fastapi import FastAPI

from toir_app.api.endpoints import router
from toir_app.core.config import settings


toir_app = FastAPI(title=settings.app_title)

# Подключаем роутер к приложению.
toir_app.include_router(router)

if __name__ == '__main__':
    uvicorn.run('main:toir_app', reload=True)


# При запуске приложения через python main.py, работа с env-файлом строится
# иначе — нужно указать полный или относительный путь до env-файла либо
# указать его в параметрах метода uvicorn.run()
