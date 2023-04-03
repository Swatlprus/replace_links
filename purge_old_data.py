from django.core.management.base import BaseCommand, CommandError
from links.models import Mailing 
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = 'Delete objects older than 25 days'

    def handle(self, *args, **options):
        Mailing.objects.filter(created_at__lte=datetime.now()-timedelta(days=25)).delete()
        self.stdout.write('Deleted objects older than 25 days')