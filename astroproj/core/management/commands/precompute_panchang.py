"""
Warm the shared panchang + festival cache so every search is instant.

    python manage.py precompute_panchang                 # 1950-2100
    python manage.py precompute_panchang --start 1900 --end 2200 --festivals

~1 s per year for panchang events, ~0.5 s per year for festivals.
Safe to re-run: years already computed are skipped.
"""
import time

from django.core.management.base import BaseCommand

from core.utils import festival_calculations as fc
from core.utils import panchang_store as ps


class Command(BaseCommand):
    help = "Precompute panchang events (and optionally festivals) for a range of years"

    def add_arguments(self, parser):
        parser.add_argument("--start", type=int, default=1950)
        parser.add_argument("--end", type=int, default=2100)
        parser.add_argument("--festivals", action="store_true", help="also build the festival cache")

    def handle(self, *args, **o):
        t0 = time.time()
        for y in range(o["start"], o["end"] + 1):
            new = ps.ensure_year(y)
            fest = fc.ensure_festivals(y) if o["festivals"] else False
            if new or fest:
                self.stdout.write(f"{y}: {'events ' if new else ''}{'festivals' if fest else ''}")
        self.stdout.write(self.style.SUCCESS(f"Done in {time.time() - t0:.0f}s"))
