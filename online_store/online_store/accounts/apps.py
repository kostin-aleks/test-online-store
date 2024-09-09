"""
app accounts
"""

from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """accounts config"""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'online_store.accounts'
    verbose_name = 'accounts'
