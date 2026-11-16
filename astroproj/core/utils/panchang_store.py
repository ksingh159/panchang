# core/utils/panchang_store.py
"""
Shared, persistent cache of panchang events.

    ensure_years(2040, 2042)            # compute + save if missing (~1 s / year)
    find_events('tithi', name='Ekadashi', paksha='Shukla', start=date(2040,1,1), end=date(2040,12,31))
    events_overlapping('nakshatra', start_utc, end_utc)

Every year is computed at most once for the whole site; after that every
query is a single indexed SELECT.  Run ``python manage.py precompute_panchang``
to warm a range of years ahead of time.
"""
import threading
from datetime import date, datetime, time, timedelta

import pytz
from django.db import transaction

from core.models import PanchangEvent, PanchangYear
from . import panchang_engine as pe

ENGINE_VERSION = 1
MIN_YEAR, MAX_YEAR = 1000, 3000   # bundled Swiss Ephemeris files cover far more; keep sane bounds

_lock = threading.Lock()


def ensure_year(year):
    if not (MIN_YEAR <= year <= MAX_YEAR):
        raise ValueError(f"Year {year} is outside the supported range {MIN_YEAR}-{MAX_YEAR}")
    if PanchangYear.objects.filter(year=year, engine_version=ENGINE_VERSION).exists():
        return False
    with _lock:
        if PanchangYear.objects.filter(year=year, engine_version=ENGINE_VERSION).exists():
            return False
        rows = []
        for e in pe.compute_year_events(year):
            rows.append(PanchangEvent(
                kind=e["kind"], number=e["number"], name=e["name"],
                start_jd=e["start_jd"], end_jd=e["end_jd"],
                start_utc=pe.jd_to_utc(e["start_jd"]), end_utc=pe.jd_to_utc(e["end_jd"]),
                year=year, extra=e["extra"],
            ))
        with transaction.atomic():
            PanchangEvent.objects.filter(year=year).delete()
            PanchangEvent.objects.bulk_create(rows, batch_size=1000, ignore_conflicts=True)
            PanchangYear.objects.update_or_create(year=year, defaults={"engine_version": ENGINE_VERSION})
        return True


def ensure_years(first, last):
    """Make sure every year in [first, last] is cached. Returns list of years computed now."""
    done = []
    for y in range(first, last + 1):
        if ensure_year(y):
            done.append(y)
    return done


def _utc(d, tz):
    """Local date/datetime -> naive UTC datetime."""
    if isinstance(tz, str):
        tz = pytz.timezone(tz)
    if isinstance(d, datetime):
        dt = d if d.tzinfo else tz.localize(d)
    else:
        dt = tz.localize(datetime.combine(d, time.min))
    return dt.astimezone(pytz.utc).replace(tzinfo=None)


def find_events(kind, start, end, tz="Asia/Kolkata", name=None, number=None, **extra_filters):
    """
    Events of ``kind`` *starting or running* within the local date range [start, end].
    ``extra_filters`` match keys of the JSON ``extra`` column, e.g. paksha='Shukla', adhik=True.
    """
    s_utc = _utc(start, tz)
    e_utc = _utc(end + timedelta(days=1) if not isinstance(end, datetime) else end, tz)
    ensure_years(s_utc.year - (1 if s_utc.month == 1 else 0), e_utc.year)
    qs = PanchangEvent.objects.filter(kind=kind, start_utc__lt=e_utc, end_utc__gt=s_utc)
    if name:
        qs = qs.filter(name__iexact=name)
    if number is not None:
        qs = qs.filter(number=number)
    rows = list(qs.order_by("start_jd"))
    if extra_filters:
        rows = [r for r in rows if all(r.extra.get(k) == v for k, v in extra_filters.items())]
    return rows


def events_overlapping(kind, start_utc, end_utc):
    """All events of ``kind`` overlapping the naive-UTC window (assumes years cached)."""
    return list(PanchangEvent.objects.filter(kind=kind, start_utc__lt=end_utc, end_utc__gt=start_utc)
                .order_by("start_jd"))


def event_at(kind, dt_utc):
    """The event of ``kind`` in force at naive-UTC instant ``dt_utc``."""
    ensure_year(dt_utc.year)
    return (PanchangEvent.objects.filter(kind=kind, start_utc__lte=dt_utc, end_utc__gt=dt_utc)
            .order_by("start_jd").first())


def as_local(event, tz="Asia/Kolkata"):
    """Serialise an event with local start/end times."""
    if isinstance(tz, str):
        tz = pytz.timezone(tz)
    start = pytz.utc.localize(event.start_utc).astimezone(tz)
    end = pytz.utc.localize(event.end_utc).astimezone(tz)
    d = {
        "kind": event.kind,
        "name": event.name,
        "number": event.number,
        "start": start,
        "end": end,
        "duration_hours": round((event.end_jd - event.start_jd) * 24, 2),
    }
    d.update(event.extra or {})
    return d


def lunar_month_at(dt_utc):
    """(amanta_masa, purnimanta_masa, adhik, paksha) at an instant."""
    p = event_at("paksha", dt_utc)
    if not p:
        return None
    ex = p.extra
    return {
        "paksha": p.name,
        "amanta": ex.get("masa_amanta"),
        "purnimanta": ex.get("masa_purnimanta"),
        "adhik": ex.get("adhik", False),
        "purnimanta_adhik": ex.get("purnimanta_adhik", ex.get("adhik", False)),
    }
