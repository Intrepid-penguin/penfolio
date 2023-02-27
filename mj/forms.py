from django import forms
from .models import Journal
from django.forms import ModelForm

class journalform(forms.ModelForm):
    class Meta:
        model = Journal
        fields = "__all__"
    




 