from django.contrib import admin
from .models import Mailing

# Register your models here.

@admin.register(Mailing)
class PersonAdmin(admin.ModelAdmin):
    list_display = ("el_tag", "author", "created_at")