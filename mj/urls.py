from django.urls import path
from .views import( 
                   home, 
                   createjournalview, 
                   viewJournal, 
                   updateJournal, 
                   MerryJournal, 
                   GloomyJournal,
                   #verify,
                   listCJournal,
                   Search
                ) 

urlpatterns = [
    path('', home.as_view(), name='home'),
    path('create-journal/', createjournalview.as_view(), name='create-j'),
    path('view-journal/<int:pk>', viewJournal.as_view(), name='view-j' ),
    path('update-journal/<int:pk>', updateJournal.as_view(), name='update-j'),
    path('journals-m/', MerryJournal.as_view(), name='m-journals'),
    path('journals-g/', GloomyJournal.as_view(), name='g-journals'),
    path('journals-c/', listCJournal.as_view(), name='c-journals'),
    #path('verify/', verify.as_view(), name='verify'),
    path('search/', Search.as_view(), name='search'),
]