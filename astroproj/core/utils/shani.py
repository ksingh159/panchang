# core/utils/shani.py
"""
Shani Sade Sati and Dhaiya over a lifetime, counted from the natal Moon sign (Lahiri, whole signs).

    Sade Sati  - Saturn in the 12th, 1st and 2nd sign from the Moon (about 7.5 years: rising, peak, setting)
    Dhaiya     - Saturn in the 4th (Kantak Shani) or the 8th (Ashtama Shani) from the Moon (about 2.5 years each)

Saturn's retrograde loops make it leave a sign and come back a few months later. Those short gaps are merged
into one period, so every row is one continuous stretch a person can plan around; the exact ingress dates of
each sign are kept in "phases" for Sade Sati.
"""
from datetime import datetime, timedelta
from functools import lru_cache

import pytz
import swisseph as swe

STEP_DAYS = 6               # Saturn's shortest retrograde dip into a sign is a few weeks
MERGE_GAP_DAYS = 400         # a retrograde exit shorter than this is not the end of the period
KIND = {12: "sade", 1: "sade", 2: "sade", 4: "kantak", 8: "ashtama"}
PHASE = {12: "rising", 1: "peak", 2: "setting"}
NAMES = {
    "sade": ("Sade Sati", "साढ़े साती"),
    "kantak": ("Dhaiya: Kantak Shani (4th from Moon)", "ढैया: कण्टक शनि (चन्द्र से चौथा)"),
    "ashtama": ("Dhaiya: Ashtama Shani (8th from Moon)", "ढैया: अष्टम शनि (चन्द्र से आठवाँ)"),
}
PHASE_NAMES = {"rising": ("rising", "आरोही"), "peak": ("peak", "मध्य (शिखर)"), "setting": ("setting", "अवरोही")}


def _saturn_sign(jd):
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    pos, _ = swe.calc_ut(jd, swe.SATURN, swe.FLG_SWIEPH)
    return int(((pos[0] - swe.get_ayanamsa_ut(jd)) % 360) // 30)


def _edge(jd_a, jd_b):
    """The moment (to ~1 hour) between jd_a and jd_b where Saturn's sign changes."""
    s = _saturn_sign(jd_a)
    while jd_b - jd_a > 0.04:
        mid = (jd_a + jd_b) / 2
        if _saturn_sign(mid) == s:
            jd_a = mid
        else:
            jd_b = mid
    return jd_b


def _to_date(jd):
    y, m, d, h = swe.revjul(jd)
    return (datetime(y, m, d) + timedelta(hours=h)).date()


@lru_cache(maxsize=256)
def _spans(jd_birth, moon_sign, years):
    """[(house from Moon, start jd, end jd)] for every Saturn stay in a sign from birth to birth + years."""
    from .panchang_engine import EPHE_PATH
    swe.set_ephe_path(EPHE_PATH)
    jd_end = jd_birth + years * 365.25
    out, jd = [], jd_birth
    cur = _saturn_sign(jd)
    start = jd
    while jd < jd_end:
        nxt = min(jd + STEP_DAYS, jd_end)
        s = _saturn_sign(nxt)
        if s != cur:
            edge = _edge(jd, nxt)
            out.append(((cur - moon_sign) % 12 + 1, start, edge))
            cur, start = _saturn_sign(edge), edge
        jd = nxt
    out.append(((cur - moon_sign) % 12 + 1, start, jd_end))
    return tuple(out)


def lifetime(birth_utc, moon_sign, years=100):
    """
    Sade Sati and Dhaiya periods from birth to birth + years, oldest first:
    [{"kind", "start", "end", "start_age", "end_age", "phases": [(phase, start, end)], "running", "past"}].
    A period that had already begun at birth starts at the birth date.
    """
    if birth_utc.tzinfo:
        birth_utc = birth_utc.astimezone(pytz.utc).replace(tzinfo=None)
    jd_b = swe.julday(birth_utc.year, birth_utc.month, birth_utc.day,
                      birth_utc.hour + birth_utc.minute / 60 + birth_utc.second / 3600)
    periods = []
    for house, a, b in _spans(round(jd_b, 4), moon_sign, years):
        kind = KIND.get(house)
        if not kind:
            continue
        last = periods[-1] if periods else None
        if last and last["kind"] == kind and a - last["jd_end"] < MERGE_GAP_DAYS:
            last["jd_end"] = b          # back after a retrograde exit (or the next sign of Sade Sati)
        else:
            periods.append({"kind": kind, "jd_start": a, "jd_end": b, "phases": []})
        if kind == "sade":
            periods[-1]["phases"].append((PHASE[house], a, b))
    birth_date = birth_utc.date()
    today = datetime.utcnow().date()
    out = []
    for p in periods:
        start, end = _to_date(p["jd_start"]), _to_date(p["jd_end"])
        if (end - start).days < 30:         # a sliver at the very start or end of the window
            continue
        firsts = []                         # each phase from Saturn's first entry into its sign
        for name, a, _b in p["phases"]:
            if name not in [f[0] for f in firsts]:
                firsts.append((name, _to_date(a)))
        phases = [(n, a, firsts[i + 1][1] if i + 1 < len(firsts) else end) for i, (n, a) in enumerate(firsts)]
        out.append({
            "kind": kind_name(p["kind"]), "key": p["kind"], "start": start, "end": end,
            "start_age": _age(birth_date, start), "end_age": _age(birth_date, end),
            "phases": [{"name": PHASE_NAMES[n], "start": a, "end": b} for n, a, b in phases],
            "running": start <= today <= end, "past": end < today,
        })
    return out


def kind_name(key):
    return NAMES[key]


def _age(birth, d):
    return d.year - birth.year - ((d.month, d.day) < (birth.month, birth.day))


def for_kundali(k, years=100):
    """lifetime() for a saved Kundali, or [] when its Moon is missing."""
    moon = ((k.planetary_positions or {}).get("Moon") or {}).get("longitude_sidereal")
    if moon is None:
        return []
    tz = pytz.timezone(k.birth_timezone or "Asia/Kolkata")
    bd = k.birth_date
    local = bd.astimezone(tz) if bd.tzinfo else tz.localize(bd)
    return lifetime(local.astimezone(pytz.utc), int(float(moon) % 360 // 30), years)
