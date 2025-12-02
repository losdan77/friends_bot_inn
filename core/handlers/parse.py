import asyncio
import aiohttp
from inspect import AGEN_CLOSED
import random
import os
import logging
from aiogram import Bot
from aiogram.types import Message
from aiogram.enums import parse_mode
from playwright.async_api import async_playwright
from playwright.sync_api import sync_playwright
from datetime import datetime

logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
]

async def get_execution_data(inn):
    """
    Получает данные через парсинг публичных источников
    """
    try:
        # Используем сервис, который парсит ФССП
        url = f"https://www.parsimo.ru/api/fssp/search"
        
        params = {
            "inn": inn
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get('found'):
                        return {
                            "status": "found",
                            "defendant": data.get('total', {}).get('defendant', '0 руб.'),
                            "plaintiff": data.get('total', {}).get('plaintiff', '0 руб.')
                        }
                    else:
                        return {
                            "defendant": "0 руб.",
                            "plaintiff": "0 руб."
                        }
    except Exception as e:
        logger.warning(f"Parsimo ошибка: {e}")
        return {
            "defendant": "0 руб.",
            "plaintiff": "0 руб."
        }

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

            # execution_data = await get_execution_data("7728786311")
            
            first_date_organization_text = await page.locator("//div[contains(@class, 'pb-company-field-value')]").nth(3).text_content()
            try:
                # Парсим дату регистрации (предполагаем формат "ДД.ММ.ГГГГ")
                registration_date = datetime.strptime(first_date_organization_text.strip(), "%d.%m.%Y")
                
                # Считаем возраст
                today = datetime.now()
                age_organization_text = (today - registration_date).days // 365
                
                # Если нужно красиво: "11 лет", "2 года", "1 год"
                if age_organization_text % 10 == 1 and age_organization_text % 100 != 11:
                    age_text = f"{age_organization_text} год"
                elif age_organization_text % 10 in [2, 3, 4] and age_organization_text % 100 not in [12, 13, 14]:
                    age_text = f"{age_organization_text} года"
                else:
                    age_text = f"{age_organization_text} лет"
                
                age_organization_text = age_text
                
            except Exception as e:
                logger.error(f"Ошибка при расчёте возраста: {e}")
                age_organization_text = "N/A"

            address_organization_text = await page.locator("//a[contains(@data-appeal-kind, 'EGRUL_ADRES')]").first.text_content()
            capital_organization_text = await page.locator("//div[contains(text(), 'Сведения об уставном капитале')]/ancestor::div[@class='pb-company-field']//div[@class='pb-company-field-value']/p").text_content()
            capital_organization_text = " ".join(capital_organization_text.split())
            main_activity_organization_text = await page.locator("//a[contains(@data-appeal-kind, 'EGRUL_OKVED')]").first.text_content()
            registrar_organization_text = await page.locator("//div[contains(text(), 'Наименование налогового органа, осуществляющего регистрацию по месту нахождения организации:')]/ancestor::div[@class='pb-company-field']//div[@class='pb-company-field-value']").text_content()

            general_director_organization_name = await page.locator(
                "//span[contains(text(), 'Сведения о лице, имеющем право без доверенности действовать от имени юридического лица')]"
                "/ancestor::div[@class='pb-company-block']"
                "/following-sibling::div[@class='pb-company-block']"
                "//div[@class='pb-company-field-value'][1]//a"
            ).first.text_content()    
            general_director_organization_inn = await page.locator(
                "//span[contains(text(), 'Сведения о лице')]"
                "/ancestor::div[@class='pb-company-block']"
                "/following-sibling::div[@class='pb-company-block']"
                "//div[contains(., 'ИНН:')]/ancestor::div[@class='pb-company-field']//div[@class='pb-company-field-value']"
            ).first.text_content()    
            general_director_organization_position = await page.locator(
                "//span[contains(text(), 'Сведения о лице')]"
                "/ancestor::div[@class='pb-company-block']"
                "/following-sibling::div[@class='pb-company-block']"
                "//div[contains(., 'Должность руководителя:')]/ancestor::div[@class='pb-company-field']//div[@class='pb-company-field-value']"
            ).first.text_content()  

            founder_name = await page.locator(
                "//span[contains(text(), 'Сведения об учредителях')]"
                "/ancestor::div[@class='pb-company-block']"
                "/following-sibling::div[@class='pb-company-block']"
                "//a[not(contains(@class, 'fs-big'))]"
            ).first.text_content()
            founder_inn = await page.locator(
                "//span[contains(text(), 'Сведения об учредителях')]"
                "/ancestor::div[@class='pb-company-block']"
                "/following-sibling::div[@class='pb-company-block']"
                "//div[contains(., 'ИНН:')]/..//div[@class='pb-company-field-value']"
            ).first.text_content()  

            employees_count = await page.locator(
                "//span[contains(text(), 'Среднесписочная численность работников организации')]"
                "/ancestor::div[@class='pb-company-block']"
                "//a[contains(@class, 'lnk-appeal')]"
            ).text_content()

            actual_data_date_text = await page.locator(
                "//span[contains(text(), 'сформировано')]/parent::div//b"
            ).first.text_content()
            actual_data_date_text = actual_data_date_text.strip()
            


            # Найти элемент
            detail_button = page.locator(
                "//span[contains(text(), 'Суммы доходов и расходов')]"
                "/ancestor::div[@class='pb-company-block']"
                "//a[contains(@class, 'lnk-detail')]"
            )
            # Прокрутить к элементу
            await detail_button.scroll_into_view_if_needed()
            # Дождаться, пока элемент станет видим (с меньшим timeout)
            await detail_button.wait_for(state="visible", timeout=5000)
            # Клик с меньшим timeout
            await detail_button.click(timeout=5000)
            # Ждём модальное окно
            await page.wait_for_selector("#modalCompanyTbody tr", state="visible", timeout=5000)
            financial_data = []
            rows_locators = await page.locator("#modalCompanyTbody tr").all()
            for row in rows_locators:
                cells = await row.locator("td").all_text_contents()
                
                if len(cells) >= 3:
                    try:
                        year = cells[0].strip()
                        income = cells[1].strip().replace(" ", "")
                        expense = cells[2].strip().replace(" ", "")
                        
                        financial_data.append({
                            "year": year,
                            "income": income,
                            "profit": int(income) - int(expense)
                        })
                    except Exception as e:
                        logger.error(f"Ошибка парсинга строки: {e}")
                        continue

            
            await page.wait_for_timeout(5000)
            await page.screenshot(path=f'./result/screenshot/third_site/{messages.text}(3).png')
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
<b>{general_director_organization_position}:</b>
{general_director_organization_name}
(ИНН {general_director_organization_inn}) период с 01.04.2014
<b>Учредители:</b>
{founder_name}
(ИНН {founder_inn}) <b>(Чистая прибыль от бизнеса за три года ~ млн. руб.)</b>

<b>ФИНАНСОВАЯ ИНФОРМАЦИЯ:</b>
Среднесписочная численность:~ {employees_count}
Выручка от продажи за {financial_data[0]['year']}: {financial_data[0]['income']}
Чистая прибыль за {financial_data[0]['year']}: {financial_data[0]['profit']}
Чистая прибыль за последние три года: ~ {financial_data[0]['profit'] + financial_data[1]['profit'] + financial_data[2]['profit']}
Исполнительное производство: 
Как ответчик   руб.
Как истец  руб

Последние изменения были совершены 
Данные актуальны на {actual_data_date_text}
''', parse_mode='HTML')

    except Exception as e:
        logger.error(f'Ошибка в парсинге публичного бизнеса: {e}')
        await messages.answer(f'{messages.from_user.first_name}, ошибка в поиске данных по ИНН:{messages.text}')

    