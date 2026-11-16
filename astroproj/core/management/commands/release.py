"""Run on every deploy, before the new version takes traffic (Railway preDeployCommand)."""
from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = ("Deploy step: migrate the database, create the cache table, compile the Hindi translations, and load the "
            "GeoNames cities if the table is empty (a fresh database has none, so place search finds nothing).")

    def handle(self, *args, **options):
        call_command("migrate", interactive=False)
        call_command("createcachetable")
        call_command("compile_translations")
        from core.models import City
        if not City.objects.exists():
            call_command("load_cities")
        self._sync_site_domain()

    def _sync_site_domain(self):
        """The Sites record starts as "example.com"; the sitemap and sign-up emails use it, so keep it on SITE_URL."""
        from urllib.parse import urlparse

        from django.conf import settings
        from django.contrib.sites.models import Site
        domain = urlparse(settings.SITE_URL).netloc
        if domain:
            Site.objects.update_or_create(id=settings.SITE_ID, defaults={"domain": domain, "name": settings.SITE_NAME})
            self.stdout.write(f"Site domain: {domain}")
