from django.urls import path
from .views import RegisterView, UserLoginView, LogoutView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='account_signup'),
    path('login/', UserLoginView.as_view(), name='account_login'),
    path('logout/', LogoutView.as_view(), name='log-out'),
]
