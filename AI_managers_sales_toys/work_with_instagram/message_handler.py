from typing import List
from work_with_instagram.utils import configure_logging

logger = configure_logging()


class MessageHandler:
    MAX_MESSAGE_LENGTH = 998

    @staticmethod
    def split_message(message: str) -> List[str]:
        if len(message) <= MessageHandler.MAX_MESSAGE_LENGTH:
            return [message]

        # Розділяємо за номерами товарів
        parts = []
        current_part = ""
        items = message.split('\n')

        for item in items:
            # Якщо починається новий товар
            if item.strip().startswith(('1.', '2.', '3.', '4.', '5.')):
                if current_part:
                    parts.append(current_part.strip())
                current_part = item + "\n"
            # Якщо це URL або деталі товару
            elif 'http' in item or '[Деталі тут]' in item:
                current_part += item + "\n"
            # Всі інші частини опису
            elif item.strip():
                if len(current_part) + len(item) + 1 <= MessageHandler.MAX_MESSAGE_LENGTH:
                    current_part += item + "\n"
                else:
                    parts.append(current_part.strip())
                    current_part = item + "\n"

        if current_part:
            parts.append(current_part.strip())

        return parts

    @staticmethod
    def validate_message(message: str) -> bool:
        if not message or not isinstance(message, str):
            logger.error("Повідомлення пусте або не є рядком")
            return False

        if len(message) == 0:
            logger.error("Довжина повідомлення дорівнює 0")
            return False

        return True

    @staticmethod
    def process_message(message: str) -> List[str]:
        if not MessageHandler.validate_message(message):
            raise ValueError("Невалідне повідомлення")

        return MessageHandler.split_message(message)