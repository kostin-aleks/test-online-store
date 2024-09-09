"""
app general
"""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class GeneralConfig(AppConfig):
    """config for general"""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'online_store.general'
    verbose_name = _('general')
