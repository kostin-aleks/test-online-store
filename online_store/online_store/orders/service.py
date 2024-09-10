"""
orders services
"""

from .models import Order, OrderItem


def cancel_orders_by_product(product):
    """
    cancel new orders for deleted product
    """
    for order_item in OrderItem.objects.filter(product=product).filter(
            order__moderation_status=Order.Statuses.NEW):
        order_item.order.status = Order.Statuses.REJECTED_BY_MANAGER
        order_item.order.save()
