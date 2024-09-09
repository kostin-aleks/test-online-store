"""
app orders
"""

from django.apps import AppConfig


class OrdersConfig(AppConfig):
    """orders config"""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'online_store.orders'
    verbose_name = 'orders'
