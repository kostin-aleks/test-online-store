"""
There are Admin Classes to present in admin interface objects related to products
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Order, OrderItem, Payment


class PaymentAdmin(admin.ModelAdmin):
    """
    An PaymentAdmin object encapsulates an instance of the Payment
    """
    verbose_name = _('Payment')
    verbose_name_plural = _('Payments')
    list_display = (
        'id', 'created_at', 'client', 'order', 'amount')
    list_filter = ['created_at']


admin.site.register(Payment, PaymentAdmin)


class OrderItemInline(admin.StackedInline):
    """
    Inline admin class to present Order Item
    """
    model = OrderItem
    verbose_name = 'Order Item'
    verbose_name_plural = 'Order Items'


class OrderAdmin(admin.ModelAdmin):
    """
    An OrderAdmin object encapsulates an instance of the Order
    with additional list of OrderItem
    """
    list_display = (
        'id', 'created_at', 'client', 'amount', 'moderation_status')
    inlines = (OrderItemInline, )
    list_filter = ['moderation_status', 'created_at']


admin.site.register(Order, OrderAdmin)
