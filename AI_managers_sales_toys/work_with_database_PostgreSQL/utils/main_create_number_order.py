from datetime import datetime
from sqlalchemy import select, desc
from AI_managers_sales_toys.work_with_database_PostgreSQL.models import Order


class OrderNumberGenerator:
    def __init__(self, session):
        self.session = session
        self.prefix = "ORDER"
        self.year = str(datetime.now().year)[-2:]

    def _get_last_order_number(self):
        """
        Отримує останній використаний номер замовлення з бази даних
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

    def _extract_number(self, order_number):
        """
        Витягує числову частину з номера замовлення
        """
        if not order_number:
            return 0
        try:
            # Пропускаємо 'ORDER' (5 символів) та рік (2 символи)
            number_str = order_number[7:]
            return int(number_str)
        except (ValueError, IndexError):
            return 0

    def generate_order_number(self) -> str:
        """
        Генерує новий унікальний номер замовлення
        """
        last_order_number = self._get_last_order_number()
        last_number = self._extract_number(last_order_number)

        # Перевірка, чи існує такий номер
        while True:
            new_number = last_number + 1
            new_order_number = f"{self.prefix}{self.year}{new_number:05d}"

            # Перевіряємо, чи існує такий номер в базі
            with self.session() as session_obj:
                existing_order = session_obj.execute(
                    select(Order).where(Order.order_number == new_order_number)
                ).scalar()

                if not existing_order:
                    return new_order_number

                last_number = new_number