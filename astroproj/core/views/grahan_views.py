# core/views/grahan_views.py
"""Grahan (eclipse) calendar with a live globe, and the Ritucharya / Aahaar guide."""
from datetime import date, datetime, timedelta

import pytz
from django.http import Http404, JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.cache import cache_control

from ..utils import aahaar as ah
from ..utils import aahaar_foods as foods
from ..utils.aahaar_regions import region_for_place
from ..utils import grahan as gr
from ..utils import muhurat as mu
from ..utils import panchang_store as ps
from ..utils.astro_calculations import get_panchang
from ..utils.panchang_engine import RITU_BY_SIGN
from .seo_views import YEAR_MIN, YEAR_MAX, _today, user_location


def _card(e, lat, lon, tz):
    view = gr.local_view(e, lat, lon, tz)
    return {**e, "when": gr.local_date(e, tz), "local": view}


def grahan_calendar(request, year=None):
    from django.utils.translation import gettext
    lat, lon, tz, city = user_location(request)
    today = _today(tz)
    if year is None:
        rows = gr.upcoming(today, 6)
        heading = gettext("Upcoming Surya and Chandra Grahan")
    else:
        if not (YEAR_MIN <= year <= YEAR_MAX):
            raise Http404("Year out of range")
        rows = gr.eclipses_in_year(year)
        heading = gettext("Surya and Chandra Grahan %(year)s") % {"year": year}
    return render(request, "grahan/calendar.html", {
        "cards": [_card(e, lat, lon, tz) for e in rows], "heading": heading, "year": year,
        # rolling window: moves forward on its own every 1 January; any year 1900-2200 also works by URL
        "this_year": today.year, "past_years": range(today.year - 1, today.year - 11, -1),
        "years": range(today.year, today.year + 6),
        "city": city, "timezone": tz,
    })


def grahan_detail(request, slug):
    e = gr.find(slug)
    if not e:
        raise Http404("No grahan on this date")
    lat, lon, tz, city = user_location(request)
    from ..utils import panchang_engine as pe, prefs
    system = prefs.month_system(request)
    # Half a day before greatest eclipse: still inside the Amavasya / Purnima that names the month
    # (at a solar eclipse's peak the Moon has often just passed conjunction into the next Shukla paksha).
    month = ps.lunar_month_at(pe.jd_to_utc(e["jd"] - 0.5)) or {}
    masa = month.get("amanta" if system == "amanta" else "purnimanta") or ""
    if masa and month.get("amanta_adhik" if system == "amanta" else "purnimanta_adhik", month.get("adhik")):
        masa = "Adhik " + masa
    return render(request, "grahan/detail.html", {
        "masa": masa, "month_label": prefs.month_label(system), "paksha": month.get("paksha", ""),
        "e": e, "when": gr.local_date(e, tz), "local": gr.local_view(e, lat, lon, tz),
        "upasana": gr.UPASANA[e["kind"]], "do_list": gr.COMMON_DO, "dont_list": gr.COMMON_DONT,
        "exempt": gr.EXEMPT, "safety": gr.SAFETY,
        "city": city, "timezone": tz, "lat": lat, "lon": lon,
    })


@cache_control(public=True, max_age=86400)
def grahan_globe(request, slug):
    e = gr.find(slug)
    if not e:
        raise Http404("No grahan on this date")
    return JsonResponse(gr.globe_data(e))


def _ritu_window(d, tz):
    """Drik (sayana) ritu around ``d``, its dates, and whether ``d`` is in Ritu Sandhi (the 14-day changeover).

    Ayurveda's ritucharya follows the tropical Sun, as Drik panchangs print it; puja and mantra
    calendars keep the nirayana ritu (see panchang_engine.sayana_ritu_windows).
    """
    from ..utils import panchang_engine as pe
    mid = pe.dt_to_jd(datetime.combine(d, datetime.min.time()))
    stamps = [{"ritu": ritu, "start": pe.jd_to_local(a, tz), "end": pe.jd_to_local(b, tz)}
              for a, b, ritu in pe.sayana_ritu_windows(mid - 100, mid + 100)]
    current = next((s for s in stamps if s["start"].date() <= d <= s["end"].date()), None)
    if not current:
        return None
    position = stamps.index(current)
    upcoming = stamps[position + 1]["ritu"] if position + 1 < len(stamps) else None
    previous = stamps[position - 1]["ritu"] if position else None
    days_left = (current["end"].date() - d).days
    days_in = (d - current["start"].date()).days
    sandhi = None
    if days_left <= 7 and upcoming:
        sandhi = (current["ritu"], upcoming)
    elif days_in <= 7 and previous:
        sandhi = (previous, current["ritu"])
    return {**current, "next": upcoming, "days_left": days_left, "sandhi": sandhi}


def aahaar_context(d, lat, lon, tz_name, city, now_time=None, region=None, month_system="purnimanta", lang=None):
    """Everything the Aahaar page and its PDF show for date ``d`` at this place, in ``lang`` (default: the
    request's language). The data in aahaar*.py is English; aahaar_hi supplies the Hindi."""
    from django.utils.translation import get_language
    lang = lang or ("hi" if (get_language() or "").startswith("hi") else "en")
    tz = pytz.timezone(tz_name)
    moment = tz.localize(datetime.combine(d, now_time or timezone.now().astimezone(tz).time()))
    p = get_panchang(target_date=moment, lat=lat, lon=lon, timezone_str=tz_name, city_name=city)

    ritu_name = p.get("ritu_sayana", "").split()[0] if p.get("ritu_sayana") else ""
    nirayana_ritu = p.get("ritu", "").split()[0] if p.get("ritu") else ""
    window = _ritu_window(d, tz_name)
    if window:
        ritu_name = window["ritu"]
    # The folk month verse and Chaturmas tables key on the month as the person counts it.
    month_key = "amanta_month" if month_system == "amanta" else "purnimanta_month"
    masa = (p.get(month_key) or p.get("purnimanta_month") or "").replace("Adhik", "").strip()
    weekday = d.strftime("%A")
    tithi_no = ah.tithi_number(p.get("paksha_tithi"))
    season = foods.SEASON_OF_RITU.get(ritu_name, "summer")
    ritu = ah.RITU.get(ritu_name)
    local_region = region_for_place(city, lat, lon)
    ctx = {
        "date": d, "prev": d - timedelta(days=1), "next": d + timedelta(days=1),
        "city": city, "timezone": tz_name, "lat": lat, "lon": lon, "weekday": weekday, "masa": masa,
        "month_system": month_system, "month_label": "Amanta" if month_system == "amanta" else "Purnimanta",
        "paksha_tithi": p.get("paksha_tithi"), "nakshatra": p.get("nakshatra"),
        "ritu_name": ritu_name, "ritu": ritu, "window": window, "nirayana_ritu": nirayana_ritu,
        "all_ritus": ah.RITU, "maas": ah.MAAS.get(masa), "maas_table": ah.MAAS,
        "chaturmas": ah.chaturmas_item(masa, p.get("paksha_tithi")), "tithi_avoid": ah.TITHI_AVOID.get(tithi_no),
        "vaar": ah.VAAR[weekday], "vaar_table": ah.VAAR, "tithi_table": ah.TITHI_AVOID,
        "doshas": ah.DOSHA, "dosha_clock": ah.DOSHA_CLOCK, "meal_rules": ah.MEAL_RULES,
        "disclaimer": ah.DISCLAIMER, "classical_sources": ah.CLASSICAL_SOURCES,
        "rhythm": ah.daily_rhythm(d, lat, lon, tz_name),
        "season": season, "season_info": foods.SEASONS[season], "seasons": foods.SEASONS,
        "regions": [dict(r, sayings=ah.sayings_for(r["key"])) for r in foods.REGIONS],
        "my_region": region or local_region or foods.REGIONS[0]["key"], "local_region": local_region,
        "guidance": ah.day_guidance(ritu_name, masa, p.get("paksha_tithi"), weekday, lang=lang), "lang": lang,
        "ritu_names_note": ah.RITU_NAMES_NOTE,
        "ingredient_groups": [{"key": k, "label": v, "rows": foods.ingredient_rows(k)}
                              for k, v in foods.INGREDIENT_GROUPS.items()],
        "age_groups": foods.AGE_GROUPS, "fitness": foods.FITNESS, "workout_timing": foods.WORKOUT_TIMING,
        "focus_dosha": (ritu or {}).get("focus", ""),
        "vaar_planet_img": VAAR_IMAGES.get(weekday),
    }
    if lang == "hi":
        _aahaar_in_hindi(ctx)
    return ctx


def _aahaar_in_hindi(ctx):
    """Swap the English data in an aahaar context for Hindi, leaving keys, codes and CSS values alone."""
    from ..utils.aahaar_hi import localize
    for key in ("ritu", "all_ritus", "maas", "maas_table", "chaturmas", "tithi_avoid", "vaar", "vaar_table", "doshas",
                "meal_rules", "disclaimer", "classical_sources", "regions", "ritu_names_note", "age_groups", "fitness",
                "workout_timing"):
        ctx[key] = localize(ctx[key])
    if ctx["rhythm"]:
        ctx["rhythm"] = dict(ctx["rhythm"], pahars=localize(ctx["rhythm"]["pahars"]))
    groups = []
    for g in ctx["ingredient_groups"]:
        rows = [dict(localize(r), name=r["hindi"], hindi="") for r in g["rows"]]
        groups.append(dict(g, rows=rows))
    ctx["ingredient_groups"] = groups


VAAR_IMAGES = {"Sunday": "sun", "Monday": "moon", "Tuesday": "mars", "Wednesday": "mercury", "Thursday": "jupiter",
               "Friday": "venus", "Saturday": "saturn"}


def aahaar(request):
    from ..utils import payments
    lat, lon, tz_name, city = user_location(request)
    d = _today(tz_name)
    if request.GET.get("date"):
        try:
            d = date.fromisoformat(request.GET["date"])
        except ValueError:
            pass
    from ..utils import prefs
    context = aahaar_context(d, lat, lon, tz_name, city, region=prefs.food_region(request, city, lat, lon),
                             month_system=prefs.month_system(request))
    context.update({"native_state": prefs.get(request, "native_state"),
                    "saved_region": prefs.clean("food_region", prefs.get(request, "food_region"))})
    currency = payments.detect_currency(request)
    context.update({
        "pdf_currency": currency, "pdf_price": payments.format_price("aahaar_pdf", currency),
        "pdf_other_currency": "USD" if currency == "INR" else "INR",
        "pdf_other_price": payments.format_price("aahaar_pdf", "USD" if currency == "INR" else "INR"),
    })
    return render(request, "aahaar.html", context)
