from typing import Any, Dict
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.views.generic import DetailView, CreateView, UpdateView, ListView, DeleteView
from .forms import journalform, Pinform
from .models import Journal
from django.contrib import messages
from django.contrib.auth.hashers import check_password
from django.urls import reverse_lazy
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin



# Create your views here
class JournalBaseListView(LoginRequiredMixin, ListView):
    model = Journal
    context_object_name = 'journals'
    fields = None
    template_name = None
    mood_tag = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        data = self.request.GET.get('display')
        context['form'] = Pinform()
        if data != None:
            context['display'] = data
        else:
            context['display'] = 'false'
        print(data, context['display'])
        return context
    
    def get_queryset(self):
        user = get_object_or_404(User, username=self.request.user)
        if self.mood_tag != None:
            return Journal.objects.filter(owner=user, mood_tag=self.mood_tag).order_by('-date_added')
        return Journal.objects.filter(owner=user).order_by('-date_added')

class home(JournalBaseListView):
    fields = ['title', 'date_added', 'mood_tag']
    template_name = 'mj/home.html'

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
    
class deleteJournal(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Journal
    success_url = reverse_lazy('home')
    
    def test_func(self):
        journal = self.get_object()
        return self.request.user == journal.owner

class MerryJournal(JournalBaseListView):
    template_name = 'mj/m-journal.html'
    mood_tag='ME'
    
class GloomyJournal(JournalBaseListView):
    template_name = 'mj/g-journal.html'
    mood_tag='GL'
             
class listCJournal(LoginRequiredMixin, UserPassesTestMixin, ListView):
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
                return 'mj/home.html'
        
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
        return check_password(pin, user.covertuser.pin)
    
    def handle_no_permission(self):
        messages.error(self.request, 'oops! you have entered an incorrect pin or you are unauthourized to view the Covert page')
        view = self.get_route_name()
        data ={'display' : True}
        if '?' in view:
            return redirect(view)
        return redirect(f'{view}?display=true')
    
    def get_queryset(self):
        user = get_object_or_404(User, username=self.request.user)
        return Journal.objects.filter(owner=user, mood_tag='CO').order_by('-date_added')
    

class Search(JournalBaseListView):
    context_object_name = 'results'
    fields = ['title', 'date_added']
    template_name = 'mj/search.html'
    
    def get_queryset(self):
        user = get_object_or_404(User, username=self.request.user)
        q = self.request.GET.get('q')
        if q is not None:
            query = Q(title__icontains=q) | Q(content__icontains=q)
        return Journal.objects.filter(query).distinct()
    
 
# class home(LoginRequiredMixin, ListView):
#     model = Journal
#     context_object_name = 'journals'
#     fields = ['title', 'date_added', 'mood_tag']
#     template_name = 'mj/home.html'
    
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context['form'] = Pinform()
#         return context
    
#     def get_queryset(self):
#         user = get_object_or_404(User, username=self.request.user)
#         return Journal.objects.filter(owner=user).order_by('-date_added')
# 
# class MerryJournal(LoginRequiredMixin, ListView):
#     model = Journal
#     context_object_name = 'journals'
#     fields = None
#     template_name = 'mj/m-journal.html'
    
#     def get_queryset(self):
#         user = get_object_or_404(User, username=self.request.user)
#         return Journal.objects.filter(owner=user, mood_tag='ME').order_by('-date_added')
    
# class GloomyJournal(LoginRequiredMixin, ListView):
#     model = Journal
#     context_object_name = 'journals'
#     fields = ['title', 'date_added']
#     template_name = 'mj/g-journal.html'
    
#     def get_queryset(self):
#         user = get_object_or_404(User, username=self.request.user)
#         return Journal.objects.filter(owner=user, mood_tag='GL').order_by('-date_added')