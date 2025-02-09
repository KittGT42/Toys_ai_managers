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
ASSISTANT_ID = 'asst_AfkpQMAiugaOGrp12k09uFpu'
ADMIN_USER_ID = int(os.getenv('ADMIN_USER_ID'))

# Таймаути та ретраї
MAX_RETRIES = 3
TIMEOUT = 60  # секунд
DB_TIMEOUT = 30  # секунд для операцій з базою даних
MESSAGE_TIMEOUT = 10  # секунд для відправки повідомлень
RETRY_DELAY = 5  # секунд між спробами

# Ініціалізація клієнтів з таймаутами
client = TelegramClient('session', API_ID, API_HASH)
openai_client = OpenAI(
    api_key=OPENAI_API_KEY,
    timeout=TIMEOUT,
    max_retries=MAX_RETRIES
)

# Ініціалізація баз даних
user_db = DatabaseUser()
order_db = DatabaseOrder()
product_db = DatabaseProduct()
db_for_messages = Messages('messages_db', 'messages_tg')
db_for_thread = Messages('threads_ai_id_db', 'threads_ai')

class Thread:
    """Клас для роботи з тредами OpenAI"""

    def __init__(self, new_thread_id):
        self.id = new_thread_id


async def get_products_by_category(age_year, age_month, gender, main_product_category, budget):
    try:
        # Конвертація типів
        if age_year != '0':
            age_year = float(age_year)
        if age_month != '0':
            age_month = float(age_month) / 12
        if gender == 'male':
            gender = 'Хлопчик'
        if gender == 'female':
            gender = 'Дівчинка'
        if budget != '0':
            budget = float(budget)

        # Використовуємо asyncio.to_thread для синхронного DB запиту
        products_from_db = await asyncio.to_thread(
            product_db.select_product_by_different_category,
            age_year=age_year,
            age_month=age_month,
            gender=gender,
            main_product_category=main_product_category,
            budget=budget
        )
        result = []

        for product in products_from_db:
           data = {
                "name": product.name,
                "price": str(product.price),
                "article": product.article,
                "age_category": getattr(product, 'age_category', ''),
                "color": getattr(product, 'color', ''),
                "material": getattr(product, 'material', ''),
                "description": getattr(product, 'description', ''),
                "main_image": getattr(product, 'main_image', ''),
                "gender": getattr(product, 'gender', ''),
                "product_status": getattr(product, 'product_status', ''),
                "product_type": getattr(product, 'product_type', ''),
                "quantity": product.quantity,
                "images_urls": getattr(product, 'images_urls', [])
            }
           print(data)
           result.append(data)

        return {
            "status": "success",
            "data": result
        }

    except Exception as e:
        logger.error(f"Помилка при отриманні товарів: {str(e)}")
        return {
            "status": "error",
            "message": f"Помилка отримання даних: {str(e)}"
        }

def validate_tool_output(output: dict) -> bool:
    """Валідація вихідних даних інструментів"""
    required_fields = ["tool_call_id", "output"]
    return all(field in output for field in required_fields)


async def get_product_info(article: str) -> dict:
    """Отримання інформації про товар з бази даних з розширеною валідацією"""
    try:
        logger.info(f"Отримання інформації про товар: {article}")

        product = await asyncio.to_thread(product_db.select_product, article)
        logger.debug(f"Отримані дані з БД: {product}")

        if not product:
            logger.warning(f"Товар {article} не знайдено у базі даних")
            return {
                "status": "error",
                "message": f"Товар з артикулом {article} не знайдено"
            }

        # Перевірка обов'язкових полів
        required_fields = ["name", "price", "article", "quantity"]
        missing_fields = [field for field in required_fields if not hasattr(product, field)]

        if missing_fields:
            logger.error(f"Відсутні обов'язкові поля: {missing_fields}")
            return {
                "status": "error",
                "message": f"Неповні дані товару: відсутні поля {', '.join(missing_fields)}"
            }

        product_data = {
            "name": product.name,
            "price": str(product.price),
            "article": product.article,
            "age_category": getattr(product, 'age_category', ''),
            "color": getattr(product, 'color', ''),
            "material": getattr(product, 'material', ''),
            "description": getattr(product, 'description', ''),
            "main_image": getattr(product, 'main_image', ''),
            "gender": getattr(product, 'gender', ''),

        }

        logger.debug(f"Підготовлені дані товару: {product_data}")

        return {
            "status": "success",
            "data": product_data
        }

    except Exception as e:
        logger.error(f"Помилка при отриманні інформації про товар {article}: {str(e)}")
        return {
            "status": "error",
            "message": f"Помилка отримання даних товару: {str(e)}"
        }


async def sent_data_for_order(
        user_name: str,
        user_phone: str,
        user_address: str,
        name: str,
        price: str,
        article: str,
        user_id: str
) -> Dict[str, str]:
    """Обробка замовлення та відправка даних"""
    try:
        logger.info(f"Обробка замовлення для користувача {user_id}")

        # Форматування телефону
        user_phone = user_phone.replace(' ', '').replace('(', '').replace(')', '')
        if not user_phone.startswith('+'):
            user_phone = '+38' + user_phone

        # Валідація даних
        if not all([user_name, user_phone, user_address, name, price, article]):
            raise ValueError("Відсутні обов'язкові поля замовлення")

        # Збереження даних користувача
        if await asyncio.to_thread(user_db.select_user, user_id=user_id) is None:
            await asyncio.to_thread(user_db.insert_user, user_id, user_name, user_phone)

        # Збереження замовлення
        products_data = [{"article": article, "quantity": 1}]
        await asyncio.to_thread(order_db.insert_order, user_id, user_address, products_data)

        # Формування повідомлення
        message = (f"🛍 Нове замовлення!\n\n"
                   f"👤 Покупець: {user_name}\n"
                   f"📱 Телефон: {user_phone}\n"
                   f"📍 Адреса: {user_address}\n\n"
                   f"📦 Товар: {name}\n"
                   f"💰 Ціна: {price}\n"
                   f"📎 Артикул: {article}")

        # Відправка повідомлення без await
        message_sent = send_telegram_message(message)

        if not message_sent:
            raise Exception("Помилка при відправці повідомлення в Telegram")

        logger.info(f"Замовлення успішно оброблено для користувача {user_id}")
        return {
            "status": "success",
            "message": "🎉 Дякуємо за ваше замовлення! Наш менеджер зв'яжеться з вами найближчим часом для підтвердження."
        }

    except Exception as e:
        error_message = str(e)
        logger.error(f"Помилка при обробці замовлення для користувача {user_id}: {error_message}")
        return {
            "status": "error",
            "message": f"Помилка при обробці замовлення: {error_message}"
        }


async def process_tool_calls(thread_id: str, run_id: str, tool_calls: list, user_id) -> list:
    tool_outputs = []

    for tool_call in tool_calls:
        try:
            logger.info(f"Обробка tool_call: {tool_call.function.name}")
            function_args = json.loads(tool_call.function.arguments)
            logger.debug(f"Аргументи функції: {function_args}")

            if tool_call.function.name == "get_products_by_category":
                result = await get_products_by_category(
                    function_args['age_year'],
                    function_args['age_month'],
                    function_args['gender'],
                    function_args['main_product_category'],
                    function_args['budget'],
                )
                logger.debug(f"Результат get_products_by_category: {result}")
                output = json.dumps(result)
                tool_outputs.append({
                    "tool_call_id": tool_call.id,
                    "output": output
                })

            elif tool_call.function.name == "get_product_info":
                result = await get_product_info(function_args['article'])
                logger.debug(f"Результат get_product_info: {result}")
                output = json.dumps(result)
                tool_outputs.append({
                    "tool_call_id": tool_call.id,
                    "output": output
                })

            elif tool_call.function.name == "sent_data_for_order":
                result = await sent_data_for_order(
                    function_args['user_name'],
                    function_args['user_phone'],
                    function_args['user_address'],
                    function_args['name'],
                    function_args['price'],
                    function_args['article'],
                    user_id)
                logger.debug(f"Результат sent_data_for_order: {result}")
                output = json.dumps(result)
                tool_outputs.append({
                    "tool_call_id": tool_call.id,
                    "output": output
                })

        except Exception as e:
            logger.error(f"Помилка обробки tool_call {tool_call.id}: {str(e)}")
            error_output = {
                "status": "error",
                "message": f"Помилка обробки запиту: {str(e)}"
            }
            logger.debug(f"Error output: {error_output}")
            tool_outputs.append({
                "tool_call_id": tool_call.id,
                "output": json.dumps(error_output)
            })

    logger.info(f"Підготовлено {len(tool_outputs)} tool_outputs")
    return tool_outputs


async def handle_run_status(run, thread_id: str, event, user_id) -> Optional[bool]:
    """Обробка статусу run з розширеним логуванням"""
    logger.info(f"Обробка run status: {run.status}")

    if run.status == 'requires_action':
        tool_calls = run.required_action.submit_tool_outputs.tool_calls
        logger.info(f"Отримано {len(tool_calls)} tool calls")

        tool_outputs = await process_tool_calls(thread_id, run.id, tool_calls, user_id=user_id)

        if tool_outputs:
            try:
                logger.debug(f"Відправка tool outputs: {json.dumps(tool_outputs, indent=2)}")
                run = openai_client.beta.threads.runs.submit_tool_outputs(
                    thread_id=thread_id,
                    run_id=run.id,
                    tool_outputs=tool_outputs
                )
                logger.info(f"Tool outputs відправлено успішно для run {run.id}")
                return None  # продовжуємо виконання
            except Exception as e:
                logger.error(f"Помилка при відправці tool outputs: {e}")
                await event.reply("Вибачте, сталася помилка при обробці запиту.")
                return False

    elif run.status == 'completed':
        logger.info("Run завершено успішно")
        return True

    elif run.status in ['failed', 'expired', 'cancelled']:
        error_message = getattr(run, 'last_error', 'Невідома помилка')
        logger.error(f"Run failed with status: {run.status}, error: {error_message}")
        await event.reply("Вибачте, сталася помилка при обробці вашого запиту.")
        return False

    return None  # продовжуємо виконання


@client.on(events.NewMessage())
async def message_handler(event):
    user_id = str(event.sender_id)
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

        start_time = asyncio.get_event_loop().time()
        retries = 0

        while True:
            # Перевірка таймауту
            if asyncio.get_event_loop().time() - start_time > TIMEOUT:
                logger.error("Перевищено час очікування відповіді")
                await event.reply("Вибачте, запит зайняв занадто багато часу. Спробуйте ще раз.")
                return

            run = openai_client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
            )

            status_result = await handle_run_status(run, thread_id, event, user_id=user_id)

            if status_result is True:  # Успішне завершення
                break
            elif status_result is False:  # Помилка
                return

            # Очікування перед наступною спробою
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


async def init_assistant():
    """Ініціалізація та перевірка асистента"""
    try:
        logger.info("Перевірка з'єднання з OpenAI API...")
        assistant = openai_client.beta.assistants.retrieve(ASSISTANT_ID)
        logger.info(f"Асистент {assistant.name} успішно знайдено")
        return True
    except Exception as e:
        logger.error(f"Помилка при ініціалізації асистента: {e}")
        return False


async def main():
    """Головна функція запуску бота"""
    try:
        assert all([API_ID, API_HASH, OPENAI_API_KEY]), "Помилка: відсутні необхідні змінні середовища"

        logger.info("Налаштування асистента...")
        if not await init_assistant():
            raise Exception("Помилка ініціалізації асистента")

        logger.info("Запуск Telegram клієнта...")
        await client.start(phone=PHONE_NUMBER)
        logger.info("Telegram клієнт успішно запущений!")

        await client.run_until_disconnected()

    except Exception as e:
        logger.error(f"Критична помилка при запуску: {e}")
        raise


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот зупинений користувачем")
    except Exception as e:
        logger.critical(f"Критична помилка: {e}")
        raise