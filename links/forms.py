from django import forms
from .models import Mailing

class MailingForm(forms.ModelForm):

   class Meta:
      model = Mailing
      fields = ['google_tag','event','cn_tag','cs_tag','ec_tag','ea_tag','el_tag','field_name']