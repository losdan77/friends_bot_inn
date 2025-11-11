import asyncio
from inspect import AGEN_CLOSED
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
        logger.info('Начало парсинга публичного бизнеса')
        
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
            name_organization = page.locator("//div[contains(@class, 'pb-card__title')]").first
            await name_organization.click()
            
            await page.wait_for_timeout(5000)
            await page.screenshot(path=f'./result/screenshot/third_site/{messages.text}(2).png')
            
            name_organization_text = await page.locator("//span[contains(@class, 'pb-company-name')]").first.text_content()
            inn_organization_text = await page.locator("//a[contains(@data-appeal-kind, 'EGRUL_INN')]").first.text_content()
            first_date_organization_text = await page.locator("//div[contains(@class, 'pb-company-field-value')]").nth(3).text_content()
            age_organization_text = "11 лет"
            address_organization_text = await page.locator("//a[contains(@data-appeal-kind, 'EGRUL_ADRES')]").first.text_content()
            capital_organization_text = 'some text'
            main_activity_organization_text = await page.locator("//a[contains(@data-appeal-kind, 'EGRUL_OKVED')]").first.text_content()
            registrar_organization_text = 'some text'
            average_number_of_employees_organization_text = await page.locator("//a[contains(@data-appeal-kind, 'SSCHR')]").first.text_content()


            logger.info('Конец парсинга публичного бизнеса')
            
            await context.close()
            await browser.close()

            await messages.answer(f'{messages.from_user.first_name}, данные по ИНН:{messages.text} успешно найдены!')
            
            await messages.answer(f'''<b>{name_organization_text}</b>

<b>ОБЩАЯ ИНФОРМАЦИЯ:</b>
ИНН: {inn_organization_text}
Возраст: {age_organization_text} (регистрация {first_date_organization_text})
Адрес: {address_organization_text}
Уставный капитал: {capital_organization_text}
Основной вид деятельности: {main_activity_organization_text}
Регистратор: {registrar_organization_text}

<b>ОРГАНЫ УПРАВЛЕНИЯ:</b>
<b>Генеральный директор:</b>

(ИНН ) период с 01.04.2014
<b>Учредители:</b>

(ИНН /) <b>(Чистая прибыль от бизнеса за три года ~ млн. руб.)</b>

<b>ФИНАНСОВАЯ ИНФОРМАЦИЯ:</b>
Среднесписочная численность:~ {average_number_of_employees_organization_text}
Выручка от продажи за 2021: 
Чистая прибыль за 2021:     
Чистая прибыль за последние три года: ~ 
Исполнительное производство: 
Как ответчик  руб.
Как истец  руб

Последние изменения были совершены 
Данные актуальны на 
''', parse_mode='HTML')

    except Exception as e:
        logger.error(f'Ошибка в парсинге публичного бизнеса: {e}')
        await messages.answer(f'{messages.from_user.first_name}, ошибка в поиске данных по ИНН:{messages.text}')

    