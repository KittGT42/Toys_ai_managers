from django.http import JsonResponse
from products.models import Product

def get_product_price(request, article):
    try:
        product = Product.objects.get(article=article)
        return JsonResponse({'price': float(product.price)})
    except Product.DoesNotExist:
        return JsonResponse({'error': 'Product not found'}, status=404)