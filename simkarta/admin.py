from django.contrib import admin
from .models import Simkarta

# Register your models here.

@admin.register(Simkarta)
class PersonAdmin(admin.ModelAdmin):
    list_display = ("id_ticket", "author", "created_at")