from django import forms


class MailingForm(forms.Form):
   google_tag = forms.CharField(label='Google Tag', initial='UA-151236093-1', max_length=255)
   event = forms.CharField(label='Event', initial='event', max_length=255)
   cn_tag = forms.CharField(label='HR Brand', initial='hrbrand', max_length=255)
   cs_tag = forms.CharField(label='Corp Email', initial='corpemail', max_length=255)
   ec_tag = forms.CharField(label='EC Tag', initial='ec_tag', max_length=255)
   ea_tag = forms.CharField(label='EA Tag', initial='ea_tag', max_length=255)
   el_tag = forms.CharField(label='EL Tag', max_length=255)
   html_letter = forms.FileField(label='Выберите HTML файл')