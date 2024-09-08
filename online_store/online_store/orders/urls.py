from django.urls import path

from .views import OrderView  # , OrderByIdView

urlpatterns = [
    path('', OrderView.as_view(), name='orders'),
    #path('<int:pk>', OrderByIdView.as_view(), name='get_order_by_id'),
]
