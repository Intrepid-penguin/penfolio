from django.urls import path
from .views import( 
                   home,
                   CreateJournalView as createjournalview,
                   viewJournal, 
                   updateJournal, 
                   MerryJournal, 
                   GloomyJournal,
                   listCJournal,
                   Search,
                   deleteJournal,
                   custom_markdownx_upload,
                    TweetJournalView as tweetify_view,
                    StreakView
                ) 

urlpatterns = [
    path('', home.as_view(), name='home'),
    path('create/', createjournalview.as_view(), name='create-j'),
    path('journal/<int:pk>', viewJournal.as_view(), name='view-j' ),
    path('update/<int:pk>', updateJournal.as_view(), name='update-j'),
    path('delete/<int:pk>', deleteJournal.as_view(), name='delete'),
    path('journal/merry/', MerryJournal.as_view(), name='m-journals'),
    path('journal/gloomy/', GloomyJournal.as_view(), name='g-journals'),
    path('journal/covert/', listCJournal.as_view(), name='c-journals'),
    path('journal/<int:pk>/tweetify/', tweetify_view.as_view(), name='tweetify'),
    path('search/', Search.as_view(), name='search'),
    path('markdownx/upload/', custom_markdownx_upload, name='markdownx_upload'),
    path('streaks/', StreakView.as_view(), name='streaks'),
]
