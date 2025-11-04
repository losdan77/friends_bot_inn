import asyncio
import os
from aiogram import Bot, Dispatcher, F
from dotenv import load_dotenv

from core.handlers.base import start_bot, stop_bot, get_start, get_help
from core.handlers.parse import parse_by_inn


load_dotenv()
TOKEN = os.getenv('TOKEN')


async def start():
    bot = Bot(token=TOKEN)
    dp = Dispatcher()

    dp.startup.register(start_bot)
    dp.shutdown.register(stop_bot)

    dp.message.register(get_start,
                        F.text == '/start')
    dp.message.register(get_help,
                        F.text == '/help')

    dp.message.register(parse_by_inn)

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(start())