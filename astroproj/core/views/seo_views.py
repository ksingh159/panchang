# core/views/seo_views.py
"""
Crawlable, server-rendered pages built on the shared panchang cache:

  /panchang-finder/                      when is a tithi / nakshatra / yoga / karana / masa / sankranti
  /festivals/<year>/  /festivals/<year>/<slug>/
  /shubh-muhurat/  /shubh-muhurat/<purpose>/<year>/
  /yogas/<yoga>/<year>/                  Guru Pushya, Sarvartha Siddhi, Pushkar ...
  /aaj-ka-panchang/                      today's panchang for Varanasi and Delhi, computed at 05:30 IST
  /aaj-ka-panchang/<city>/               the same for one more city (utils/cities.py)
  /aaj-ka-choghadiya/[<city>/]  /aaj-ki-hora/[<city>/]   today's choghadiya / hora
  /vrat/  /vrat/<kind>/<year>/           Ekadashi, Pradosh, Sankashti, Purnima, Amavasya ... date lists
  /robots.txt  /ads.txt  /sitemap.xml
"""
import calendar
from datetime import date, timedelta

import pytz
from django.conf import settings
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import render
from django.urls import reverse
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
    from ..utils import festival_about as fa
    month_label = prefs.month_label(system)
    for f in rows:
        f["starts_at"] = fa.parse_moment(f["details"].get("starts_at"))
        f["ends_at"] = fa.parse_moment(f["details"].get("ends_at"))
        f["start_moment"] = fa.moment_panchang(f["starts_at"]) if f["starts_at"] else None
        f["days"] = [fa.day_panchang(d, month_label) for d in dict.fromkeys((f["date"], f["end_date"]))]
    carried = [dict(e, ends_at=fa.parse_moment(e["details"].get("ends_at")))
               for e in fc.get_carryover_periods(year) if e["slug"] == slug]
    about = fa.ABOUT.get(slug)
    from ..utils import kumbh
    kumbh_snans = kumbh.snans_on(slug, first["date"])
    muhurat_links = [(p, mu.PURPOSES[p]) for p in (about or {}).get("muhurat", [])]
    return render(request, "seo/festival_detail.html", {
        "year": year, "slug": slug, "rows": rows, "festival": first,
        "other_years": other_years, "related": related, "varanasi": fc.VARANASI,
        "puja": puja, "city": city, "timezone": tz, "month_label": month_label,
        "carried": carried, "about": about, "muhurat_links": muhurat_links, "kumbh_snans": kumbh_snans,
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
    for key in ("vivah", "griha-pravesh", "mundan", "namkaran", "gold", "vehicle", "property", "investment", "loan"):
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
# Aaj Ka Panchang
# ---------------------------------------------------------------------------

def _hindi(request):
    return (getattr(request, "LANGUAGE_CODE", "") or "").startswith("hi")


def _day_label(x, hindi):
    """Django's Hindi month names drop the halant ("नवमबर"); use the site's spelling."""
    from ..templatetags.vp import EXTRA_HI
    month = x.strftime("%B")
    return f"{x.day} {EXTRA_HI[month] if hindi else month} {x.year}"


def aaj_ka_panchang(request):
    """Today's panchang for Varanasi and Delhi (stored at 05:30 IST), or for a city the visitor picks."""
    from ..utils import aaj_panchang as ap
    snap = ap.today_snapshot()
    custom = None
    if request.GET.get("city") or request.GET.get("place_id"):
        lat, lon, tz, city = user_location(request)
        custom = ap.city_day({"key": "custom", "name": (city, city), "query": city, "lat": lat, "lon": lon, "tz": tz},
                             _today(tz))
    cities = [custom] if custom else snap["cities"]
    hindi = _hindi(request)
    return _render_aaj(request, snap, cities, custom=custom, computed_at=snap["computed_at"],
                       diet=snap["diet"]["hi" if hindi else "en"],
                       good_groups=ap._good_groups(cities) if custom else snap["good_groups"])


def aaj_ka_panchang_city(request, city):
    """/aaj-ka-panchang/<city>/: one city's panchang for today, built at 05:30 IST with the main page."""
    from django.shortcuts import redirect
    from ..utils import aaj_panchang as ap
    from ..utils import cities as cl
    place = cl.get(city)
    if place is None:
        raise Http404("City not found")
    if city in cl.ON_PANCHANG_INDEX:
        return redirect("aaj_ka_panchang", permanent=True)
    if request.GET.get("city") or request.GET.get("place_id"):
        return redirect(f"{reverse('aaj_ka_panchang')}?{request.GET.urlencode()}")
    snap = ap.today_snapshot()
    cs = ap.city_snapshot(city)
    hindi = _hindi(request)
    return _render_aaj(request, snap, [cs["city"]], city_page=place, computed_at=cs["computed_at"],
                       diet=cs["diet"]["hi" if hindi else "en"], good_groups=ap._good_groups([cs["city"]]))


def _render_aaj(request, snap, cities, custom=None, city_page=None, computed_at=None, diet=None, good_groups=None):
    from django.utils.http import http_date
    from ..utils import aaj_panchang as ap
    from ..utils import cities as cl
    hindi = _hindi(request)
    i = 1 if hindi else 0
    name = city_page["name"][i] if city_page else ""
    lede = ap.TEXT["city_lede"][i].format(city=name) if city_page else ap.TEXT["lede"][i]
    response = render(request, "seo/aaj_ka_panchang.html", {
        "d_label": _day_label(snap["date"], hindi),
        "stamp_label": f"{_day_label(computed_at, hindi)}, {computed_at:%H:%M}",
        "s": snap, "d": snap["date"], "cities": cities, "custom": custom, "city_page": city_page, "city_name": name,
        "lede": lede, "computed_at": computed_at,
        "good_groups": good_groups, "muhurat_rows": ap.muhurat_rows(cities),
        "first": cities[0], "diet": diet,
        "T": ap.TEXT, "tomorrow": snap["date"] + timedelta(days=1), "year": snap["date"].year,
        "city": custom["name"][0] if custom else "", "timezone": custom["tz"] if custom else "Asia/Kolkata",
        "city_links": cl.PANCHANG_PAGES, "here": city_page["key"] if city_page else "",
        "periods_city": city_page["key"] if city_page else cl.DEFAULT,
    })
    if not custom:
        response["Last-Modified"] = http_date(computed_at.timestamp())
    return response


# ---------------------------------------------------------------------------
# Choghadiya and Hora
# ---------------------------------------------------------------------------

PERIOD_TEXT = {
    "chog_h1": ("Aaj Ka Choghadiya", "आज का चौघड़िया"),
    "hora_h1": ("Aaj Ki Hora", "आज की होरा"),
    "chog_lede": ("Today's choghadiya for {city}: the day (sunrise to sunset) and the night (sunset to the next sunrise) "
                  "are each split into eight equal parts. Amrit, Shubh and Labh are good for starting work, Char suits "
                  "travel and luxury but not work that needs stability, and Udveg, Rog and Kaal are best kept for routine work.",
                  "{city} का आज का चौघड़िया: दिन (सूर्योदय से सूर्यास्त) और रात (सूर्यास्त से अगले सूर्योदय) को आठ-आठ बराबर भागों में "
                  "बाँटा जाता है। अमृत, शुभ और लाभ काम शुरू करने के लिए अच्छे हैं, चर यात्रा और विलासिता के लिए ठीक है पर स्थिरता "
                  "वाले कामों के लिए नहीं, और उद्वेग, रोग और काल में रोज़ के काम ही करें।"),
    "hora_lede": ("Today's hora for {city}: each hora is ruled by one planet and suits that planet's kind of work. The "
                  "first hora at sunrise belongs to the lord of the day, and the day and the night each have twelve.",
                  "{city} की आज की होरा: हर होरा एक ग्रह की होती है और उस ग्रह से जुड़े कामों के लिए अच्छी होती है। सूर्योदय की "
                  "पहली होरा वार के स्वामी की होती है, और दिन और रात दोनों में बारह-बारह होरा होती हैं।"),
    "day": ("Day choghadiya", "दिन का चौघड़िया"), "night": ("Night choghadiya", "रात का चौघड़िया"),
    "day_hora": ("Day hora", "दिन की होरा"), "night_hora": ("Night hora", "रात की होरा"),
    "time": ("Time", "समय"), "name": ("Choghadiya", "चौघड़िया"), "good_for": ("Good for", "किसके लिए"),
    "planet": ("Planet", "ग्रह"), "now": ("Now", "अभी"),
    "good": ("Good", "शुभ"), "neutral": ("Travel, luxury", "यात्रा, विलासिता"), "avoid": ("Avoid new work", "नया काम टालें"),
    "sunrise": ("Sunrise", "सूर्योदय"), "sunset": ("Sunset", "सूर्यास्त"), "next_sunrise": ("Next sunrise", "अगला सूर्योदय"),
    "rahu": ("Rahu Kaal today", "आज राहुकाल"),
    "rahu_note": ("Even in a good choghadiya, new work is traditionally not started in Rahu Kaal.",
                  "अच्छे चौघड़िये में भी राहुकाल में नया काम परम्परा से शुरू नहीं किया जाता।"),
    "other": ("Other cities", "अन्य शहर"),
    "next_day": ("next day", "अगले दिन"),
    "panchang": ("Today's full panchang", "आज का पूरा पंचांग"),
    "hora_tip": ("Jupiter, Venus, Mercury and Moon horas are the ones usually chosen for good work.",
                 "शुभ कामों के लिए प्रायः गुरु, शुक्र, बुध और चन्द्र की होरा चुनी जाती है।"),
    "times_note": ("All times are local and change with your city's sunrise and sunset.",
                   "सभी समय स्थानीय हैं और आपके शहर के सूर्योदय और सूर्यास्त से बदलते हैं।"),
}


def _periods_page(request, city, template, url_name):
    from django.shortcuts import redirect
    from ..utils import aaj_panchang as ap
    from ..utils import cities as cl
    from ..utils import day_periods as dp
    if city is not None and city == cl.DEFAULT:
        return redirect(url_name, permanent=True)
    place = cl.get(city or cl.DEFAULT)
    if place is None:
        raise Http404("City not found")
    custom = False
    if request.GET.get("city") or request.GET.get("place_id"):
        lat, lon, tz, name = user_location(request)
        place = {"key": "custom", "name": (name, name), "query": name, "lat": lat, "lon": lon, "tz": tz}
        custom = True
    d = _today(place["tz"]) if custom else ap.today_ist()
    data = dp.cached(place, d)
    hindi = _hindi(request)
    i = 1 if hindi else 0
    name = place["name"][i]
    lede = PERIOD_TEXT["chog_lede" if url_name == "choghadiya" else "hora_lede"][i].format(city=name)
    return render(request, template, {
        "p": data, "d": d, "d_label": _day_label(d, hindi), "place": place, "custom": custom, "lede": lede,
        "city_name": name, "cities": cl.CITIES, "here": place["key"], "default_city": cl.DEFAULT,
        "url_name": url_name, "T": PERIOD_TEXT, "year": d.year,
        "city": place["name"][0] if custom else "", "timezone": place["tz"],
        "weekday_hi": ["रविवार", "सोमवार", "मंगलवार", "बुधवार", "गुरुवार", "शुक्रवार", "शनिवार"][data["weekday_index"]],
        "panchang_url": (reverse("aaj_ka_panchang") if place["key"] in cl.ON_PANCHANG_INDEX or custom
                         else reverse("aaj_ka_panchang_city", args=[place["key"]])),
    })


def choghadiya(request, city=None):
    """/aaj-ka-choghadiya/ (Varanasi) and /aaj-ka-choghadiya/<city>/: today's 16 choghadiyas, the running one marked."""
    return _periods_page(request, city, "seo/choghadiya.html", "choghadiya")


def hora(request, city=None):
    """/aaj-ki-hora/ (Varanasi) and /aaj-ki-hora/<city>/: today's 24 horas, the running one marked."""
    return _periods_page(request, city, "seo/hora.html", "hora")


# ---------------------------------------------------------------------------
# Rashifal
# ---------------------------------------------------------------------------

def _rashifal_data(request):
    from ..utils import aaj_panchang as ap
    from ..utils import rashifal as rf
    d = ap.today_ist()
    data = rf.day(d)
    hindi = _hindi(request)
    lang, i = ("hi", 1) if hindi else ("en", 0)
    for r in data["readings"]:          # wording for this language: the LLM polish if it passed its checks, else the template
        p = (r.get("polished") or {}).get(lang) or {}
        r["say"] = {"headline": p.get("headline") or r["headline"][i],
                    **{a: p.get(a) or r["areas"][a]["text"][i] for a in rf.AREAS}}
    return d, data, hindi, {
        "d": d, "d_label": _day_label(d, hindi), "data": data, "T": rf.TEXT, "signs": data["readings"],
        "computed_at": data["computed_at"], "stamp_label": f"{_day_label(data['computed_at'], hindi)}, {data['computed_at']:%H:%M}",
        "weekday_hi": ["सोमवार", "मंगलवार", "बुधवार", "गुरुवार", "शुक्रवार", "शनिवार", "रविवार"][d.weekday()],
    }


def rashifal(request):
    """/rashifal/: today's rashifal for all 12 Moon signs (core/utils/rashifal.py), built at 05:30 IST."""
    from django.utils.http import http_date
    d, data, hindi, ctx = _rashifal_data(request)
    response = render(request, "seo/rashifal.html", ctx)
    response["Last-Modified"] = http_date(data["computed_at"].timestamp())
    return response


def rashifal_sign(request, sign):
    """/rashifal/<sign>/: one rashi's reading for today."""
    from django.utils.http import http_date
    from ..utils import rashifal as rf
    if sign not in rf.SLUGS:
        raise Http404("Rashi not found")
    d, data, hindi, ctx = _rashifal_data(request)
    r = data["readings"][rf.SLUGS.index(sign)]
    i = 1 if hindi else 0
    name = r["name"][i]
    icons = {"career": "💼", "money": "💰", "family": "❤️", "health": "🌿"}
    area_rows = [{"icon": icons[a], "title": rf.TEXT[a], "level": r["areas"][a]["level"],
                  "level_label": r["areas"][a]["level_label"], "text": r["say"][a]} for a in rf.AREAS]
    ctx.update(r=r, name=name, h1=rf.TEXT["sign_h1"][i].format(name=name), area_rows=area_rows,
               how=rf.TEXT["how"][i].format(name=name))
    response = render(request, "seo/rashifal_sign.html", ctx)
    response["Last-Modified"] = http_date(data["computed_at"].timestamp())
    return response


# ---------------------------------------------------------------------------
# Monthly Hindu calendar grid + printable PDF
# ---------------------------------------------------------------------------

def _calendar_month(year, month):
    """(year, month number) from the URL, or 404."""
    from ..utils import hindu_calendar as hc
    if month not in hc.MONTH_SLUGS or not hc.in_range(year):
        raise Http404("Month not found")
    return year, hc.MONTH_SLUGS.index(month) + 1


def _calendar_titles(year, m, hindi):
    from ..utils import hindu_calendar as hc
    label = f"{hc.MONTHS_HI[m - 1]} {year}" if hindi else f"{calendar.month_name[m]} {year}"
    return label, (f"हिन्दू कैलेंडर {label}" if hindi else f"Hindu Calendar {label}")


def hindu_calendar(request, year=None, month=None):
    """/hindu-calendar/ (this month) and /hindu-calendar/<year>/<month>/: tithi, nakshatra, festivals for each day."""
    from ..templatetags.vp import t
    from ..utils import aaj_panchang as ap
    from ..utils import hindu_calendar as hc
    today = ap.today_ist()
    current = year is None
    y, m = (today.year, today.month) if current else _calendar_month(year, month)
    cal = hc.month(y, m)
    hindi = _hindi(request)
    i = 1 if hindi else 0
    label, h1 = _calendar_titles(y, m, hindi)
    masas = []
    for purn, _ in cal["masas"]:
        if purn and purn not in masas:
            masas.append(purn)
    py, pm = hc.shift(y, m, -1)
    ny, nm = hc.shift(y, m, 1)
    link = lambda yy, mm: reverse("hindu_calendar_month", args=[yy, hc.MONTH_SLUGS[mm - 1]]) if hc.in_range(yy) else ""
    return render(request, "seo/hindu_calendar.html", {
        "cal": cal, "y": y, "m": m, "label": label, "h1": h1, "today": today, "current": current,
        "masas": [t(x) for x in masas],
        "weekdays": [w[i] for w in hc.WEEKDAYS], "weekdays_long": [w[i] for w in hc.WEEKDAYS_LONG],
        "prev_url": link(py, pm), "next_url": link(ny, nm),
        "prev_label": _calendar_titles(py, pm, hindi)[0], "next_label": _calendar_titles(ny, nm, hindi)[0],
        "pdf_url": reverse("hindu_calendar_pdf", args=[y, hc.MONTH_SLUGS[m - 1]]),
        "month_url": reverse("hindu_calendar_month", args=[y, hc.MONTH_SLUGS[m - 1]]),
        "year_months": [(hc.MONTHS_HI[k] if hindi else calendar.month_abbr[k + 1], reverse("hindu_calendar_month", args=[y, s]), k + 1 == m)
                        for k, s in enumerate(hc.MONTH_SLUGS)],
    })


def hindu_calendar_pdf(request, year, month):
    """The month as a one-page A4 PDF to print (free). Cached per month and language."""
    from django.core.cache import cache
    from ..pdf import calendar_pdf
    y, m = _calendar_month(year, month)
    hindi = _hindi(request)
    key = f"hindu-calendar-pdf:v{calendar_pdf.VERSION}:{y}-{m:02d}:{'hi' if hindi else 'en'}"
    data = cache.get(key)
    if data is None:
        site = getattr(settings, "SITE_URL", "") or request.build_absolute_uri("/").rstrip("/")
        data = calendar_pdf.render(y, m, hindi, site)
        cache.set(key, data, 30 * 24 * 3600)
    from ..utils import hindu_calendar as hc
    name = f"hindu-calendar-{hc.MONTH_SLUGS[m - 1]}-{y}{'-hindi' if hindi else ''}.pdf"
    response = HttpResponse(data, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="{name}"'
    response["X-Robots-Tag"] = "noindex"
    return response


# ---------------------------------------------------------------------------
# Vrat calendar
# ---------------------------------------------------------------------------

def vrat_hub(request):
    """/vrat/: the monthly vrats with the next date of each."""
    from ..utils import vrat as vr
    d = _today("Asia/Kolkata")
    hindi = _hindi(request)
    items = []
    for key, k in vr.KINDS.items():
        n = vr.next_date(key, d)
        items.append({"key": key, "k": k, "next": n,
                      "next_label": vr.label(n["date"], hindi, weekday=True) if n else ""})
    return render(request, "seo/vrat_hub.html", {"items": items, "year": d.year, "T": vr.TEXT, "d": d})


def vrat_list(request, kind, year):
    """/vrat/<kind>/<year>/: every date of one vrat in a year."""
    from ..utils import vrat as vr
    if kind not in vr.KINDS:
        raise Http404("Vrat not found")
    year = _year(year, None)
    d = _today("Asia/Kolkata")
    hindi = _hindi(request)
    rows = vr.rows(kind, year, today=d, hindi=hindi)
    if not rows:
        raise Http404("No dates")
    k = vr.KINDS[kind]
    i = 1 if hindi else 0
    name = k["name"][i]
    return render(request, "seo/vrat_list.html", {
        "kind": kind, "k": k, "year": year, "rows": rows, "next": next((r for r in rows if not r["past"]), None),
        "T": vr.TEXT, "kinds": vr.KINDS, "name": name,
        "h1": vr.TEXT["h1"][i].format(name=name, year=year),
        "count": vr.TEXT["count"][i].format(n=len(rows), year=year),
        "next_h": vr.TEXT["next_one"][i].format(name=name),
        "years": [y for y in range(d.year - 1, d.year + 4) if YEAR_MIN <= y <= YEAR_MAX],
        "is_ekadashi": kind == "ekadashi",
    })


def kumbh_mela(request):
    """Kumbh Mela: next melas with snan dates, Guru's sign windows behind them, Ardh / Purna / Maha Kumbh explained."""
    from ..utils import kumbh
    d = _today("Asia/Kolkata")
    melas = kumbh.upcoming(d)
    for m in melas:
        m["status_label"] = kumbh.STATUS[m["status"]]
        for s in m["snans"]:
            s["festival"] = _kumbh_festival(s)
    magh = []
    for slug, name in kumbh.MAGH_MELA_SNANS:
        y = d.year if d.month <= 3 else d.year + 1
        rows = fc.get_festival_by_slug(slug, y)
        if rows:
            magh.append({"name": name, "date": rows[0]["date"], "slug": slug, "year": y})
    return render(request, "seo/kumbh_mela.html", {
        "d": d, "melas": melas, "next": kumbh.next_snan(d), "guru_rows": kumbh.guru_rows(d),
        "status": kumbh.STATUS, "sections": kumbh.SECTIONS, "faq": kumbh.FAQ, "magh": magh,
        "magh_year": magh[0]["year"] if magh else d.year, "year": d.year,
    })


def _kumbh_festival(snan):
    """The (year, slug) of our own festival page for a Kumbh snan, when we have one for that day (a day either side)."""
    if not snan["slug"]:
        return None
    for f in fc.get_festival_by_slug(snan["slug"], snan["date"].year):
        if abs((f["date"] - snan["date"]).days) <= 1:
            return {"year": f["date"].year, "slug": snan["slug"], "date": f["date"]}
    return None


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


def indexnow_key(request, key):
    """/<INDEXNOW_KEY>.txt - proves to IndexNow (Bing) that the pinged URLs are ours."""
    from ..utils import indexnow
    if not indexnow.key() or key != indexnow.key():
        raise Http404("No such file")
    return HttpResponse(key, content_type="text/plain")


def ads_txt(request):
    client = getattr(settings, "ADSENSE_CLIENT_ID", "")
    if not client:
        raise Http404("AdSense not configured")
    pub = client.replace("ca-", "")
    return HttpResponse(f"google.com, {pub}, DIRECT, f08c47fec0942fa0\n", content_type="text/plain")
