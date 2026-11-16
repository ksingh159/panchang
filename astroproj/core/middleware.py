"""Small request hooks."""
from django.conf import settings
from django.core.exceptions import MiddlewareNotUsed

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
