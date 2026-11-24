"""Daily jobs, for one Railway cron job at "0 0 * * *" (= 05:30 IST): python manage.py daily

It first builds today's /aaj-ka-panchang/ page, so the page's "Updated 05:30 IST" is when it was really computed,
then does the housekeeping.

Expired order PDFs are not purged here: they live on the web service's volume, which a cron service cannot see.
The web service purges them itself once a day (core/utils/pdf_store.py, DailyHousekeepingMiddleware).
"""
from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Build today's Aaj Ka Panchang, delete expired sessions and unclaimed guest kundalis, refill the grahan cache."

    def handle(self, *args, **options):
        from core.utils import aaj_panchang
        snap = aaj_panchang.build()
        self.stdout.write(f"Aaj Ka Panchang for {snap['date']} built at {snap['computed_at']:%H:%M} IST")
        from core.utils import indexnow
        self.stdout.write(f"IndexNow: {indexnow.ping_today()}")
        call_command("clearsessions")
        from core.view_kundali import purge_guest_kundalis
        self.stdout.write(f"Guest kundalis older than 30 days deleted: {purge_guest_kundalis()}")
        # Cached globe data lasts 90 days and the cache can cull entries, and the year window moves every
        # 1 January; refilling nightly means a visitor never pays for the calculation.
        call_command("precompute_grahan")
        self.stdout.write(self.style.SUCCESS("Daily housekeeping done."))
