from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from markdownx.utils import markdownify
from markdownx.models import MarkdownxField
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from cryptography.fernet import Fernet, InvalidToken

class EncryptedMdxField(MarkdownxField):
    """
    Encrypts data when saving to the database and decrypts when retrieving.
    """
    
    def __init__(self, *args, **kwargs):
        key = settings.ENCRYPTION_KEY
        
        if not key:
            raise ImproperlyConfigured("ENCRYPTION_KEY must be set in settings.")
        if isinstance(key, str):
            key = key.encode()
        try:
            self.fernet = Fernet(key)
        except ValueError as e:
            raise ImproperlyConfigured(f"Invalid ENCRYPTION_KEY: {e}")
        super().__init__(*args, **kwargs)
    
    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        try:
            return markdownify(self.fernet.decrypt(value.encode()).decode())
        except InvalidToken:
            raise ValueError("Decryption failed. Invalid or corrupted data.")
    
    def get_prep_value(self, value):
        if value is None:
            return value
        return self.fernet.encrypt(value.encode()).decode()

class Journal(models.Model):
    class Mood(models.TextChoices):
        merry = 'ME', _('Merry')
        gloomy = 'GL', _('Gloomy')
        covert = 'CO', _('Covert')

    title = models.CharField(max_length=100)
    content = EncryptedMdxField()
    date_added = models.DateTimeField(default=timezone.now)
    mood_tag = models.CharField(max_length=2, choices=Mood.choices, default=Mood.merry)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    
    def __str__(self):
        return self.title

    
    def get_absolute_url(self):
        return reverse("view-j", kwargs={"pk": self.pk})