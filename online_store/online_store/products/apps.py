"""
app products
"""

from django.apps import AppConfig


class ProductsConfig(AppConfig):
    """confif for products"""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'online_store.products'
    verbose_name = 'products'
