from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.views.generic import DetailView, CreateView, UpdateView, ListView, DeleteView
#from .forms import journalform, Pinform
from .models import Todos
from django.contrib import messages
from django.urls import reverse_lazy
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

# Create your views here.
class TodoBaseListView(LoginRequiredMixin, ListView):
    model = Todos
    context_object_name = 'todos'
    fields = None
    template_name = None
    status = None
    tag = None

class TodoListView(TodoBaseListView):
    template_name = 'todos/index.html'