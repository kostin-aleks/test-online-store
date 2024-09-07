from django.urls import path

from .views import CategoriesView, ProductView

urlpatterns = [
    path('categories', CategoriesView.as_view(), name='categories'),
    path('', ProductView.as_view(), name='products'),
]
