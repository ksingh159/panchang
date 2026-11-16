# core/utils/grahan.py
"""
Surya and Chandra Grahan: when, where it is seen, and whether sutak applies.

All circumstances come from Swiss Ephemeris.  Results are deterministic, so the
global catalogue and the (slower) globe data are kept in the shared Django cache.

Sutak rules followed (Dharma Sindhu / Nirnaya Sindhu, as used by Kashi panchangs):
  * applies only where the grahan is actually visible
  * 4 prahar (12 hours) before sparsha for Surya Grahan, 3 prahar (9 hours) for Chandra Grahan
  * ends at moksha
  * a penumbral lunar eclipse (Upachchhaya) is not counted as a grahan
"""
import pytz
import swisseph as swe
from django.core.cache import cache

from . import panchang_engine as pe
from .constants import NAKSHATRA_NAMES, ZODIAC_SIGNS

CACHE_V = "grahan:v1"
CACHE_TTL = 60 * 60 * 24 * 90
_FLAG = swe.FLG_SWIEPH

SUTAK_HOURS = {"solar": 12, "lunar": 9}
NAME = {"solar": "Surya Grahan", "lunar": "Chandra Grahan"}
NAME_EN = {"solar": "Solar Eclipse", "lunar": "Lunar Eclipse"}
HINDI = {"solar": "सूर्य ग्रहण", "lunar": "चन्द्र ग्रहण"}

# (label, lat, lon) sampled to say in words where an eclipse is seen
SAMPLE_PLACES = [
    ("India", 28.61, 77.21), ("Nepal", 27.72, 85.32), ("Sri Lanka", 6.93, 79.86), ("UAE", 25.20, 55.27),
    ("Singapore", 1.35, 103.82), ("Japan", 35.68, 139.69), ("Australia", -33.87, 151.21),
    ("East Africa", -1.29, 36.82), ("West Africa", 6.52, 3.38), ("Egypt", 30.04, 31.24), ("UK", 51.51, -0.13),
    ("Germany", 52.52, 13.40), ("Canada", 43.65, -79.38), ("USA East", 40.71, -74.01), ("USA West", 34.05, -118.24),
    ("Brazil", -23.55, -46.63), ("Mauritius", -20.16, 57.50), ("Fiji", -18.14, 178.44),
]

COMMON_DO = [
    "Japa of your Ishta mantra or Guru mantra: japa done during grahan is held to give many times the usual fruit.",
    "Bhajan, meditation and quiet reading of scripture.",
    "Place tulsi leaves or kusha grass in stored water, milk and food before sutak begins.",
    "After moksha: bathe, sprinkle Ganga jal in the home and puja room, then cook fresh food.",
    "Give daan after moksha: grain, clothes or money to those in need.",
]
COMMON_DONT = [
    "No cooking or eating during the grahan; during sutak healthy adults also avoid food.",
    "No new work, shubh muhurat, or touching of temple idols (temples close during sutak).",
    "No sleeping during the grahan itself, except for children, the elderly and the unwell.",
    "Avoid cutting, sewing and similar sharp work during the grahan (customary, especially for expectant mothers).",
]
EXEMPT = ("Children, the elderly, the sick and expectant mothers are exempt from the fast and may take food, water and "
          "medicine as needed. Never skip prescribed medicine.")

UPASANA = {
    "solar": {
        "deity": "Surya Narayan",
        "mantras": [("ॐ घृणिः सूर्याय नमः", "Surya mantra, 108 times or more"),
                    ("ॐ ह्रां ह्रीं ह्रौं सः सूर्याय नमः", "Surya beej mantra"),
                    ("Gayatri Mantra", "as many malas as you can sustain through the grahan")],
        "paath": ["Aditya Hridaya Stotra", "Surya Ashtakam"],
        "daan": "wheat, jaggery, copper, red cloth, after moksha",
        "fast": "Fast from the start of sutak until moksha and bath. The evening meal is taken after that.",
    },
    "lunar": {
        "deity": "Chandra Dev and Bhagwan Shiva",
        "mantras": [("ॐ सों सोमाय नमः", "Chandra mantra, 108 times or more"),
                    ("ॐ श्रां श्रीं श्रौं सः चन्द्रमसे नमः", "Chandra beej mantra"),
                    ("Maha Mrityunjaya Mantra", "for health and protection"),
                    ("ॐ नमः शिवाय", "Panchakshari japa")],
        "paath": ["Shiva Chalisa", "Chandra Kavach"],
        "daan": "rice, milk, white cloth, silver, sugar, after moksha",
        "fast": "Fast from the start of sutak until moksha and bath. A light meal may follow.",
    },
}
SAFETY = ("Never look at a solar eclipse with the naked eye, sunglasses or through a phone. Use only certified "
          "ISO 12312-2 eclipse glasses or a pinhole projector. A lunar eclipse is safe to view.")


def _utc(jd):
    return pytz.utc.localize(pe.jd_to_utc(jd).replace(tzinfo=None))


def _sidereal_position(jd, body):
    swe.set_sid_mode(pe.SID_MODE)
    lon = swe.calc_ut(jd, body, pe._FLAGS)[0][0] % 360
    return int(lon // 30), int(lon // (360 / 27))


def _solar_type(flag):
    if flag & swe.ECL_ANNULAR_TOTAL:
        return "Hybrid"
    if flag & swe.ECL_TOTAL:
        return "Total"
    if flag & swe.ECL_ANNULAR:
        return "Annular"
    return "Partial"


def _lunar_type(flag):
    if flag & swe.ECL_TOTAL:
        return "Total"
    if flag & swe.ECL_PARTIAL:
        return "Partial"
    return "Penumbral"


def _entry(kind, jd, subtype, begin, end, magnitude, contacts=None):
    d = _utc(jd).date()
    sign, nak = _sidereal_position(jd, swe.SUN if kind == "solar" else swe.MOON)
    return {
        "kind": kind, "subtype": subtype, "jd": jd, "begin_jd": begin, "end_jd": end, "magnitude": round(magnitude, 3),
        "slug": f"{d.isoformat()}-{'surya' if kind == 'solar' else 'chandra'}-grahan",
        "name": f"{subtype} {NAME[kind]}", "name_en": f"{subtype} {NAME_EN[kind]}", "hindi": HINDI[kind],
        "rashi_index": sign, "rashi": ZODIAC_SIGNS[sign], "nakshatra": NAKSHATRA_NAMES[nak],
        "contacts": contacts,
    }


def _scan(year):
    jd0, jd1 = swe.julday(year, 1, 1, 0), swe.julday(year + 1, 1, 1, 0)
    found = []
    jd = jd0
    while True:
        flag, t = swe.sol_eclipse_when_glob(jd, _FLAG, 0)
        if t[0] >= jd1:
            break
        attr = swe.sol_eclipse_where(t[0], _FLAG)[2]
        found.append(_entry("solar", t[0], _solar_type(flag), t[2], t[3], attr[0]))
        jd = t[0] + 25
    jd = jd0
    while True:
        flag, t = swe.lun_eclipse_when(jd, _FLAG, 0)
        if t[0] >= jd1:
            break
        attr = swe.lun_eclipse_how(t[0], (0, 0, 0), _FLAG)[1]
        # lunar contacts are the same instant everywhere; the _loc variant blanks those below the horizon
        found.append(_entry("lunar", t[0], _lunar_type(flag), t[6], t[7], attr[0] or attr[1],
                            {"partial": (t[2], t[3]), "total": (t[4], t[5])}))
        jd = t[0] + 25
    found = [e for e in found if e["jd"] >= jd0]
    return sorted(found, key=lambda e: e["jd"])


def eclipses_in_year(year):
    key = f"{CACHE_V}:year:{year}"
    rows = cache.get(key)
    if rows is None:
        rows = _scan(year)
        for e in rows:
            e["visible_in"] = _seen_from(e)
        cache.set(key, rows, CACHE_TTL)
    return rows


def upcoming(today, count=6):
    out = []
    for y in range(today.year, today.year + 4):
        out += [e for e in eclipses_in_year(y) if _utc(e["end_jd"]).date() >= today]
        if len(out) >= count:
            break
    return out[:count]


def find(slug):
    try:
        year = int(slug[:4])
    except ValueError:
        return None
    return next((e for e in eclipses_in_year(year) if e["slug"] == slug), None)


# ---------------------------------------------------------------------------
# Circumstances at one place
# ---------------------------------------------------------------------------

def _solar_local(e, lat, lon):
    flag, t, attr = swe.sol_eclipse_when_loc(e["jd"] - 1.5, (lon, lat, 0), _FLAG)
    if abs(t[0] - e["jd"]) > 0.3 or not flag & swe.ECL_VISIBLE:
        return None
    return {
        "sparsha": t[1] or e["begin_jd"], "madhya": t[0], "moksha": t[4] or e["end_jd"],
        "full_begin": t[2] or None, "full_end": t[3] or None,
        "sparsha_seen": bool(flag & swe.ECL_1ST_VISIBLE), "moksha_seen": bool(flag & swe.ECL_4TH_VISIBLE),
        "magnitude": attr[0], "obscuration": attr[2],
    }


def _lunar_local(e, lat, lon):
    flag, t, attr = swe.lun_eclipse_when_loc(e["jd"] - 1.5, (lon, lat, 0), _FLAG)
    if abs(t[0] - e["jd"]) > 0.3:
        return None
    if e["subtype"] == "Penumbral":
        if not flag & swe.ECL_VISIBLE:
            return None
        return {"sparsha": e["begin_jd"], "madhya": t[0], "moksha": e["end_jd"], "full_begin": None, "full_end": None,
                "sparsha_seen": bool(flag & swe.ECL_PENUMBBEG_VISIBLE), "moksha_seen": bool(flag & swe.ECL_PENUMBEND_VISIBLE),
                "magnitude": attr[1], "obscuration": 0}
    seen = swe.ECL_PARTBEG_VISIBLE | swe.ECL_PARTEND_VISIBLE | swe.ECL_TOTBEG_VISIBLE | swe.ECL_TOTEND_VISIBLE | swe.ECL_MAX_VISIBLE
    if not flag & seen:
        return None
    partial, total = e["contacts"]["partial"], e["contacts"]["total"]
    return {
        "sparsha": partial[0], "madhya": t[0], "moksha": partial[1], "full_begin": total[0] or None, "full_end": total[1] or None,
        "sparsha_seen": bool(flag & swe.ECL_PARTBEG_VISIBLE), "moksha_seen": bool(flag & swe.ECL_PARTEND_VISIBLE),
        "magnitude": attr[0], "obscuration": 0,
    }


def _raw_local(e, lat, lon):
    return (_solar_local if e["kind"] == "solar" else _lunar_local)(e, lat, lon)


def _seen_from(e):
    return [name for name, lat, lon in SAMPLE_PLACES if _raw_local(e, lat, lon)]


def local_view(e, lat, lon, tz_name):
    """What this grahan means at one place: contact times, visibility and sutak."""
    tz = pytz.timezone(tz_name)
    raw = _raw_local(e, lat, lon)
    if not raw:
        return {"visible": False, "sutak_applies": False,
                "sutak_reason": "This grahan is not visible from your location, so sutak and its restrictions do not apply."}

    def t(jd):
        return pe.jd_to_local(jd, tz) if jd else None

    view = {
        "visible": True,
        "sparsha": t(raw["sparsha"]), "madhya": t(raw["madhya"]), "moksha": t(raw["moksha"]),
        "full_begin": t(raw["full_begin"]), "full_end": t(raw["full_end"]),
        "magnitude": round(raw["magnitude"], 3), "obscuration": round(raw["obscuration"] * 100),
        "starts_before_rise": not raw["sparsha_seen"], "ends_after_set": not raw["moksha_seen"],
        "duration_minutes": round((raw["moksha"] - raw["sparsha"]) * 1440),
    }
    if e["subtype"] == "Penumbral":
        view.update(sutak_applies=False, sutak_reason=(
            "This is a penumbral (Upachchhaya) eclipse: the Moon only dims slightly and is not actually eclipsed, "
            "so it is not counted as a grahan. No sutak, no fast, no temple closure."))
        return view
    hours = SUTAK_HOURS[e["kind"]]
    start = raw["sparsha"] - hours / 24
    view.update(
        sutak_applies=True, sutak_hours=hours, sutak_prahar=4 if e["kind"] == "solar" else 3,
        sutak_start=t(start), sutak_end=t(raw["moksha"]),
        sutak_reason=f"The grahan is visible from your location, so sutak applies from {hours} hours before sparsha until moksha.",
    )
    return view


# ---------------------------------------------------------------------------
# Globe data
# ---------------------------------------------------------------------------

def _sub_point(jd, body):
    ra, dec = swe.calc_ut(jd, body, _FLAG | swe.FLG_EQUATORIAL)[0][:2]
    lon = (ra - swe.sidtime(jd) * 15 + 180) % 360 - 180
    return [round(lon, 2), round(dec, 2)]


def _solar_grid(e, step=6, samples=9):
    """Where the Sun is partly covered: [[lon, lat, greatest obscuration], ...]."""
    span = e["end_jd"] - e["begin_jd"]
    times = [e["begin_jd"] + span * (i + .5) / samples for i in range(samples)]
    cells = []
    for lat in range(-84, 85, step):
        for lon in range(-180, 180, step):
            best = 0
            for jd in times:
                flag, attr = swe.sol_eclipse_how(jd, (lon, lat, 0), _FLAG)
                if flag and attr[2] > best and attr[4] > 0:
                    best = attr[2]
            if best > .005:
                cells.append([lon, lat, round(best, 2)])
    return cells


def _central_path(e):
    flag, t = swe.sol_eclipse_when_glob(e["jd"] - 1, _FLAG, 0)
    if not (t[6] and t[7]) or t[7] <= t[6]:
        return []
    n = max(2, int((t[7] - t[6]) * 1440 / 3))
    pts = []
    for i in range(n + 1):
        jd = t[6] + (t[7] - t[6]) * i / n
        ret, geo, _attr = swe.sol_eclipse_where(jd, _FLAG)
        if ret > 0 and (geo[0] or geo[1]):
            pts.append([round(geo[0], 2), round(geo[1], 2)])
    return pts


_SHADOW_ON_EARTH = swe.ECL_TOTAL | swe.ECL_ANNULAR | swe.ECL_ANNULAR_TOTAL


def globe_data(e):
    key = f"{CACHE_V}:globe2:{e['slug']}"
    data = cache.get(key)
    if data is not None:
        return data
    frames = []
    n = 96
    for i in range(n + 1):
        jd = e["begin_jd"] + (e["end_jd"] - e["begin_jd"]) * i / n
        frame = {"t": int(_utc(jd).timestamp() * 1000), "sun": _sub_point(jd, swe.SUN)}
        if e["kind"] == "lunar":
            frame["moon"] = _sub_point(jd, swe.MOON)
        else:
            # The dark umbra/antumbra is drawn only while it actually touches the Earth. In the partial phases
            # before and after, swe's "point of greatest eclipse" sits on the sunrise/sunset line, which drifts
            # west as the Earth turns, so a dot drawn there seemed to run backwards. Now the shadow rises out of
            # the night edge at sunrise and sinks into it at sunset, as it really does.
            ret, geo, _attr = swe.sol_eclipse_where(jd, _FLAG)
            if ret & _SHADOW_ON_EARTH:
                frame["shadow"] = [round(geo[0], 2), round(geo[1], 2)]
        frames.append(frame)
    data = {"kind": e["kind"], "subtype": e["subtype"], "frames": frames,
            "peak": _sub_point(e["jd"], swe.MOON if e["kind"] == "lunar" else swe.SUN),
            "path": _central_path(e) if e["kind"] == "solar" else [],
            "grid": _solar_grid(e) if e["kind"] == "solar" else []}
    if e["kind"] == "solar":
        geo = swe.sol_eclipse_where(e["jd"], _FLAG)[1]
        data["peak"] = [round(geo[0], 2), round(geo[1], 2)]
    cache.set(key, data, CACHE_TTL)
    return data


def as_date(e):
    return _utc(e["jd"]).date()


def local_date(e, tz_name):
    return _utc(e["jd"]).astimezone(pytz.timezone(tz_name))
