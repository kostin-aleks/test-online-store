
from django.urls import path

from .views import ProfileView, TopUpAccountView

urlpatterns = [
    path('profile', ProfileView.as_view(), name='profile'),
    path('topup/account', TopUpAccountView.as_view(), name='top-up-account'),
]
