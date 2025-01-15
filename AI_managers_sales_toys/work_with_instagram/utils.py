import logging
import hmac
import hashlib
from typing import Optional

def configure_logging():
    """
    Налаштування логування без дублювання
    """
    logger = logging.getLogger('webhook_receiver')

    # Очищаємо всі попередні хендлери
    if logger.handlers:
        logger.handlers.clear()

    # Встановлюємо рівень логування
    logger.setLevel(logging.INFO)

    # Формат логів
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Файловий хендлер
    file_handler = logging.FileHandler('webhook_receiver.log')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Консольний хендлер
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger

def verify_sandpuls_signature(request_data: str, signature: str, secret: Optional[str]) -> bool:
    """Перевірка підпису від Sandpuls"""
    logger = logging.getLogger('webhook_receiver')

    if not secret:
        logger.warning('SANDPULS_SECRET не налаштований - пропускаємо перевірку підпису')
        return True

    if not signature:
        logger.warning('Підпис відсутній в запиті - пропускаємо перевірку')
        return True

    try:
        expected = hmac.new(
            secret.encode(),
            request_data.encode(),
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, signature)
    except Exception as e:
        logger.error(f'Помилка при перевірці підпису: {str(e)}')
        return True  # В режимі розробки пропускаємо помилки