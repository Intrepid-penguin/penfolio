from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

# Create your models here.
class Todos(models.Model):
    class Tags(models.TextChoices):
        low = 'LO', _('Low')
        medium = 'ME', _('Medium')
        high = 'HI', _('High')
        urgent = 'UR', _('Urgent')
    class Status(models.TextChoices):
        completed = 'CO', _('Completed')
        pending = 'PE', _('Pending')
        progress = 'IN', _('In-progress')
    title= models.CharField(max_length=50)
    description = models.CharField(max_length=100)
    due_date = models.DateField(auto_now=False, auto_now_add=False)
    date_added = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=2, choices=Status.choices, default=Status.pending)
    tag = models.CharField(max_length=2, choices=Tags.choices, default=Tags.low)
    # owner = models.ForeignKey(User, on_delete=models.CASCADE)
    
    
    def __str__(self):
        return self.title

    class Meta:
        verbose_name_plural = 'Todos'