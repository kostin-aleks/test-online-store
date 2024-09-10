"""
products urls
"""

from django.urls import path

from .views import (
    CategoriesView, ProductView, ProductByIdView, InvoiceView, ProductPriceView,
    PriceActionView, DisableActionView,
)

urlpatterns = [
    path('categories', CategoriesView.as_view(), name='categories'),
    path('', ProductView.as_view(), name='products'),
    path('<int:pk>', ProductByIdView.as_view(), name='get_product_by_id'),
    path('invoice', InvoiceView.as_view(), name='invoice'),
    path('<int:pk>/price', ProductPriceView.as_view(), name='product-price'),
    path('action', PriceActionView.as_view(), name='actions'),
    path(
        'action/disable', DisableActionView.as_view(), name='disable-price-action'),
]
