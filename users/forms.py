from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django import forms
from .models import UserProfile



class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()
    
    class Meta:
       model = User
       fields = ['username', 'email', 'password1', 'password2']
       
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