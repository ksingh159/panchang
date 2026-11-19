"""Run on every deploy, before the new version takes traffic (Railway preDeployCommand)."""
from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = ("Deploy step: migrate the database, create the cache table, compile the Hindi translations, load the "
            "GeoNames cities if the table is empty (a fresh database has none, so place search finds nothing), "
            "load the Markdown articles in articles/, and precompute grahan globe data.")

    def handle(self, *args, **options):
        call_command("migrate", interactive=False)
        call_command("createcachetable")
        call_command("compile_translations")
        from core.models import City
        if not City.objects.exists():
            call_command("load_cities")
        self._sync_site_domain()
        self._import_articles()
        self._warm_grahan()

    def _import_articles(self):
        """Publish or update the Markdown articles in articles/. A bad file must not stop a deploy."""
        try:
            call_command("import_articles")
        except Exception as exc:  # noqa: BLE001
            self.stderr.write(f"Article import failed: {exc}")

    def _warm_grahan(self):
        """Fill the shared cache with the eclipse list and globe data, so no visitor waits ~1-3 s for them.
        Entries already cached are skipped, so after the first deploy this takes a second or two.
        A failure here must never stop a deploy: the pages still work, only slower on first view."""
        try:
            call_command("precompute_grahan")
        except Exception as exc:  # noqa: BLE001
            self.stderr.write(f"Grahan warm-up skipped: {exc}")

    def _sync_site_domain(self):
        """The Sites record starts as "example.com"; the sitemap and sign-up emails use it, so keep it on SITE_URL."""
        from urllib.parse import urlparse

        from django.conf import settings
        from django.contrib.sites.models import Site
        domain = urlparse(settings.SITE_URL).netloc
        if domain:
            Site.objects.update_or_create(id=settings.SITE_ID, defaults={"domain": domain, "name": settings.SITE_NAME})
            self.stdout.write(f"Site domain: {domain}")
