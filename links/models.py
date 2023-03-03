from django.db import models


class Mailing(models.Model):
    google_tag = models.CharField(default='UA-151236093-1', max_length= 255)
    event = models.CharField(default='event', max_length= 255)
    cn_tag = models.CharField(default='hrbrand', max_length= 255)
    cs_tag = models.CharField(default='corpemail', max_length= 255)
    ec_tag = models.CharField(default='email', max_length= 255)
    ea_tag = models.CharField(default='open', max_length= 255)
    el_tag = models.CharField(default='230301rinat', max_length= 255)
    field_name = models.FileField(upload_to='files/')

    def __repr__(self):
        return 'Mailing(%s, %s)' % (self.ea_tag, self.el_tag)

    def __str__ (self):
        return self.el_tag