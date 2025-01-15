from datetime import datetime
from toys_e_commerce.products.models import Product

class ArticleGenerator:
    @staticmethod
    def generate_article():
        prefix = "PR"
        year = str(datetime.now().year)[-2:]
        last_product = Product.objects.filter(
            article__startswith=f"{prefix}{year}"
        ).order_by('-article').first()

        if not last_product:
            new_number = 1
        else:
            try:
                last_number = int(last_product.article[4:])
                new_number = last_number + 1
            except (ValueError, IndexError):
                new_number = 1

        return f"{prefix}{year}{new_number:05d}"