# core/utils/festival_calculations.py
"""
Festival dates per Kashi (Varanasi) panchang conventions.

How a date is decided
---------------------
1. Months are Purnimanta (month ends on Purnima), as used in Varanasi and
   North India.  Adhik maas runs Amavasya to Amavasya and is skipped for
   annual festivals.
2. Each festival names its tithi and the *kaal* (part of the day) in which
   that tithi must prevail - this is the "kaal-vyapti" rule of Nirnaya
   Sindhu / Dharma Sindhu that the Kashi panchangs follow:
       udaya      - tithi at sunrise              (most vratas)
       arunodaya  - 4 ghati (96 min) before sunrise (Vaishnava Ekadashi, Narak Chaturdashi)
       purvahna   - first half of the day          (Vasant Panchami, Akshaya Tritiya)
       madhyahna  - 3rd fifth of the day           (Rama Navami, Ganesh Chaturthi)
       aparahna   - 4th fifth of the day           (Vijaya Dashami, Bhai Dooj, Raksha Bandhan)
       pradosh    - 3 muhurta (1/5 night) after sunset (Diwali, Dhanteras, Pradosh vrat)
       nishita    - 8th muhurta of the night       (Janmashtami, Mahashivratri)
       moonrise   - at moonrise                    (Karwa Chauth, Sankashti, Sharad Purnima)
       sunset     - at sunset                      (Chhath sandhya arghya)
3. If the tithi covers the kaal on both candidate days, or on neither, the
   festival's ``both`` / ``none`` policy picks the day ('first', 'second' or
   'max' coverage), matching the published Kashi decisions.

All computation uses the shared PanchangEvent table, so a year is computed
once (~1 s) and then served from the FestivalDate cache.
"""
from datetime import date, datetime, time, timedelta

import pytz
from django.db import transaction
from django.utils.text import slugify

from . import panchang_engine as pe
from . import panchang_store as ps

ENGINE_VERSION = 4

VARANASI = {
    "name": "Varanasi",
    "lat": 25.3176,
    "lon": 82.9739,
    "tz": "Asia/Kolkata",
}
TZ = pytz.timezone(VARANASI["tz"])

WEEKDAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def T(paksha, n):
    """Tithi index 0..29 from paksha ('S'/'K') and 1..15."""
    return (n - 1) + (0 if paksha == "S" else 15)


# (name, purnimanta month, paksha, tithi 1-15, kaal, both, none, category, importance, note)
TITHI_FESTIVALS = [
    ("Vasant Panchami", "Magha", "S", 5, "purvahna", "first", "second", "Major Festival", "high",
     "Saraswati puja; Panchami must prevail in Purvahna."),
    ("Ratha Saptami", "Magha", "S", 7, "udaya", "first", "first", "Festival", "normal",
     "Surya jayanti; arghya to Surya at sunrise."),
    ("Bhishma Ashtami", "Magha", "S", 8, "madhyahna", "first", "second", "Festival", "normal",
     "Tarpan for Bhishma Pitamah in Madhyahna."),
    ("Magha Purnima", "Magha", "S", 15, "udaya", "first", "first", "Snan-Daan", "high",
     "Ganga snan and daan; end of Magha snan / Kalpavas."),
    ("Mauni Amavasya", "Magha", "K", 15, "udaya", "first", "first", "Snan-Daan", "high",
     "Silent Ganga snan; most important snan of Magha."),
    ("Maha Shivaratri", "Phalguna", "K", 14, "nishita", "first", "second", "Major Festival", "high",
     "Chaturdashi at Nishita kaal; night-long worship at Kashi Vishwanath."),
    ("Holika Dahan", "Phalguna", "S", 15, "pradosh_no_bhadra", "max", "first", "Major Festival", "high",
     "Purnima in Pradosh, avoiding Bhadra (Vishti karana)."),
    ("Chaitra Navratri / Ghatasthapana", "Chaitra", "S", 1, "udaya", "first", "first", "Major Festival", "high",
     "Pratipada at sunrise; Hindu new year (Vikram Samvat), Gudi Padwa, Ugadi."),
    ("Rama Navami", "Chaitra", "S", 9, "madhyahna", "first", "second", "Major Festival", "high",
     "Navami in Madhyahna - the hour of Shri Rama's birth."),
    ("Hanuman Jayanti", "Chaitra", "S", 15, "udaya", "first", "first", "Major Festival", "high",
     "Chaitra Purnima (North Indian tradition)."),
    ("Akshaya Tritiya", "Vaishakha", "S", 3, "purvahna", "first", "second", "Major Festival", "high",
     "Tritiya in Purvahna; auspicious for gold, daan and new beginnings."),
    ("Ganga Saptami", "Vaishakha", "S", 7, "madhyahna", "first", "second", "Festival", "normal",
     "Ganga's descent from Shiva's matted hair; Madhyahna puja."),
    ("Sita Navami", "Vaishakha", "S", 9, "madhyahna", "first", "second", "Festival", "normal",
     "Janaki jayanti; Madhyahna puja."),
    ("Narasimha Jayanti", "Vaishakha", "S", 14, "sunset", "first", "second", "Festival", "normal",
     "Chaturdashi at sunset (Sayankala)."),
    ("Buddha Purnima", "Vaishakha", "S", 15, "udaya", "first", "first", "Festival", "high",
     "Vaishakha Purnima - Buddha jayanti; Sarnath celebrations."),
    ("Vat Savitri Vrat", "Jyeshtha", "K", 15, "udaya", "first", "first", "Vrat", "high",
     "Jyeshtha Amavasya (North Indian Purnimanta tradition)."),
    ("Ganga Dussehra", "Jyeshtha", "S", 10, "udaya", "first", "first", "Major Festival", "high",
     "Descent of Ganga; snan at Dashashwamedh ghat."),
    ("Jagannath Rath Yatra", "Ashadha", "S", 2, "udaya", "first", "first", "Festival", "high",
     "Ashadha Shukla Dwitiya."),
    ("Guru Purnima", "Ashadha", "S", 15, "guru_purnima", "first", "first", "Major Festival", "high",
     "Purnima must prevail for 3 muhurta after sunrise, else the previous day."),
    ("Hariyali Teej", "Shravana", "S", 3, "udaya", "first", "first", "Vrat", "normal",
     "Shravana Shukla Tritiya."),
    ("Nag Panchami", "Shravana", "S", 5, "udaya", "first", "first", "Festival", "high",
     "Naga puja; Shravana Shukla Panchami (Kashi tradition)."),
    ("Raksha Bandhan", "Shravana", "S", 15, "aparahna_no_bhadra", "first", "second", "Major Festival", "high",
     "Purnima in Aparahna free of Bhadra; else Pradosh."),
    ("Kajari Teej", "Bhadrapada", "K", 3, "udaya", "first", "first", "Vrat", "normal",
     "Bhadrapada Krishna Tritiya (Purnimanta)."),
    ("Krishna Janmashtami", "Bhadrapada", "K", 8, "nishita", "first", "second", "Major Festival", "high",
     "Ashtami at Nishita (Smarta); Vaishnava may observe a day later."),
    ("Hartalika Teej", "Bhadrapada", "S", 3, "udaya", "second", "first", "Vrat", "high",
     "Tritiya at sunrise; Dwitiya-viddha day avoided."),
    ("Ganesh Chaturthi", "Bhadrapada", "S", 4, "madhyahna", "first", "second", "Major Festival", "high",
     "Chaturthi in Madhyahna; Ganapati sthapana."),
    ("Rishi Panchami", "Bhadrapada", "S", 5, "madhyahna", "first", "second", "Vrat", "normal",
     "Saptarishi puja in Madhyahna."),
    ("Anant Chaturdashi", "Bhadrapada", "S", 14, "udaya", "first", "first", "Festival", "normal",
     "Anant Vishnu puja; Ganesh visarjan."),
    ("Pitru Paksha begins", "Ashwina", "K", 1, "aparahna", "first", "second", "Shraddha", "high",
     "Pratipada shraddha; fortnight of ancestor rites."),
    ("Sarva Pitru Amavasya", "Ashwina", "K", 15, "aparahna", "first", "second", "Shraddha", "high",
     "Mahalaya; shraddha for all ancestors in Aparahna."),
    ("Sharad Navratri / Ghatasthapana", "Ashwina", "S", 1, "udaya", "first", "first", "Major Festival", "high",
     "Pratipada at sunrise; Kalash sthapana in Pratah kaal."),
    ("Durga Ashtami", "Ashwina", "S", 8, "udaya", "first", "first", "Major Festival", "high",
     "Maha Ashtami; Kanya puja."),
    ("Maha Navami", "Ashwina", "S", 9, "udaya", "first", "first", "Major Festival", "high",
     "Navami puja and havan."),
    ("Vijaya Dashami / Dussehra", "Ashwina", "S", 10, "aparahna", "first", "second", "Major Festival", "high",
     "Dashami in Aparahna; Ramlila (Ramnagar) and Shami puja."),
    ("Sharad Purnima", "Ashwina", "S", 15, "moonrise", "first", "first", "Festival", "high",
     "Purnima at moonrise; kheer under moonlight."),
    ("Karwa Chauth", "Kartika", "K", 4, "moonrise", "first", "first", "Vrat", "high",
     "Chaturthi at moonrise; fast broken after moon sighting."),
    ("Ahoi Ashtami", "Kartika", "K", 8, "sunset", "first", "first", "Vrat", "normal",
     "Ashtami at sunset; star sighting."),
    ("Dhanteras", "Kartika", "K", 13, "pradosh", "first", "second", "Major Festival", "high",
     "Trayodashi in Pradosh; Dhanvantari puja, Yama deepdaan, auspicious purchases."),
    ("Narak Chaturdashi", "Kartika", "K", 14, "arunodaya", "first", "first", "Major Festival", "high",
     "Chaturdashi before sunrise (Abhyang snan); Choti Diwali."),
    ("Diwali / Lakshmi Puja", "Kartika", "K", 15, "pradosh", "max", "second", "Major Festival", "high",
     "Amavasya in Pradosh; if both days, the day with greater Pradosh coverage (Kashi Vidvat Parishad)."),
    ("Govardhan Puja / Annakut", "Kartika", "S", 1, "udaya", "first", "first", "Major Festival", "high",
     "Pratipada in Pratah kaal; Annakut at Kashi temples."),
    ("Bhai Dooj / Yama Dwitiya", "Kartika", "S", 2, "aparahna", "max", "second", "Major Festival", "high",
     "Dwitiya in Aparahna; Chitragupta puja."),
    ("Chhath Puja (Sandhya Arghya)", "Kartika", "S", 6, "sunset", "first", "first", "Major Festival", "high",
     "Shashthi at sunset - evening arghya to Surya at the ghats."),
    ("Akshaya Navami", "Kartika", "S", 9, "udaya", "first", "first", "Festival", "normal",
     "Amla tree puja."),
    ("Tulsi Vivah", "Kartika", "S", 12, "udaya", "first", "first", "Festival", "normal",
     "Kartika Shukla Dwadashi."),
    ("Dev Deepawali / Kartik Purnima", "Kartika", "S", 15, "pradosh", "first", "first", "Major Festival", "high",
     "Purnima in Pradosh; lakhs of diyas on the Varanasi ghats. Also Guru Nanak Jayanti."),
    ("Vivah Panchami", "Margashirsha", "S", 5, "udaya", "first", "first", "Festival", "normal",
     "Wedding anniversary of Shri Rama and Sita."),
    ("Annapurna Jayanti / Datta Jayanti", "Margashirsha", "S", 15, "pradosh", "first", "first", "Festival", "normal",
     "Margashirsha Purnima - Mata Annapurna of Kashi."),
    ("Kalabhairav Jayanti", "Margashirsha", "K", 8, "pradosh", "first", "second", "Festival", "high",
     "Ashtami in the night (Pradosh); Kalabhairav is the Kotwal of Kashi."),
]

# Ekadashi names keyed by (purnimanta month, paksha)
EKADASHI_NAMES = {
    ("Chaitra", "K"): "Papmochani Ekadashi", ("Chaitra", "S"): "Kamada Ekadashi",
    ("Vaishakha", "K"): "Varuthini Ekadashi", ("Vaishakha", "S"): "Mohini Ekadashi",
    ("Jyeshtha", "K"): "Apara Ekadashi", ("Jyeshtha", "S"): "Nirjala Ekadashi",
    ("Ashadha", "K"): "Yogini Ekadashi", ("Ashadha", "S"): "Devshayani Ekadashi",
    ("Shravana", "K"): "Kamika Ekadashi", ("Shravana", "S"): "Shravana Putrada Ekadashi",
    ("Bhadrapada", "K"): "Aja Ekadashi", ("Bhadrapada", "S"): "Parivartini Ekadashi",
    ("Ashwina", "K"): "Indira Ekadashi", ("Ashwina", "S"): "Papankusha Ekadashi",
    ("Kartika", "K"): "Rama Ekadashi", ("Kartika", "S"): "Devutthana Ekadashi",
    ("Margashirsha", "K"): "Utpanna Ekadashi", ("Margashirsha", "S"): "Mokshada Ekadashi",
    ("Pausha", "K"): "Saphala Ekadashi", ("Pausha", "S"): "Pausha Putrada Ekadashi",
    ("Magha", "K"): "Shattila Ekadashi", ("Magha", "S"): "Jaya Ekadashi",
    ("Phalguna", "K"): "Vijaya Ekadashi", ("Phalguna", "S"): "Amalaki Ekadashi",
}
ADHIK_EKADASHI = {"S": "Padmini Ekadashi", "K": "Parama Ekadashi"}

SANKRANTI_NAMES = {
    "Mesh": "Mesha Sankranti", "Vrishabh": "Vrishabha Sankranti", "Mithun": "Mithuna Sankranti",
    "Kark": "Karka Sankranti", "Simha": "Simha Sankranti", "Kanya": "Kanya Sankranti",
    "Tula": "Tula Sankranti", "Vrishchik": "Vrishchika Sankranti", "Dhanu": "Dhanu Sankranti",
    "Makar": "Makar Sankranti", "Kumbh": "Kumbha Sankranti", "Meen": "Meena Sankranti",
}

# Published annual yatra windows (official temple / shrine board announcements).
PILGRIMAGE_WINDOWS = {
    2026: [
        ("Yamunotri Dham Kapat", "2026-04-19", "2026-11-11", "Char Dham", "Yamunotri Dham open season."),
        ("Gangotri Dham Kapat", "2026-04-19", "2026-11-10", "Char Dham", "Gangotri Dham open season."),
        ("Kedarnath Dham Kapat", "2026-04-22", "2026-11-11", "Char Dham", "Kedarnath Dham open season."),
        ("Badrinath Dham Kapat", "2026-04-23", "2026-11-13", "Char Dham", "Badrinath Dham open season."),
        ("Shri Amarnath Ji Yatra", "2026-07-03", "2026-08-28", "Yatra", "Official Shri Amarnath Ji Yatra window."),
    ]
}


# ---------------------------------------------------------------------------
# Day kaals at Varanasi
# ---------------------------------------------------------------------------

_day_cache = {}


def day_info(d):
    """Sunrise/sunset/next sunrise and kaal windows for local date ``d`` at Varanasi."""
    if d in _day_cache:
        return _day_cache[d]
    lat, lon = VARANASI["lat"], VARANASI["lon"]
    sr, ss = pe.sun_times(d, lat, lon, TZ)
    nsr, _ = pe.sun_times(d + timedelta(days=1), lat, lon, TZ)
    day = ss - sr
    night = nsr - ss
    mr = pe.moonrise_on(d, lat, lon, TZ)
    info = {
        "date": d,
        "sunrise": sr,
        "sunset": ss,
        "next_sunrise": nsr,
        "moonrise": mr,
        "kaal": {
            "udaya": (sr, sr),
            "arunodaya": (sr - timedelta(minutes=96), sr),
            "pratah": (sr, sr + day / 5),
            "purvahna": (sr, sr + day / 2),
            "madhyahna": (sr + day * 2 / 5, sr + day * 3 / 5),
            "aparahna": (sr + day * 3 / 5, sr + day * 4 / 5),
            "sunset": (ss, ss),
            "pradosh": (ss, ss + night / 5),
            "nishita": (ss + night * 7 / 15, ss + night * 8 / 15),
        },
    }
    if len(_day_cache) > 3000:
        _day_cache.clear()
    _day_cache[d] = info
    return info


def _overlap(a0, a1, b0, b1):
    """Overlap in seconds; instants (b0 == b1) count as 1 if inside [a0, a1)."""
    if b0 == b1:
        return 1.0 if a0 <= b0 < a1 else 0.0
    return max(0.0, (min(a1, b1) - max(a0, b0)).total_seconds())


def _local(dt_utc):
    return pytz.utc.localize(dt_utc).astimezone(TZ)


def _bhadra_windows(t_start, t_end):
    """Vishti karana windows (local aware datetimes) overlapping the range."""
    rows = ps.events_overlapping(
        "karana", t_start.astimezone(pytz.utc).replace(tzinfo=None), t_end.astimezone(pytz.utc).replace(tzinfo=None))
    return [(_local(r.start_utc), _local(r.end_utc)) for r in rows if r.name == "Vishti"]


def _coverage(kaal, d, t0, t1):
    """Seconds the tithi [t0, t1) covers ``kaal`` on date ``d``."""
    info = day_info(d)
    if kaal == "moonrise":
        mr = info["moonrise"]
        if mr is None:
            return 0.0
        return 1.0 if t0 <= mr < t1 else 0.0
    if kaal in ("pradosh_no_bhadra", "aparahna_no_bhadra"):
        base = "pradosh" if kaal.startswith("pradosh") else "aparahna"
        k0, k1 = info["kaal"][base]
        cov = _overlap(t0, t1, k0, k1)
        if cov == 0:
            return 0.0
        for b0, b1 in _bhadra_windows(k0, k1):
            cov -= _overlap(max(t0, k0), min(t1, k1), b0, b1)
        if base == "pradosh":
            # Holika Dahan is still done the same night once Bhadra ends (Bhadra-puchha),
            # so a Purnima night never loses out entirely
            return max(cov, 0.5)
        return max(cov, 0.0)
    if kaal == "guru_purnima":
        sr = info["sunrise"]
        day = info["sunset"] - sr
        need_end = sr + day * 3 / 15
        return 1.0 if t0 <= sr and t1 >= need_end else 0.0
    k0, k1 = info["kaal"][kaal]
    return _overlap(t0, t1, k0, k1)


def resolve_day(t0, t1, kaal, both="first", none="first"):
    """Pick the observance date for a tithi running [t0, t1) (aware local datetimes)."""
    candidates = []
    d = (t0 - timedelta(days=1)).date()
    while d <= t1.date():
        info = day_info(d)
        # civil "Hindu day" runs sunrise to next sunrise; skip days the tithi never touches
        if info["next_sunrise"] > t0 and info["sunrise"] - timedelta(hours=2) < t1:
            candidates.append((d, _coverage(kaal, d, t0, t1)))
        d += timedelta(days=1)
    hits = [(d, c) for d, c in candidates if c > 0]
    if len(hits) == 1:
        return hits[0][0]
    pool = hits if hits else candidates
    policy = both if hits else none
    if policy == "max":
        return max(pool, key=lambda x: x[1])[0]
    if policy == "second" and len(pool) > 1:
        return pool[1][0]
    if hits:
        return pool[0][0]
    # no coverage anywhere: 'first' = day the tithi begins (after its sunrise), 'second' = following day
    starts = [d for d, _ in pool if day_info(d)["sunrise"] <= t0 < day_info(d)["next_sunrise"]]
    first = starts[0] if starts else pool[0][0]
    return first if policy == "first" else first + timedelta(days=1)


# ---------------------------------------------------------------------------
# Year builder
# ---------------------------------------------------------------------------

def _tithi_table(year):
    """Tithi events around ``year`` annotated with purnimanta month."""
    start = date(year - 1, 12, 1)
    end = date(year + 1, 1, 31)
    tithis = ps.find_events("tithi", start, end, tz=TZ)
    pakshas = ps.find_events("paksha", start - timedelta(days=20), end + timedelta(days=20), tz=TZ)
    out = []
    pi = 0
    for t in tithis:
        mid = t.start_jd + (t.end_jd - t.start_jd) / 2
        while pi < len(pakshas) and pakshas[pi].end_jd <= mid:
            pi += 1
        p = pakshas[pi] if pi < len(pakshas) else None
        if not p or not (p.start_jd <= mid < p.end_jd):
            continue
        out.append({
            "n": t.number,
            "start": _local(t.start_utc),
            "end": _local(t.end_utc),
            "masa": p.extra.get("masa_purnimanta"),
            "adhik": p.extra.get("purnimanta_adhik", p.extra.get("adhik", False)) if t.number >= 15
            else p.extra.get("adhik", False),
            "amanta": p.extra.get("masa_amanta"),
            "paksha": "S" if t.number < 15 else "K",
        })
    return out


def lunar_eclipse_on(d):
    """
    Max time of an umbral (partial/total) lunar eclipse *visible from Varanasi*
    on local date ``d``, else None.  Penumbral or invisible eclipses carry no sutak.
    """
    import swisseph as swe
    jd0 = pe.local_midnight_jd(d, TZ) - 20
    geopos = (VARANASI["lon"], VARANASI["lat"], 80)
    res, tret, _attr = swe.lun_eclipse_when_loc(jd0, geopos, swe.FLG_SWIEPH, False)
    if res <= 0 or not (res & (swe.ECL_TOTAL | swe.ECL_PARTIAL)):
        return None
    at = pe.jd_to_local(tret[0], TZ)
    return at if at.date() == d else None


def _fest(slug, name, d, category, importance, rule, note, **details):
    return {
        "slug": slug, "name": name, "date": d, "category": category, "importance": importance,
        "rule": rule, "note": note, "details": details,
    }


def _fmt(dt):
    return dt.strftime("%d %b %Y, %I:%M %p") if dt else None


def compute_festivals(year):
    """All festivals observed in ``year`` (local dates, Varanasi rules)."""
    table = _tithi_table(year)
    out = []

    def in_year(d):
        return d.year == year

    # Annual tithi festivals
    for (name, masa, pak, n, kaal, both, none, cat, imp, note) in TITHI_FESTIVALS:
        idx = T(pak, n)
        for t in table:
            if t["n"] == idx and t["masa"] == masa and not t["adhik"]:
                d = resolve_day(t["start"], t["end"], kaal, both, none)
                if in_year(d):
                    out.append(_fest(slugify(name.split("/")[0]), name, d, cat, imp,
                                     f"{masa} {'Shukla' if pak == 'S' else 'Krishna'} {n} - {kaal.replace('_', ' ')} vyapini",
                                     note, tithi_start=_fmt(t["start"]), tithi_end=_fmt(t["end"]), masa=masa))

    # Derived festivals
    by_slug = {f["slug"]: f for f in out}
    if "holika-dahan" in by_slug:
        d = by_slug["holika-dahan"]["date"] + timedelta(days=1)
        note = "Festival of colours; Chaitra Krishna Pratipada."
        eclipse = lunar_eclipse_on(d)
        if eclipse:
            d += timedelta(days=1)
            note += f" Moved a day because of the Chandra Grahan on {eclipse:%d %b}."
        out.append(_fest("holi", "Holi (Rangwali / Dhulandi)", d, "Major Festival", "high",
                         "Day after Holika Dahan (shifted if a lunar eclipse falls that day)", note))
    if "krishna-janmashtami" in by_slug:
        f = by_slug["krishna-janmashtami"]
        t = next(x for x in table if x["n"] == T("K", 8) and x["masa"] == "Bhadrapada" and not x["adhik"]
                 and x["start"].date() <= f["date"] + timedelta(days=1) and x["end"].date() >= f["date"])
        udaya = resolve_day(t["start"], t["end"], "udaya", "first", "first")
        if udaya != f["date"]:
            f["details"]["vaishnava_date"] = udaya.isoformat()
            f["note"] += f" Udaya-Ashtami (Vaishnava / Mathura-Vrindavan) observance on {udaya:%d %b}."
    if "chhath-puja-sandhya-arghya" in by_slug:
        d = by_slug["chhath-puja-sandhya-arghya"]["date"]
        out.append(_fest("chhath-nahay-khay", "Chhath - Nahay Khay", d - timedelta(days=2), "Major Festival", "normal",
                         "Two days before Sandhya Arghya", "First day of Chhath."))
        out.append(_fest("chhath-kharna", "Chhath - Kharna", d - timedelta(days=1), "Major Festival", "normal",
                         "Day before Sandhya Arghya", "Kheer prasad after day-long fast."))
        out.append(_fest("chhath-usha-arghya", "Chhath - Usha Arghya", d + timedelta(days=1), "Major Festival", "high",
                         "Morning after Sandhya Arghya", "Arghya to the rising Sun; parana."))

    if "pitru-paksha-begins" in by_slug and "sarva-pitru-amavasya" in by_slug:
        a = by_slug["pitru-paksha-begins"]["date"] - timedelta(days=1)   # Purnima shraddha
        b = by_slug["sarva-pitru-amavasya"]["date"]
        out.append(_fest("pitru-paksha", "Pitru Paksha (Shraddh)", a, "Period", "high",
                         "Bhadrapada Purnima to Ashwin Amavasya",
                         "Shraddha and tarpan; new purchases and auspicious ceremonies are traditionally avoided.",
                         end_date=b.isoformat()))

    # Ekadashi (Smarta = udaya; Vaishnava = Dashami-free arunodaya)
    for t in table:
        if t["n"] not in (10, 25):
            continue
        pak = t["paksha"]
        name = ADHIK_EKADASHI[pak] if t["adhik"] else EKADASHI_NAMES.get((t["masa"], pak), "Ekadashi")
        dw = next((x for x in table if x["start"] == t["end"]), None)
        smarta = resolve_day(t["start"], t["end"], "udaya", "first", "first")
        vaishnava = smarta
        if day_info(smarta)["kaal"]["arunodaya"][0] < t["start"]:
            vaishnava = smarta + timedelta(days=1)
        # Parana must fall in Dwadashi.  If Dwadashi ends before the next sunrise
        # (kshaya Dwadashi) and Ekadashi already ran on the previous day, Smartas fast a day earlier.
        if dw and dw["end"] < day_info(smarta)["next_sunrise"] and                 t["start"] < day_info(smarta)["sunrise"] and                 t["start"] < day_info(smarta - timedelta(days=1))["next_sunrise"] - timedelta(hours=3):
            smarta = smarta - timedelta(days=1)
        if not in_year(smarta):
            continue
        nxt = day_info(smarta + timedelta(days=1))
        parana = None
        if dw:
            hari_vasara_end = dw["start"] + (dw["end"] - dw["start"]) / 4
            p0 = max(nxt["sunrise"], hari_vasara_end)
            parana = {"from": _fmt(p0), "dwadashi_ends": _fmt(dw["end"])}
        out.append(_fest(slugify(name), name, smarta, "Ekadashi", "high",
                         "Ekadashi at sunrise (Smarta)", "Vishnu puja and upvas.",
                         tithi_start=_fmt(t["start"]), tithi_end=_fmt(t["end"]), masa=t["masa"],
                         vaishnava_date=vaishnava.isoformat() if vaishnava != smarta else None,
                         parana=parana, adhik=t["adhik"]))

    # Monthly vratas
    for t in table:
        masa = ("Adhik " if t["adhik"] else "") + (t["masa"] or "")
        common = dict(tithi_start=_fmt(t["start"]), tithi_end=_fmt(t["end"]), masa=masa)
        if t["n"] in (12, 27):
            d = resolve_day(t["start"], t["end"], "pradosh", "first", "first")
            wd = WEEKDAY_NAMES[d.weekday()]
            prefix = {"Monday": "Som ", "Tuesday": "Bhaum ", "Saturday": "Shani "}.get(wd, "")
            out.append(_fest("pradosh-vrat", f"{prefix}Pradosh Vrat", d, "Vrat", "normal",
                             "Trayodashi in Pradosh", "Shiva puja at twilight.", **common))
        elif t["n"] == 18:
            d = resolve_day(t["start"], t["end"], "moonrise", "first", "first")
            special = " (Angaraki)" if d.weekday() == 1 else ""
            out.append(_fest("sankashti-chaturthi", f"Sankashti Chaturthi{special}", d, "Vrat", "normal",
                             "Krishna Chaturthi at moonrise", "Ganesha vrat; break after moonrise.",
                             moonrise=_fmt(day_info(d)["moonrise"]), **common))
        elif t["n"] == 3:
            d = resolve_day(t["start"], t["end"], "madhyahna", "first", "second")
            out.append(_fest("vinayaka-chaturthi", "Vinayaka Chaturthi", d, "Vrat", "normal",
                             "Shukla Chaturthi in Madhyahna", "Ganesha puja.", **common))
        elif t["n"] == 28:
            d = resolve_day(t["start"], t["end"], "nishita", "first", "second")
            out.append(_fest("masik-shivaratri", "Masik Shivaratri", d, "Vrat", "normal",
                             "Krishna Chaturdashi at Nishita", "Monthly Shiva night.", **common))
        elif t["n"] == 14:
            d = resolve_day(t["start"], t["end"], "udaya", "first", "first")
            vrat = resolve_day(t["start"], t["end"], "moonrise", "first", "first")
            out.append(_fest("purnima", f"{masa} Purnima", d, "Purnima", "normal",
                             "Purnima at sunrise (snan-daan)", "Satyanarayan katha; snan-daan.",
                             vrat_date=vrat.isoformat() if vrat != d else None, **common))
        elif t["n"] == 29:
            d = resolve_day(t["start"], t["end"], "udaya", "first", "first")
            wd = WEEKDAY_NAMES[d.weekday()]
            special = {"Monday": "Somvati ", "Saturday": "Shani "}.get(wd, "")
            out.append(_fest("amavasya", f"{special}{masa} Amavasya", d, "Amavasya", "normal",
                             "Amavasya at sunrise", "Pitru tarpan and daan.", **common))
        elif t["n"] == 7:
            d = resolve_day(t["start"], t["end"], "udaya", "first", "first")
            out.append(_fest("masik-durgashtami", "Masik Durgashtami", d, "Vrat", "normal",
                             "Shukla Ashtami at sunrise", "Durga puja.", **common))

    # Sankranti: punya kaal on the same day if before sunset, else next day
    sankrantis = ps.find_events("sun_sign", date(year - 1, 12, 20), date(year, 12, 31), tz=TZ)
    for s in sankrantis:
        at = _local(s.start_utc)
        d = at.date()
        if at < day_info(d)["sunrise"]:
            d = d - timedelta(days=1) if at < day_info(d)["sunrise"] - timedelta(hours=6) else d
        if at >= day_info(d)["sunset"]:
            d = d + timedelta(days=1)
        if not in_year(d):
            continue
        name = SANKRANTI_NAMES.get(s.name, f"{s.name} Sankranti")
        imp = "high" if s.name in ("Makar", "Mesh") else "normal"
        out.append(_fest(slugify(name), name, d, "Sankranti", imp,
                         "Sun's sidereal ingress; punya kaal next day if after sunset",
                         f"Sun enters {s.name} at {_fmt(at)}.", ingress=_fmt(at)))
        if s.name == "Makar":
            out.append(_fest("lohri", "Lohri", d - timedelta(days=1), "Regional Festival", "normal",
                             "Eve of Makar Sankranti", "Punjab harvest bonfire."))

    # Sawan Somvar - Mondays of purnimanta Shravana
    for t in table:
        if t["masa"] == "Shravana" and not t["adhik"]:
            d = t["start"].date()
            while d <= t["end"].date():
                info = day_info(d)
                if d.weekday() == 0 and t["start"] <= info["sunrise"] < t["end"] and in_year(d):
                    out.append(_fest("sawan-somvar", "Sawan Somvar", d, "Vrat", "high",
                                     "Monday in Shravana (Purnimanta)", "Jalabhishek at Kashi Vishwanath."))
                d += timedelta(days=1)

    # Periods
    out.extend(_periods(year, table))

    # de-duplicate (same slug + date)
    seen, uniq = set(), []
    for f in sorted(out, key=lambda f: (f["date"], f["name"])):
        key = (f["slug"], f["date"], f["name"])
        if key not in seen and f["date"].year == year:
            seen.add(key)
            uniq.append(f)
    return uniq


def _periods(year, table):
    """Multi-day periods: Adhik maas, Kharmas, Pitru Paksha, Navratri, Holashtak, Chaturmas, Panchak."""
    out = []
    months = ps.find_events("amanta_masa", date(year, 1, 1), date(year, 12, 31), tz=TZ, adhik=True)
    for m in months:
        s, e = _local(m.start_utc), _local(m.end_utc)
        out.append(_fest("adhik-maas", f"Adhik {m.name} Maas (Purushottam Maas)", s.date(), "Period", "high",
                         "Lunar month without a sankranti",
                         "Mal maas: marriages, griha pravesh and new purchases are avoided; japa, daan, vrata encouraged.",
                         end_date=e.date().isoformat(), starts_at=s.isoformat(), ends_at=e.isoformat()))
    suns = ps.find_events("sun_sign", date(year - 1, 11, 1), date(year, 12, 31), tz=TZ)
    for s in suns:
        if s.name in ("Dhanu", "Meen"):
            a, b = _local(s.start_utc), _local(s.end_utc)
            if a.year == year:                       # stored once, under the year it begins
                out.append(_fest("kharmas", "Kharmas (Malmas)", a.date(), "Period", "high",
                                 f"Sun in {s.name}",
                                 "Marriages, griha pravesh, mundan and new ventures are avoided.",
                                 end_date=b.date().isoformat(), starts_at=a.isoformat(), ends_at=b.isoformat()))
    for t in table:
        if t["n"] == 0 and not t["adhik"] and t["masa"] in ("Chaitra", "Ashwina"):
            d = resolve_day(t["start"], t["end"], "udaya", "first", "first")
            if d.year == year:
                name = "Chaitra Navratri" if t["masa"] == "Chaitra" else "Sharad Navratri"
                out.append(_fest(slugify(name), name, d, "Period", "high", "Pratipada to Navami",
                                 "Nine nights of Durga upasana.", end_date=(d + timedelta(days=8)).isoformat()))
    # Holashtak: Phalguna Shukla Ashtami to Purnima
    for t in table:
        if t["n"] == 7 and t["masa"] == "Phalguna" and not t["adhik"]:
            d = resolve_day(t["start"], t["end"], "udaya", "first", "first")
            if d.year == year:
                out.append(_fest("holashtak", "Holashtak", d, "Period", "normal", "Phalguna Shukla Ashtami to Purnima",
                                 "Eight days before Holi; auspicious ceremonies avoided.",
                                 end_date=(d + timedelta(days=7)).isoformat()))
    return out


# ---------------------------------------------------------------------------
# Cache + public API
# ---------------------------------------------------------------------------

def ensure_festivals(year):
    from core.models import FestivalDate
    if FestivalDate.objects.filter(year=year, engine_version=ENGINE_VERSION).exists():
        return False
    rows = [FestivalDate(year=year, engine_version=ENGINE_VERSION, slug=f["slug"], name=f["name"],
                         date=f["date"], category=f["category"], importance=f["importance"],
                         rule=f["rule"], note=f["note"], details=f["details"])
            for f in compute_festivals(year)]
    with transaction.atomic():
        FestivalDate.objects.filter(year=year).delete()
        FestivalDate.objects.bulk_create(rows)
    return True


def _row_to_event(r):
    end = r.details.get("end_date")
    end_date = date.fromisoformat(end) if end else r.date
    return {
        "slug": r.slug,
        "name": r.name,
        "date": r.date,
        "end_date": end_date,
        "date_display": _format_event_range(r.date, end_date),
        "weekday": WEEKDAY_NAMES[r.date.weekday()],
        "category": r.category,
        "importance": r.importance,
        "rule": r.rule,
        "note": r.note,
        "month": r.details.get("masa", ""),
        "tithi": r.rule,
        "details": r.details,
    }


def _format_event_range(start_date, end_date=None):
    if not end_date or start_date == end_date:
        return start_date.strftime("%b %d, %Y")
    return f"{start_date.strftime('%b %d, %Y')} - {end_date.strftime('%b %d, %Y')}"


def get_festivals_for_year(year, categories=None):
    from core.models import FestivalDate
    ensure_festivals(year)
    qs = FestivalDate.objects.filter(year=year)
    if categories:
        qs = qs.filter(category__in=categories)
    return [_row_to_event(r) for r in qs.order_by("date", "name")]


def get_carryover_periods(year):
    """Periods that began in ``year - 1`` and are still running on 1 January of ``year``."""
    return [e for e in get_festivals_for_year(year - 1, ["Period"]) if e["end_date"].year >= year]


def get_festivals_between(start, end, categories=None):
    from core.models import FestivalDate
    for y in range(start.year - 1, end.year + 1):      # a period may start in the previous year
        ensure_festivals(y)
    qs = FestivalDate.objects.filter(date__gte=start, date__lte=end)
    if categories:
        qs = qs.filter(category__in=categories)
    return [_row_to_event(r) for r in qs.order_by("date", "name")]


def get_festivals_for_day(target, panchang_data=None):
    """Festivals (and running periods) observed on a local date. ``panchang_data`` kept for compatibility."""
    from core.models import FestivalDate
    d = target.date() if isinstance(target, datetime) else target
    ensure_festivals(d.year - 1)
    ensure_festivals(d.year)
    out = [_row_to_event(r) for r in FestivalDate.objects.filter(date=d)]
    # running multi-day periods that started earlier
    for r in FestivalDate.objects.filter(category="Period", date__lt=d, date__gte=d - timedelta(days=40)):
        ev = _row_to_event(r)
        if ev["end_date"] >= d:
            out.append(ev)
    return out


def get_festival_by_slug(slug, year):
    from core.models import FestivalDate
    ensure_festivals(year)
    return [_row_to_event(r) for r in FestivalDate.objects.filter(slug=slug, year=year).order_by("date")]


def get_pilgrimage_windows_for_year(year, tz=None):
    events = []
    for name, start_str, end_str, category, note in PILGRIMAGE_WINDOWS.get(year, []):
        start = date.fromisoformat(start_str)
        end = date.fromisoformat(end_str)
        events.append({
            "slug": slugify(name), "date": start, "end_date": end,
            "date_display": _format_event_range(start, end), "name": name, "category": category,
            "month": "", "tithi": "", "rule": "Official shrine board announcement", "note": note,
            "importance": "high", "weekday": WEEKDAY_NAMES[start.weekday()], "details": {},
        })
    return events
