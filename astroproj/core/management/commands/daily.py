"""Daily housekeeping, for one Railway cron job (e.g. "30 21 * * *" = 03:00 IST): python manage.py daily

Expired order PDFs are not purged here: they live on the web service's volume, which a cron service cannot see.
The web service purges them itself once a day (core/utils/pdf_store.py, DailyHousekeepingMiddleware).
"""
from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Delete expired login sessions."

    def handle(self, *args, **options):
        call_command("clearsessions")
        self.stdout.write(self.style.SUCCESS("Daily housekeeping done."))
