"""
There are Admin Classes to present in admin interface objects related to accounts
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model
from .models import UserProfile


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
