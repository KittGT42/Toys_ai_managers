import os
from dotenv import load_dotenv
import logging

# Завантаження змінних середовища
load_dotenv()

# Конфігурація логера
logger = logging.getLogger(__name__)

def get_env_variable(var_name: str, required: bool = True) -> str:
    """
    Отримання змінної середовища з валідацією

    Args:
        var_name: Назва змінної
        required: Чи є змінна обов'язковою

    Returns:
        str: Значення змінної

    Raises:
        ValueError: Якщо required=True і змінна не знайдена
    """
    value = os.getenv(var_name)
    if required and not value:
        error_msg = f'Відсутня обов\'язкова змінна середовища: {var_name}'
        logger.error(error_msg)
        raise ValueError(error_msg)
    return value

# Конфігурація для Telegram
ADMIN_USER_ID = get_env_variable('ADMIN_USER_ID')
TELEGRAM_BOT_TOKEN = get_env_variable('TELEGRAM_BOT_TOKEN')
