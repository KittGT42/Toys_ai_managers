from AI_managers_sales_toys.work_with_database_PostgreSQL.models import Product
from AI_managers_sales_toys.work_with_database_PostgreSQL.database import session
import json
import datetime
from decimal import Decimal


def decimal_handler(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
    raise TypeError(f'Object of type {type(obj)} is not JSON serializable')


def clean_product_name(name: str) -> str:
    """Очищує назву продукту від дужок та їх вмісту"""
    import re
    # Видаляємо вміст у дужках разом з дужками
    cleaned_name = re.sub(r'\s*\([^)]*\)', '', name)
    # Видаляємо зайві пробіли
    cleaned_name = ' '.join(cleaned_name.split())
    return cleaned_name


def download_product_data():
    # Створюємо нову сесію з sessionmaker
    db_session = session()

    try:
        # Отримання всіх продуктів
        products = db_session.query(Product).all()

        # Конвертація в список словників
        products_list = []
        for product in products:
            # Очищуємо назву від дужок
            cleaned_name = clean_product_name(product.name)

            product_dict = {
                'article': product.article,
                'name': cleaned_name,  # Використовуємо очищену назву
                'gender': product.gender,
                'description': product.description,
                'age_category': product.age_category,
                'color': product.color,
                'material': product.material,
            }
            products_list.append(product_dict)

        # Зберігання в JSON файл
        with open('products_data_price.json', 'w', encoding='utf-8') as f:
            json.dump(products_list, f, ensure_ascii=False, indent=2, default=decimal_handler)

        print(f"Успішно збережено {len(products_list)} продуктів у файл products_data.json")
        return products_list

    except Exception as e:
        print(f"Помилка при отриманні даних: {str(e)}")
        return []

    finally:
        db_session.close()


if __name__ == "__main__":
    download_product_data()