from django.db import models
from django.contrib.auth import get_user_model
User=get_user_model()


class Mailing(models.Model):
    author = models.ForeignKey(User, verbose_name='Автор', on_delete=models.CASCADE, default=get_user_model())
    google_tag = models.CharField(default='UA-151236093-1', max_length=255)
    event = models.CharField(default='event', max_length=255)
    cn_tag = models.CharField(default='hrbrand', max_length=255)
    cs_tag = models.CharField(default='corpemail', max_length=255)
    ec_tag = models.CharField(max_length=255)
    ea_tag = models.CharField(max_length=255)
    el_tag = models.CharField(max_length=255)
    field_name = models.FileField(upload_to='files/', verbose_name='Выберите html файл')
    created_at = models.DateTimeField(auto_now_add=True)

    def __repr__(self):
        return 'Замена ссылок'

    def __str__ (self):
        return self.el_tag