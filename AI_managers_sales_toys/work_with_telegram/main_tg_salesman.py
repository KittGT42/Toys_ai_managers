import os
import time
import logging
import re

from dotenv import load_dotenv
from telethon import TelegramClient, events
from openai import OpenAI

# Налаштування логування
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()

API_ID = os.getenv('TELEGRAM_API_ID')
API_HASH = os.getenv('TELEGRAM_API_HASH')
PHONE_NUMBER = os.getenv('PHONE_NUMBER')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
ASSISTANT_ID = os.getenv('ASSISTANT_ID_telegram_bot_sale_animals_items')
ADMIN_USER_ID = int(os.getenv('ADMIN_USER_ID'))

client = TelegramClient('session', API_ID, API_HASH)
openai_client = OpenAI(api_key=OPENAI_API_KEY)

user_threads = {}
user_order_info = {}


def extract_order_info(text):
    patterns = {
        'user_name': r'user_name:\s*(.+)',
        'user_phone': r'user_phone:\s*(.+)',
        'user_address': r'user_address:\s*(.+)',
        'url_product': r'url_product:\s*(.+)'
    }
    info = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, text)
        if match:
            info[key] = match.group(1).strip()
    return info


async def sent_data_for_order(user_name, user_phone, user_address, url_product):
    await asyncio.sleep(5)
    message = f"Ім'я: {user_name}\nТелефон: {user_phone}\nАдреса: {user_address}\nПосилання на продукт: {url_product}"
    await client.send_message(ADMIN_USER_ID, message)
    logging.info(f"Дані замовлення відправлено адміністратору: {message}")


@client.on(events.NewMessage())
async def message_handler(event):
    user_id = event.sender_id
    user_message = event.message.text.strip()

    if user_message.startswith('/'):
        return

    try:
        if user_id not in user_threads:
            thread = openai_client.beta.threads.create()
            user_threads[user_id] = thread.id
        thread_id = user_threads[user_id]

        openai_client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=user_message
        )

        run = openai_client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=ASSISTANT_ID
        )

        while run.status != 'completed':
            run = openai_client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
            )
            await asyncio.sleep(1)

        messages = openai_client.beta.threads.messages.list(thread_id=thread_id)
        assistant_response = messages.data[0].content[0].text.value

        # Оновлюємо інформацію про замовлення
        new_order_info = extract_order_info(assistant_response)
        user_order_info[user_id] = {**user_order_info.get(user_id, {}), **new_order_info}

        logging.info(f"Оновлена інформація про замовлення для користувача {user_id}: {user_order_info[user_id]}")

        if "sent_data_for_order" in assistant_response:
            order_info = user_order_info.get(user_id, {})
            if all(key in order_info for key in ['user_name', 'user_phone', 'user_address', 'url_product']):
                await sent_data_for_order(**order_info)
                del user_order_info[user_id]
                await event.reply("Дякуємо за замовлення! Ваші дані відправлено адміністратору.")
            else:
                missing_fields = [key for key in ['user_name', 'user_phone', 'user_address', 'url_product'] if
                                  key not in order_info]
                await event.reply(
                    f"Вибачте, не вистачає деяких даних для оформлення замовлення: {', '.join(missing_fields)}. Будь ласка, надайте всю необхідну інформацію.")
        else:
            await event.reply(assistant_response)

    except Exception as e:
        logging.error(f"Помилка: {e}")
        await event.reply("Вибачте, сталася помилка при обробці вашого запиту.")


async def main():
    logging.info("Запуск Telegram клієнта...")
    await client.start(phone=PHONE_NUMBER)
    logging.info("Telegram клієнт успішно запущено!")
    await client.run_until_disconnected()


if __name__ == '__main__':
    import asyncio

    asyncio.run(main())