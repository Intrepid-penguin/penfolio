from django.urls import path
from . import views

urlpatterns = [
    # URL to redirect the user to Twitter for authorization
    path('twitter/authorize/', views.twitter_authorize, name='twitter_authorize'),

    # URL Twitter redirects back to after user authorization (Callback URL)
    path('twitter/callback/', views.twitter_callback, name='twitter_callback'),

    # Example page showing a link to start authorization
    path('connect/', views.connect_page, name='connect_page'),

    # Example success page
    path('success/', views.success_page, name='success_page'),
]