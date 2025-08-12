import asyncio

from aiogram import Bot, Dispatcher
from fastapi import FastAPI

from core.config import settings
from routers.routers import main_dp as dp

bot = Bot(token=settings.tg_bot_token)  # TODO -> свой токен
app = FastAPI()


@app.post('/notify')
async def send_notification(chat_id: int, text: str):
    print('хотя бы пришел')
    await bot.send_message(chat_id=chat_id, text=text)
    return {"status": "ok"}


async def start_webhook():
    from uvicorn import Config, Server
    config = Config(app=app, host="0.0.0.0", port=8000)
    server = Server(config)
    await server.serve()


if __name__ == '__main__':
    asyncio.run(start_webhook())
