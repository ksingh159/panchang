# core/utils/pdf_store.py
"""
Where bought PDFs are kept.

The first download of an order builds the PDF and saves it; later downloads (up to payments.DOWNLOAD_LIMIT within
payments.DOWNLOAD_DAYS) are served from the saved file. That keeps the buyer's copy identical every time (even if a
calculation rule changes later) and spares the CPU, which matters more than disk: a kundali PDF takes seconds to
build but is only ~0.5-1.5 MB.

Storage is the Django storage alias "pdfs" (settings.STORAGES). By default it is a private folder on the server's
disk (PDF_STORAGE_ROOT, never under MEDIA_ROOT or STATIC_ROOT, so there is no public URL); point it at S3 or
Cloudflare R2 (django-storages) when the server's disk is small. Files are deleted once the download window
closes: the web service does this once a day by itself (maybe_purge_in_background, below); ``manage.py
purge_order_pdfs`` does the same by hand.

Rough sizing: 1,000 orders a month x ~1 MB x 2 languages at most = ~2 GB held at any time with a 30-day window.
"""
import logging
import threading
import time
from datetime import date, timedelta

from django.core.files.base import ContentFile
from django.core.files.storage import storages
from django.utils import timezone

logger = logging.getLogger(__name__)
ALIAS = "pdfs"


def _storage():
    return storages[ALIAS]


def path_for(purchase, lang):
    """Fixed for the life of the order (created_at never changes), so a saved file is always found again."""
    return f"orders/{purchase.created_at:%Y/%m}/{purchase.ref}-{lang}.pdf"


# One PDF build at a time per worker process. Builds are CPU-bound (7-13 s) and Python runs them on one core, so
# parallel builds finish no sooner; they only add ~30-70 MB each and slow every page in the worker together.
_BUILD_SLOT = threading.Lock()


def _read_saved(store, name):
    try:
        if store.exists(name):
            with store.open(name, "rb") as fh:
                return fh.read()
    except Exception:
        logger.exception("Could not read saved PDF %s", name)
    return None


def get_or_build(purchase, lang, build):
    """Bytes of the order's PDF in ``lang``: the saved copy, else ``build()`` and save it.

    A storage failure never blocks the buyer: the PDF is built and sent anyway, and the error is logged.
    """
    name = path_for(purchase, lang)
    store = _storage()
    data = _read_saved(store, name)
    if data is not None:
        return data
    with _BUILD_SLOT:
        data = _read_saved(store, name)      # a double click waits here, then gets the copy the first one saved
        if data is not None:
            return data
        data = build()
        try:
            store.save(name, ContentFile(data))
        except Exception:
            logger.exception("Could not save PDF %s", name)
    return data


def forget(purchase):
    """Delete every saved language of one order (e.g. after a refund or a deleted kundali)."""
    store = _storage()
    for lang in ("en", "hi"):
        name = path_for(purchase, lang)
        try:
            if store.exists(name):
                store.delete(name)
        except Exception:
            logger.exception("Could not delete PDF %s", name)


def purge_expired(days, grace_days=2, dry_run=False):
    """Delete saved PDFs of orders whose download window closed; returns (files, bytes)."""
    from core.models import Purchase
    cutoff = timezone.now() - timedelta(days=days + grace_days)
    store = _storage()
    files = size = 0
    for p in Purchase.objects.filter(paid_at__lt=cutoff).only("ref", "paid_at", "created_at").iterator():
        for lang in ("en", "hi"):
            name = path_for(p, lang)
            try:
                if not store.exists(name):
                    continue
                files += 1
                size += store.size(name)
                if not dry_run:
                    store.delete(name)
            except Exception:
                logger.exception("Could not purge PDF %s", name)
    return files, size


# Daily purge from inside the web service. On Railway a volume belongs to one service, so a separate cron service
# cannot see these files; the web workers own them and do it themselves (DailyHousekeepingMiddleware).
_PURGE_CHECK_EVERY = 3600          # seconds between checks in one worker process
_next_purge_check = 0.0
_purge_check_lock = threading.Lock()


def maybe_purge_in_background():
    """Cheap enough for every request: at most once an hour per worker, start a thread that purges if no worker has
    purged today yet. The visitor's request never waits for it."""
    global _next_purge_check
    now = time.monotonic()
    if now < _next_purge_check or not _purge_check_lock.acquire(blocking=False):
        return
    try:
        if now < _next_purge_check:
            return
        _next_purge_check = now + _PURGE_CHECK_EVERY
    finally:
        _purge_check_lock.release()
    threading.Thread(target=run_daily_purge, name="pdf-purge", daemon=True).start()


def run_daily_purge():
    """Purge once per calendar day across all workers: the shared cache key is the claim. Returns True if it ran."""
    from django.core.cache import cache
    from django.db import close_old_connections

    from core.utils import payments
    key = f"pdf-purge:{date.today():%Y-%m-%d}"
    try:
        if not cache.add(key, 1, timeout=2 * 24 * 3600):
            return False
        try:
            files, size = purge_expired(payments.DOWNLOAD_DAYS)
        except Exception:
            cache.delete(key)          # let the next hourly check try again
            raise
        logger.info("Daily PDF purge: deleted %s file(s), %.1f MB", files, size / 1_048_576)
        return True
    except Exception:
        logger.exception("Daily PDF purge failed")
        return False
    finally:
        close_old_connections()
