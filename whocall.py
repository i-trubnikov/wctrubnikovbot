import logging
import time
from aiogram import Bot, Dispatcher, types, executor
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

TOKEN = '7710767802:AAFFRYTh4Ovbr845FNm00rIvLAdxNbbe_ME'
CHROME_DRIVER_PATH = '/Users/ilatrubnikov/Downloads/chromedriver-mac-arm64/chromedriver'

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

def check_text_selenium(phone):
    url = f"https://www.tbank.ru/oleg/who-called/info/{phone}/"
    try:
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")

        service = Service(CHROME_DRIVER_PATH)
        driver = webdriver.Chrome(service=service, options=options)
        driver.get(url)

        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        page_text = driver.page_source
        driver.quit()

        if "Такого номера нет" in page_text:
            return "✅ Номер чистый"
        elif (
            "жалоба" in page_text or
            "негатив" in page_text or
            "оценка" in page_text or
            "назван" in page_text or
            "По нашей информации номер" in page_text
        ):
            return "❌ Пора бы поменять. Номер в спаме"
        else:
            return "❔ Не удалось точно определить"

    except Exception as e:
        return f"⚠️ Ошибка: {e}"

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    text = (
        "👋 Привет! Этот бот проверяет номера по базе tbank.ru\n\n"
        "📌 *Как пользоваться:*\n"
        "— Отправь 1 или сразу несколько номеров (через пробел, запятую или в столбик)\n"
        "— Максимум 15 номеров за раз\n"
        "— Через минуту получишь файл с результатом\n\n"
        "📋 *Примеры ввода:*\n"
        "`74951234567 74959876543`\n"
        "`79031234567,\n74950123456`\n\n"
        "Если номер найден в базе — бот предупредит, что он в спаме.\n"
        "Если всё чисто — тоже сообщит ✅"
    )
    await message.reply(text, parse_mode='Markdown')

@dp.message_handler()
async def handle_message(message: types.Message):
    raw_text = message.text.replace(',', ' ').replace('\n', ' ')
    numbers = list(filter(None, [num.strip() for num in raw_text.split()]))

    if not numbers:
        await message.reply("📭 Не вижу ни одного номера.")
        return

    if len(numbers) > 15:
        await message.reply("⚠️ Не больше 15 номеров за раз. Попробуй разделить список.")
        return

    temp_msg = await message.reply("🔄 Проверяю... Это займёт чуть больше времени, но будет точнее")

    results = []
    spam_numbers = []

    for idx, number in enumerate(numbers, 1):
        result = check_text_selenium(number)
        results.append(f"{idx}. {number} — {result}")
        if "❌ Пора бы поменять" in result:
            spam_numbers.append(number)
        time.sleep(1.5)

    await temp_msg.delete()

    with open("results.txt", "w", encoding="utf-8") as f:
        f.write('\n'.join(results))
        f.write('\n\n📛 Номера, которые в спаме:\n')
        if spam_numbers:
            f.write('\n'.join(spam_numbers))
        else:
            f.write('Все номера чистые ✅')

    await message.reply_document(open("results.txt", "rb"), caption="📄 Готово! Вот результаты проверки.")

if __name__ == '__main__':
    executor.start_polling(dp)
