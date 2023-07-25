from django import forms
from django.core.validators import RegexValidator


class SimcardsForm(forms.Form):
    ticket = forms.CharField(max_length=11, label='Введите номер тикета с SD',
                             validators=[RegexValidator(r'SD-\d*')])
