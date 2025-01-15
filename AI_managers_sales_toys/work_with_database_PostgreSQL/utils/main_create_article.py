from datetime import datetime
from sqlalchemy import select, desc
from work_with_database_PostgreSQL.models import Product

class ArticleGenerator:
    def __init__(self, session):
        self.session = session
        self.prefix = "PR"  # Префікс для всіх артикулів
        self.year = str(datetime.now().year)[-2:]  # Останні 2 цифри поточного року

    def _get_last_article(self):
        """
        Отримує останній використаний артикул з бази даних
        """
        with self.session() as session_obj:
            query = (
                select(Product.article)
                .where(Product.article.like(f"{self.prefix}{self.year}%"))
                .order_by(desc(Product.article))
                .limit(1)
            )
            result = session_obj.execute(query)
            last_article = result.scalar()
            return last_article

    def generate_article(self) -> str:
        """
        Генерує новий унікальний артикул
        Формат: PR23XXXXX, де:
        - PR: префікс
        - 23: рік
        - XXXXX: п'ятизначний порядковий номер
        """
        last_article = self._get_last_article()

        if not last_article:
            # Якщо артикулів ще немає, починаємо з 00001
            new_number = 1
        else:
            # Отримуємо номер з останнього артикула і збільшуємо його на 1
            try:
                last_number = int(last_article[4:])  # Пропускаємо префікс і рік
                new_number = last_number + 1
            except (ValueError, IndexError):
                # Якщо виникла помилка при парсингу, починаємо з 1
                new_number = 1

        # Форматуємо новий номер як п'ятизначне число
        formatted_number = f"{new_number:05d}"
        new_article = f"{self.prefix}{self.year}{formatted_number}"

        return new_article