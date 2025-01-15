from datetime import datetime
from sqlalchemy import select, desc
from AI_managers_sales_toys.work_with_database_PostgreSQL.models import Order

class OrderNumberGenerator:
    def __init__(self, session):
        self.session = session
        self.prefix = "ORDER"  # Префікс для всіх артикулів
        self.year = str(datetime.now().year)[-2:]  # Останні 2 цифри поточного року

    def _get_last_order_number(self):
        """
        Отримує останній використаний артикул з бази даних
        """
        with self.session() as session_obj:
            query = (
                select(Order.order_number)
                .where(Order.order_number.like(f"{self.prefix}{self.year}%"))
                .order_by(desc(Order.order_number))
                .limit(1)
            )
            result = session_obj.execute(query)
            last_order_number = result.scalar()
            return last_order_number

    def generate_order_number(self) -> str:
        """
        Генерує новий унікальний артикул
        Формат: PR23XXXXX, де:
        - PR: префікс
        - 23: рік
        - XXXXX: п'ятизначний порядковий номер
        """
        last_order_number = self._get_last_order_number()

        if not last_order_number:
            # Якщо артикулів ще немає, починаємо з 00001
            new_number = 1
        else:
            # Отримуємо номер з останнього артикула і збільшуємо його на 1
            try:
                last_number = int(last_order_number[4:])  # Пропускаємо префікс і рік
                new_number = last_number + 1
            except (ValueError, IndexError):
                # Якщо виникла помилка при парсингу, починаємо з 1
                new_number = 1

        # Форматуємо новий номер як п'ятизначне число
        formatted_number = f"{new_number:05d}"
        new_order_number = f"{self.prefix}{self.year}{formatted_number}"

        return new_order_number
