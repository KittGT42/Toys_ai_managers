import os
import asyncio
from dotenv import load_dotenv
from telethon import TelegramClient, events
from openai import OpenAI
from typing import Optional, Dict, Any, Set
import json
from AI_managers_sales_toys.work_with_telegram.utils import configure_logging
from AI_managers_sales_toys.work_with_telegram.work_with_telegram_bot.telegram_bot_handler import send_telegram_message
from AI_managers_sales_toys.work_with_database_MongoDB.mongodb_messages import Messages
from AI_managers_sales_toys.work_with_database_PostgreSQL.database import DatabaseUser, DatabaseOrder, DatabaseProduct

# Ініціалізація логера
logger = configure_logging()

# Завантаження змінних середовища
load_dotenv()

# Конфігураційні змінні
API_ID = os.getenv('TELEGRAM_API_ID')
API_HASH = os.getenv('TELEGRAM_API_HASH')
PHONE_NUMBER = os.getenv('PHONE_NUMBER')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
ASSISTANT_ID = 'asst_wc7I7XK5BLFe0ZMzbduchn8W'
ADMIN_USER_ID = int(os.getenv('ADMIN_USER_ID'))

# Ініціалізація баз даних
user_db = DatabaseUser()
order_db = DatabaseOrder()
product_db = DatabaseProduct()
db_for_messages = Messages('messages_db', 'messages_tg')
db_for_thread = Messages('threads_ai_id_db', 'threads_ai')

# Ініціалізація клієнтів
client = TelegramClient('session', API_ID, API_HASH)
openai_client = OpenAI(api_key=OPENAI_API_KEY)


class Thread:
    """Клас для роботи з тредами OpenAI"""

    def __init__(self, new_thread_id):
        self.id = new_thread_id


def validate_tool_output(output: dict) -> bool:
    """Валідація вихідних даних інструментів"""
    required_fields = ["tool_call_id", "output"]
    return all(field in output for field in required_fields)


async def get_product_info(article: str) -> dict:
    """Отримання інформації про товар з бази даних"""
    try:
        logger.info(f"Отримання інформації про товар: {article}")

        try:
            product = product_db.select_product(article)
            logger.debug(f"Результат запиту: {product}")
        except Exception as db_error:
            logger.error(f"Помилка бази даних: {str(db_error)}")
            return {"status": "error", "message": f"Помилка бази даних: {str(db_error)}"}

        if not product:
            logger.warning(f"Товар {article} не знайдено у базі даних")
            return {
                "status": "error",
                "message": f"Товар з артикулом {article} не знайдено"
            }

        return {
            "status": "success",
            "data": {
                "name": product.name,
                "price": str(product.price),
                "article": product.article,
                "age_category": product.age_category,
                "color": product.color,
                "material": product.material,
                "description": product.description,
                "main_image": product.main_image,
                "gender": product.gender,
                "product_status": product.product_status,
                "product_type": product.product_type,
                "quantity": product.quantity,
                "images_urls": product.images_urls
            }
        }

    except Exception as e:
        logger.error(f"Помилка при отриманні інформації про товар: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


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

        # Формування повідомлення
        message = (f"🛍 Нове замовлення!\n\n"
                   f"👤 Покупець: {user_name}\n"
                   f"📱 Телефон: {user_phone}\n"
                   f"📍 Адреса: {user_address}\n\n"
                   f"📦 Товар: {name}\n"
                   f"💰 Ціна: {price}\n"
                   f"📎 Артикул: {article}")

        # Збереження даних користувача
        if user_db.select_user(user_id=int(user_id)) is None:
            await asyncio.to_thread(user_db.insert_user, int(user_id), user_name, user_phone)

        # Збереження замовлення
        products_data = [{"article": article, "quantity": 1}]
        await asyncio.to_thread(order_db.insert_order, int(user_id), user_address, products_data)

        # Відправка повідомлення
        await send_telegram_message(message)

        return {
            "status": "success",
            "message": "🎉 Дякуємо за ваше замовлення! Наш менеджер зв'яжеться з вами найближчим часом для підтвердження."
        }

    except Exception as e:
        logger.error(f"Помилка при обробці замовлення: {e}")
        return {"status": "error", "message": str(e)}


async def process_tool_calls(thread_id: str, run_id: str, tool_calls: list) -> list:
    """Обробка викликів функцій від асистента"""
    tool_outputs = []

    for tool_call in tool_calls:
        try:
            logger.info(f"Обробка виклику: {tool_call.function.name}")
            function_args = json.loads(tool_call.function.arguments)

            if tool_call.function.name == "get_product_info":
                result = await get_product_info(**function_args)
            elif tool_call.function.name == "sent_data_for_order":
                result = await sent_data_for_order(**function_args)
            else:
                logger.warning(f"Невідома функція: {tool_call.function.name}")
                continue

            tool_outputs.append({
                "tool_call_id": tool_call.id,
                "output": json.dumps(result)
            })

        except Exception as e:
            logger.error(f"Помилка при обробці tool_call {tool_call.id}: {str(e)}")
            continue

    return tool_outputs


@client.on(events.NewMessage())
async def message_handler(event):
    user_id = event.sender_id
    user_message = event.message.text.strip()
    sender = await event.get_sender()
    username = sender.username if sender and hasattr(sender, 'username') else "No username"

    if user_message.startswith('/'):
        return

    try:
        # Записуємо повідомлення користувача
        await asyncio.to_thread(db_for_messages.add_message_to_tg_db,
                              username=username,
                              user_id_tg=user_id,
                              messenger_name='Telegram',
                              role='user',
                              content=user_message)

        # Отримуємо або створюємо thread
        try:
            thread_data = db_for_thread.search_tread_id(user_id)
            thread_id = thread_data['thread_id'] if thread_data else None
        except Exception as e:
            thread_id = None
            logger.error(f'Помилка при отриманні потоку: {e}')

        if thread_id:
            logger.info(f'Знайдено потік: {thread_id}')
        else:
            thread = openai_client.beta.threads.create()
            db_for_thread.add_thread_id(user_id, thread.id)
            logger.info(f'Створено новий тред: {thread.id}')
            thread_id = thread.id

        # Додаємо повідомлення користувача до треду
        openai_client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=user_message
        )

        # Створюємо та запускаємо run
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
                tool_calls = run.required_action.submit_tool_outputs.tool_calls
                tool_outputs = []

                for tool_call in tool_calls:
                    if tool_call.function.name == "get_product_info":
                        article = json.loads(tool_call.function.arguments)["article"]
                        result = await get_product_info(article)
                        tool_outputs.append({
                            "tool_call_id": tool_call.id,
                            "output": json.dumps(result)
                        })
                    elif tool_call.function.name == "sent_data_for_order":
                        function_args = json.loads(tool_call.function.arguments)
                        result = await sent_data_for_order(**function_args)
                        tool_outputs.append({
                            "tool_call_id": tool_call.id,
                            "output": json.dumps(result)
                        })

                if tool_outputs:
                    run = openai_client.beta.threads.runs.submit_tool_outputs(
                        thread_id=thread_id,
                        run_id=run.id,
                        tool_outputs=tool_outputs
                    )

            elif run.status == 'completed':
                break
            elif run.status in ['failed', 'expired', 'cancelled']:
                logger.error(f"Run failed with status: {run.status}")
                await event.reply("Вибачте, сталася помилка при обробці вашого запиту.")
                return

            await asyncio.sleep(1)

        # Отримуємо та відправляємо відповідь
        messages = openai_client.beta.threads.messages.list(thread_id=thread_id)
        assistant_response = messages.data[0].content[0].text.value

        # Зберігаємо відповідь асистента
        await asyncio.to_thread(db_for_messages.add_message_to_tg_db,
                              username=username,
                              user_id_tg=user_id,
                              messenger_name='Telegram',
                              role='assistant',
                              content=assistant_response)

        await event.reply(assistant_response)

    except Exception as e:
        logger.error(f"Помилка при обробці повідомлення: {e}")
        await event.reply("Вибачте, сталася помилка при обробці вашого запиту.")


async def main():
    """Головна функція запуску бота"""
    try:
        assert all([API_ID, API_HASH, OPENAI_API_KEY]), "Помилка: відсутні необхідні змінні середовища"

        logger.info("Налаштування асистента...")
        logger.info("Запуск Telegram клієнта...")

        await client.start(phone=PHONE_NUMBER)
        logger.info("Telegram клієнт успішно запущений!")

        await client.run_until_disconnected()

    except Exception as e:
        logger.error(f"Критична помилка при запуску: {e}")
        raise


if __name__ == '__main__':
    asyncio.run(main())