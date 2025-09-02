from datetime import timedelta, timezone
from html import escape
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.views.generic import DetailView, CreateView, UpdateView, ListView, DeleteView

from users.models import UserProfile
from .forms import journalform, Pinform
from .models import Journal
from django.contrib import messages
from django.contrib.auth.hashers import check_password
from django.urls import reverse_lazy
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
import cloudinary.uploader
from django.http import JsonResponse
from django.views import View
from django.utils.http import urlencode
from .utils import generate_tweet, get_twitter_inspo
from collections import defaultdict
from datetime import date



# Create your views here
class HomePage(View):
    template_name='home.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

class JournalBaseListView(LoginRequiredMixin, ListView):
    model = Journal
    context_object_name = 'journals'
    fields = None
    template_name = None
    mood_tag = None
    paginate_by = 5  # Show 10 journals per page
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        data = self.request.GET.get('display')
        context['form'] = Pinform()
        if data is not None:
            context['display'] = data
        else:
            context['display'] = 'false'
        print(data, context['display'])
        return context
    
    def get_queryset(self):
        user = get_object_or_404(User, username=self.request.user)
        if self.mood_tag is not None:
            return Journal.objects.filter(owner=user, mood_tag=self.mood_tag).order_by('-date_added')
        return Journal.objects.filter(owner=user).order_by('-date_added')

class Dashboard(JournalBaseListView):
    fields = ['title', 'date_added', 'mood_tag']
    template_name = 'mj/dashboard.html'

class CreateJournalView(LoginRequiredMixin, CreateView):
    template_name = 'mj/create.html'
    form_class = journalform
    success_url = '/dashboard/'
    
    def form_valid(self, form):
        form.instance.owner = self.request.user
        print(form.cleaned_data['mood_tag'])
        if form.cleaned_data['mood_tag'] == 'CO':
            if not self.request.user.user_profile.pin:
                messages.info(self.request, 'You must set a PIN in your profile to create a Covert journal.')
            return self.render_to_response(self.get_context_data(form=form))
        response = super().form_valid(form)
    
        journal = self.object
        self.update_streak(journal)
        
        return response

    def update_streak(self, journal):
        """Update user's streak based on the journal creation date"""
        user = self.request.user
        user_profile, created = UserProfile.objects.get_or_create(user=user)
        
        journal_date = journal.date_added.date()
        
        if user_profile.last_content_date == journal_date:
            return  # Already counted for today
        
        if user_profile.last_content_date:
            # Check if consecutive day
            if user_profile.last_content_date == journal_date - timedelta(days=1):
                user_profile.current_streak += 1
            else:
                # Reset streak if not consecutive
                user_profile.current_streak = 1
        else:
            # First journal entry
            user_profile.current_streak = 1
        
        # Update longest streak if needed
        if user_profile.current_streak > user_profile.longest_streak:
            user_profile.longest_streak = user_profile.current_streak
        
        # Update last content date
        user_profile.last_content_date = journal_date
        user_profile.save()
    
class viewJournal(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Journal
    template_name = "mj/j-detail.html"
    form_class = Pinform
    
    def test_func(self):
        journal = self.get_object()
        if journal.mood_tag == 'CO':
            return self.request.user == journal.owner
        return self.request.user == journal.owner
    
    def get(self, request, *args, **kwargs):
        journal = self.get_object()
        if journal.mood_tag == 'CO':
            if not request.user.user_profile.pin:
                messages.error(request, 'You need to set a pin to view covert journals.')
                return redirect('/')

            session_key = f'covert_journal_verified_{journal.id}'
            if not request.session.get(session_key, False):
                messages.error(request, 'Unauthorized access to covert journal. Why are you trying to peek?')
                return redirect('/')
        
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        journal = self.get_object()
        if journal.mood_tag == 'CO':
            form = self.form_class(request.POST)
            if form.is_valid():
                pin = request.POST.get('pin')
                    
                if check_password(pin, self.request.user.user_profile.pin):
                    session_key = f'covert_journal_verified_{journal.id}'
                    request.session[session_key] = True
                    return super().get(request, *args, **kwargs)
                else:
                    messages.error(request, 'Incorrect pin entered')
                    return redirect('/')
            else:
                messages.error(request, 'Incorrect pin entered')
                return redirect('/')
        return super().post(request, *args, **kwargs)

    def dispatch(self, request, *args, **kwargs):
        journal = self.get_object()
        session_key = f'covert_journal_verified_{journal.id}'
        
        # If this is a GET request and not the initial load, clear the session
        if request.method == 'GET' and request.META.get('HTTP_REFERER'):
            if session_key in request.session:
                del request.session[session_key]
        
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        journal = self.get_object()
        
        if journal.mood_tag == 'CO' and self.request.method != 'POST':
            context['requires_pin'] = True
            context['form'] = self.form_class()
        
        context.update(
            title = self.object.title,
            content = self.object.content,
            date = self.object.date_added,
         )
        print(context)
        return context
    
class TweetJournalView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    A view to handle converting a journal entry into a tweet.
    On POST, it constructs a Twitter intent URL with the journal's content
    and redirects the user to Twitter to post it.
    """
    def test_func(self):
        journal = self.get_journal()
        # Ensure the user owns the journal and it's not a covert entry
        return journal.owner == self.request.user and journal.mood_tag != 'CO'

    def handle_no_permission(self):
        messages.error(self.request, "You are not authorized to tweet this journal, or it is a covert journal.")
        return redirect('dashboard')

    def get_journal(self):
        if not hasattr(self, '_journal'):
            pk = self.kwargs.get('pk')
            self._journal = get_object_or_404(Journal, pk=pk)
        return self._journal

    def post(self, request, *args, **kwargs):
        journal = self.get_journal()

        x_user_inspo = request.POST.get('twitter-handle', '').strip()
        print(x_user_inspo)
        
        print(f"Received inspiration: {x_user_inspo}")
        
        x_user_tweet = get_twitter_inspo(x_user_inspo, scrolls=10, proxy=None)
        
        if x_user_tweet is None:
            messages.error(request, f"Could not find tweets for user {x_user_inspo} or user doesn't exist.")
            return redirect('view-j', pk=journal.pk)
        
        tweet = generate_tweet(x_user_tweet, journal.content)
        print(f"Generated tweet: {tweet}")

        # Construct the Twitter intent URL
        base_url = "https://twitter.com/intent/tweet"
        params = urlencode({'text': tweet})
        tweet_url = f"{base_url}?{params}"

        return redirect(tweet_url)

    def get(self, request, *args, **kwargs):
        pk = self.kwargs.get('pk')
        return redirect('view-j', pk=pk)
     
class updateJournal(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Journal
    form_class = journalform
    template_name = 'mj/j-update.html'
    
    def test_func(self):
        journal = self.get_object()
        return self.request.user == journal.owner
    
    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)
    
class deleteJournal(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Journal
    success_url = reverse_lazy('dashboard')
    
    def test_func(self):
        journal = self.get_object()
        return self.request.user == journal.owner

class MerryJournal(JournalBaseListView):
    template_name = 'mj/m-journal.html'
    mood_tag='ME'
    
class GloomyJournal(JournalBaseListView):
    template_name = 'mj/g-journal.html'
    mood_tag='GL'
             
class listCJournal(UserPassesTestMixin, JournalBaseListView):
    model = Journal
    context_object_name = 'journals'
    fields = ['title', 'date_added']
    form_class = Pinform
    template_name = 'mj/c-journal.html'
    
    def tempelate_name(self):
        route_name = self.get_route_name()        
        match route_name:
            case 'm-journals':
                return 'mj/m-journal.html'
            case 'g-journals':
                return 'mj/g-journal.html'
            case _:
                return 'mj/dashboard.html'
        
    def get_route_name(self):
        route_name = self.request.META.get('HTTP_REFERER')
        return route_name[21:]
    
    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            return self.get(self, request, *args, **kwargs)
        else:
            form = self.form_class()
            template = self.tempelate_name()
            return render(request, template, {'form': form})
    
    def test_func(self):
        user = get_object_or_404(User, username=self.request.user)
        pin = self.request.POST.get('pin')
        return check_password(pin, user.user_profile.pin)
    
    def handle_no_permission(self):
        messages.error(self.request, 'oops! you have entered an incorrect pin or you are unauthourized to view the Covert page')
        view = self.get_route_name()
        if '?' in view:
            return redirect(view)
        return redirect(f'{view}?display=true')
    
    def get_queryset(self):
        user = get_object_or_404(User, username=self.request.user)
        return Journal.objects.filter(owner=user, mood_tag='CO').order_by('-date_added')

class StreakView(LoginRequiredMixin, View):
    template_name = 'mj/streak.html'

    def get(self, request, *args, **kwargs):
        user = request.user
        user_profile, created = UserProfile.objects.get_or_create(user=user)
        
        journals = Journal.objects.filter(owner=user).order_by('date_added')
        
        contributions = defaultdict(int)
        for journal in journals:
            contributions[journal.date_added.date()] += 1
            
        today = date.today()
        start_date = today - timedelta(days=365)
        
        # Generate a list of all days in the past year
        days_data = []
        current_date = start_date
        while current_date <= today:
            days_data.append({
                'date': current_date,
                'count': contributions.get(current_date, 0)
            })
            current_date += timedelta(days=1)
        
        # Get month names for the header
        month_names = []
        last_month = -1
        for day_data in days_data:
            day = day_data['date']
            if day.month != last_month:
                month_names.append(day.strftime('%b'))
                last_month = day.month

        context = {
            'current_streak': user_profile.current_streak,
            'longest_streak': user_profile.longest_streak,
            'days_data': days_data,
            'month_names': month_names,
            'today': today,
        }
        
        return render(request, self.template_name, context)

class Search(JournalBaseListView):
    context_object_name = 'results'
    fields = ['title', 'date_added']
    template_name = 'mj/search.html'
    
    def get_queryset(self):
        user = get_object_or_404(User, username=self.request.user)
        q = escape(self.request.GET.get('q'))
        print(q)
        if q is not None:
            query = Q(title__icontains=q) | Q(content__icontains=q)
        return Journal.objects.filter(query).distinct()
    
 
def custom_markdownx_upload(request):
    if request.method == 'POST' and request.FILES.get('image'):
        upload = request.FILES['image']
        cloudinary.config(
            cloud_name= 'dh9zsffcy',
            api_key= '442972459732815',
            api_secret= '13CWZag20_99j70upV8r8kU_8ns'
        )

        # Upload image to Cloudinary
        result = cloudinary.uploader.upload(
            upload,
            transformation={
                'width': 800,  # Set desired width
                'height': 800,  # Set desired height
                'crop': 'limit',  # Ensures the image is not stretched
            }
        )
        # Get the secure URL of the uploaded image
        image_url = result['secure_url']
        # Return the URL in a format that Markdownx expects
        return JsonResponse({'image_code': f'![alt text]({image_url})'})
    return JsonResponse({'error': 'Upload failed'}, status=400)

def update_streak_on_creation(user):
    """Updates the current and longest streak for a user when content is created."""
    try:
        user_profile = user.user_profile
    except UserProfile.DoesNotExist:
        return  # Should not happen due to signals, but for safety

    today = timezone.now().date()

    if user_profile.last_content_date == today:
        # User already created content today, no streak change
        return

    if user_profile.last_content_date == today - timedelta(days=1):
        # Streak continues
        user_profile.current_streak += 1
    else:
        # Streak broken or this is the first content
        user_profile.current_streak = 1

    user_profile.longest_streak = max(user_profile.longest_streak, user_profile.current_streak)
    user_profile.last_content_date = today
    user_profile.save()
    
def update_streak_based_on_journal(user, journal):
    """Update streak based on the journal's actual creation date"""
    try:
        user_profile = user.user_profile
    except UserProfile.DoesNotExist:
        return

    journal_date = journal.date_added.date()
    
    if user_profile.last_content_date == journal_date:
        return

    if user_profile.last_content_date == journal_date - timedelta(days=1):
        user_profile.current_streak += 1
    else:
        user_profile.current_streak = 1

    user_profile.longest_streak = max(user_profile.longest_streak, user_profile.current_streak)
    user_profile.last_content_date = journal_date
    user_profile.save()
