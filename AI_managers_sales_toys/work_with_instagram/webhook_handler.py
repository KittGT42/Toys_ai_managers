from datetime import datetime
import requests
from typing import Dict, Any
from AI_managers_sales_toys.work_with_instagram.utils import configure_logging

logger = configure_logging()

def forward_message(message: Dict[str, Any]) -> bool:
    try:
        response = requests.post(
            json=message,
            headers={'Content-Type': 'application/json'},
            timeout=5
        )
        response.raise_for_status()
        logger.info(f'Повідомлення успішно переслано: {message}')
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f'Помилка при пересиланні повідомлення: {str(e)}')
        return False