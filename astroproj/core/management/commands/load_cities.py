"""
Load the GeoNames gazetteer into the City table.

    python manage.py load_cities                 # cities with population >= 1000 (~165k rows)
    python manage.py load_cities --dataset cities500

Files are downloaded once into core/data/geonames/ (CC-BY 4.0, https://www.geonames.org).
Each row already carries its IANA timezone, so no runtime geocoding or
timezone guessing is needed and place names stay short: "Varanasi, Uttar Pradesh, India".
"""
import csv
import io
import sys
import urllib.request
import zipfile
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from core.models import City

BASE = "https://download.geonames.org/export/dump/"


class Command(BaseCommand):
    help = "Download and load GeoNames cities (offline birth-place / location search)"

    def add_arguments(self, parser):
        parser.add_argument("--dataset", default="cities1000",
                            choices=["cities500", "cities1000", "cities5000", "cities15000"])

    def _fetch(self, name):
        folder = Path(settings.BASE_DIR) / "core" / "data" / "geonames"
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / name
        if not path.exists():
            self.stdout.write(f"Downloading {name} ...")
            urllib.request.urlretrieve(BASE + name, path)
        return path

    def handle(self, *args, **opts):
        csv.field_size_limit(sys.maxsize if sys.maxsize < 2**31 else 2**31 - 1)
        countries = {}
        for line in self._fetch("countryInfo.txt").read_text(encoding="utf-8").splitlines():
            if line and not line.startswith("#"):
                p = line.split("\t")
                countries[p[0]] = p[4]
        admin1 = {}
        for line in self._fetch("admin1CodesASCII.txt").read_text(encoding="utf-8").splitlines():
            p = line.split("\t")
            if len(p) >= 2:
                admin1[p[0]] = p[1]

        ds = opts["dataset"]
        with zipfile.ZipFile(self._fetch(f"{ds}.zip")) as z:
            raw = z.read(f"{ds}.txt").decode("utf-8")

        rows = []
        for p in csv.reader(io.StringIO(raw), delimiter="\t", quoting=csv.QUOTE_NONE):
            if len(p) < 18 or p[6] != "P":          # populated places only
                continue
            cc = p[8]
            state = admin1.get(f"{cc}.{p[10]}", "")
            ascii_name = p[2] or p[1]
            pop = int(p[14] or 0)
            aliases = ""
            if pop >= 50000 and p[3]:
                alts = {a.strip().lower() for a in p[3].split(",")
                        if a.strip() and a.isascii() and " " not in a.strip()[:1] and len(a) <= 40}
                alts.discard(ascii_name.lower())
                aliases = "|" + "|".join(sorted(alts)) + "|" if alts else ""
            rows.append(City(
                geoname_id=int(p[0]), name=p[1], ascii_name=ascii_name,
                search_name=ascii_name.lower(), state=state,
                country=countries.get(cc, cc), country_code=cc,
                latitude=float(p[4]), longitude=float(p[5]),
                timezone=p[17], population=pop, aliases=aliases[:4000],
                slug=slugify(f"{ascii_name}-{state}" if state else ascii_name)[:150],
            ))

        with transaction.atomic():
            City.objects.all().delete()
            City.objects.bulk_create(rows, batch_size=2000)
        self.stdout.write(self.style.SUCCESS(f"Loaded {len(rows)} places from {ds}"))
