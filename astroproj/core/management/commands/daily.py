"""Daily housekeeping, for one Railway cron job (e.g. "30 21 * * *" = 03:00 IST): python manage.py daily"""
from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Delete expired order PDFs and expired login sessions."

    def handle(self, *args, **options):
        call_command("purge_order_pdfs")
        call_command("clearsessions")
        self.stdout.write(self.style.SUCCESS("Daily housekeeping done."))
