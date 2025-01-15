from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey, text, Numeric, Computed, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase, relationship
import enum
import datetime
from typing import Annotated, List
from decimal import Decimal

int_pk = Annotated[int, mapped_column(primary_key=True)]
created_at = Annotated[datetime.datetime, mapped_column(server_default=text("TIMEZONE('utc', now())"))]
updated_at = Annotated[datetime.datetime, mapped_column(server_default=text("TIMEZONE('utc', now())"),
                                                           onupdate=text("TIMEZONE('utc', now())"))]
str_255 = Annotated[str, 255]

class Base(DeclarativeBase):
    type_annotation_map = {
        str_255: String(255),

    }

class OrderStatus(enum.Enum):
    NEW = 'new'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'

class Gender(enum.Enum):
    MALE = 'male'
    FEMALE = 'female'
    UNISEX = 'unisex'

class AgeCategory(enum.Enum):
    ZERO_PLUS = '0+'      # Від народження
    THREE_PLUS = '3+'     # Від 3 років
    FIVE_PLUS = '5+'      # Від 5 років
    EIGHT_PLUS = '8+'     # Від 8 років
    TWELVE_PLUS = '12+'   # Від 12 років
    FOURTEEN_PLUS = '14+' # Від 14 років
    EIGHTEEN_PLUS = '18+' # Від 18 років

order_products = Table(
    'orders_orderproduct',
    Base.metadata,
    Column('order_number', String(255), ForeignKey('orders_order.order_number', ondelete='CASCADE')),
    Column('article', String(255), ForeignKey('products_product.article')),
    Column('quantity', Integer, nullable=False, default=1)
)


class User(Base):
    __tablename__ = 'users_user'
    id: Mapped[int_pk]
    user_id: Mapped[int] = mapped_column(
        nullable=False,
        index=True
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]

    # Додаємо зв'язок з ордерами
    orders: Mapped[List["Order"]] = relationship("Order", back_populates="user")


class Order(Base):
    __tablename__ = 'orders_order'
    id: Mapped[int_pk]
    order_number: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users_user.id', ondelete='CASCADE'), nullable=False)
    delivery_address: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]
    status: Mapped[str] = mapped_column(
        String(20),
        default=OrderStatus.NEW.value,
        nullable=False
    )

    # Додаємо зв'язки
    user: Mapped["User"] = relationship("User", back_populates="orders")
    products: Mapped[List["Product"]] = relationship(
        "Product",
        secondary=order_products,
        back_populates="orders"
    )

    total_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)

    def calculate_total_price(self, session):
        """Обчислює загальну вартість замовлення"""
        result = session.execute(
            text("""
                SELECT COALESCE(SUM(p.price * op.quantity), 0) as total
                FROM products_product p 
                JOIN orders_orderproduct op ON p.article = op.article
                WHERE op.order_number = :order_number
            """),
            {"order_number": self.order_number}
        )
        self.total_price = result.scalar()


class Product(Base):
    __tablename__ = 'products_product'
    id: Mapped[int_pk]
    article: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    stock_article: Mapped[str] = mapped_column(String(255), nullable=True, unique=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    gender: Mapped[str] = mapped_column(
        String(255),
        nullable=True,
        default=Gender.UNISEX.value
    )
    main_image: Mapped[str] = mapped_column(Text, nullable=True)
    images_urls: Mapped[dict] = mapped_column(JSON, nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    age_category: Mapped[str] = mapped_column(String(255), nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    color: Mapped[str] = mapped_column(String(255), nullable=False)
    material: Mapped[str] = mapped_column(String(255), nullable=False)
    product_status: Mapped[str] = mapped_column(String(255), nullable=False)
    product_type: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]
    quantity: Mapped[int] = mapped_column(nullable=True, default=0)

    # Додаємо зв'язок з ордерами
    orders: Mapped[List["Order"]] = relationship(
        "Order",
        secondary=order_products,
        back_populates="products"
    )