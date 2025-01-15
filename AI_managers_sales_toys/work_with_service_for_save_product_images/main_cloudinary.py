import os
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv
import time
from typing import Optional
import json
from work_with_database_PostgreSQL.database import DatabaseProduct
from decimal import Decimal

database_product = DatabaseProduct()


def clean_price(price_str: str) -> Decimal:
    """
    Конвертує строкове представлення ціни в Decimal.

    Args:
        price_str: Ціна у форматі "1 499,00 ГРН" або подібному

    Returns:
        Decimal: Очищене значення ціни
    """
    # Видаляємо 'ГРН' та пробіли
    price_str = price_str.replace('ГРН', '').replace(' ', '').strip()
    # Заміняємо кому на крапку
    price_str = price_str.replace(',', '.')
    # Конвертуємо в Decimal
    return Decimal(price_str)


def setup_cloudinary() -> None:
    """Налаштування з'єднання з Cloudinary."""
    load_dotenv()

    cloudinary.config(
        cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
        api_key=os.getenv('CLOUDINARY_API_KEY'),
        api_secret=os.getenv('CLOUDINARY_SECRET'),
        secure=True
    )


def upload_file(file_path: str) -> Optional[str]:
    """
    Завантаження окремого файлу на Cloudinary.

    Args:
        file_path: Шлях до файлу для завантаження

    Returns:
        URL завантаженого файлу або None у випадку помилки
    """
    # folder_path = os.path.dirname(file_path).lstrip('./')
    folder_path = 'toys_product/' + os.path.basename(os.path.dirname(file_path))

    try:
        result = cloudinary.uploader.upload(
            file=file_path,
            folder=folder_path,
            use_filename=True,
            unique_filename=False
        )
        return result['url']
    except Exception as e:
        print(f"Помилка при завантаженні {file_path}: {str(e)}")
        return None


def process_directory(base_dir: str) -> None:
    global database_product
    """
    Обробка директорії та завантаження всіх знайдених зображень.

    Args:
        base_dir: Базова директорія для пошуку зображень
    """
    supported_extensions = ('.jpg', '.jpeg', '.png')
    total_files = 0
    uploaded_files = 0

    print(f"Початок обробки директорії: {base_dir}")
    with open('bontoi_product_data.json') as f:
        all_data = json.load(f)

        for root, _, files in os.walk(base_dir):
            image_files = [f for f in files if f.lower().endswith(supported_extensions)]
            folder_name = os.path.basename(root)
            images_urls = []

            for file in image_files:
                main_image_flag = False
                total_files += 1
                file_path = os.path.join(root, file)
                if '_1.' in file:
                    main_image_flag = True

                print(f"\nОбробка файлу {total_files}: {file_path}")

                url = upload_file(file_path)
                if url and main_image_flag==False:
                    uploaded_files += 1
                    print(f"Успішно завантажено. URL: {url}")
                    images_urls.append(url)
                elif url and main_image_flag==True:
                    main_image = url

                # Невелика затримка між завантаженнями
                time.sleep(0.5)
            for i in all_data:
                new_data = None
                if i['article'] == folder_name:
                    new_data = {
                        "name": i['name'],
                        'main_image': main_image,
                        "images_urls": images_urls,
                        "price": i['price'],
                        "article": i['article'],
                        "gender": i['gender'],
                        "age": i['age'],
                        "color": i['color'],
                        "material": i['material'],
                        "product_status": i['product_status'],
                        "product_type": i['product_type'],
                        "description": i['description'],
                    }
                    print(f'save to update_bontoy_product_data: {new_data["name"]}')
                    if new_data:
                        database_product.insert_product(name=new_data['name'],
                                                    main_image=new_data['main_image'],
                                                    images_urls=new_data['images_urls'],
                                                    price=clean_price(new_data['price']),
                                                    stock_article=new_data['article'],
                                                    gender=new_data['gender'],
                                                    age_category=new_data['age'],
                                                    color=new_data['color'],
                                                    material=new_data['material'],
                                                    product_status=new_data['product_status'],
                                                    product_type=new_data['product_type'],
                                                    description=new_data['description'],
                                                    quantity=1
                                                    )


    print(f"\nЗавершено!")
    print(f"Всього файлів оброблено: {total_files}")
    print(f"Успішно завантажено: {uploaded_files}")
    print(f"Помилок: {total_files - uploaded_files}")


def main():
    # Базова директорія з даними
    base_dir = '../bontoy_toys_data'

    # Налаштування Cloudinary
    setup_cloudinary()

    # Перевірка наявності директорії
    if not os.path.exists(base_dir):
        print(f"Помилка: Директорія {base_dir} не існує!")
        return

    # Початок обробки
    process_directory(base_dir)


if __name__ == "__main__":
    main()