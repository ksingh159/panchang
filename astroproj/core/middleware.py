"""Small request hooks."""
from django.conf import settings
from urllib.parse import urlsplit

from django.core.exceptions import MiddlewareNotUsed
from django.http import HttpResponsePermanentRedirect

from core.utils.pdf_store import maybe_purge_in_background


class DailyHousekeepingMiddleware:
    """Deletes expired order PDFs once a day from the web service, which owns the PDF volume.
    Off unless PDF_PURGE_IN_WEB (default: on when DEBUG is off, i.e. on the server)."""

    def __init__(self, get_response):
        if not getattr(settings, "PDF_PURGE_IN_WEB", False):
            raise MiddlewareNotUsed
        self.get_response = get_response

    def __call__(self, request):
        maybe_purge_in_background()
        return self.get_response(request)


class CanonicalHostMiddleware:
    """301s www.<site> (and any other alias of SITE_URL's host) to SITE_URL in one hop, keeping path and query.
    Without it www served every page with 200 + a canonical tag, which Search Console reports as
    'Alternate page with proper canonical tag' and which doubles the crawl. Runs first, so http://www goes
    straight to https://<site> instead of hopping through https://www."""

    def __init__(self, get_response):
        site = urlsplit(getattr(settings, "SITE_URL", "") or "")
        if not site.netloc:
            raise MiddlewareNotUsed
        self.scheme, self.host = site.scheme or "https", site.netloc.lower()
        bare = self.host[4:] if self.host.startswith("www.") else self.host
        self.aliases = {bare, "www." + bare} - {self.host}
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().split(":")[0].lower() if request.META.get("HTTP_HOST") else ""
        if host in self.aliases:
            return HttpResponsePermanentRedirect(f"{self.scheme}://{self.host}{request.get_full_path()}")
        return self.get_response(request)
