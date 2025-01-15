from django.contrib import admin
from django.db.models import Q
from .models import Product
from django import forms

class ProductSearchForm(forms.Form):
    search_field = forms.ChoiceField(
        choices=(
            ('name', 'Назва'),
            ('article', 'Артикул'),
            ('price', 'Ціна'),
            ('quantity', 'Кількість'),
        ),
        required=False,
        label='Шукати по'
    )
    search_query = forms.CharField(required=False, label='Пошуковий запит')


class PriceFilter(admin.SimpleListFilter):
    title = 'Ціновий діапазон'
    parameter_name = 'price_range'

    def lookups(self, request, model_admin):
        return (
            ('lt_100', 'Менше 100'),
            ('100_500', '100-500'),
            ('500_1000', '500-1000'),
            ('gt_1000', 'Більше 1000'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'lt_100':
            return queryset.filter(price__lt=100)
        if self.value() == '100_500':
            return queryset.filter(price__gte=100, price__lte=500)
        if self.value() == '500_1000':
            return queryset.filter(price__gte=500, price__lte=1000)
        if self.value() == 'gt_1000':
            return queryset.filter(price__gt=1000)


class QuantityFilter(admin.SimpleListFilter):
    title = 'Кількість'
    parameter_name = 'quantity_range'

    def lookups(self, request, model_admin):
        return (
            ('lt_5', 'Менше 5'),
            ('5_10', '5-10'),
            ('10_20', '10-20'),
            ('gt_20', 'Більше 20'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'lt_5':
            return queryset.filter(quantity__lt=5)
        if self.value() == '5_10':
            return queryset.filter(quantity__gte=5, quantity__lte=10)
        if self.value() == '10_20':
            return queryset.filter(quantity__gte=10, quantity__lte=20)
        if self.value() == 'gt_20':
            return queryset.filter(quantity__gt=20)


class ProductAdmin(admin.ModelAdmin):
    list_display = ('article', 'name', 'price', 'quantity')
    search_fields = ('article', 'name')
    list_filter = (PriceFilter, QuantityFilter)

    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)

        try:
            price_value = float(search_term)
            queryset |= self.model.objects.filter(
                Q(price__gte=price_value) | Q(price__lte=price_value)
            )
        except ValueError:
            pass

        return queryset, use_distinct


admin.site.register(Product, ProductAdmin)