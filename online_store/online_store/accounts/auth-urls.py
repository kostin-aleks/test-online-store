from django.urls import path

from rest_framework_simplejwt.views import TokenRefreshView

from .views import SignInView, SignUpView


urlpatterns = [
    path('login', SignInView.as_view(), name='login'),
    path('token/refresh', TokenRefreshView.as_view(), name='token_refresh'),
    path('signup', SignUpView.as_view(), name='signup-user'),
]
