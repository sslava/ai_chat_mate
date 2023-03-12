import logging
import os
from urllib.parse import urlparse
from aiohttp import web
from aiogram.utils.executor import Executor
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage


__all__ = ['bot', 'dp', 'executor', 'run_pooling', 'run_webhook']


bot = Bot(token=os.getenv("TELEGRAM_KEY"))
dp = Dispatcher(bot, storage=MemoryStorage())
storage = MemoryStorage()
executor = Executor(dispatcher=dp)


async def on_startup(*args, **kwargs):
    await bot.set_webhook(os.getenv("WEBHOOK_URL"))
    return web.Response(body="WebHook is registered\n")


async def ok(*args, **kwargs):
    return web.Response(body="OK\n")


async def on_shutdown(*args, **kwargs):
    await bot.delete_webhook()
    await dp.storage.close()


def run_pooling():
    executor.start_polling(dp)


def run_webhook():
    parts = urlparse(os.getenv("WEBHOOK_URL"))
    executor.set_webhook(parts.path)

    web_app: web.Application = executor.web_app

    web_app.on_startup.append(on_startup)
    web_app.add_routes([
        web.get('/webhook', on_startup),
        web.get('/ping', ok),
        web.get('/', ok),
    ])

    web.run_app(app=web_app, port=os.getenv("PORT"))
