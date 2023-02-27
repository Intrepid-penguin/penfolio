from django.urls import path
from .views import home, createjournalview

urlpatterns = [
    path('', home, name='home'),
    path('create-journal/', createjournalview.as_view(), name='create-j')
]