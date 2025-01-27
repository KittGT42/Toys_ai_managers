import logging
import hmac
import hashlib
from typing import Optional
from AI_managers_sales_toys.work_with_database_PostgreSQL.database import DatabaseUser, DatabaseOrder, DatabaseProduct

product_db = DatabaseProduct()

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
        return True


async def get_product_info(article: str) -> dict:
    """Отримання інформації про товар з бази даних з розширеною валідацією"""
    try:
        product = product_db.select_product_for_inst_with_stock_article(article)

        if not product:
            return {
                "status": "error",
                "message": f"Товар з артикулом {article} не знайдено"
            }

        # Перевірка обов'язкових полів
        required_fields = ["name", "price", "article", "quantity"]
        missing_fields = [field for field in required_fields if not hasattr(product, field)]

        if missing_fields:
            return {
                "status": "error",
                "message": f"Неповні дані товару: відсутні поля {', '.join(missing_fields)}"
            }

        product_data = {
            "name": product.name,
            "price": str(product.price),
            "article": product.article,
            "age_category": getattr(product, 'age_category', ''),
            "color": getattr(product, 'color', ''),
            "material": getattr(product, 'material', ''),
            "description": getattr(product, 'description', ''),
            "gender": getattr(product, 'gender', ''),
            'quantity': product.quantity,
            'product_type': product.product_type

        }


        return {
            "status": "success",
            "data": product_data
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Помилка отримання даних товару: {str(e)}"
        }