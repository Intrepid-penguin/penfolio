from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from allauth.account.forms import SignupForm
from django import forms
from .models import UserProfile



class UserRegisterForm(SignupForm):
    
    def save(self, request):
        user = super().save(request)
        return user
       
class CovertuserForm(forms.ModelForm):
    pin = forms.CharField(
            label='pin',
            required=False,
            strip=False,
            max_length=50,
            min_length=4,
            widget=forms.PasswordInput(attrs={"autocomplete": "new-pin"}),
        )
    class Meta:
        model = UserProfile
        fields = ['pin']
