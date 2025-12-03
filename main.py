import asyncio
import os
from aiogram import Bot, Dispatcher, F
from dotenv import load_dotenv

from core.handlers.base import start_bot, stop_bot, get_start, get_help
from core.handlers.parse import start_parse_by_inn, parse_by_inn
from core.handlers.error import error_message
from core.utils.state import UsersSteps

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

    dp.message.register(start_parse_by_inn,
                        F.text=='Поиск по ИНН')
    dp.message.register(parse_by_inn,
                        UsersSteps.GET_INN)



    dp.message.register(error_message)

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(start())