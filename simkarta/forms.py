import re
from django import forms
from .models import Simkarta
from django.core.exceptions import ValidationError


class SimkartaForm(forms.ModelForm):
    class Meta:
        model = Simkarta
        fields = ['author', 'id_ticket']
