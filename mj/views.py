from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views.generic.edit import FormView
from django.views.generic import DetailView, CreateView
from .forms import journalform
from .models import Journal
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin


# Create your views here.
def home(request):
    return HttpResponse("hello, its time")

class createjournalview(LoginRequiredMixin ,CreateView):
    template_name = 'mj/create.html'
    form_class = journalform
    success_url = '/'
    
    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)
    
class viewjournal(UserPassesTestMixin ,DetailView):
    model = Journal
    template_name = "mj/j-detail.html"
