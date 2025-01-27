from django.db import models

class Product(models.Model):
    article = models.CharField(max_length=255, unique=True, db_index=True)
    stock_article = models.CharField(max_length=255, unique=True, null=True, db_index=True)
    name = models.TextField()
    gender = models.CharField(max_length=255, null=True)
    main_image = models.TextField(null=True)
    images_urls = models.JSONField(null=True)
    description = models.TextField(null=True)
    age_category = models.CharField(max_length=255, null=True, db_index=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, db_index=True)
    color = models.CharField(max_length=255, db_index=True)
    material = models.CharField(max_length=255)
    product_status = models.CharField(max_length=255, db_index=True)
    product_type = models.CharField(max_length=255, db_index=True)
    quantity = models.IntegerField(default=0, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    age_category_years = models.FloatField(null=True, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=['price', 'product_type'], name='product_price_type_idx'),
            models.Index(fields=['price', 'product_status'], name='product_price_status_idx'),
        ]

    def __str__(self):
        return f"{self.name}"