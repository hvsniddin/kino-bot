import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from app import handlers
from app.config import BOT_TOKEN, validate_config


async def main():
    validate_config()
    logging.basicConfig(level=logging.INFO)
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="Markdown"))
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(handlers.admin.router)
    dp.include_router(handlers.user.router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

