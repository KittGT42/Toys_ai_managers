import requests
from work_with_telegram.work_with_telegram_bot.config import TELEGRAM_BOT_TOKEN, ADMIN_USER_ID
from work_with_telegram.work_with_telegram_bot.utils import configure_logging

logger = configure_logging()


def send_telegram_message(message: str) -> bool:
    """
    Відправка повідомлення через Telegram Bot API

    Args:
        message: Текст повідомлення

    Returns:
        bool: True якщо повідомлення успішно відправлено, False у випадку помилки
    """
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": ADMIN_USER_ID,
            "text": message,
            "parse_mode": "HTML"
        }

        response = requests.post(url, json=payload)
        response.raise_for_status()

        logger.info("Повідомлення успішно відправлено в Telegram")
        return True

    except Exception as e:
        logger.error(f"Помилка при відправці повідомлення в Telegram: {str(e)}")
        return False