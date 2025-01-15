from django.db import models
from users.models import User
from products.models import Product


class Order(models.Model):
    ORDER_STATUS = (
        ('new', 'New'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )

    order_number = models.CharField(max_length=255, unique=True, db_index=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    delivery_address = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=ORDER_STATUS, default='new', db_index=True)
    products = models.ManyToManyField(Product, through='OrderProduct')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['status', 'created_at'], name='order_status_created_idx'),
        ]

    def calculate_total_price(self):
        total = sum(
            order_product.quantity * order_product.product.price
            for order_product in self.orderproduct_set.select_related('product').all()
        )
        self.total_price = total
        self.save(update_fields=['total_price'])


class OrderProduct(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.order.calculate_total_price()

    def delete(self, *args, **kwargs):
        order = self.order
        super().delete(*args, **kwargs)
        order.calculate_total_price()

    def __str__(self):
        return f"{self.product.name if self.product else 'No product'}"

    class Meta:
        verbose_name = 'Товар в замовленні'
        verbose_name_plural = 'Товари в замовленні'
        indexes = [
            models.Index(fields=['order', 'product'], name='order_product_idx'),
        ]