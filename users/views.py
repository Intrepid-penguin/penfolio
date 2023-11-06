from django.shortcuts import render, redirect
from .forms import UserRegisterForm, CovertuserForm
from django.contrib import messages
from django.db import transaction

# Create your views here.
@transaction.atomic
def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        pin_form = CovertuserForm(request.POST)
        if form.is_valid() and pin_form.is_valid():
            user = form.save()
            pin_form = CovertuserForm(request.POST, instance=user)
            pin_form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account creation for Username : { username} was successful.') 
            return redirect('home')
    else:
        form = UserRegisterForm()
        pin_form = CovertuserForm()
    return render(request, 'users/register.html', {'form': form,
                                                    'pin_form': pin_form
                                                   })