import os
from dotenv import load_dotenv
from telethon import TelegramClient, events
from openai import OpenAI
import json
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Set
from AI_managers_sales_toys.work_with_telegram.utils import configure_logging
from AI_managers_sales_toys.work_with_telegram.work_with_telegram_bot.telegram_bot_handler import send_telegram_message
from AI_managers_sales_toys.work_with_database_MongoDB.mongodb_messages import Messages
from AI_managers_sales_toys.work_with_database_PostgreSQL.database import DatabaseUser, DatabaseOrder

user_db = DatabaseUser()
order_db = DatabaseOrder()


db_for_messages = Messages('messages_db', 'messages_tg')
db_for_thread = Messages('threads_ai_id_db', 'threads_ai')

# Завантажуємо змінні середовища
load_dotenv()
logger = configure_logging()

# Отримуємо значення зі змінних середовища
API_ID = os.getenv('TELEGRAM_API_ID')
API_HASH = os.getenv('TELEGRAM_API_HASH')
PHONE_NUMBER = os.getenv('PHONE_NUMBER')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
ASSISTANT_ID = os.getenv('ASSISTANT_ID_telegram_bot_sale_toys')
ADMIN_USER_ID = int(os.getenv('ADMIN_USER_ID'))

class Thread:
    def __init__(self, new_thread_id):
        self.id = new_thread_id


# Створюємо клієнт Telegram
client = TelegramClient('session', API_ID, API_HASH)

# Створюємо клієнт OpenAI
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# async def sent_data_for_order(user_name, user_phone, user_address, name, price, article, user_id):
#     message = (f"ПІБ: {user_name}\nТелефон: {user_phone}\nАдреса: {user_address}"
#                f"\nТовар: {name}\nЦіна: {price}\nАртикул: {article}"f"")
#
#     # await asyncio.to_thread(user_db.insert_user(user_id=int(user_id), full_name=user_name, phone_number=user_phone,))
#
#     order_data = {
#                 'user_id': int(user_id),
#                 'full_name': user_name,
#                 'product_name': name,
#                 'price': float(price[:-4]),
#                 'delivery_address': user_address
#             }
#     return send_telegram_message(message)

async def sent_data_for_order(
        user_name: str,
        user_phone: str,
        user_address: str,
        name: str,
        price: str,
        article: str,
        user_id: int
) -> Dict[str, str]:
    """Обробка замовлення та відправка даних"""
    try:
        # Форматування телефону
        user_phone = user_phone.replace(' ', '').replace('(', '').replace(')', '')
        if not user_phone.startswith('+'):
            user_phone = '+38' + user_phone

        # Форматування ціни
        if not price.endswith('грн'):
            price = f"{price} грн"

        # Формування повідомлення для адміністратора
        message = (f"🛍 Нове замовлення!\n\n"
                   f"👤 Покупець: {user_name}\n"
                   f"📱 Телефон: {user_phone}\n"
                   f"📍 Адреса: {user_address}\n\n"
                   f"📦 Товар: {name}\n"
                   f"💰 Ціна: {price}\n"
                   f"📎 Артикул: {article}")

        logger.info(f"Підготовлено повідомлення про замовлення для користувача {user_id}")

        # Збереження користувача
        if user_db.select_user(user_id=int(user_id)) is None:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, user_db.insert_user, int(user_id), user_name, user_phone)
            logger.info(f"Збережено нового користувача: {user_id}")

        # Збереження замовлення
        products_data = [{"article": article, "quantity": 1}]
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            order_db.insert_order,
            int(user_id),
            user_address,
            products_data
        )
        logger.info(f"Збережено замовлення для користувача {user_id}")

        # Відправка повідомлення адміністратору
        await send_telegram_message(message)
        logger.info("Відправлено повідомлення адміністратору")

        return {
            "status": "success",
            "message": "🎉 Дякуємо за ваше замовлення! Наш менеджер зв'яжеться з вами найближчим часом для підтвердження."
        }

    except Exception as e:
        logger.error(f"Помилка при обробці замовлення: {e}")
        return {"status": "error", "message": str(e)}


@client.on(events.NewMessage())
async def message_handler(event):
    user_id = event.sender_id
    user_message = event.message.text.strip()
    sender = await event.get_sender()
    username = sender.username if sender and hasattr(sender, 'username') else "No username"

    await asyncio.to_thread(db_for_messages.add_message_to_tg_db,
                            username=username,
                            user_id_tg=user_id,
                            messenger_name='Telegram',
                            role='user',
                            content=user_message)

    if user_message.startswith('/'):
        return

    try:
        try:
            thread_data = db_for_thread.search_tread_id(user_id)
            thread_id = thread_data['thread_id'] if thread_data else None
        except Exception as e:
            thread_id = None
            logger.error(f'Помилка при отриманні потоку: {e}')
        if thread_id:
            thread = Thread(thread_id)
            logger.info(f'Знайдено потік: {thread.id}')
        else:
            thread = openai_client.beta.threads.create()
            db_for_thread.add_thread_id(user_id, thread.id)
            logger.info(f'Створено новий тред: {thread.id}')
            thread_id = thread.id

        openai_client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=user_message
        )

        run = openai_client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=ASSISTANT_ID
        )

        while True:
            run = openai_client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
            )

            if run.status == 'requires_action':
                # Обробка виклику функції
                tool_calls = run.required_action.submit_tool_outputs.tool_calls
                tool_outputs = []

                for tool_call in tool_calls:
                    if tool_call.function.name == "sent_data_for_order":
                        function_args = json.loads(tool_call.function.arguments)

                        # Викликаємо функцію з отриманими аргументами
                        await sent_data_for_order(
                            function_args['user_name'],
                            function_args['user_phone'],
                            function_args['user_address'],
                            function_args['name'],
                            function_args['price'],
                            function_args['article'],
                            user_id

                        )

                        tool_outputs.append({
                            "tool_call_id": tool_call.id,
                            "output": "Order data sent successfully"
                        })

                # Відправляємо результати виконання функції назад асистенту
                run = openai_client.beta.threads.runs.submit_tool_outputs(
                    thread_id=thread_id,
                    run_id=run.id,
                    tool_outputs=tool_outputs
                )

            elif run.status == 'completed':
                break

            await asyncio.sleep(1)

        messages = openai_client.beta.threads.messages.list(thread_id=thread_id)
        assistant_response = messages.data[0].content[0].text.value

        await asyncio.to_thread(db_for_messages.add_message_to_tg_db,
                                username=username,
                                user_id_tg=user_id,
                                messenger_name='Telegram',
                                role='assistant',
                                content=assistant_response)

        await event.reply(assistant_response)
    except Exception as e:
        print(f"Error: {e}")
        await event.reply("Вибачте, сталася помилка при обробці вашого запиту.")


async def main():
    print("Starting Telegram client...")
    await client.start(phone=PHONE_NUMBER)
    print("Telegram client started successfully!")
    await client.run_until_disconnected()


if __name__ == '__main__':
    import asyncio

    asyncio.run(main())