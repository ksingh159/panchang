# core/utils/hindu_calendar.py
"""
The monthly Hindu calendar grid (/hindu-calendar/<year>/<month>/) and its free printable PDF.

    month(year, m)     {"days", "weeks", "periods", "masas", ...} for one Gregorian month, Varanasi sunrise
    MONTH_SLUGS        "january" ... "december" (the URL uses the name: /hindu-calendar/2026/november/)

Each day: tithi and nakshatra in force at Varanasi sunrise (the udaya tithi a printed panchang shows), when the
tithi ends, festivals and vrats from the festival engine (same dates as /festivals/ and /vrat/), Purnima,
Amavasya and Ekadashi markers. Kept in the cache for 30 days; a month never changes once computed.
"""
import calendar
from datetime import date, datetime, timedelta

import pytz
from django.core.cache import cache

from . import cities
from . import festival_calculations as fc
from . import panchang_engine as pe
from . import panchang_store as ps

CACHE_VERSION = 1
MIN_YEAR, MAX_YEAR = 2000, 2100
MONTH_SLUGS = [m.lower() for m in calendar.month_name[1:]]
MONTHS_HI = ["जनवरी", "फ़रवरी", "मार्च", "अप्रैल", "मई", "जून", "जुलाई", "अगस्त", "सितंबर", "अक्टूबर", "नवंबर", "दिसंबर"]
WEEKDAYS = [("Sun", "रवि"), ("Mon", "सोम"), ("Tue", "मंगल"), ("Wed", "बुध"), ("Thu", "गुरु"), ("Fri", "शुक्र"),
            ("Sat", "शनि")]
WEEKDAYS_LONG = [("Sunday", "रविवार"), ("Monday", "सोमवार"), ("Tuesday", "मंगलवार"), ("Wednesday", "बुधवार"),
                 ("Thursday", "गुरुवार"), ("Friday", "शुक्रवार"), ("Saturday", "शनिवार")]
SKIP_CATEGORIES = {"Period"}           # multi-day spells are listed above the grid, not in every cell


def _at(events, t):
    """The event running at naive-UTC instant t (events sorted by start)."""
    for e in events:
        if e.start_utc <= t < e.end_utc:
            return e
    return None


def _local(e, tz):
    return pytz.utc.localize(e.end_utc).astimezone(tz)


def compute(year, m):
    place = cities.get("varanasi")
    tz = pytz.timezone(place["tz"])
    first = date(year, m, 1)
    last = date(year, m, calendar.monthrange(year, m)[1])
    span = (first - timedelta(days=1), last + timedelta(days=1))
    tithis = ps.find_events("tithi", *span)
    naks = ps.find_events("nakshatra", *span)
    pakshas = ps.find_events("paksha", *span)
    fests = [f for f in fc.get_festivals_for_year(year) if f["date"].month == m]
    periods = [f for f in fc.get_carryover_periods(year) + fc.get_festivals_for_year(year)
               if f["category"] in SKIP_CATEGORIES and f["date"] <= last and (f.get("end_date") or f["date"]) >= first]

    days, masas = [], []
    d = first
    while d <= last:
        sunrise, sunset = pe.sun_times(d, place["lat"], place["lon"], tz)
        t_utc = sunrise.astimezone(pytz.utc).replace(tzinfo=None)
        ti, nk, pk = _at(tithis, t_utc), _at(naks, t_utc), _at(pakshas, t_utc)
        tithi_end = _local(ti, tz) if ti else None
        nak_end = _local(nk, tz) if nk else None
        num = ti.number + 1 if ti else 0               # stored 0-29; here 1-15 Shukla, 16-30 Krishna
        paksha = (ti.extra or {}).get("paksha", "") if ti else ""
        masa = (pk.extra or {}).get("masa_purnimanta", "") if pk else ""
        amanta = (pk.extra or {}).get("masa_amanta", "") if pk else ""
        if masa and (not masas or masas[-1] != (masa, amanta)):
            masas.append((masa, amanta))
        todays = sorted((f for f in fests if f["date"] == d and f["category"] not in SKIP_CATEGORIES),
                        key=lambda f: (f["importance"] != "high", f["category"] != "Major Festival", f["name"]))
        days.append({
            "date": d, "day": d.day, "weekday": (d.weekday() + 1) % 7,          # 0 = Sunday
            "wd": WEEKDAYS_LONG[(d.weekday() + 1) % 7],
            "sunrise": sunrise, "sunset": sunset,
            "tithi": ti.name if ti else "", "tithi_no": num if num <= 15 else num - 15, "paksha": paksha,
            "tithi_end": tithi_end if tithi_end and tithi_end.date() <= d + timedelta(days=1) else None,
            "kshaya": _skipped(ti, tithis, d, place, tz) if ti else "",
            "nakshatra": nk.name if nk else "", "nakshatra_end": nak_end,
            "masa": masa, "amanta": amanta,
            "purnima": num == 15, "amavasya": num == 30, "ekadashi": num in (11, 26),
            "festivals": [{"name": f["name"], "slug": f["slug"], "category": f["category"],
                           "high": f["importance"] == "high", "year": f["date"].year} for f in todays],
        })
        d += timedelta(days=1)

    lead = days[0]["weekday"]
    cells = [None] * lead + days
    cells += [None] * (-len(cells) % 7)
    weeks = [cells[i:i + 7] for i in range(0, len(cells), 7)]
    return {
        "year": year, "month": m, "slug": MONTH_SLUGS[m - 1], "days": days, "weeks": weeks, "masas": masas,
        "periods": [{"name": p["name"], "slug": p["slug"], "start": p["date"], "end": p.get("end_date") or p["date"],
                     "year": p["date"].year} for p in periods],
        "festival_count": sum(len(x["festivals"]) for x in days),
    }


def _skipped(ti, tithis, d, place, tz):
    """The tithi that begins and ends between this sunrise and the next (kshaya: never at sunrise), else ""."""
    nxt = next((e for e in tithis if e.start_jd >= ti.end_jd - 1e-6), None)
    if not nxt:
        return ""
    next_sunrise, _ = pe.sun_times(d + timedelta(days=1), place["lat"], place["lon"], tz)
    return nxt.name if _local(nxt, tz) < next_sunrise else ""


def _key(year, m):
    return f"hindu-calendar:v{CACHE_VERSION}:{year}-{m:02d}"


def month(year, m):
    data = cache.get(_key(year, m))
    if data is None:
        data = compute(year, m)
        cache.set(_key(year, m), data, 30 * 24 * 3600)
    return data


def shift(year, m, by):
    k = year * 12 + (m - 1) + by
    return k // 12, k % 12 + 1


def in_range(year):
    return MIN_YEAR <= year <= MAX_YEAR
