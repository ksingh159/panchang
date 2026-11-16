from django.core.management.base import BaseCommand
from django.utils import timezone

from core.utils import grahan as gr


class Command(BaseCommand):
    help = "Fill the shared cache with the eclipse catalogue and globe data, so no visitor waits for them."

    def add_arguments(self, parser):
        year = timezone.now().year
        parser.add_argument("--from", dest="start", type=int, default=year - 10)
        parser.add_argument("--to", dest="end", type=int, default=year + 5)

    def handle(self, *args, **options):
        for year in range(options["start"], options["end"] + 1):
            rows = gr.eclipses_in_year(year)
            for e in rows:
                gr.globe_data(e)
            self.stdout.write(f"{year}: {len(rows)} eclipses")
