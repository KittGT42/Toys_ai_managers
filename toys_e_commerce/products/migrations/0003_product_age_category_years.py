# Generated by Django 5.1.5 on 2025-02-05 05:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0002_alter_product_age_category_alter_product_article_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='age_category_years',
            field=models.FloatField(db_index=True, null=True),
        ),
    ]
