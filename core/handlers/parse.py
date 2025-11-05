import asyncio
import random
import os
import logging
from aiogram import Bot
from aiogram.types import Message
from aiogram.enums import parse_mode
from playwright.async_api import async_playwright
from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
]


async def parse_by_inn(messages: Message, bot: Bot):
    await messages.answer(f'{messages.from_user.first_name} подождите немного! Ищем данные по ИНН:{messages.text}')

    try:
        logger.info('Начало третьего сайта')
        
        async with async_playwright() as p:
            # Выбираем рандомный User-Agent
            random_user_agent = random.choice(USER_AGENTS)
            
            # Запускаем браузер
            browser = await p.chromium.launch(headless=True)
            
            # Создаём контекст с рандомным User-Agent
            context = await browser.new_context(user_agent=random_user_agent)
            page = await context.new_page()
            
            # Переходим на сайт
            await page.goto("https://pb.nalog.ru/index.html")
            
            # Ищем и заполняем input
            input_inn = page.locator("//input[contains(@class, 'u3-editor')]").first
            await input_inn.click()
            await input_inn.fill(messages.text)
            await input_inn.press("Enter")
            
            # Даём время на загрузку
            await page.wait_for_timeout(5000)
            await page.screenshot(path=f'./result/screenshot/third_site/{messages.text}(1).png')
            
            # Кликаем на организацию
            name_organization = page.locator("//div[contains(@class, 'pb-card__title')]")
            await name_organization.click()
            
            await page.wait_for_timeout(5000)
            
            # Скроллим и берём скриншоты
            result_info = page.locator("//span[contains(text(), 'Сведения о лице, имеющем право без доверенности действовать от имени юридического лица')]")
            await result_info.scroll_into_view_if_needed()
            await page.screenshot(path=f'./result/screenshot/third_site/{messages.text}(2).png')
            
            await page.wait_for_timeout(2000)
            
            result_info = page.locator("//span[contains(text(), 'Сведения о непредставлении налоговой отчетности более года')]")
            await result_info.scroll_into_view_if_needed()
            await page.screenshot(path=f'./result/screenshot/third_site/{messages.text}(3).png')
            
            logger.info('Конец третьего сайта')
            
            await context.close()
            await browser.close()
            
    except Exception as e:
        logger.error(f'Ошибка в третьем сайте: {e}')