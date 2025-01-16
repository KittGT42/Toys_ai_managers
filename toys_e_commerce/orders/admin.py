from django.contrib import admin
from django.db.models import Prefetch
from django.core.cache import cache
from django.utils.html import format_html
from .models import Order, OrderProduct
from products.models import Product

class OrderProductInline(admin.TabularInline):
    model = OrderProduct
    extra = 1
    max_num = 10
    can_delete = True
    raw_id_fields = ('product',)  # Використовуємо raw_id_fields для popup вікна пошуку
    readonly_fields = ('get_article', 'get_name', 'get_price')
    fields = ('product', 'get_article', 'get_name', 'get_price', 'quantity')  # Змінили порядок полів
    verbose_name = "товар в замовленні"
    verbose_name_plural = "товари в замовленні"

    def get_article(self, obj):
        if obj.product:
            return format_html(
                '<a href="#" onclick="return showProductPopup(\'{}\');">{}</a>',
                obj.product.id,
                obj.product.article
            )
        return '-'
    get_article.short_description = 'Артикул'
    get_article.allow_tags = True

    def get_name(self, obj):
        return obj.product.name if obj.product else '-'
    get_name.short_description = 'Назва продукту'

    def get_price(self, obj):
        return f"{obj.product.price} грн" if obj.product else '-'
    get_price.short_description = 'Ціна'

    class Media:
        js = ('admin/js/vendor/jquery/jquery.min.js',
              'admin/js/jquery.init.js',
              'orders/js/order_product_search.js',)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'user', 'status', 'total_price', 'created_at']
    list_select_related = ['user']
    list_filter = ['status', 'created_at']
    readonly_fields = ['order_number', 'user', 'delivery_address', 'total_price', 'created_at', 'updated_at']
    fields = ['order_number', 'user', 'delivery_address', 'status', 'total_price', 'created_at', 'updated_at']
    search_fields = ['order_number', 'user__full_name']
    inlines = [OrderProductInline]

    def get_queryset(self, request):
        cache_key = f'order_admin_queryset_{request.user.id}'
        queryset = cache.get(cache_key)

        if queryset is None:
            queryset = super().get_queryset(request)
            queryset = queryset.select_related('user').prefetch_related(
                Prefetch(
                    'orderproduct_set',
                    queryset=OrderProduct.objects.select_related('product')
                )
            )
            cache.set(cache_key, queryset, 60)
        return queryset

    class Media:
        css = {'all': ('admin/css/forms.css',)}