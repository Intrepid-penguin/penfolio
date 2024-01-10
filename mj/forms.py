from django import forms
from .models import Journal


mood = [
    ('ME', 'Merry'),
    ('GL', 'Gloomy'),
    ('CO', 'Covert')
]

class journalform(forms.ModelForm):
    mood_tag = forms.CharField(
                        initial='ME',
                        widget=forms.RadioSelect(choices=mood) 
                    )
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
        self.fields['mood_tag'].widget.attrs.update({
            "type": "radio"
        })
        
    class Meta:
        model = Journal
        fields = ['title', 'content', 'link1', 'link2', 'mood_tag']
        
class Pinform(forms.Form):
    """Pinform definition."""
    pin = forms.CharField(min_length=4 ,max_length=10, label='pin')
    
    