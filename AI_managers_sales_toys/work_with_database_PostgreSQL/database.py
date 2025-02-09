import random
from decimal import Decimal
import datetime
from sqlalchemy import create_engine, text, select, func, cast, Integer
from AI_managers_sales_toys.work_with_database_PostgreSQL.config import settings
from sqlalchemy.orm import Session, sessionmaker
from AI_managers_sales_toys.work_with_database_PostgreSQL.models import Order, Base, User, Product, OrderStatus, \
    order_products, Gender
from AI_managers_sales_toys.work_with_database_PostgreSQL.utils.main_create_article import ArticleGenerator
from AI_managers_sales_toys.work_with_database_PostgreSQL.utils.main_create_number_order import OrderNumberGenerator
from sqlalchemy import or_

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

   def insert_user(self, user_id: str, full_name: str, phone_number: str):
       current_time = datetime.datetime.now(datetime.timezone.utc)
       first_data = User(
           user_id=str(user_id),
           full_name=full_name,
           phone_number=phone_number,
           created_at=current_time,
           updated_at=current_time
       )
       with self.session() as session_obj:
           try:
               session_obj.add(first_data)
               session_obj.commit()
           except Exception as e:
               session_obj.rollback()
               raise e

   def select_user(self, user_id: str):
       with self.session() as session_obj:
           user = session_obj.query(User).filter(User.user_id == user_id).first()
           return user

   def select_users(self):
       with self.session() as session_obj:
           query = select(User)
           result = session_obj.execute(query)
           users = result.scalars().all()
           return users

   def update_user(self, user_id: int, name: str, phone_number: str):
       with self.session() as session_obj:
           try:
               user = session_obj.query(User).filter(User.user_id == user_id).first()
               if user:
                   user.full_name = name
                   user.phone_number = phone_number
                   user.updated_at = datetime.datetime.now(datetime.timezone.utc)
                   session_obj.commit()
           except Exception as e:
               session_obj.rollback()
               raise e

   def delete_user(self, user_id: int):
       with self.session() as session_obj:
           try:
               user = session_obj.query(User).filter(User.user_id == user_id).first()
               if user:
                   session_obj.delete(user)
                   session_obj.commit()
                   return True
               return False
           except Exception as e:
               session_obj.rollback()
               raise e

   def get_user_orders(self, user_id: int):
       with self.session() as session_obj:
           user = session_obj.query(User).filter(User.user_id == user_id).first()
           if user:
               return user.orders
           return []

class DatabaseOrder:
   def __init__(self):
       global sync_engine, session
       self.engine = sync_engine
       self.session = session

   def insert_order(self, user_id, delivery_address: str, products_data: list[dict]):
       with self.session() as session_obj:
           try:
               # Знаходимо user.id за user_id
               user = session_obj.query(User).filter(User.user_id == user_id).first()
               if not user:
                   raise ValueError(f"User with user_id={user_id} not found")

               order_number = order_number_generator.generate_order_number()
               current_time = datetime.datetime.now(datetime.timezone.utc)

               new_order = Order(
                   order_number=order_number,
                   user_id=str(user.id),  # використовуємо user.id
                   delivery_address=delivery_address,
                   status=OrderStatus.NEW.value,
                   created_at=current_time,
                   updated_at=current_time
               )
               session_obj.add(new_order)
               session_obj.flush()

               for product_data in products_data:
                   product = session_obj.query(Product).filter(
                       Product.article == product_data["article"]
                   ).first()
                   if product:
                       stmt = order_products.insert().values(
                           order_id=new_order.id,
                           product_id=product.id,
                           quantity=product_data["quantity"]
                       )
                       session_obj.execute(stmt)

               new_order.calculate_total_price(session_obj)
               session_obj.commit()
           except Exception as e:
               session_obj.rollback()
               raise e

   def select_order(self, order_number: str):
       with self.session() as session_obj:
           order = session_obj.query(Order).filter(Order.order_number == order_number).first()
           return order

   def select_orders(self):
       with self.session() as session_obj:
           query = select(Order)
           result = session_obj.execute(query)
           orders = result.scalars().all()
           return orders

   def update_order(self, order_id: int, **kwargs):
       with self.session() as session_obj:
           try:
               order = session_obj.get(Order, {"order_id": order_id})
               if order:
                   for key, value in kwargs.items():
                       if hasattr(order, key):
                           setattr(order, key, value)
                   order.updated_at = datetime.datetime.now(datetime.timezone.utc)
                   session_obj.commit()
                   return True
               return False
           except Exception as e:
               session_obj.rollback()
               raise e

   def select_orders_avg_total_amount(self):
       with self.session() as session_obj:
           query = select(Order.status,
               cast(func.avg(Order.total_price), Integer))
           result = session_obj.execute(query)
           avg_total_amount = result.scalar()
           return avg_total_amount

   def delete_order(self, order_number: str):
       with self.session() as session_obj:
           try:
               order = session_obj.query(Order).filter(Order.order_number == order_number).first()
               if order:
                   session_obj.delete(order)
                   session_obj.commit()
                   return True
               return False
           except Exception as e:
               session_obj.rollback()
               raise e

   def get_orders_by_status(self, status: str):
       with self.session() as session_obj:
           orders = session_obj.query(Order).filter(Order.status == status).all()
           return orders

   def get_orders_by_date_range(self, start_date: datetime.datetime, end_date: datetime.datetime):
       with self.session() as session_obj:
           orders = session_obj.query(Order).filter(
               Order.created_at >= start_date,
               Order.created_at <= end_date
           ).all()
           return orders

   def get_order_with_products(self, order_number: str):
       with self.session() as session_obj:
           order = session_obj.query(Order).filter(
               Order.order_number == order_number
           ).first()
           if order:
               # Завантажуємо продукти разом з замовленням
               return {
                   'order': order,
                   'products': order.products
               }
           return None

class DatabaseProduct:
   def __init__(self):
       global sync_engine, session
       self.engine = sync_engine
       self.session = session

   def insert_product(self, name: str, price: Decimal, description: str, quantity: int, main_image: str,
                     images_urls: list[str], age_category: str, color: str, material: str, product_status: str,
                     product_type: str, stock_article: str, gender: str):
       try:
           current_time = datetime.datetime.now(datetime.timezone.utc)
           first_data = Product(
               article=article_generator.generate_article(),
               stock_article=stock_article,
               name=name,
               main_image=main_image,
               images_urls=images_urls,
               age_category=age_category,
               color=color,
               material=material,
               gender=gender,
               product_status=product_status,
               product_type=product_type,
               price=price,
               description=description,
               quantity=quantity,
               created_at=current_time,
               updated_at=current_time
           )
           with self.session() as session_obj:
               session_obj.add(first_data)
               session_obj.commit()
               return first_data.article
       except Exception as e:
           session_obj.rollback()
           raise e

   def select_product(self, article: str):
       with self.session() as session_obj:
           product = session_obj.query(Product).filter(Product.article == article).first()
           return product

   def select_product_for_inst_with_stock_article(self, article: str):
       with self.session() as session_obj:
           product = session_obj.query(Product).filter(func.lower(Product.stock_article) == article.lower()).first()
           return product

   def select_product_by_different_category(self, age_year, age_month, gender, main_product_category, budget):
       with self.session() as session_obj:
           # Конвертуємо вхідні параметри в потрібні типи
           age_year = float(age_year) if isinstance(age_year, str) else age_year
           age_month = float(age_month) if isinstance(age_month, str) else age_month
           budget = float(budget) if isinstance(budget, str) else budget
           if age_year > 0:
               base_query = session_obj.query(Product).filter(
                   Product.age_category_years <= age_year,
                   Product.gender.in_([gender, 'Унісекс']),
                   Product.price <= budget
               )

               if main_product_category and main_product_category != 'toys':
                   # Видаляємо закінчення для кращого пошуку
                   search_term = main_product_category.rstrip('иіїа')  # Прибираємо типові закінчення
                   search_pattern = f"%{search_term}%"

                   base_query = base_query.filter(
                       or_(
                           Product.name.ilike(search_pattern),
                           Product.name.ilike(f"%{search_term}и%"),
                           Product.name.ilike(f"%{search_term}а%"),
                           Product.name.ilike(f"%{search_term}ів%"),
                           # Product.description.ilike(search_pattern),
                           # Product.description.ilike(f"%{search_term}и%"),
                           # Product.description.ilike(f"%{search_term}а%"),
                           # Product.description.ilike(f"%{search_term}ів%")
                       )
                   )

               products = base_query.all()

               if len(products) > 3:
                   return random.sample(products, 3)
               return products
           if age_month > 0:
               base_query = session_obj.query(Product).filter(
                   Product.age_category_years <= age_month,
                   Product.gender.in_([gender, 'Унісекс']),
                   Product.price <= budget
               )

               if main_product_category and main_product_category != 'toys':
                   # Видаляємо закінчення для кращого пошуку
                   search_term = main_product_category.rstrip('иіїа')  # Прибираємо типові закінчення
                   search_pattern = f"%{search_term}%"

                   base_query = base_query.filter(
                       or_(
                           Product.name.ilike(search_pattern),
                           Product.description.ilike(search_pattern),
                           # Додаткові варіанти пошуку для різних форм слова
                           Product.name.ilike(f"%{search_term}и%"),
                           Product.name.ilike(f"%{search_term}а%"),
                           Product.name.ilike(f"%{search_term}ів%"),
                           Product.description.ilike(f"%{search_term}и%"),
                           Product.description.ilike(f"%{search_term}а%"),
                           Product.description.ilike(f"%{search_term}ів%")
                       )
                   )

               products = base_query.all()

               if len(products) > 3:
                   return random.sample(products, 3)
               return products


   def select_products(self):
       with self.session() as session_obj:
           query = select(Product)
           result = session_obj.execute(query)
           products = result.scalars().all()
           return products

   def update_product(self, article: str, **kwargs):
       with self.session() as session_obj:
           try:
               product = session_obj.query(Product).filter(Product.article == article).first()
               if product:
                   for key, value in kwargs.items():
                       if hasattr(product, key):
                           setattr(product, key, value)
                   product.updated_at = datetime.datetime.now(datetime.timezone.utc)
                   session_obj.commit()
                   return True
               return False
           except Exception as e:
               session_obj.rollback()
               raise e

   def delete_product(self, article: str):
       with self.session() as session_obj:
           try:
               product = session_obj.query(Product).filter(Product.article == article).first()
               if product:
                   session_obj.delete(product)
                   session_obj.commit()
                   return True
               return False
           except Exception as e:
               session_obj.rollback()
               raise e

   def get_products_by_category(self, age_category: str):
       with self.session() as session_obj:
           products = session_obj.query(Product).filter(Product.age_category == age_category).all()
           return products

   def get_products_by_price_range(self, min_price: Decimal, max_price: Decimal):
       with self.session() as session_obj:
           products = session_obj.query(Product).filter(
               Product.price >= min_price,
               Product.price <= max_price
           ).all()
           return products

   def get_products_in_stock(self):
       with self.session() as session_obj:
           products = session_obj.query(Product).filter(Product.quantity > 0).all()
           return products