import os
from aiogram import Bot
from aiogram.types import Message
from aiogram.enums import parse_mode
from dotenv import load_dotenv


async def parse_by_inn(messages: Message, bot: Bot):
    await bot.send_message('Подождите немного!')