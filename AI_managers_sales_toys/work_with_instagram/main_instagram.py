from flask import Flask, request, jsonify
from AI_managers_sales_toys.work_with_instagram.config import SANDPULS_SECRET
from AI_managers_sales_toys.work_with_instagram.utils import configure_logging, verify_sandpuls_signature
from AI_managers_sales_toys.work_with_instagram.ai_handler import process_with_assistant
from AI_managers_sales_toys.work_with_instagram.sandpuls_handler import send_message_to_sandpuls
import traceback
from datetime import datetime
from AI_managers_sales_toys.work_with_database_MongoDB.mongodb_messages import Messages
import asyncio

logger = configure_logging()
app = Flask(__name__)

db = Messages('messages_db', 'messages_inst')

@app.route('/webhook/sandpuls', methods=['POST', 'GET'])
async def handle_webhook():
    try:
        logger.info('====== Початок обробки webhook ======')
        logger.info(f'Headers: {dict(request.headers)}')

        if request.method == 'GET':
            return jsonify({
                'error': 'Method not allowed',
                'message': 'This endpoint only accepts POST requests',
                'allowed_methods': ['POST']
            }), 405

        request_data = request.get_data(as_text=True)
        logger.info(f'Raw data: {request_data}')

        if not request.is_json:
            return jsonify({'error': 'Content type must be application/json'}), 400

        signature = request.headers.get('X-Sandpuls-Signature', '')
        if 'X-Sandpuls-Signature' in request.headers and not verify_sandpuls_signature(request_data, signature,
                                                                                       SANDPULS_SECRET):
            return jsonify({'error': 'Invalid signature'}), 401

        webhook_data = request.get_json()
        logger.info(f'JSON дані: {webhook_data}')

        if not isinstance(webhook_data, list) or not webhook_data:
            return jsonify({'error': 'Invalid data format - expected non-empty list'}), 400

        first_item = webhook_data[0]
        contact = first_item.get('contact', {})
        bot = first_item.get('bot', {})

        contact_id = contact.get('id')
        bot_id = bot.get('id')
        message = contact.get('last_message')
        username = contact.get('username', '')

        if not all([contact_id, bot_id, message]):
            return jsonify({'error': 'Missing required fields'}), 400

        logger.info(f'Отримане повідомлення від {username}: {message}')
        logger.info(f'Підготовка до обробки повідомлення через OpenAI')

        try:
            ai_response = await process_with_assistant(message, contact_id)
            logger.info(f'Отримано відповідь від AI: {ai_response}')

            await asyncio.to_thread(db.add_message_to_inst_db,
                                    username=username,
                                    user_id_inst=contact_id,
                                    messenger_name='Instagram',
                                    role='user',
                                    content=message)

            await asyncio.to_thread(db.add_message_to_inst_db,
                                    user_id_inst=contact_id,
                                    username=username,
                                    messenger_name='Instagram',
                                    role='assistant',
                                    content=ai_response)

            if not ai_response:
                return jsonify({'error': 'Empty AI response'}), 500

        except Exception as e:
            logger.error(f'Помилка при обробці через OpenAI: {str(e)}')
            return jsonify({'error': 'AI processing failed'}), 500

        try:
            logger.info(f'Спроба відправки відповіді через Sandpuls для {username}')
            sent = await asyncio.to_thread(
                send_message_to_sandpuls,
                contact_id=contact_id,
                message=ai_response,
                bot_id=bot_id
            )

        except Exception as e:
            logger.error(f'Помилка Sandpuls API: {str(e)}')
            sent = False

        except Exception as e:
            logger.error(f'Помилка при відправці через Sandpuls: {str(e)}')
            sent = False

        response_data = {
            'timestamp': datetime.now().isoformat(),
            'source': 'openai_assistant',
            'username': username,
            'contact_id': contact_id,
            'original_message': message,
            'ai_response': ai_response,
            'sent_to_sandpuls': sent
        }

        logger.info('====== Успішне завершення обробки webhook ======')
        return jsonify(response_data), 200

    except Exception as e:
        error_tb = traceback.format_exc()
        logger.error(f'Глобальна помилка при обробці webhook:\n{error_tb}')
        return jsonify({
            'error': str(e),
            'error_type': type(e).__name__,
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/health', methods=['GET'])
async def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    }), 200