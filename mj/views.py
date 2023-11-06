from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.db.models import Q
from django.views.generic.edit import FormView
from django.views.generic import DetailView, CreateView, UpdateView, ListView, TemplateView
from .forms import journalform
from .models import Journal
from django.contrib import messages
#from user.forms import Covertform
from django.urls import reverse_lazy
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

verified = False
# Create your views here.
class home(LoginRequiredMixin, ListView):
    model = Journal
    context_object_name = 'journals'
    fields = ['title', 'date_added', 'mood_tag']
    template_name = 'mj/home.html'
    
    def get_queryset(self):
        user = get_object_or_404(User, username=self.request.user)
        return Journal.objects.filter(owner=user).order_by('-date_added')

class createjournalview(LoginRequiredMixin, CreateView):
    template_name = 'mj/create.html'
    form_class = journalform
    success_url = '/'
    
    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)
    
class viewJournal(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Journal
    template_name = "mj/j-detail.html"
    
    def test_func(self):
        journal = self.get_object()
        return self.request.user == journal.owner 

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            title = self.object.title,
            content = self.object.content,
            date = self.object.date_added,
            link1 = self.object.link1,
            link2 = self.object.link2
         )
        return context
     
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
    
class MerryJournal(LoginRequiredMixin, ListView):
    model = Journal
    context_object_name = 'journals'
    fields = ['title']
    template_name = 'mj/m-journal.html'
    
    # def test_func(self):
    #     journal = self.get_object()
    #     return self.request.user == journal.owner
    
    def get_queryset(self):
        user = get_object_or_404(User, username=self.request.user)
        return Journal.objects.filter(owner=user, mood_tag='ME').order_by('-date_added')
    
class GloomyJournal(LoginRequiredMixin, ListView):
    model = Journal
    context_object_name = 'journals'
    fields = ['title', 'date_added']
    template_name = 'mj/g-journal.html'
    
    def get_queryset(self):
        user = get_object_or_404(User, username=self.request.user)
        return Journal.objects.filter(owner=user, mood_tag='GL').order_by('-date_added')
    
            
class listCJournal(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Journal
    context_object_name = 'journals'
    fields = ['title', 'date_added']
    template_name = 'mj/c-journal.html'
    
    def test_func(self):
        user = get_object_or_404(User, username=self.request.user)
        pin = self.request.GET.get('pin')
        return user.covertuser.pin == int(pin)
    
    def handle_no_permission(self):
        messages.error(self.request, 'oops! you have entered an incorrect pin')
        return redirect(reverse_lazy('home'))
    
    def get_queryset(self):
        user = get_object_or_404(User, username=self.request.user)
        return Journal.objects.filter(owner=user, mood_tag='CO').order_by('-date_added')
    

class Search(LoginRequiredMixin, ListView):
    model = Journal
    context_object_name = 'results'
    fields = ['title', 'date_added']
    template_name = 'mj/search.html'
    
    def get_queryset(self):
        user = get_object_or_404(User, username=self.request.user)
        q = self.request.GET.get('q')
        if q:
            query = Q(title__icontains=q) | Q(content__icontains=q)
        return Journal.objects.filter(query).distinct()