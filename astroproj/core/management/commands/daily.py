"""Daily housekeeping, for one Railway cron job (e.g. "30 21 * * *" = 03:00 IST): python manage.py daily

Expired order PDFs are not purged here: they live on the web service's volume, which a cron service cannot see.
The web service purges them itself once a day (core/utils/pdf_store.py, DailyHousekeepingMiddleware).
"""
from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Delete expired login sessions and refill the grahan cache."

    def handle(self, *args, **options):
        call_command("clearsessions")
        # Cached globe data lasts 90 days and the cache can cull entries, and the year window moves every
        # 1 January; refilling nightly means a visitor never pays for the calculation.
        call_command("precompute_grahan")
        self.stdout.write(self.style.SUCCESS("Daily housekeeping done."))
