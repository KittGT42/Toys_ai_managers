from django.urls import path
from .views import get_product_price

urlpatterns = [
    path('api/products/price/<str:article>/', get_product_price, name='get_product_price'),
]