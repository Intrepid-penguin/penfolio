from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# Create your models here.
class Covertuser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='covertuser')
    pin = models.CharField(max_length=50)
    
    def __str__(self):
        return self.user.username
    
@receiver(post_save, sender=User)
def create_covertuser(sender, instance, created, **kwargs):
    if created:
        Covertuser.objects.create(user=instance)
        
@receiver(post_save, sender=User)
def save_covertuser(sender, instance, created, **kwargs):
    instance.covertuser.save()