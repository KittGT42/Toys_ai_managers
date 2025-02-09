import json
import os
from typing import List, Dict


def split_products_json(input_file: str, output_dir: str, num_parts: int = 9):
    """
    Розбиває великий JSON файл з продуктами на декілька менших файлів.

    Args:
        input_file (str): Шлях до вхідного JSON файлу
        output_dir (str): Директорія для збереження результатів
        num_parts (int): Кількість частин для розбиття
    """
    # Створюємо директорію якщо її не існує
    os.makedirs(output_dir, exist_ok=True)

    # Читаємо вхідний файл
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Отримуємо список всіх продуктів
    products = data if isinstance(data, list) else data.get('products', [])

    # Розраховуємо розмір кожної частини
    chunk_size = len(products) // num_parts
    remaining = len(products) % num_parts

    # Створюємо індексний файл
    index = {
        "total_products": len(products),
        "parts": {}
    }

    # Розбиваємо на частини та зберігаємо
    current_position = 0
    for i in range(num_parts):
        # Визначаємо розмір поточної частини
        current_chunk_size = chunk_size + (1 if i < remaining else 0)

        # Вибираємо продукти для поточної частини
        start_idx = current_position
        end_idx = current_position + current_chunk_size
        chunk_products = products[start_idx:end_idx]

        # Формуємо назву файлу
        filename = f'products_part_{i + 1}.json'
        filepath = os.path.join(output_dir, filename)

        # Зберігаємо частину в окремий файл
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({
                "part": i + 1,
                "total_parts": num_parts,
                "products_count": len(chunk_products),
                "products": chunk_products
            }, f, ensure_ascii=False, indent=2)

        # Оновлюємо індекс
        index["parts"][f"part_{i + 1}"] = {
            "filename": filename,
            "products_count": len(chunk_products),
            "start_article": chunk_products[0]["article"],
            "end_article": chunk_products[-1]["article"]
        }

        current_position = end_idx

    # Зберігаємо індексний файл
    with open(os.path.join(output_dir, 'index.json'), 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, indent=2)


# Функція для пошуку потрібного файлу за артикулом
def find_product_file(article: str, index_path: str) -> str:
    """
    Знаходить файл, який містить продукт за артикулом.

    Args:
        article (str): Артикул продукту
        index_path (str): Шлях до індексного файлу

    Returns:
        str: Назва файлу, де знаходиться продукт
    """
    with open(index_path, 'r', encoding='utf-8') as f:
        index = json.load(f)

    for part_info in index["parts"].values():
        if part_info["start_article"] <= article <= part_info["end_article"]:
            return part_info["filename"]

    return None


# Приклад використання
if __name__ == "__main__":
    input_file = "products_data.json"  # Ваш вхідний файл
    output_dir = "../chank_data"  # Директорія для результатів

    # Розбиваємо файл
    split_products_json(input_file, output_dir)

    print(f"JSON файл успішно розбито на частини в директорії: {output_dir}")