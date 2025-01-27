import json
from openai import OpenAI
from AI_managers_sales_toys.work_with_instagram.config import OPENAI_API_KEY, ASSISTANT_ID_instagram
from AI_managers_sales_toys.work_with_instagram.utils import configure_logging
import traceback
from AI_managers_sales_toys.work_with_database_MongoDB.mongodb_messages import Messages
import asyncio
from AI_managers_sales_toys.work_with_telegram.work_with_telegram_bot.telegram_bot_handler import send_telegram_message
from AI_managers_sales_toys.work_with_instagram.utils import get_product_info
from AI_managers_sales_toys.work_with_database_PostgreSQL.database import DatabaseUser, DatabaseOrder, DatabaseProduct


user_db = DatabaseUser()
order_db = DatabaseOrder()
threads_ai_id_db = Messages('threads_ai_id_db', 'threads_ai')

logger = configure_logging()
client_openai = OpenAI(api_key=OPENAI_API_KEY)


class Thread:
    def __init__(self, new_thread_id):
        self.id = new_thread_id


async def sent_data_for_order(user_name: str,
        user_phone: str,
        user_address: str,
        name: str,
        price: str,
        article: str,
        user_id: str):
    try:
        user_phone = user_phone.replace(' ', '').replace('(', '').replace(')', '')
        if not user_phone.startswith('+'):
            user_phone = '+38' + user_phone

        # Валідація даних
        if not all([user_name, user_phone, user_address, name, price, article]):
            raise ValueError("Відсутні обов'язкові поля замовлення")

        # Збереження даних користувача
        if await asyncio.to_thread(user_db.select_user, user_id=user_id) is None:
            await asyncio.to_thread(user_db.insert_user, user_id, user_name, user_phone)

        products_data = [{"article": article, "quantity": 1}]
        await asyncio.to_thread(order_db.insert_order, user_id, user_address, products_data)

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


async def process_with_assistant(message: str, contact_id: str) -> str:
    try:
        logger.info(f'Початок обробки повідомлення: {message}')

        try:
            thread_data = threads_ai_id_db.search_tread_id(contact_id)
            thread_id = thread_data['thread_id'] if thread_data else None
        except Exception as e:
            thread_id = None
            logger.error(f'Помилка при отриманні потоку: {e}')

        if thread_id:
            thread = Thread(thread_id)
            logger.info(f'Знайдено потік: {thread.id}')
        else:
            thread = client_openai.beta.threads.create()
            threads_ai_id_db.add_thread_id(contact_id, thread.id)
            logger.info(f'Створено новий тред: {thread.id}')

        client_openai.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=message
        )
        logger.info('Повідомлення додано до треду')

        run = client_openai.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=ASSISTANT_ID_instagram
        )
        logger.info(f'Запущено асистента: {run.id}')

        while True:
            run = client_openai.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
            logger.info(f'Статус асистента: {run.status}')
            if run.status == 'requires_action':
                tool_calls = run.required_action.submit_tool_outputs.tool_calls
                tool_outputs = []

                for tool_call in tool_calls:
                    function_args = json.loads(tool_call.function.arguments)
                    if tool_call.function.name == "sent_data_for_order":
                        await sent_data_for_order(
                            function_args['user_name'],
                            function_args['user_phone'],
                            function_args['user_address'],
                            function_args['name'],
                            function_args['price'],
                            function_args['article'],
                            user_id=contact_id
                        )

                        tool_outputs.append({
                            "tool_call_id": tool_call.id,
                            "output": "Order data sent successfully"
                        })
                    elif tool_call.function.name == "get_product_info":
                        result = await get_product_info(function_args['article'])
                        logger.debug(f"Результат get_product_info: {result}")
                        output = json.dumps(result)
                        tool_outputs.append({
                            "tool_call_id": tool_call.id,
                            "output": output
                        })

                run = client_openai.beta.threads.runs.submit_tool_outputs(
                    thread_id=thread.id,
                    run_id=run.id,
                    tool_outputs=tool_outputs
                )

            elif run.status == 'completed':
                break

            await asyncio.sleep(1)

        messages = client_openai.beta.threads.messages.list(thread_id=thread.id)
        logger.info('Отримано відповідь від асистента')

        assistant_response = messages.data[0].content[0].text.value
        logger.info(f'Відповідь асистента: {assistant_response}')

        return assistant_response

    except Exception as e:
        logger.error(f'Помилка при обробці повідомлення через OpenAI: {str(e)}')
        logger.error(traceback.format_exc())
        raise