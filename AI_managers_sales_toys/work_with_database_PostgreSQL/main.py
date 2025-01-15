from work_with_database_PostgreSQL.database import DatabaseUser, create_tables, DatabaseProduct, DatabaseOrder
from decimal import Decimal

create_tables()

# db_user = DatabaseUser()
# db_user.insert_user(user_id=1122334455 ,full_name="John Doe", email="yK7oV@example.com", password="password123")
# db_user.insert_user(user_id=333344552, full_name="Jane Smith", email="2L8dM@example.com", password="password456")
#
# db_product = DatabaseProduct()
# db_product.insert_product(name="Product A", price=Decimal(9.99), description="Description for Product A", quantity=10)
# db_product.insert_product(name="Product B", price=Decimal(19.99), description="Description for Product B", quantity=5)
# db_product.insert_product(name="Product C", price=Decimal(29.99), description="Description for Product C", quantity=3)
#
# db_order = DatabaseOrder()
# db_order.insert_order(
#     user_id=2,
#     delivery_address="123 Main St, Anytown, USA",
#     products_data=[
#         {"article": 'PR2400001', "quantity": 2},
#         {"article": 'PR2400002', "quantity": 1},
#         {"article": 'PR2400003', "quantity": 3}
#     ])
