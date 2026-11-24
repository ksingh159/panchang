# core/utils/aaj_panchang.py
"""
"Aaj Ka Panchang" (/aaj-ka-panchang/): today's panchang for Varanasi and Delhi, built once a day and served to everyone.

    today_snapshot()          today's page data (IST date), built on first use if the 05:30 IST job has not run yet
    build(d)                  compute and store the page data for date ``d``; stamps the real time it was computed
    city_day(place, d)        one city's panchang, muhurats, Rahu/Gulika and Do's/Don'ts (also used for ?city=)

The scheduled job (``manage.py daily``, Railway cron "0 0 * * *" = 05:30 IST) rebuilds the day at 05:30 IST, so the
"Updated" time on the page is when the numbers were really computed. Visitors before 05:30 get a build made on
demand, stamped with its own time.

Panchang limbs are the ones in force at each city's sunrise (udaya), as a printed panchang reads the day.
Owner's tone rule: reassure, never frighten (Sade Sati is a time for patience, not fear).
"""
import logging
from datetime import date, datetime, timedelta

import pytz
from django.core.cache import cache
from django.utils import timezone

from . import festival_calculations as fc
from . import muhurat as mu
from . import panchang_engine as pe
from . import panchang_store as ps
from . import shani
from .astro_calculations import get_panchang
from .constants import ZODIAC_SIGNS

logger = logging.getLogger(__name__)

IST = pytz.timezone("Asia/Kolkata")
CACHE_VERSION = 1
CACHE_SECONDS = 3 * 24 * 3600
FESTIVAL_DAYS = 30           # upcoming festivals shown
UNFAVOURABLE_DAYS = 90       # Kharmas, Shraddh, Holashtak, Panchak, Bhadra, asta, grahan ...
SHANI_DAYS = 180             # Moon signs entering or under Sade Sati / Dhaiya

CITIES = [
    {"key": "varanasi", "name": ("Varanasi", "वाराणसी"), "query": "Varanasi",
     "lat": fc.VARANASI["lat"], "lon": fc.VARANASI["lon"], "tz": fc.VARANASI["tz"]},
    {"key": "delhi", "name": ("Delhi", "दिल्ली"), "query": "New Delhi",
     "lat": 28.6139, "lon": 77.2090, "tz": "Asia/Kolkata"},
]

# Period slugs that have their own festival page (/festivals/<year>/<slug>/)
FESTIVAL_PAGE_PERIODS = {"Kharmas": "kharmas", "Holashtak": "holashtak", "Pitru Paksha": "pitru-paksha",
                         "Adhik Maas": "adhik-maas"}
# Festival rows that are blackout periods: listed under "unfavourable", not under "festivals"
BLACKOUT_SLUGS = set(mu.BLOCKS) | {"panchak"}

MUHURAT_NAMES = [("Brahma Muhurat", "ब्रह्म मुहूर्त"), ("Abhijit Muhurat", "अभिजीत मुहूर्त"),
                 ("Vijay Muhurat", "विजय मुहूर्त"), ("Pradosh Kaal", "प्रदोष काल")]
# Hindi for constants.DISHA_SHOOL_REMEDY (owner's list)
REMEDY_HI = {"Eat Sajjika/Rasala": "सज्जिका / रसाला खाकर निकलें", "Eat Kheer": "खीर खाकर निकलें",
             "Eat Kanji": "कांजी खाकर निकलें", "Eat Milk": "दूध पीकर निकलें", "Eat Dahi": "दही खाकर निकलें",
             "Eat Sesame and rice": "तिल और चावल खाकर निकलें"}

PANCHAK_NOTE = ("Moon in Kumbha and Meena (Dhanishta 3rd pada to Revati): buying wood, roofing, southward travel and "
                "cremation rites are traditionally done only with remedy.",
                "चन्द्रमा कुम्भ और मीन में (धनिष्ठा तीसरे चरण से रेवती तक): लकड़ी खरीदना, छत डालना, दक्षिण की यात्रा और "
                "दाह-संस्कार परम्परा से केवल उपाय के साथ किए जाते हैं।")
BHADRA_NOTE = ("Vishti karana. New work, travel and ceremonies are traditionally kept outside it.",
               "विष्टि करण। नया काम, यात्रा और संस्कार परम्परा से इसके बाहर रखे जाते हैं।")

# Page text as (English, Hindi) pairs, shown with |pick
TEXT = {
    "h1": ("Aaj Ka Panchang", "आज का पंचांग"),
    "updated": ("Updated", "अपडेट"),
    "computed_now": ("Calculated just now for", "अभी गणना की गई:"),
    "lede": ("Today's panchang for Varanasi and Delhi: tithi, nakshatra, yoga and karana at sunrise, shubh muhurat, "
             "Rahu Kaal and Gulika Kaal, Disha Shool with its remedy, what to do and avoid, food for the day, festivals and "
             "the unfavourable periods ahead.",
             "वाराणसी और दिल्ली का आज का पंचांग: सूर्योदय के समय की तिथि, नक्षत्र, योग और करण, शुभ मुहूर्त, राहुकाल और "
             "गुलिक काल, दिशा शूल और उसका उपाय, आज क्या करें और क्या न करें, आज का आहार, त्योहार और आने वाले अशुभ काल।"),
    "other_city": ("See today's panchang for your city", "अपने शहर का आज का पंचांग देखें"),
    "back_two": ("Back to Varanasi and Delhi", "वाराणसी और दिल्ली पर वापस जाएँ"),
    "panchang_h": ("Today's panchang", "आज का पंचांग"),
    "sunrise_note": ("Tithi, nakshatra, yoga and karana are the ones in force at sunrise in each city; the time shows when each one ends.",
                     "तिथि, नक्षत्र, योग और करण हर शहर में सूर्योदय के समय के हैं; समय बताता है कि हर एक कब समाप्त होता है।"),
    "vaar": ("Vaar", "वार"), "tithi": ("Tithi", "तिथि"), "nakshatra": ("Nakshatra", "नक्षत्र"), "yoga": ("Yoga", "योग"),
    "karana": ("Karana", "करण"), "moon_sign": ("Moon sign (Chandra rashi)", "चन्द्र राशि"),
    "month": ("Month (Purnimanta / Amanta)", "मास (पूर्णिमान्त / अमान्त)"), "ritu": ("Ritu", "ऋतु"),
    "sunrise": ("Sunrise", "सूर्योदय"), "sunset": ("Sunset", "सूर्यास्त"), "moonrise": ("Moonrise", "चन्द्रोदय"),
    "moonset": ("Moonset", "चन्द्रास्त"), "upto": ("until", "तक"),
    "muhurat_h": ("Shubh muhurat today", "आज के शुभ मुहूर्त"),
    "abhijit_wed": ("Abhijit Muhurat is traditionally not used on a Wednesday.", "बुधवार को अभिजीत मुहूर्त परम्परा से नहीं लिया जाता।"),
    "special_yogas": ("Special yogas today", "आज के विशेष योग"),
    "avoid_h": ("Rahu Kaal and Gulika Kaal", "राहुकाल और गुलिक काल"),
    "rahu": ("Rahu Kaal", "राहुकाल"), "gulika": ("Gulika Kaal", "गुलिक काल"),
    "rahu_note": ("Do not begin new work, purchases or journeys in Rahu Kaal. Gulika Kaal is avoided for funerals and debt, and some families avoid starting anything in it too.",
                  "राहुकाल में नया काम, खरीदारी या यात्रा शुरू न करें। गुलिक काल अन्त्येष्टि और ऋण के लिए टाला जाता है, और कुछ परिवार इसमें कोई भी शुरुआत नहीं करते।"),
    "shool_h": ("Disha Shool today", "आज का दिशा शूल"),
    "shool_dir": ("Avoid starting a journey towards", "इस दिशा में यात्रा शुरू करने से बचें:"),
    "shool_remedy": ("If you must travel", "यदि यात्रा करनी ही हो"),
    "dos_h": ("Do's and Don'ts today", "आज क्या करें, क्या न करें"),
    "dos": ("Do", "करें"), "donts": ("Don't", "न करें"),
    "good_for": ("Good windows today", "आज के शुभ समय"),
    "wear": ("Colours to wear", "पहनने के रंग"),
    "buy": ("Good to buy today", "आज खरीदने के लिए अच्छा"),
    "avoid_buy": ("Traditionally avoided today", "आज परम्परा से टाला जाता है"),
    "travel": ("Do not set out towards", "इस दिशा में यात्रा पर न निकलें:"),
    "no_good": ("No classical muhurat window today; everyday work goes on as usual.", "आज कोई शास्त्रीय मुहूर्त नहीं है; रोज़ के काम सामान्य रूप से चलते रहें।"),
    "diet_h": ("Food for the day (aahaar)", "आज का आहार"),
    "favour": ("Favour", "लें"), "avoid": ("Avoid", "टालें"),
    "diet_more": ("Full aahaar guide for your city and region", "अपने शहर और क्षेत्र के लिए पूरा आहार मार्गदर्शन"),
    "fest_today": ("Festivals and vrats today", "आज के त्योहार और व्रत"),
    "fest_none": ("No major festival today.", "आज कोई बड़ा त्योहार नहीं है।"),
    "fest_next": ("Upcoming festivals (next 30 days)", "आने वाले त्योहार (अगले 30 दिन)"),
    "fest_all": ("Full festival calendar", "पूरा त्योहार कैलेंडर"),
    "unfav_h": ("Unfavourable periods ahead (next 90 days)", "आने वाले अशुभ काल (अगले 90 दिन)"),
    "unfav_lede": ("Times when marriage, griha pravesh, big purchases or new beginnings are traditionally put off. Everyday life and worship go on as usual.",
                   "वे समय जब विवाह, गृह प्रवेश, बड़ी खरीदारी या नई शुरुआत परम्परा से टाली जाती है। रोज़ का जीवन और पूजा-पाठ सामान्य रूप से चलते रहते हैं।"),
    "running": ("running now", "अभी चल रहा है"),
    "period": ("Period", "काल"), "from": ("From", "से"), "to": ("To", "तक"), "why": ("What it means", "अर्थ"),
    "details": ("Details", "विवरण"),
    "none_90": ("No blackout period in the next 90 days.", "अगले 90 दिनों में कोई वर्जित काल नहीं है।"),
    "bhadra_h": ("Bhadra (Vishti karana) in the next 90 days", "अगले 90 दिनों में भद्रा (विष्टि करण)"),
    "times_ist": ("All times IST; Bhadra and Panchak begin and end at the same moment everywhere.",
                  "सभी समय IST में; भद्रा और पंचक हर जगह एक ही क्षण शुरू और समाप्त होते हैं।"),
    "shani_h": ("Shani Sade Sati and Dhaiya: Moon signs in the next 180 days", "शनि साढ़े साती और ढैया: अगले 180 दिनों में किन राशियों पर"),
    "shani_lede": ("Sade Sati and Dhaiya are counted from the Moon sign you were born with (janma rashi), not from your Sun sign or name. They are seasons for patience, steady effort and care with health and money, not a reason for fear. Your free kundali shows your Moon sign and your own Sade Sati dates.",
                   "साढ़े साती और ढैया आपकी जन्म राशि (जन्म के समय चन्द्रमा की राशि) से गिनी जाती है, नाम राशि या सूर्य राशि से नहीं। यह धैर्य, लगातार मेहनत और स्वास्थ्य व धन में सावधानी का समय है, डरने का कारण नहीं। आपकी निःशुल्क कुण्डली आपकी जन्म राशि और आपकी अपनी साढ़े साती की तिथियाँ दिखाती है।"),
    "rashi": ("Moon sign", "राशि"), "shani_kind": ("Shani period", "शनि का काल"), "phase": ("Phase now", "अभी का चरण"),
    "begins": ("begins", "शुरू"), "ends": ("ends", "समाप्त"), "since": ("since", "से"),
    "next_phase": ("next phase", "अगला चरण"),
    "check_kundali": ("Check yours: free kundali", "अपनी देखें: निःशुल्क कुण्डली"),
    "kundali_cta": ("Not sure of your Moon sign? Make your free kundali to see your own Sade Sati and Dhaiya dates.",
                    "अपनी जन्म राशि पता नहीं? अपनी साढ़े साती और ढैया की तिथियाँ देखने के लिए निःशुल्क कुण्डली बनाएँ।"),
    "more_h": ("More for today", "आज के लिए और"),
    "full_panchang": ("Full panchang with choghadiya and hora", "चौघड़िया और होरा के साथ पूरा पंचांग"),
    "tomorrow": ("Tomorrow's panchang", "कल का पंचांग"),
    "shubh_page": ("Shubh muhurat for buying, money and ceremonies", "खरीदारी, धन और संस्कारों के शुभ मुहूर्त"),
    "kashi_note": ("Festival dates follow Kashi (Varanasi) panchang rules.", "त्योहारों की तिथियाँ काशी (वाराणसी) पंचांग के नियमों से हैं।"),
    "bhadra_note": BHADRA_NOTE, "panchak": ("Panchak", "पंचक"), "bhadra": ("Bhadra", "भद्रा"), "city": ("City", "शहर"),
    "faq_h": ("Questions about today's panchang", "आज के पंचांग से जुड़े प्रश्न"),
}


def _key(d):
    return f"aaj-panchang:v{CACHE_VERSION}:{d.isoformat()}"


def today_ist():
    return timezone.now().astimezone(IST).date()


def _when(text, tz):
    """'25-11-2026, 16:50' (engine format) -> aware datetime, or None."""
    try:
        return tz.localize(datetime.strptime(text, "%d-%m-%Y, %H:%M"))
    except (TypeError, ValueError):
        return None


def _clock(d, text, tz):
    """'HH:MM' on local date d -> aware datetime, or None."""
    try:
        return tz.localize(datetime.combine(d, datetime.strptime(text, "%H:%M").time()))
    except (TypeError, ValueError):
        return None


def city_day(place, d):
    """Panchang at sunrise, muhurats, Rahu/Gulika Kaal, Disha Shool and Do's/Don'ts for one place on local date d."""
    tz = pytz.timezone(place["tz"])
    lat, lon = place["lat"], place["lon"]
    sunrise, _ = pe.sun_times(d, lat, lon, tz)
    at = sunrise + timedelta(minutes=2)          # the limbs in force at sunrise (the vaar has begun)
    name = place["name"][0] if isinstance(place["name"], (list, tuple)) else place["name"]
    p = get_panchang(target_date=at, lat=lat, lon=lon, timezone_str=place["tz"], city_name=name)
    g = mu.day_guidance(d, lat, lon, place["tz"])
    c = lambda key: _clock(d, p.get(key), tz)
    shool = p.get("disha_shool") or {}
    moon_sign = ZODIAC_SIGNS[int((p.get("moon_longitude") or 0) // 30) % 12]
    return {
        "key": place.get("key", "custom"), "name": place["name"], "query": place.get("query", name),
        "lat": lat, "lon": lon, "tz": place["tz"],
        "weekday": d.strftime("%A"), "vaar": p.get("weekday"),
        "paksha_tithi": p.get("paksha_tithi"), "tithi_end": _when(p.get("tithi_end"), tz),
        "nakshatra": p.get("nakshatra"), "nakshatra_end": _when(p.get("nakshatra_end"), tz),
        "yoga": p.get("yoga"), "yoga_end": _when(p.get("yoga_end"), tz),
        "karana": p.get("karana"), "karana_end": _when(p.get("karana_end"), tz),
        "moon_sign": moon_sign,
        "amanta_month": p.get("amanta_month"), "purnimanta_month": p.get("purnimanta_month"),
        "ritu": (p.get("ritu_sayana") or "").split(" (")[0],
        "sunrise": c("sunrise"), "sunset": c("sunset"), "moonrise": p.get("moonrise"), "moonset": p.get("moonset"),
        "muhurats": [
            (MUHURAT_NAMES[0], c("brahma_muhurat_start"), c("brahma_muhurat_end")),
            (MUHURAT_NAMES[1], c("abhijeetstart"), c("abhijeetend")),
            (MUHURAT_NAMES[2], c("vijaymuhuratstart"), c("vijaymuhuratend")),
            (MUHURAT_NAMES[3], c("pradoshstart"), c("pradoshend")),
        ],
        "rahu_kaal": (c("rahukaalstart"), c("rahukaalend")),
        "gulika_kaal": (c("gulikakaalstart"), c("gulikakaalend")),
        "disha_shool": {"directions": shool.get("directions", ""),
                        "remedy": (shool.get("remedy", ""), REMEDY_HI.get(shool.get("remedy", ""), ""))},
        # Do's and Don'ts
        "good_for": g["good_for"],
        "special_yogas": g["special_yogas"],
        "cautions": [x for x in g["cautions"] if x["key"] != "Rahu Kaal"],    # Rahu Kaal has its own row
        "shopping": g["shopping"], "guide": g["guide"], "colours": g["colours"]["day"],
    }


def _good_groups(cities):
    """Purposes that share the same windows in every city:
    [{"purposes": [(key, title)...], "per_city": [(city name pair, [(start, end)...]) ...]}]."""
    groups = {}
    for p in cities[0]["good_for"]:
        wins = []
        for city in cities:
            match = next((x for x in city["good_for"] if x["key"] == p["key"]), None)
            wins.append(tuple((w["start"], w["end"]) for w in (match["windows"] if match else [])))
        grp = groups.setdefault(tuple(wins), {"purposes": [], "per_city": [(c["name"], list(w)) for c, w in zip(cities, wins)]})
        grp["purposes"].append((p["key"], p["title"]))
    return list(groups.values())


def muhurat_rows(cities):
    """[(name pair, [(start, end) per city])] for the muhurat table."""
    return [(cities[0]["muhurats"][i][0], [(c["muhurats"][i][1], c["muhurats"][i][2]) for c in cities])
            for i in range(len(cities[0]["muhurats"]))]


def _diet(d, place):
    from ..views.grahan_views import aahaar_context
    out = {}
    for lang in ("en", "hi"):
        ctx = aahaar_context(d, place["lat"], place["lon"], place["tz"], place["name"][0],
                             now_time=datetime.strptime("12:00", "%H:%M").time(), lang=lang)
        out[lang] = ctx["guidance"]
    return out


def _festivals(d):
    today = fc.get_festivals_for_day(d)
    upcoming = [f for f in fc.get_festivals_between(d + timedelta(days=1), d + timedelta(days=FESTIVAL_DAYS))
                if f["importance"] == "high" and f["slug"] not in BLACKOUT_SLUGS]
    return ([f for f in today if f["slug"] not in BLACKOUT_SLUGS], upcoming)


def _panchak(d, end):
    """Panchak spells (Moon in Kumbha then Meena) overlapping [d, end], IST."""
    rows = [r for r in ps.find_events("moon_sign", d, end) if r.number in (10, 11)]
    spans = []
    for r in rows:
        a, b = ps.as_local(r, IST)["start"], ps.as_local(r, IST)["end"]
        if spans and abs((a - spans[-1][1]).total_seconds()) < 60:
            spans[-1] = (spans[-1][0], b)
        else:
            spans.append((a, b))
    return spans


def _bhadra(d, end):
    return [(ps.as_local(r, IST)["start"], ps.as_local(r, IST)["end"])
            for r in ps.find_events("karana", d, end, name="Vishti")]


def _unfavourable(d):
    """Every blackout period touching the next 90 days, plus Panchak; Bhadra separately (it comes twice a fortnight)."""
    end = d + timedelta(days=UNFAVOURABLE_DAYS)
    v = fc.VARANASI
    rows = []
    for d0, d1, name, note in mu.blocked_periods(d, end, "vivah", v["lat"], v["lon"], v["tz"]):
        slug = FESTIVAL_PAGE_PERIODS.get(name)
        if name.startswith("Adhik"):
            slug = "adhik-maas"
        rows.append({"name": name, "start": d0, "end": d1, "note": note, "kind": "period",
                     "slug": slug, "year": d0.year, "running": d0 <= d})
    for a, b in _panchak(d, end):
        rows.append({"name": "Panchak", "start": a, "end": b, "note": PANCHAK_NOTE, "kind": "panchak",
                     "running": a.date() <= d, "timed": True})
    rows.sort(key=lambda r: (r["start"].date() if isinstance(r["start"], datetime) else r["start"]))
    return rows, _bhadra(d, end)


def _shani(d):
    """Moon signs (janma rashi) under, or entering, Sade Sati or Dhaiya within the next 180 days."""
    horizon = d + timedelta(days=SHANI_DAYS)
    out = []
    for i, sign in enumerate(ZODIAC_SIGNS):
        for p in shani.lifetime(datetime(d.year - 10, d.month, 1), i, 20):
            if p["end"] < d or p["start"] > horizon:
                continue
            phase = next((ph for ph in p["phases"] if ph["start"] <= max(d, p["start"]) < ph["end"]), None)
            next_phase = next((ph for ph in p["phases"] if d < ph["start"] <= horizon), None)
            out.append({"sign": sign, "index": i, "key": p["key"], "kind": p["kind"], "start": p["start"],
                        "end": p["end"], "running": p["start"] <= d, "begins_soon": p["start"] > d,
                        "ends_soon": p["end"] <= horizon, "phase": phase, "next_phase": next_phase})
    out.sort(key=lambda r: (not r["begins_soon"], r["index"]))
    return out


def build(d=None, now=None):
    """Compute the page for date d (default: today in IST), store it, and return it."""
    d = d or today_ist()
    cities = [city_day(c, d) for c in CITIES]
    festivals_today, upcoming = _festivals(d)
    unfavourable, bhadra = _unfavourable(d)
    snap = {
        "date": d,
        "computed_at": (now or timezone.now()).astimezone(IST),
        "cities": cities,
        "good_groups": _good_groups(cities),
        "diet": _diet(d, CITIES[0]),
        "festivals_today": festivals_today,
        "upcoming_festivals": upcoming,
        "unfavourable": unfavourable,
        "bhadra": bhadra,
        "shani": _shani(d),
    }
    cache.set(_key(d), snap, CACHE_SECONDS)
    return snap


def today_snapshot():
    """Today's stored page; built now (and stamped now) if the morning job has not run yet."""
    d = today_ist()
    snap = cache.get(_key(d))
    if snap is None:
        snap = build(d)
    return snap


def stamp_for(d):
    """When the stored page for d was computed (for the sitemap), or None."""
    snap = cache.get(_key(d))
    return snap["computed_at"] if snap else None
