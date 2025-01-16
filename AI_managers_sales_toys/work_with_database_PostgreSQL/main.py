from decimal import Decimal

from AI_managers_sales_toys.work_with_database_PostgreSQL.database import DatabaseUser, DatabaseOrder

# db_user = DatabaseUser()
# db_user.insert_user(user_id=1122334455 ,full_name="John Doe", phone_number="+380123456789")
# db_user.insert_user(user_id=333344552, full_name="Jane Smith", phone_number="+380987654321")


db_order = DatabaseOrder()
db_order.insert_order(
    user_id=333344552,
    delivery_address="123 Main St, Anytown, USA",
    products_data=[
        {"article": 'PR2502375', "quantity": 2},
        {"article": 'PR2502374', "quantity": 1},
        {"article": 'PR2502373', "quantity": 3}
    ])
