"""
There are Admin Classes to present in admin interface objects related to accounts
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from .models import UserProfile, TopUpAccount


class UserInline(admin.StackedInline):
    """
    Inline admin class to present User Profile
    """
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'User Profiles'


class UserAdmin(BaseUserAdmin):
    """
    An UserAdmin object encapsulates an instance of the Django User
    with additional fields from model UserProfile
    """
    inlines = (UserInline, )


admin.site.unregister(get_user_model())
admin.site.register(get_user_model(), UserAdmin)


class TopUpAccountAdmin(admin.ModelAdmin):
    """
    An TopUpAccountAdmin object encapsulates an instance of the TopUpAccount
    """
    verbose_name = _('Top Up Account')
    verbose_name_plural = _('Top Up Accounts')
    list_display = (
        'id', 'user', 'amount', 'created_at')
    list_filter = ['created_at']


admin.site.register(TopUpAccount, TopUpAccountAdmin)
