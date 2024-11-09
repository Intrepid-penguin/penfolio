from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from markdownx.utils import markdownify
from markdownx.models import MarkdownxField

# Create your models here.
    
class Journal(models.Model):
    class Mood(models.TextChoices):
        merry = 'ME', _('Merry')
        gloomy = 'GL', _('Gloomy')
        covert = 'CO', _('Covert')

    title = models.CharField(max_length=100)
    content = MarkdownxField()
    date_added = models.DateTimeField(default=timezone.now)
    mood_tag = models.CharField(max_length=2, choices=Mood.choices, default=Mood.merry)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    
    @property
    def formatted_markdown(self):
        return markdownify(self.content)
    
    def __str__(self):
        return self.title

    
    def get_absolute_url(self):
        return reverse("view-j", kwargs={"pk": self.pk})
