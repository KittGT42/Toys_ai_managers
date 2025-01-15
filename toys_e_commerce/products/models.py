from django.db import models

class Product(models.Model):
    article = models.CharField(max_length=255, unique=True)
    stock_article = models.CharField(max_length=255, unique=True, null=True)
    name = models.TextField()
    gender = models.CharField(max_length=255, null=True)
    main_image = models.TextField(null=True)
    images_urls = models.JSONField(null=True)
    description = models.TextField(null=True)
    age_category = models.CharField(max_length=255, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    color = models.CharField(max_length=255)
    material = models.CharField(max_length=255)
    product_status = models.CharField(max_length=255)
    product_type = models.CharField(max_length=255)
    quantity = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.article})"