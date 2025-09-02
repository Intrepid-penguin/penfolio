"""m_journal URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.dashboard, name='dashboard')
Class-based views
    1. Add an import:  from other_app.views import dashboard
    2. Add a URL to urlpatterns:  path('', dashboard.as_view(), name='dashboard')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.contrib.auth import views as auth_views
from mj.views import HomePage
from users import views as users_views
from django.conf.urls.static import static
from django.conf import settings
from django.views.static import serve
from allauth.account.urls import urlpatterns as original_allauth_urls
from allauth.socialaccount.providers.oauth2.urls import default_urlpatterns
from allauth.socialaccount.providers.twitter_oauth2.provider import TwitterOAuth2Provider


filtered_allauth_urls = [
    url for url in original_allauth_urls 
    if url.name not in ['account_login', 'account_signup', 'account_logout']
] + [
    path('', include('allauth.socialaccount.urls')),
    path("3rdparty/", include("allauth.socialaccount.urls"))
] + default_urlpatterns(TwitterOAuth2Provider)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('users.urls')),
    path('accounts/', include(filtered_allauth_urls)),
    path('', HomePage.as_view(), name='home-page'),
    path('dashboard/', include('mj.urls')),
    path('todos/', include('todos.urls')),
    path('markdownx/', include('markdownx.urls')),
    re_path(r"^static/(?P<path>.*)$", serve, {"document_root": settings.STATIC_ROOT}),
]

# if settings.DEBUG:
#     urlpatterns += static(settings.MEDIA_URL,
#                               document_root=settings.MEDIA_ROOT)
