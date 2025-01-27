import requests
from typing import Optional, List
from AI_managers_sales_toys.work_with_instagram.utils import configure_logging
from AI_managers_sales_toys.work_with_instagram.message_handler import MessageHandler
from AI_managers_sales_toys.work_with_instagram.config import SANDPULS_SECRET

logger = configure_logging()


class SandpulsAPI:
    def __init__(self):
        self.base_url = "https://api.sendpulse.com"
        self.access_token = None
        self.message_handler = MessageHandler()

    def get_access_token(self) -> Optional[str]:
        try:
            client_id, client_secret = SANDPULS_SECRET.split(':')

            url = f"{self.base_url}/oauth/access_token"
            payload = {
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret
            }

            response = requests.post(url, json=payload)
            response.raise_for_status()

            data = response.json()
            self.access_token = data['access_token']
            return self.access_token

        except Exception as e:
            logger.error(f"Помилка при отриманні access token: {str(e)}")
            return None

    def send_message(self, contact_id: str, message: str, bot_id: str) -> bool:
        try:
            if not self.access_token:
                self.get_access_token()

            if not self.access_token:
                raise Exception("Не вдалося отримати access token")

            message_parts = self.message_handler.process_message(message)

            for part in message_parts:
                success = self._send_single_message(contact_id, part, bot_id)
                if not success:
                    return False

            return True

        except Exception as e:
            logger.error(f"Помилка при відправці повідомлення: {str(e)}")
            return False

    def _send_single_message(self, contact_id: str, message: str, bot_id: str) -> bool:
        try:
            url = f"{self.base_url}/instagram/contacts/send"
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }

            payload = {
                "contact_id": contact_id,
                "bot_id": bot_id,
                "messages": [
                    {
                        "type": "text",
                        "message": {
                            "text": message
                        }
                    }
                ]
            }

            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return True

        except Exception as e:
            logger.error(f"Помилка при відправці частини повідомлення: {str(e)}")
            return False


# Створюємо глобальний екземпляр API клієнта
api_client = SandpulsAPI()


def send_message_to_sandpuls(contact_id: str, message: str, bot_id: str) -> bool:
    """
    Відправка повідомлення через Sandpuls API
    """
    return api_client.send_message(contact_id, message, bot_id)