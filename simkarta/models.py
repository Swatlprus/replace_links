from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
User=get_user_model()


class Simkarta(models.Model):
    author = models.ForeignKey(User, verbose_name='Автор', on_delete=models.CASCADE, default=get_user_model())
    id_ticket = models.CharField(default='SD-2601850', max_length=11, validators=[RegexValidator('SD-\d*')], verbose_name='Номер тикета')
    created_at = models.DateTimeField(auto_now_add=True)

    def __repr__(self):
        return 'Заявления на симкарту'

    def __str__ (self):
        return self.id_ticket
