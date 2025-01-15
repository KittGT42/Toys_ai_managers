from decimal import Decimal

from sqlalchemy import create_engine, text, select, func, cast, Integer
from AI_managers_sales_toys.work_with_database_PostgreSQL.config import settings
from sqlalchemy.orm import Session, sessionmaker
from AI_managers_sales_toys.work_with_database_PostgreSQL.models import Order, Base, User, Product, OrderStatus, order_products
from AI_managers_sales_toys.work_with_database_PostgreSQL.utils.main_create_article import ArticleGenerator
from AI_managers_sales_toys.work_with_database_PostgreSQL.utils.main_create_number_order import OrderNumberGenerator

sync_engine = create_engine(
    url=settings.db_url_psycopg2,
    echo=False,
    pool_size=5,
    max_overflow=10
)

session = sessionmaker(bind=sync_engine)

article_generator = ArticleGenerator(session=session)
order_number_generator = OrderNumberGenerator(session=session)

class DatabaseUser:
    def __init__(self):
        global sync_engine, session
        self.engine = sync_engine
        self.session = session
    def insert_user(self, user_id: int, full_name: str, phone_number: str):
        first_data = User(
            user_id=user_id,
            full_name=full_name,
            phone_number=phone_number,

        )
        with self.session() as session_obj:
            session_obj.add(first_data)
            session_obj.commit()
    def select_user(self, user_id: int):
        with self.session() as session_obj:
            user = session_obj.get(User, {"user_id": user_id})
            return user

    def select_users(self):
        with self.session() as session_obj:
            query = select(User)
            result = session_obj.execute(query)
            users = result.scalars().all()
            return users


    def update_user(self, user_id: int, name: str, email: str, password: str):
        with self.session() as session_obj:
            user = session_obj.get(User, {"user_id": user_id})
            user.full_name = name
            user.email = email
            user.password = password
            session_obj.commit()


class DatabaseOrder:
    def __init__(self):
        global sync_engine, session
        self.engine = sync_engine
        self.session = session

    def insert_order(self, user_id: int, full_name: str, delivery_address: str,
                     products_data: list[dict]):
        with self.session() as session_obj:
            # Генеруємо номер замовлення
            order_number = order_number_generator.generate_order_number()

            # Створюємо новий ордер
            new_order = Order(
                order_number=order_number,
                user_id=user_id,
                full_name=full_name,
                delivery_address=delivery_address,
                status=OrderStatus.NEW
            )
            session_obj.add(new_order)
            session_obj.flush()

            # Додаємо продукти до ордеру
            for product_data in products_data:
                product = session_obj.query(Product).filter(Product.article == product_data["article"]).first()
                if product:
                    stmt = order_products.insert().values(
                        order_number=new_order.order_number,  # Використовуємо order_number
                        article=product_data["article"],
                        quantity=product_data["quantity"]
                    )
                    session_obj.execute(stmt)

            # Обчислюємо загальну вартість
            new_order.calculate_total_price(session_obj)
            session_obj.commit()

    def select_order(self, order_id: int):
        with self.session() as session_obj:
            order = session_obj.get(Order, {"order_id": order_id})
            return order

    def select_orders(self):
        with self.session() as session_obj:
            query = select(Order)
            result = session_obj.execute(query)
            orders = result.scalars().all()
            return orders

    def update_order(self, order_id: int, user_id: int, status: str, created_at: str, updated_at: str):
        with self.session() as session_obj:
            order = session_obj.get(Order, {"order_id": order_id})
            order.user_id = user_id
            order.status = status
            order.created_at = created_at
            order.updated_at = updated_at
            session_obj.commit()

    def select_orders_avg_total_amount(self):
        with self.session() as session_obj:
            query = select(Order.status,
                cast(func.avg(Order.total_price)), Integer)
            result = session_obj.execute(query)
            avg_total_amount = result.scalar()
            return avg_total_amount


class DatabaseProduct:
    def __init__(self):
        global sync_engine, session
        self.engine = sync_engine
        self.session = session

    def insert_product(self, name: str, price: Decimal, description: str, quantity: int, main_image: str,
                       images_urls: list[str], age_category: str, color: str, material: str, product_status: str,
                       product_type: str, stock_article: str, gender: str):
        first_data = Product(
            article=article_generator.generate_article(),
            stock_article=stock_article,
            name=name,
            main_image=main_image,
            images_urls=images_urls,
            age_category = age_category,
            color=color,
            material=material,
            gender=gender,
            product_status=product_status,
            product_type=product_type,
            price=price,
            description=description,
            quantity=quantity
        )
        with self.session() as session_obj:
            session_obj.add(first_data)
            session_obj.commit()

    def select_product(self, product_id: int):
        with self.session() as session_obj:
            product = session_obj.get(Product, {"product_id": product_id})
            return product

    def select_products(self):
        with self.session() as session_obj:
            query = select(Product)
            result = session_obj.execute(query)
            products = result.scalars().all()
            return products

    def update_product(self, product_id: int, name: str, price: float):
        with self.session() as session_obj:
            product = session_obj.get(Product, {"product_id": product_id})
            product.name = name
            product.price = price
            session_obj.commit()