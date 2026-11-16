# core/views/naam_views.py
"""Naamkaran: name letters and suggestions from a baby's birth details, with the naming-day muhurat."""
from datetime import date, datetime, time

import pytz
import swisseph as swe
from django.shortcuts import render

from ..utils import naamkaran as nk
from ..utils.astro_calculations import get_panchang
from ..utils.dosha_remedies import gand_mool
from .seo_views import user_location


def _moon_lahiri(dt_utc):
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    jd = swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, dt_utc.hour + dt_utc.minute / 60 + dt_utc.second / 3600)
    pos, _ = swe.calc_ut(jd, swe.MOON, swe.FLG_SWIEPH)
    return (pos[0] - swe.get_ayanamsa_ut(jd)) % 360


def naamkaran(request):
    g = request.GET
    gender = g.get("gender") if g.get("gender") in ("m", "f") else ""
    ctx = {"gyaan": nk.GYAAN, "nakshatras": [(i, n[0], n[1]) for i, n in enumerate(nk.NAKSHATRAS)],
           "gender": gender, "form": g}
    result = None
    if g.get("nak") not in (None, ""):          # parents who already know the nakshatra and pada
        try:
            nak = min(26, max(0, int(g["nak"])))
            pada = min(4, max(1, int(g.get("pada") or 1)))
        except ValueError:
            nak, pada = 0, 1
        span = 360 / 27
        result = nk.reading(nak * span + (pada - 0.5) * span / 4, gender)
    elif g.get("date"):
        try:
            d = date.fromisoformat(g["date"])
            t = time.fromisoformat(g.get("time") or "12:00")
        except ValueError:
            ctx["error"] = "Please enter a valid date and time."
            return render(request, "naamkaran.html", ctx)
        lat, lon, tz_name, city = user_location(request)
        tz = pytz.timezone(tz_name)
        birth = tz.localize(datetime.combine(d, t))
        moon = _moon_lahiri(birth.astimezone(pytz.utc))
        result = nk.reading(moon, gender)
        result["birth"] = birth
        result["city"] = city
        result["time_unknown"] = not g.get("time")
        gm = gand_mool(moon)
        result["gand_mool"] = gm if gm.get("present") else None
        today = datetime.now(tz).date()
        if (today - d).days <= 20:              # the naming days are still ahead: show their muhurat
            def morning(day):
                try:
                    return get_panchang(target_date=tz.localize(datetime.combine(day, time(9, 0))), lat=lat, lon=lon,
                                        timezone_str=tz_name, city_name=city)
                except Exception:
                    return {}
            result["days"] = nk.namakarana_days(d, morning)
    ctx["result"] = result
    return render(request, "naamkaran.html", ctx)
