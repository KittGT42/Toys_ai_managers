from django.views.generic import ListView
from .models import Product
from django.db.models import Q

class ProductSearchView(ListView):
    model = Product
    template_name = 'admin/product_search_popup.html'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        search_term = self.request.GET.get('q', '')
        if search_term:
            queryset = queryset.filter(
                Q(article__icontains=search_term) |
                Q(name__icontains=search_term)
            )
        return queryset