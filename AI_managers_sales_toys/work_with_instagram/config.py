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

# Конфігурація для Sandpuls
SANDPULS_SECRET = get_env_variable('SAND_PULSE_SECRET')

# Конфігурація для OpenAI
OPENAI_API_KEY = get_env_variable('OPENAI_API_KEY')
ASSISTANT_ID = get_env_variable('ASSISTANT_ID_telegram_bot_sale_animals_items')

# Режим додатку
APP_ENV = get_env_variable('APP_ENV', required=False) or 'development'
DEBUG = APP_ENV == 'development'

# Налаштування безпеки
VERIFY_SIGNATURE = get_env_variable('VERIFY_SIGNATURE', required=False) or 'true'
VERIFY_SIGNATURE = VERIFY_SIGNATURE.lower() == 'true'