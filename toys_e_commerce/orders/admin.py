from django.contrib import admin
from django.db.models import Prefetch
from django.core.cache import cache
from django.utils.html import format_html
from .models import Order, OrderProduct


class OrderProductInline(admin.TabularInline):
    model = OrderProduct
    extra = 1
    max_num = 10
    can_delete = True
    raw_id_fields = ('product',)
    readonly_fields = ('get_article', 'product_link')
    fields = ('product','get_article', 'product_link', 'quantity',)
    verbose_name = "товар в замовленні"
    verbose_name_plural = "товари в замовленні"

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        # Для відображення артикула разом з назвою в селекті
        formset.form.base_fields['product'].label_from_instance = lambda prod: f"{prod.article} - {prod.name}"
        return formset


    def get_article(self, obj):
        return obj.product.article if obj.product else '-'
    get_article.short_description = 'Артикул'

    def product_link(self, obj):
        if obj.product:
            url = f'/admin/products/product/{obj.product.id}/change/'
            return format_html('<a href="{}">{}</a>', url, obj.product.name)
        return '-'
    product_link.short_description = 'Назва продукту'

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('product')


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

    def get_inline_instances(self, request, obj=None):
        # Оптимізація для створення нового об'єкту
        if not obj:
            return []
        return super().get_inline_instances(request, obj)

    class Media:
        css = {
            'all': ('admin/css/forms.css',)
        }
        js = (
            'admin/js/vendor/jquery/jquery.min.js',
            'admin/js/jquery.init.js',
            'orders/js/order_total.js',
        )


# @admin.register(OrderProduct)
# class OrderProductAdmin(admin.ModelAdmin):
#     list_display = ['get_order_number', 'get_article', 'product_link', 'quantity']
#     list_select_related = ['order', 'product']
#     search_fields = ['order__order_number', 'product__article', 'product__name']
#     raw_id_fields = ('product',)
#
#     def get_order_number(self, obj):
#         return obj.order.order_number
#     get_order_number.short_description = 'Номер замовлення'
#     get_order_number.admin_order_field = 'order__order_number'
#
#     def get_article(self, obj):
#         return obj.product.article if obj.product else '-'
#     get_article.short_description = 'Артикул'
#     get_article.admin_order_field = 'product__article'
#
#     def product_link(self, obj):
#         if obj.product:
#             url = f'/admin/products/product/{obj.product.id}/change/'
#             return format_html('<a href="{}">{}</a>', url, obj.product.name)
#         return '-'
#     product_link.short_description = 'Назва продукту'
#     product_link.admin_order_field = 'product__name'