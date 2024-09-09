from django.urls import path

from .views import OrderView, OrderByIdView, PaymentView

urlpatterns = [
    path('', OrderView.as_view(), name='orders'),
    path('<int:pk>', OrderByIdView.as_view(), name='get_order_by_id'),
    path('payment/', PaymentView.as_view(), name='payments'),
]
