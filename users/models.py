from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# Create your models here.
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='user_profile')
    current_streak = models.IntegerField(default=0)
    longest_streak = models.IntegerField(default=0)
    last_content_date = models.DateField(null=True, blank=True)
    pin = models.CharField(max_length=500)
    
    def __str__(self):
        return self.user.username
    
@receiver(post_save, sender=User)
def create_covertuser(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
        
@receiver(post_save, sender=User)
def save_covertuser(sender, instance, created, **kwargs):
    instance.user_profile.save()