import json
from openai import OpenAI
from work_with_instagram.config import OPENAI_API_KEY, ASSISTANT_ID
from work_with_instagram.utils import configure_logging
import traceback
from work_with_database_MongoDB.mongodb_messages import Messages
import asyncio
from work_with_telegram.work_with_telegram_bot.telegram_bot_handler import send_telegram_message

logger = configure_logging()
client_openai = OpenAI(api_key=OPENAI_API_KEY)


class Thread:
    def __init__(self, new_thread_id):
        self.id = new_thread_id


async def sent_data_for_order(user_name, user_phone, user_address, product_name, product_price, product_description,
                              product_link):
    try:
        message = (f"ПІБ: {user_name}\nТелефон: {user_phone}\nАдреса: {user_address}"
                   f"\nТовар: {product_name}\nЦіна: {product_price}\nОпис: {product_description}\nПосилання: {product_link}")

        success = await asyncio.to_thread(send_telegram_message, message)

        if not success:
            raise Exception("Failed to send message to Telegram")

    except Exception as e:
        logger.error(f"Помилка при відправці замовлення: {str(e)}")
        raise


db = Messages('threads_ai_id_db', 'threads_ai')


async def process_with_assistant(message: str, username: str) -> str:
    try:
        logger.info(f'Початок обробки повідомлення: {message}')

        try:
            thread_data = db.search_tread_id(username)
            thread_id = thread_data['thread_id'] if thread_data else None
        except Exception as e:
            thread_id = None
            logger.error(f'Помилка при отриманні потоку: {e}')

        if thread_id:
            thread = Thread(thread_id)
            logger.info(f'Знайдено потік: {thread.id}')
        else:
            thread = client_openai.beta.threads.create()
            db.add_thread_id(username, thread.id)
            logger.info(f'Створено новий тред: {thread.id}')

        client_openai.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=message
        )
        logger.info('Повідомлення додано до треду')

        run = client_openai.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=ASSISTANT_ID
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
                    if tool_call.function.name == "sent_data_for_order":
                        function_args = json.loads(tool_call.function.arguments)
                        await sent_data_for_order(
                            user_name=function_args['user_name'],
                            user_phone=function_args['user_phone'],
                            user_address=function_args['user_address'],
                            product_name=function_args['product_name'],
                            product_price=function_args['product_price'],
                            product_description=function_args['product_description'],
                            product_link=function_args['product_link']
                        )

                        tool_outputs.append({
                            "tool_call_id": tool_call.id,
                            "output": "Order data sent successfully"
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