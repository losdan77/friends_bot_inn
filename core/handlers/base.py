import os
from aiogram import Bot
from aiogram.types import Message, BotCommand, BotCommandScopeDefault
from aiogram.enums import parse_mode
from dotenv import load_dotenv

from core.keyboards.keyboard import main_menu


load_dotenv()
ADMIN_ID = os.getenv('ADMIN_ID')

async def set_commands(bot: Bot):
    commands = [
        BotCommand(command='start',
                   description='Начало работы'),
        BotCommand(command='help',
                   description='Помощь с ботом'),
    ]
    await bot.set_my_commands(commands, BotCommandScopeDefault())


async def start_bot(bot: Bot):
    await set_commands(bot)
    await bot.send_message(ADMIN_ID, 'Бот запущен!',
                           parse_mode='HTML')


async def stop_bot(bot: Bot):
    await bot.send_message(ADMIN_ID, 'Бот остановлен!')


async def get_help(message: Message, bot: Bot):
    username = message.from_user.first_name
    help_text = f'''
                    Доброго времени суток, <b>{username}</b>,\
 убидительная просьба <u>использовать кнопки</u> приведенные в боте,\
 а так же <u>следовать рекомендациям бота</u> по заполнению форм.
                '''
    await message.answer(help_text,
                         parse_mode='HTML')

async def get_start(message: Message, bot: Bot):
    user_id = message.from_user.id

    username = message.from_user.first_name
    hello_text = f'''
                    Привет, <b>{username}</b> Я бот в котором ты можешь проверить компанию перед встречей и т.д.\
                    Выберете что Вас интересует в меню ниже.
                '''
    await message.answer(hello_text,
                         reply_markup=main_menu,
                         parse_mode='HTML')