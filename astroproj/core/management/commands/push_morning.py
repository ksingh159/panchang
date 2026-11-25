"""python manage.py push_morning - send today's morning panchang notification (also run by `manage.py daily`)."""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Send the morning panchang notification to every subscribed browser."

    def handle(self, *args, **options):
        from core.utils import webpush
        self.stdout.write(f"Morning notification: {webpush.send_morning()}")
