import os
from dotenv import load_dotenv
from telethon import TelegramClient, events
from openai import OpenAI
import json
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from AI_managers_sales_toys.work_with_telegram.utils import configure_logging
from AI_managers_sales_toys.work_with_telegram.work_with_telegram_bot.telegram_bot_handler import send_telegram_message
from AI_managers_sales_toys.work_with_database_MongoDB.mongodb_messages import Messages
from AI_managers_sales_toys.work_with_database_PostgreSQL.database import DatabaseUser, DatabaseOrder

# Ініціалізація баз даних
user_db = DatabaseUser()
order_db = DatabaseOrder()
db_for_messages = Messages('messages_db', 'messages_tg')
db_for_thread = Messages('threads_ai_id_db', 'threads_ai')

# Налаштування
load_dotenv()
logger = configure_logging()

API_ID = os.getenv('TELEGRAM_API_ID')
API_HASH = os.getenv('TELEGRAM_API_HASH')
PHONE_NUMBER = os.getenv('PHONE_NUMBER')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
ASSISTANT_ID = os.getenv('ASSISTANT_ID_telegram_bot_sale_toys')
ADMIN_USER_ID = int(os.getenv('ADMIN_USER_ID'))

# Ініціалізація клієнтів
client = TelegramClient('session', API_ID, API_HASH)
openai_client = OpenAI(api_key=OPENAI_API_KEY)


async def wait_for_run_completion(thread_id: str, run_id: str, timeout_seconds: int = 60) -> Any:
    """Очікування завершення run з таймаутом"""
    start_time = datetime.now()
    timeout = timedelta(seconds=timeout_seconds)

    logger.info(f"Початок очікування завершення run {run_id}")

    while (datetime.now() - start_time) < timeout:
        try:
            current_run = openai_client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run_id
            )

            logger.info(f"Run {run_id} статус: {current_run.status}")

            if current_run.status == 'requires_action':
                logger.info(f"Run {run_id} потребує дій, обробляємо...")
                return current_run

            if current_run.status in ['completed', 'failed', 'expired']:
                logger.info(f"Run {run_id} завершено зі статусом: {current_run.status}")
                return current_run

            await asyncio.sleep(2)

        except Exception as e:
            logger.error(f"Помилка при перевірці статусу run: {e}")
            await asyncio.sleep(2)

    try:
        logger.warning(f"Таймаут для run {run_id}, спроба скасування...")
        openai_client.beta.threads.runs.cancel(
            thread_id=thread_id,
            run_id=run_id
        )
    except Exception as e:
        logger.error(f"Помилка при скасуванні run: {e}")

    raise TimeoutError(f"Run {run_id} не завершився протягом {timeout_seconds} секунд")


async def cleanup_existing_runs(thread_id: str) -> None:
    """Очищення всіх активних run в треді"""
    try:
        runs = openai_client.beta.threads.runs.list(thread_id=thread_id)
        for run in runs.data:
            if run.status in ['in_progress', 'requires_action']:
                try:
                    openai_client.beta.threads.runs.cancel(
                        thread_id=thread_id,
                        run_id=run.id
                    )
                    logger.info(f"Скасовано run {run.id} в треді {thread_id}")
                except Exception as e:
                    logger.error(f"Помилка при скасуванні run {run.id}: {e}")
    except Exception as e:
        logger.error(f"Помилка при очищенні runs: {e}")


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

        # Повернення успішної відповіді
        return {
            "status": "success",
            "message": "🎉 Дякуємо за ваше замовлення! Наш менеджер зв'яжеться з вами найближчим часом для підтвердження."
        }

    except Exception as e:
        logger.error(f"Помилка при обробці замовлення: {e}")
        return {"status": "error", "message": str(e)}


@client.on(events.NewMessage())
async def message_handler(event):
    """Обробник повідомлень"""
    user_id = event.sender_id
    user_message = event.message.text.strip()
    sender = await event.get_sender()
    username = sender.username if sender and hasattr(sender, 'username') else "No username"

    # Збереження повідомлення користувача
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, db_for_messages.add_message_to_tg_db,
                             username, user_id, 'Telegram', 'user', user_message)

    if user_message.startswith('/'):
        return

    try:
        # Отримання або створення треду
        thread_data = None
        try:
            thread_data = db_for_thread.search_tread_id(user_id)
        except Exception as e:
            logger.error(f'Помилка при отриманні потоку: {e}')

        if not thread_data:
            thread = openai_client.beta.threads.create()
            await loop.run_in_executor(None, db_for_thread.update_thread_id, user_id, thread.id)
            thread_id = thread.id
            logger.info(f'Створено новий тред: {thread.id}')
        else:
            thread_id = thread_data['thread_id']
            logger.info(f'Знайдено потік: {thread_id}')
            await cleanup_existing_runs(thread_id)

        # Додавання повідомлення до треду
        openai_client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=user_message
        )

        # Створення та обробка run
        run = openai_client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=ASSISTANT_ID
        )

        try:
            run = await wait_for_run_completion(thread_id, run.id)

            if run.status == 'requires_action':
                tool_calls = run.required_action.submit_tool_outputs.tool_calls
                tool_outputs = []

                for tool_call in tool_calls:
                    if tool_call.function.name == "sent_data_for_order":
                        try:
                            function_args = json.loads(tool_call.function.arguments)
                            result = await sent_data_for_order(
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
                                "output": json.dumps(result)
                            })
                            logger.info(f"Успішно оброблено tool_call {tool_call.id}")
                        except Exception as e:
                            logger.error(f"Помилка в обробці tool_call: {e}")
                            tool_outputs.append({
                                "tool_call_id": tool_call.id,
                                "output": json.dumps({"status": "error", "message": str(e)})
                            })

                if tool_outputs:
                    run = openai_client.beta.threads.runs.submit_tool_outputs(
                        thread_id=thread_id,
                        run_id=run.id,
                        tool_outputs=tool_outputs
                    )
                    run = await wait_for_run_completion(thread_id, run.id)

            # Отримання відповіді асистента
            messages = openai_client.beta.threads.messages.list(thread_id=thread_id)
            assistant_response = messages.data[0].content[0].text.value

            # Збереження відповіді асистента
            await loop.run_in_executor(None, db_for_messages.add_message_to_tg_db,
                                     username, user_id, 'Telegram', 'assistant', assistant_response)

            # Відправка відповіді користувачу
            await event.reply(assistant_response)

        except TimeoutError as e:
            logger.warning(str(e))
            await event.reply("Вибачте, відповідь займає більше часу ніж очікувалося. Спробуйте повторити запит.")
            return

    except Exception as e:
        logger.error(f"Помилка при обробці повідомлення: {e}")
        await event.reply("Вибачте, сталася помилка при обробці вашого запиту.")


async def main():
    """Головна функція запуску бота"""
    print("Starting Telegram client...")
    await client.start(phone=PHONE_NUMBER)
    print("Telegram client started successfully!")
    await client.run_until_disconnected()


if __name__ == '__main__':
    asyncio.run(main())