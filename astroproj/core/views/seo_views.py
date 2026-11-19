# core/views/seo_views.py
"""
Crawlable, server-rendered pages built on the shared panchang cache:

  /panchang-finder/                      when is a tithi / nakshatra / yoga / karana / masa / sankranti
  /festivals/<year>/  /festivals/<year>/<slug>/
  /shubh-muhurat/  /shubh-muhurat/<purpose>/<year>/
  /yogas/<yoga>/<year>/                  Guru Pushya, Sarvartha Siddhi, Pushkar ...
  /robots.txt  /ads.txt  /sitemap.xml
"""
from datetime import date, timedelta

import pytz
from django.conf import settings
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils import timezone

from ..utils import festival_calculations as fc
from ..utils import muhurat as mu
from ..utils import panchang_store as ps
from ..utils.constants import NAKSHATRA_NAMES, YOGA_NAMES, ZODIAC_SIGNS
from ..utils.geo import resolve_place
from ..utils.panchang_engine import KARANA_MOVABLE, LUNAR_MONTHS, RITU_BY_SIGN

YEAR_MIN, YEAR_MAX = 1900, 2200
TITHI_CHOICES = ["Pratipada", "Dvitiya", "Tritiya", "Chaturthi", "Panchami", "Shashthi", "Saptami", "Ashtami",
                 "Navami", "Dashami", "Ekadashi", "Dvadashi", "Trayodashi", "Chaturdashi", "Purnima", "Amavasya"]
KARANA_CHOICES = KARANA_MOVABLE + ["Shakuni", "Chatushpada", "Naga", "Kimstughna"]
RITU_CHOICES = ["Vasanta", "Grishma", "Varsha", "Sharad", "Hemanta", "Shishira"]


def user_location(request):
    """(lat, lon, tz, city) from ?place_id/?city, profile or session; default New Delhi."""
    place_id, text = request.GET.get("place_id"), request.GET.get("city", "").strip()
    if place_id or text:
        hit = resolve_place(text, geoname_id=place_id)
        if hit:
            return hit["lat"], hit["lon"], hit["timezone"], hit["name"]
    p = getattr(request.user, "profile", None) if request.user.is_authenticated else None
    if p:
        return p.latitude, p.longitude, p.timezone or "Asia/Kolkata", p.city
    s = request.session
    return s.get("lat", 28.6139), s.get("lon", 77.2090), s.get("timezone", "Asia/Kolkata"), s.get("city", "New Delhi")


def _today(tz):
    return timezone.now().astimezone(pytz.timezone(tz)).date()


def _year(value, default):
    try:
        y = int(value)
    except (TypeError, ValueError):
        return default
    if not (YEAR_MIN <= y <= YEAR_MAX):
        raise Http404("Year out of range")
    return y


# ---------------------------------------------------------------------------
# Panchang Finder
# ---------------------------------------------------------------------------

def _finder_labels():
    from django.utils.translation import get_language
    if not (get_language() or "").startswith("hi"):
        return {}
    from ..templatetags.vp import t
    return {v: t(v) for _, values in FINDER_KINDS.values() for v in values}


FINDER_KINDS = {
    "tithi": ("Tithi", TITHI_CHOICES),
    "nakshatra": ("Nakshatra", NAKSHATRA_NAMES),
    "yoga": ("Yoga", YOGA_NAMES),
    "karana": ("Karana", KARANA_CHOICES),
    "masa": ("Lunar month (Maas)", LUNAR_MONTHS),
    "adhik": ("Adhik Maas", []),
    "sankranti": ("Sankranti (Sun sign)", ZODIAC_SIGNS),
    "ritu": ("Ritu (season)", RITU_CHOICES),
    "moon_sign": ("Moon sign (Rashi)", ZODIAC_SIGNS),
}


def _finder_query(kind, name, paksha, y0, y1, tz):
    start, end = date(y0, 1, 1), date(y1, 12, 31)
    extra = {}
    if kind == "tithi":
        if name in ("Purnima", "Amavasya"):
            paksha = ""
        if paksha:
            extra["paksha"] = paksha
        rows = ps.find_events("tithi", start, end, tz=tz, name=name, **extra)
    elif kind == "masa":
        rows = ps.find_events("amanta_masa", start, end, tz=tz, name=name)
    elif kind == "adhik":
        rows = ps.find_events("amanta_masa", start, end, tz=tz, adhik=True)
    elif kind == "sankranti":
        rows = ps.find_events("sun_sign", start, end, tz=tz, name=name)
    elif kind == "ritu":
        # a ritu spans two solar signs; join the consecutive pair into one season
        out = []
        for r in ps.find_events("sun_sign", start, end, tz=tz, ritu=name):
            item = ps.as_local(r, tz)
            item["name"] = name
            if out and out[-1]["end"] == item["start"]:
                out[-1]["end"] = item["end"]
                out[-1]["duration_hours"] += item["duration_hours"]
            else:
                out.append(item)
        return out
    else:
        rows = ps.find_events(kind, start, end, tz=tz, name=name)
    return [ps.as_local(r, tz) for r in rows]


def panchang_finder(request):
    lat, lon, tz, city = user_location(request)
    today = _today(tz)
    kind = request.GET.get("type", "tithi")
    if kind not in FINDER_KINDS:
        kind = "tithi"
    name = request.GET.get("name", "")
    paksha = request.GET.get("paksha", "")
    y0 = _year(request.GET.get("from"), today.year)
    y1 = _year(request.GET.get("to"), y0)
    if y1 < y0:
        y0, y1 = y1, y0
    y1 = min(y1, y0 + 49)          # 50 years per query keeps responses small
    results, searched = [], False
    if name or kind == "adhik":
        searched = True
        results = _finder_query(kind, name, paksha, y0, y1, tz)
        if kind == "masa":
            for r in results:
                r["label"] = ("Adhik " if r.get("adhik") else "") + r["name"]

    if request.GET.get("format") == "json":
        return JsonResponse({"results": [
            {**{k: v for k, v in r.items() if k not in ("start", "end")},
             "start": r["start"].isoformat(), "end": r["end"].isoformat()} for r in results]})

    context = {
        "kinds": FINDER_KINDS, "kind": kind, "kind_label": FINDER_KINDS[kind][0], "name": name, "paksha": paksha,
        "choices": FINDER_KINDS[kind][1], "from_year": y0, "to_year": y1,
        "results": results, "searched": searched, "city": city, "timezone": tz,
        "all_choices": {k: v[1] for k, v in FINDER_KINDS.items()},
        # Hindi names for the options the page script builds (empty on the English site)
        "choice_labels": _finder_labels(),
    }
    return render(request, "seo/panchang_finder.html", context)


# ---------------------------------------------------------------------------
# Festivals
# ---------------------------------------------------------------------------

def festival_detail(request, year, slug):
    year = _year(year, None)
    rows = fc.get_festival_by_slug(slug, year)
    if not rows:
        raise Http404("Festival not found")
    other_years = []
    for y in (year - 1, year + 1, year + 2):
        if YEAR_MIN <= y <= YEAR_MAX:
            r = fc.get_festival_by_slug(slug, y)
            if r:
                other_years.append((y, r[0]))
    first = rows[0]
    from ..utils import prefs
    system = prefs.month_system(request)
    for f in rows:
        krishna = "Krishna" in (f.get("rule") or "") or "Amavasya" in (f.get("name") or "")
        f["month_shown"] = prefs.month_in_system(f.get("month"), krishna, system)
    lat, lon, tz, city = user_location(request)
    from ..utils import festival_muhurat as fm
    puja = fm.puja_muhurats(slug, first["date"], lat, lon, tz)
    related = [f for f in fc.get_festivals_between(first["date"] - timedelta(days=10), first["date"] + timedelta(days=10))
               if f["slug"] != slug and f["importance"] == "high"][:8]
    return render(request, "seo/festival_detail.html", {
        "year": year, "slug": slug, "rows": rows, "festival": first,
        "other_years": other_years, "related": related, "varanasi": fc.VARANASI,
        "puja": puja, "city": city, "timezone": tz, "month_label": prefs.month_label(system),
    })


# ---------------------------------------------------------------------------
# Shubh Muhurat
# ---------------------------------------------------------------------------

def shubh_muhurat(request):
    lat, lon, tz, city = user_location(request)
    d = _today(tz)
    if request.GET.get("date"):
        try:
            d = date.fromisoformat(request.GET["date"])
        except ValueError:
            pass
    natal = mu.natal_from_user(request.user)
    guidance = mu.day_guidance(d, lat, lon, tz, natal)
    from ..utils import prefs
    system = prefs.month_system(request)
    if guidance.get("colours"):
        guidance["colours"]["masa_shown"] = prefs.month_in_system(
            guidance["colours"].get("masa"), guidance.get("krishna"), system)
    upcoming = {}
    for key in ("vivah", "gold", "vehicle", "property", "investment", "loan"):
        upcoming[key] = mu.muhurat_dates(key, d + timedelta(days=1), d + timedelta(days=45), lat, lon, tz, natal)[:4]
    blocked = mu.blocked_periods(d, d + timedelta(days=120), "vivah", lat, lon, tz)
    return render(request, "seo/shubh_muhurat.html", {
        "g": guidance, "city": city, "timezone": tz, "date": d,
        "prev": d - timedelta(days=1), "next": d + timedelta(days=1),
        "upcoming": upcoming, "purposes": mu.PURPOSES, "blocked": blocked,
        "has_natal": bool(natal), "year": d.year,
    })


def muhurat_purpose(request, purpose, year):
    if purpose not in mu.PURPOSES:
        raise Http404("Unknown muhurat")
    year = _year(year, None)
    lat, lon, tz, city = user_location(request)
    natal = mu.natal_from_user(request.user) if request.GET.get("personal") == "1" else None
    dates = mu.muhurat_dates(purpose, date(year, 1, 1), date(year, 12, 31), lat, lon, tz, natal)
    months = {}
    for item in dates:
        months.setdefault(item["date"].strftime("%B"), []).append(item)
    return render(request, "seo/muhurat_purpose.html", {
        "purpose": purpose, "rule": mu.PURPOSES[purpose], "year": year, "months": months,
        "count": len(dates), "city": city, "timezone": tz, "personal": bool(natal),
        "purposes": mu.PURPOSES, "blocked": mu.blocked_periods(date(year, 1, 1), date(year, 12, 31), mu.rule_level(mu.PURPOSES[purpose]), lat, lon, tz),
        "nakshatra_names": sorted(NAKSHATRA_NAMES[i] for i in mu.PURPOSES[purpose]["nakshatras"]),
        "weekday_names": [mu.WEEKDAY_EN[i] for i in sorted(mu.PURPOSES[purpose]["weekdays"])],
        "articles": _articles_linking(purpose),
    })


def _articles_linking(purpose):
    """Published articles whose body links to this muhurat page (filtered in Python: JSON 'contains' needs Postgres)."""
    from ..models import Article
    qs = Article.objects.filter(status="published").exclude(muhurat_purposes=[]).only("title", "slug", "muhurat_purposes")
    return [a for a in qs if purpose in a.muhurat_purposes][:3]


# ---------------------------------------------------------------------------
# Special yogas
# ---------------------------------------------------------------------------

def yoga_calendar(request, yoga, year):
    if yoga not in mu.YOGA_INFO:
        raise Http404("Unknown yoga")
    year = _year(year, None)
    lat, lon, tz, city = user_location(request)
    windows = mu.special_yogas(date(year, 1, 1), date(year, 12, 31), lat, lon, tz, kinds={yoga})
    name, meaning = mu.YOGA_INFO[yoga]
    return render(request, "seo/yoga_calendar.html", {
        "yoga": yoga, "name": name, "meaning": meaning, "year": year, "windows": windows,
        "city": city, "timezone": tz, "all_yogas": mu.YOGA_INFO,
    })


# ---------------------------------------------------------------------------
# robots / ads / sitemap
# ---------------------------------------------------------------------------

def panchang_on_date(request, ymd):
    """Clean, indexable URL for a day's panchang: /panchang/date/2026-11-08/."""
    from .astro_views import home
    try:
        date.fromisoformat(ymd)
    except ValueError:
        raise Http404("Bad date")
    request.GET = request.GET.copy()
    request.GET["date"] = ymd
    return home(request)


# Private pages, kept out of every crawler's group (a crawler obeys only the most specific group that names it).
ROBOTS_PRIVATE = [
    "/admin/", "/accounts/", "/api/", "/profile/", "/settings/", "/my-kundalis/", "/kundali/",
    "/eclipses/update/", "/eclipses/cleanup/", "/pay/", "/my-orders/",
    "/hi/profile/", "/hi/settings/", "/hi/my-kundalis/", "/hi/kundali/", "/hi/pay/", "/hi/my-orders/", "/hi/api/",
]
ROBOTS_PUBLIC_EXCEPTIONS = ["/kundali/create", "/hi/kundali/create"]

# Owner's rule (2026-11-18): AI assistants may open pages when a person asks them to (ChatGPT, Claude), but their
# crawlers that gather pages for training or for their own search index are kept out.
AI_USER_AGENTS = ["ChatGPT-User", "Claude-User"]
AI_CRAWLERS = ["GPTBot", "OAI-SearchBot", "ClaudeBot", "Claude-SearchBot", "Claude-Web", "anthropic-ai",
               "DeepSeekBot"]


def robots_txt(request):
    base = getattr(settings, "SITE_URL", "") or request.build_absolute_uri("/").rstrip("/")
    rules = [f"Disallow: {p}" for p in ROBOTS_PRIVATE] + [f"Allow: {p}" for p in ROBOTS_PUBLIC_EXCEPTIONS]
    lines = ["User-agent: *", *rules, ""]
    lines += [f"User-agent: {ua}" for ua in AI_USER_AGENTS] + rules + [""]
    lines += [f"User-agent: {ua}" for ua in AI_CRAWLERS] + ["Disallow: /", ""]
    lines.append(f"Sitemap: {base.rstrip('/')}/sitemap.xml")
    return HttpResponse("\n".join(lines) + "\n", content_type="text/plain")


def ads_txt(request):
    client = getattr(settings, "ADSENSE_CLIENT_ID", "")
    if not client:
        raise Http404("AdSense not configured")
    pub = client.replace("ca-", "")
    return HttpResponse(f"google.com, {pub}, DIRECT, f08c47fec0942fa0\n", content_type="text/plain")
