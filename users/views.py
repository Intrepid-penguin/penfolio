from django.shortcuts import render, redirect
from .forms import UserRegisterForm, CovertuserForm
from django.contrib import messages
from django.db import transaction
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password, check_password

# Create your views here.
@transaction.atomic
def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        pin_form = CovertuserForm(request.POST)
        if form.is_valid() and pin_form.is_valid():
            user = form.save()
            pin = make_password(pin_form.cleaned_data['pin'])
            print(pin_form.cleaned_data['pin'])
            # if pin_form.cleaned_data['pin'] == '':
            #     pin_form.pin = form.cleaned_data.get('password')
            # pin_form = CovertuserForm(instance=user)
            # print(pin_form.pin)
            user.covertuser.pin = pin
            # print(pin_form.pin)
            user.covertuser.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account creation for Username : { username} was successful.') 
            return redirect('home')
    else:
        form = UserRegisterForm()
        pin_form = CovertuserForm()
    return render(request, 'users/register.html', {'form': form,
                                                    'pin_form': pin_form
                                                   })
@login_required   
def Logout(request):
    logout(request)
    return redirect('login')