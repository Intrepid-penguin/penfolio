"""m_journal URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.contrib.auth import views as auth_views
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
    path('login/', auth_views.LoginView.as_view(template_name='users/auth.html'), name='account_login'),
    path('signup/', users_views.RegisterView.as_view(), name='account_signup'),
    path('logout/', users_views.LogoutView.as_view(), name='log-out'),
    path('accounts/', include(filtered_allauth_urls)),
    path('', include('mj.urls')),
    path('todos/', include('todos.urls')),
    # path('users/', include('users.urls')),
    path('markdownx/', include('markdownx.urls')),
    re_path(r"^static/(?P<path>.*)$", serve, {"document_root": settings.STATIC_ROOT}),
]

# if settings.DEBUG:
#     urlpatterns += static(settings.MEDIA_URL,
#                               document_root=settings.MEDIA_ROOT)
