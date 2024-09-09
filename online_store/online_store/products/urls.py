"""
products urls
"""

from django.urls import path

from .views import CategoriesView, ProductView, ProductByIdView, InvoiceView

urlpatterns = [
    path('categories', CategoriesView.as_view(), name='categories'),
    path('', ProductView.as_view(), name='products'),
    path('<int:pk>', ProductByIdView.as_view(), name='get_product_by_id'),
    path('invoice', InvoiceView.as_view(), name='invoice'),
]
