from django.contrib import admin
from .models import Journal
from markdownx.admin import MarkdownxModelAdmin


# Register your models here.


admin.site.register(Journal, MarkdownxModelAdmin)

