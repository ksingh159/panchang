# core/utils/panchang_engine.py
"""
Fast, location-independent panchang event engine.

Tithi, nakshatra, yoga, karana, paksha, lunar month (masa), Moon sign and
Sun sign (sankranti) change at the same *instant* everywhere on Earth - only
the local clock time differs.  So instead of re-scanning the ephemeris on
every request we compute every transition of a calendar year once, store it
in the ``PanchangEvent`` table and answer all later questions ("when is
Shukla Ekadashi in 2047?", "which month is Adhik in 2039?") with a single
indexed query.  A year that nobody has asked for yet is computed on demand
(~1 s) and saved, so the next user gets it instantly.

All angles are sidereal (True Chitrapaksha ayanamsa, same as get_panchang).
"""
import math
from datetime import datetime, timedelta

import pytz
import swisseph as swe

from .constants import NAKSHATRA_NAMES, YOGA_NAMES, ZODIAC_SIGNS, TITHI_NAMES

EPHE_PATH = None
try:
    from django.conf import settings
    EPHE_PATH = str(settings.BASE_DIR / "core" / "data" / "sweph")
except Exception:  # pragma: no cover - engine usable outside Django
    pass

if EPHE_PATH:
    swe.set_ephe_path(EPHE_PATH)

SID_MODE = swe.SIDM_TRUE_CITRA
_FLAGS = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED

LUNAR_MONTHS = [
    "Chaitra", "Vaishakha", "Jyeshtha", "Ashadha", "Shravana", "Bhadrapada",
    "Ashwina", "Kartika", "Margashirsha", "Pausha", "Magha", "Phalguna",
]

# Ritu by sidereal solar sign pairs (Meena+Mesha = Vasanta, ...)
RITU_BY_SIGN = [
    "Vasanta", "Grishma", "Grishma", "Varsha", "Varsha", "Sharad",
    "Sharad", "Hemanta", "Hemanta", "Shishira", "Shishira", "Vasanta",
]

KARANA_MOVABLE = ["Bava", "Balava", "Kaulava", "Taitila", "Garaja", "Vanija", "Vishti"]


def karana_name(k):
    """Karana for half-tithi number k (0..59)."""
    if k == 0:
        return "Kimstughna"
    if k == 57:
        return "Shakuni"
    if k == 58:
        return "Chatushpada"
    if k == 59:
        return "Naga"
    return KARANA_MOVABLE[(k - 1) % 7]


def tithi_label(n):
    """Tithi number 0..29 -> (paksha, name)."""
    paksha = "Shukla" if n < 15 else "Krishna"
    i = n % 15
    if i == 14:
        name = "Purnima" if paksha == "Shukla" else "Amavasya"
    else:
        name = TITHI_NAMES[i]
    return paksha, name


# ---------------------------------------------------------------------------
# Low level ephemeris helpers
# ---------------------------------------------------------------------------

def _sun_moon(jd):
    swe.set_sid_mode(SID_MODE)
    s = swe.calc_ut(jd, swe.SUN, _FLAGS)[0]
    m = swe.calc_ut(jd, swe.MOON, _FLAGS)[0]
    return s[0], s[3], m[0], m[3]


def angle_and_speed(jd, key):
    """Return (angle in degrees 0-360, speed in deg/day) of a monotonic quantity."""
    s, ss, m, ms = _sun_moon(jd)
    if key in ("tithi", "karana", "paksha"):
        return (m - s) % 360, ms - ss
    if key in ("nakshatra", "moon_sign"):
        return m % 360, ms
    if key == "yoga":
        return (s + m) % 360, ss + ms
    if key in ("sun_sign", "sun_nakshatra"):
        return s % 360, ss
    raise ValueError(key)


# ---------------------------------------------------------------------------
# Drik (sayana) ritu: Ayurveda's seasons follow the real solstices and equinoxes,
# so they are read from the tropical Sun (Shishira opens at the winter solstice).
# Puja, vrata and mantra calendars keep the nirayana ritu of RITU_BY_SIGN on the
# sidereal Sun.  This is computed live (6 boundaries a year), not stored.
# ---------------------------------------------------------------------------

def _sayana_sun(jd):
    s = swe.calc_ut(jd, swe.SUN, swe.FLG_SWIEPH | swe.FLG_SPEED)[0]
    return s[0] % 360, s[3]


def _solve_sayana(target, jd_guess):
    jd = jd_guess
    for _ in range(30):
        ang, spd = _sayana_sun(jd)
        step = ((target - ang + 180.0) % 360.0 - 180.0) / spd
        jd += step
        if abs(step) < 1e-6:
            break
    return jd


def sayana_ritu_at(jd):
    ang, _ = _sayana_sun(jd)
    return RITU_BY_SIGN[int(ang // 30) % 12]


def sayana_ritu_windows(jd_start, jd_end):
    """[(start_jd, end_jd, ritu)] of Drik ritus overlapping jd_start..jd_end (boundaries at 330, 30, 90 ... deg)."""
    ang, spd = _sayana_sun(jd_start)
    first = math.floor((ang - 330) / 60) * 60 + 330
    jd = _solve_sayana(first % 360, jd_start - ((ang - first) % 360) / spd)
    edges = [jd]
    target = first
    while edges[-1] <= jd_end:
        target += 60
        edges.append(_solve_sayana(target % 360, edges[-1] + 60 / 0.9856))
    return [(a, b, sayana_ritu_at((a + b) / 2)) for a, b in zip(edges, edges[1:])]


SEGMENTS = {
    "tithi": 12.0,
    "karana": 6.0,
    "paksha": 180.0,
    "nakshatra": 360.0 / 27,
    "yoga": 360.0 / 27,
    "moon_sign": 30.0,
    "sun_sign": 30.0,
    "sun_nakshatra": 360.0 / 27,
}


def solve_angle(key, target, jd_guess, tol_days=1e-6):
    """Newton iteration: JD at which ``key`` angle equals ``target`` (deg)."""
    jd = jd_guess
    for _ in range(30):
        ang, spd = angle_and_speed(jd, key)
        diff = (target - ang + 180.0) % 360.0 - 180.0
        step = diff / spd
        jd += step
        if abs(step) < tol_days:
            break
    return jd


def next_transition(jd, key):
    """JD of the next boundary of ``key`` after ``jd`` (fast replacement for scanning)."""
    seg = SEGMENTS[key]
    ang, spd = angle_and_speed(jd, key)
    target = (math.floor(ang / seg) + 1) * seg % 360
    dist = (target - ang) % 360
    if dist < 1e-9:
        dist = seg
        target = (target + seg) % 360
    return solve_angle(key, target, jd + dist / spd)


def prev_transition(jd, key):
    """JD of the boundary of ``key`` at or before ``jd`` (start of current segment)."""
    seg = SEGMENTS[key]
    ang, spd = angle_and_speed(jd, key)
    target = math.floor(ang / seg) * seg % 360
    dist = (ang - target) % 360
    return solve_angle(key, target, jd - dist / spd)


def index_at(jd, key):
    ang, _ = angle_and_speed(jd, key)
    return int(ang // SEGMENTS[key]) % int(round(360 / SEGMENTS[key]))


# ---------------------------------------------------------------------------
# Time conversion
# ---------------------------------------------------------------------------

def dt_to_jd(dt):
    """Aware (or naive-UTC) datetime -> Julian day UT."""
    if dt.tzinfo is not None:
        dt = dt.astimezone(pytz.utc).replace(tzinfo=None)
    h = dt.hour + dt.minute / 60 + (dt.second + dt.microsecond / 1e6) / 3600
    return swe.julday(dt.year, dt.month, dt.day, h)


def jd_to_utc(jd):
    """Julian day UT -> naive UTC datetime (rounded to the second)."""
    y, mo, d, h = swe.revjul(jd)
    base = datetime(y, mo, d)
    return base + timedelta(seconds=round(h * 3600))


def jd_to_local(jd, tz):
    if isinstance(tz, str):
        tz = pytz.timezone(tz)
    return pytz.utc.localize(jd_to_utc(jd)).astimezone(tz)


# ---------------------------------------------------------------------------
# Year computation
# ---------------------------------------------------------------------------

def _boundaries(key, jd_start, jd_end):
    """All boundary JDs of ``key`` in (jd_start, jd_end]."""
    out = []
    jd = jd_start
    while True:
        jd = next_transition(jd + 1e-5, key)
        if jd > jd_end:
            break
        out.append(jd)
    return out


def _intervals(key, jd_start, jd_end):
    """[(start_jd, end_jd, index)] covering jd_start..jd_end for ``key``."""
    bounds = _boundaries(key, jd_start, jd_end)
    first = prev_transition(jd_start, key)
    edges = [first] + bounds + [next_transition(bounds[-1] + 1e-5, key) if bounds else next_transition(jd_start, key)]
    res = []
    for a, b in zip(edges, edges[1:]):
        res.append((a, b, index_at((a + b) / 2, key)))
    return res


def _event(kind, number, name, a, b, **extra):
    return {
        "kind": kind,
        "number": number,
        "name": name,
        "start_jd": a,
        "end_jd": b,
        "extra": extra,
    }


def compute_lunar_months(jd_start, jd_end):
    """
    Amanta lunar months (new moon to new moon) with Adhik/Kshaya detection,
    plus the Purnimanta naming of each paksha (North Indian / Varanasi usage).

    Rule: the month takes the name of the rashi the Sun enters during it
    (Sun entering Mesha -> Vaishakha ...).  A month with no sankranti is Adhik
    and borrows the name of the following month.
    """
    pak = _intervals("paksha", jd_start - 40, jd_end + 40)  # index 0 = Shukla, 1 = Krishna
    new_moons = [a for (a, b, i) in pak if i == 0]
    months = []
    for nm, nm_next in zip(new_moons, new_moons[1:]):
        r0 = index_at(nm, "sun_sign")
        r1 = index_at(nm_next, "sun_sign")
        adhik = r0 == r1
        # Sun in Meena(11) at the starting new moon -> Chaitra(0)
        name_idx = (r0 + 1) % 12
        kshaya = (r1 - r0) % 12 == 2
        months.append({"start": nm, "end": nm_next, "idx": name_idx, "adhik": adhik, "kshaya": kshaya})

    events = []
    for k, m in enumerate(months):
        name = LUNAR_MONTHS[m["idx"]]
        events.append(_event("amanta_masa", m["idx"], name, m["start"], m["end"],
                             adhik=m["adhik"], kshaya=m["kshaya"]))
    # Purnimanta: Shukla paksha keeps the amanta name; Krishna paksha belongs
    # to the next month - except inside an Adhik month, which runs Amavasya to
    # Amavasya in North Indian panchangs as well.
    for k, m in enumerate(months):
        full = [a for (a, b, i) in pak if i == 1 and m["start"] < a < m["end"]]
        if not full:
            continue
        fm = full[0]
        events.append(_event("paksha", 0, "Shukla", m["start"], fm,
                             masa_amanta=LUNAR_MONTHS[m["idx"]], masa_purnimanta=LUNAR_MONTHS[m["idx"]],
                             adhik=m["adhik"]))
        if m["adhik"]:
            p_idx, p_adhik = m["idx"], True
        else:
            nxt = months[k + 1] if k + 1 < len(months) else None
            p_idx = nxt["idx"] if nxt else (m["idx"] + 1) % 12
            p_adhik = False
        events.append(_event("paksha", 1, "Krishna", fm, m["end"],
                             masa_amanta=LUNAR_MONTHS[m["idx"]], masa_purnimanta=LUNAR_MONTHS[p_idx],
                             adhik=m["adhik"], purnimanta_adhik=p_adhik))
    return events


def compute_year_events(year):
    """
    Every panchang transition whose start lies in the given Gregorian year (UTC).
    Returns a list of plain dicts (see ``_event``).
    """
    y0 = swe.julday(year, 1, 1, 0.0)
    y1 = swe.julday(year + 1, 1, 1, 0.0)
    events = []

    for a, b, i in _intervals("tithi", y0, y1):
        paksha, name = tithi_label(i)
        events.append(_event("tithi", i, name, a, b, paksha=paksha))
    for a, b, i in _intervals("karana", y0, y1):
        events.append(_event("karana", i, karana_name(i), a, b))
    for a, b, i in _intervals("nakshatra", y0, y1):
        events.append(_event("nakshatra", i, NAKSHATRA_NAMES[i], a, b))
    for a, b, i in _intervals("yoga", y0, y1):
        events.append(_event("yoga", i, YOGA_NAMES[i], a, b))
    for a, b, i in _intervals("moon_sign", y0, y1):
        events.append(_event("moon_sign", i, ZODIAC_SIGNS[i], a, b))
    for a, b, i in _intervals("sun_nakshatra", y0, y1):
        events.append(_event("sun_nakshatra", i, NAKSHATRA_NAMES[i], a, b))
    for a, b, i in _intervals("sun_sign", y0, y1):
        events.append(_event("sun_sign", i, ZODIAC_SIGNS[i], a, b, ritu=RITU_BY_SIGN[i]))

    events.extend(compute_lunar_months(y0, y1))

    # keep only events that start inside the year (neighbouring years own the rest)
    return [e for e in events if y0 <= e["start_jd"] < y1]


# ---------------------------------------------------------------------------
# Convenience: snapshot of the five limbs at an instant (no DB needed)
# ---------------------------------------------------------------------------

def limbs_at(jd):
    """Tithi/nakshatra/yoga/karana at ``jd`` with exact start/end JDs."""
    out = {}
    for key in ("tithi", "nakshatra", "yoga", "karana", "moon_sign", "sun_sign"):
        idx = index_at(jd, key)
        out[key] = {
            "index": idx,
            "start_jd": prev_transition(jd, key),
            "end_jd": next_transition(jd, key),
        }
    return out


# ---------------------------------------------------------------------------
# Rise / set (Swiss Ephemeris; upper limb with refraction, like printed panchangs)
# ---------------------------------------------------------------------------

def _rise_set_jd(jd_start, body, which, lat, lon, alt=0.0):
    flag = swe.CALC_RISE if which == "rise" else swe.CALC_SET
    res, tret = swe.rise_trans(jd_start, body, flag, (lon, lat, alt), 1013.25, 15.0, swe.FLG_SWIEPH)
    return tret[0] if res == 0 else None


def local_midnight_jd(d, tz):
    if isinstance(tz, str):
        tz = pytz.timezone(tz)
    return dt_to_jd(tz.localize(datetime(d.year, d.month, d.day)))


def sun_times(d, lat, lon, tz):
    """Sunrise and sunset (aware datetimes) for local date ``d``."""
    jd0 = local_midnight_jd(d, tz)
    sr = _rise_set_jd(jd0, swe.SUN, "rise", lat, lon)
    ss = _rise_set_jd(sr if sr else jd0, swe.SUN, "set", lat, lon)
    return (jd_to_local(sr, tz) if sr else None, jd_to_local(ss, tz) if ss else None)


def moonrise_on(d, lat, lon, tz):
    """Moonrise on local date ``d`` or None if the Moon does not rise that day."""
    jd0 = local_midnight_jd(d, tz)
    mr = _rise_set_jd(jd0, swe.MOON, "rise", lat, lon)
    if mr is None or mr >= jd0 + 1:
        return None
    return jd_to_local(mr, tz)
