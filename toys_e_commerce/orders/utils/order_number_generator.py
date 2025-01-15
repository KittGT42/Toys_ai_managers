from datetime import datetime
from toys_e_commerce.orders.models import Order


class OrderNumberGenerator:
    @staticmethod
    def generate_order_number():
        prefix = "ORDER"
        year = str(datetime.now().year)[-2:]
        last_order = Order.objects.filter(
            order_number__startswith=f"{prefix}{year}"
        ).order_by('-order_number').first()

        if not last_order:
            new_number = 1
        else:
            try:
                last_number = int(last_order.order_number[4:])
                new_number = last_number + 1
            except (ValueError, IndexError):
                new_number = 1

        return f"{prefix}{year}{new_number:05d}"