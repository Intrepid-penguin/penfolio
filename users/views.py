from django.shortcuts import redirect
from allauth.account.views import SignupView
from .forms import UserRegisterForm, CovertuserForm
from django.contrib import messages
from django.db import transaction
from django.contrib.auth import logout
from django.contrib.auth.hashers import make_password

from django.views.generic import CreateView
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin


# Create your views here.
class RegisterView(SignupView):
    form_class = UserRegisterForm
    template_name = 'users/auth.html'
    success_url = '/'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'pin_form' not in context:
            context['pin_form'] = CovertuserForm()
        context['sign_up_form'] = context['form']
        return context
    
    def post(self, request, *args, **kwargs):
        self.object = None
        form = self.get_form()
        pin_form = CovertuserForm(request.POST)
        print(form.is_valid(), 'not valid')
        
        if form.is_valid() and pin_form.is_valid():
            return self.form_valid(form, pin_form)
        else:
            return self.form_invalid(form, pin_form)
    
    @transaction.atomic
    def form_valid(self, form, pin_form):
        response = super().form_valid(form)
        print(response)
        user = self.user
        pin = make_password(pin_form.cleaned_data['pin'])
        print(user)
        user.user_profile.pin = pin
        user.user_profile.save()
        
        username = form.cleaned_data.get('username')
        messages.success(self.request, f'Account creation for {username} was successful.')
        
        return response
    
    def form_invalid(self, form, pin_form):
        context = self.get_context_data(form=form, pin_form=pin_form)
        return self.render_to_response(context)

class LogoutView(LoginRequiredMixin, View):
    def get(self, request):
        logout(request)
        return redirect('account_login')
    
    def post(self, request):
        logout(request)
        return redirect('account_login')