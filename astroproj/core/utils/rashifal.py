# core/utils/rashifal.py
"""
Daily rashifal (/rashifal/ and /rashifal/<sign>/), worked out from the real sky - nothing copied, nothing random.

Layers
  1. Astronomy     Swiss Ephemeris positions of all nine grahas at Varanasi sunrise (sidereal, the panchang's
                   ayanamsa; Rahu = true node, Ketu opposite), with speed (vakri) and distance from the Sun (asta).
  2. Astrology     For each Moon sign (janma rashi), every graha's house counted from it (gochar), with
                   * the classical favourable houses (Phaladeepika ch. 26): Sun 3 6 10 11, Moon 1 3 6 7 10 11,
                     Mars 3 6 11, Mercury 2 4 6 8 10 11, Jupiter 2 5 7 9 11, Venus 1 2 3 4 5 8 9 11 12,
                     Saturn / Rahu / Ketu 3 6 11;
                   * vedha: a good house is blocked when another graha sits in its vedha house
                     (no vedha between Sun and Saturn, or Moon and Mercury);
                   * strength: exalted x1.25, own sign x1.1, debilitated x0.75, combust x0.6, and the Moon's
                     brightness (paksha bala) on the Moon's good results;
                   * graha drishti on the rashi: all grahas 7th, Mars 4 and 8, Jupiter 5 and 9, Saturn 3 and 10
                     (Rahu and Ketu are given no drishti here);
                   * the Moon's company: grahas in the Moon's sign (Gaja Kesari with Jupiter, Vish yoga with Saturn,
                     Grahan yoga with Rahu or Ketu ...) and Jupiter's, Saturn's or Mars's drishti on the Moon.
  3. Interpretation Weighted score -> 2-5 stars (the Moon weighs most because it is the daily mover); per-area
                   scores (work, money, family, health) from the grahas that rule each area -> good / mixed / care;
                   text variants from rashifal_text.py picked by a hash of (date, rashi, slot).
                   If the Moon changes sign between sunrise and 22:00, both parts of the day are rated.
  4. Publishing    Built at 05:30 IST by `manage.py daily`, cached for the day; optional wording polish by an LLM
                   (rashifal_llm.py) that may rephrase but never change a rating, level, number, colour or time.

Lucky attributes: the graha giving the rashi the most support today (largest positive share of the score among the
seven hora grahas, else the rashi lord) -> its colour (turning daily), its number and the rashi lord's number
(Chaldean: Sun 1, Moon 2, Jupiter 3, Rahu 4, Mercury 5, Venus 6, Ketu 7, Saturn 8, Mars 9), and its first hora at
Varanasi clear of Rahu Kaal.

Owner's tone rule: reassure, never frighten; never below 2 stars. Readings need an acharya's review.
"""
import hashlib
from datetime import date, datetime, timedelta

import pytz
import swisseph as swe
from django.core.cache import cache

from . import cities
from . import day_periods
from . import muhurat as mu
from . import panchang_engine as pe
from . import rashifal_text as RT
from .constants import NAKSHATRA_NAMES, ZODIAC_SIGNS

CACHE_VERSION = 2
MIN_PART = timedelta(hours=2)    # shortest part of the day worth its own rating
IST = pytz.timezone("Asia/Kolkata")

# slug, (English, Hindi), Western name, lord, symbol
SIGNS = [
    ("mesh", ("Mesh", "मेष"), "Aries", "Mars", "♈"),
    ("vrishabh", ("Vrishabh", "वृषभ"), "Taurus", "Venus", "♉"),
    ("mithun", ("Mithun", "मिथुन"), "Gemini", "Mercury", "♊"),
    ("kark", ("Kark", "कर्क"), "Cancer", "Moon", "♋"),
    ("simha", ("Simha", "सिंह"), "Leo", "Sun", "♌"),
    ("kanya", ("Kanya", "कन्या"), "Virgo", "Mercury", "♍"),
    ("tula", ("Tula", "तुला"), "Libra", "Venus", "♎"),
    ("vrishchik", ("Vrishchik", "वृश्चिक"), "Scorpio", "Mars", "♏"),
    ("dhanu", ("Dhanu", "धनु"), "Sagittarius", "Jupiter", "♐"),
    ("makar", ("Makar", "मकर"), "Capricorn", "Saturn", "♑"),
    ("kumbh", ("Kumbh", "कुम्भ"), "Aquarius", "Saturn", "♒"),
    ("meen", ("Meen", "मीन"), "Pisces", "Jupiter", "♓"),
]
SLUGS = [s[0] for s in SIGNS]

PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
HORA_PLANETS = PLANETS[:7]
BODY = {"Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS, "Mercury": swe.MERCURY, "Jupiter": swe.JUPITER,
        "Venus": swe.VENUS, "Saturn": swe.SATURN, "Rahu": swe.TRUE_NODE}
PLANET_HI = {"Sun": "सूर्य", "Moon": "चन्द्र", "Mars": "मंगल", "Mercury": "बुध", "Jupiter": "गुरु", "Venus": "शुक्र",
             "Saturn": "शनि", "Rahu": "राहु", "Ketu": "केतु"}

GOOD = {"Sun": {3, 6, 10, 11}, "Moon": {1, 3, 6, 7, 10, 11}, "Mars": {3, 6, 11}, "Mercury": {2, 4, 6, 8, 10, 11},
        "Jupiter": {2, 5, 7, 9, 11}, "Venus": {1, 2, 3, 4, 5, 8, 9, 11, 12}, "Saturn": {3, 6, 11},
        "Rahu": {3, 6, 11}, "Ketu": {3, 6, 11}}
MOON_MIXED = {2, 5, 9}
# good house -> vedha house
VEDHA = {"Sun": {3: 9, 6: 12, 10: 4, 11: 5}, "Moon": {1: 5, 3: 9, 6: 12, 7: 2, 10: 4, 11: 8},
         "Mars": {3: 12, 6: 9, 11: 5}, "Mercury": {2: 5, 4: 3, 6: 9, 8: 1, 10: 8, 11: 12},
         "Jupiter": {2: 12, 5: 4, 7: 3, 9: 10, 11: 8},
         "Venus": {1: 8, 2: 7, 3: 1, 4: 10, 5: 9, 8: 5, 9: 11, 11: 3, 12: 6},
         "Saturn": {3: 12, 6: 9, 11: 5}, "Rahu": {3: 12, 6: 9, 11: 5}, "Ketu": {3: 12, 6: 9, 11: 5}}
NO_VEDHA = {frozenset({"Sun", "Saturn"}), frozenset({"Moon", "Mercury"})}
EXALT = {"Sun": 0, "Moon": 1, "Mars": 9, "Mercury": 5, "Jupiter": 3, "Venus": 11, "Saturn": 6, "Rahu": 1, "Ketu": 7}
OWN = {"Sun": {4}, "Moon": {3}, "Mars": {0, 7}, "Mercury": {2, 5}, "Jupiter": {8, 11}, "Venus": {1, 6},
       "Saturn": {9, 10}, "Rahu": set(), "Ketu": set()}
COMBUST_ORB = {"Moon": 12, "Mars": 17, "Mercury": 14, "Jupiter": 11, "Venus": 10, "Saturn": 15}
DRISHTI = {"Sun": [7], "Moon": [7], "Mercury": [7], "Venus": [7], "Mars": [4, 7, 8], "Jupiter": [5, 7, 9],
           "Saturn": [3, 7, 10], "Rahu": [], "Ketu": []}
WEIGHT = {"Moon": 3.0, "Sun": 1.0, "Mars": 1.0, "Mercury": 0.8, "Venus": 0.8, "Jupiter": 1.5, "Saturn": 1.5,
          "Rahu": 0.6, "Ketu": 0.6}
RASHI_DRISHTI = {"Jupiter": 0.75, "Venus": 0.3, "Mercury": 0.2, "Saturn": -0.5, "Mars": -0.5, "Sun": -0.25}
MOON_COMPANY = {"Jupiter": 0.6, "Venus": 0.3, "Mercury": 0.3, "Mars": 0.0, "Saturn": -0.5, "Rahu": -0.6, "Ketu": -0.5,
                "Sun": -0.4}
MOON_DRISHTI = {"Jupiter": 0.5, "Saturn": -0.3, "Mars": -0.3}
AREA_WEIGHT = {
    "career": {"Moon": 1.0, "Sun": 1.0, "Saturn": 1.0, "Mercury": 0.7, "Mars": 0.5, "Jupiter": 0.4, "Rahu": 0.3},
    "money": {"Moon": 1.0, "Jupiter": 1.0, "Venus": 0.8, "Mercury": 0.8, "Saturn": 0.3, "Rahu": 0.3},
    "family": {"Moon": 1.2, "Venus": 1.0, "Jupiter": 0.7, "Mars": 0.5, "Ketu": 0.3},
    "health": {"Moon": 1.2, "Sun": 0.8, "Mars": 0.8, "Saturn": 0.6, "Ketu": 0.3},
}
MOON_HOUSE_AREA = {1: {"health": .5}, 2: {"money": -.5}, 3: {"career": .5}, 4: {"family": .3, "health": -.3},
                   5: {"money": -.5}, 6: {"health": .5, "career": .3}, 7: {"family": .7},
                   8: {"health": -.5, "money": -.3}, 9: {}, 10: {"career": .7}, 11: {"money": .7},
                   12: {"money": -.5, "health": -.3}}
AREAS = ("career", "money", "family", "health")
# Calibrated on every rashi and day of 2026 (calibrate()): ~20% 2 stars, 30% 3, 30% 4, 20% 5;
# areas ~25% care, 40% mixed, 35% good.
STAR_CUTS = (-3.42, -1.15, 1.25)
AREA_CUTS = (-1.21, 0.16)

NUMBER = {"Sun": 1, "Moon": 2, "Jupiter": 3, "Rahu": 4, "Mercury": 5, "Venus": 6, "Ketu": 7, "Saturn": 8, "Mars": 9}
COLOUR_KEY = {"Sun": 0, "Moon": 1, "Mars": 2, "Mercury": 3, "Jupiter": 4, "Venus": 5, "Saturn": 6}   # muhurat.DAY_COLOURS
COLOUR_HI = {"Red": "लाल", "Orange": "नारंगी", "Saffron": "केसरिया", "Gold": "सुनहरा", "White": "सफ़ेद", "Silver": "चाँदी",
             "Cream": "क्रीम", "Light blue": "हल्का नीला", "Maroon": "मैरून", "Coral": "मूँगिया", "Green": "हरा",
             "Emerald": "पन्ना हरा", "Light green": "हल्का हरा", "Turquoise": "फ़िरोज़ी", "Yellow": "पीला", "Pink": "गुलाबी",
             "Pastel blue": "हल्का आसमानी", "Black": "काला", "Navy": "गहरा नीला", "Dark blue": "गहरा नीला", "Purple": "बैंगनी"}

TEXT = {
    "h1": ("Aaj Ka Rashifal", "आज का राशिफल"),
    "lede": ("Today's rashifal for all 12 rashis, worked out from where all nine grahas really are today. "
             "Read it for your Moon sign (janma rashi). Not sure of yours? Many families go by the first letter of the name.",
             "सभी 12 राशियों का आज का राशिफल, आज नौ ग्रहों की वास्तविक स्थिति से निकाला गया। इसे अपनी जन्म राशि "
             "(चन्द्र राशि) के लिए पढ़ें। अपनी राशि पता नहीं? बहुत से परिवार नाम के पहले अक्षर से राशि मानते हैं।"),
    "sign_h1": ("{name} Rashifal Today", "आज का {name} राशिफल"),
    "read": ("Read full rashifal", "पूरा राशिफल पढ़ें"),
    "career": ("Work and career", "काम और करियर"), "money": ("Money", "धन"), "family": ("Family and love", "परिवार और प्रेम"),
    "health": ("Health", "स्वास्थ्य"), "today_good": ("Good for today", "आज किसके लिए अच्छा"),
    "colour": ("Colour", "रंग"), "number": ("Number", "अंक"), "good_time": ("Good time", "शुभ समय"),
    "hora_of": ("{planet} hora, Varanasi", "{planet} की होरा, वाराणसी"),
    "lucky_from": ("from {planet}, your most supportive graha today", "{planet} से, आज आपके सबसे सहायक ग्रह"),
    "influences_h": ("Today's key influences", "आज के मुख्य प्रभाव"),
    "sky_h": ("Today's sky", "आज का आकाश"),
    "longer_h": ("The longer picture: Guru and Shani", "लम्बी अवधि: गुरु और शनि"),
    "tara_h": ("Tarabalam for your nakshatra", "आपके नक्षत्र का ताराबल"),
    "tara_note": ("Each rashi holds parts of three nakshatras. If you know your birth nakshatra, this is your tara today.",
                  "हर राशि में तीन नक्षत्रों के भाग होते हैं। यदि आप अपना जन्म नक्षत्र जानते हैं, तो यह आज आपका तारा है।"),
    "level": {"good": ("Good", "अच्छा"), "mixed": ("Mixed", "मिश्रित"), "care": ("Go gently", "सावधानी")},
    "letters": ("Name letters", "नाम अक्षर"),
    "how_h": ("How this rashifal is worked out", "यह राशिफल कैसे निकाला जाता है"),
    "how": ("This is a general reading for everyone born with the Moon in {name}. Each morning the positions of all nine "
            "grahas are computed with the Swiss Ephemeris. Their houses from {name} (gochar) are scored by the classical "
            "favourable houses, with vedha, exaltation and debilitation, combustion, the Moon's brightness, graha drishti and "
            "the Moon's company taken into account. The Moon weighs most because it changes the day. The lucky colour, number "
            "and time come from the graha giving {name} the most support today. Your own kundali, with your dasha and exact "
            "birth time, says much more. For health, always follow your doctor.",
            "यह उन सबके लिए सामान्य फल है जिनके जन्म के समय चन्द्रमा {name} राशि में था। हर सुबह नौ ग्रहों की स्थिति स्विस "
            "एफ़ेमेरिस से निकाली जाती है। {name} से उनके भाव (गोचर) शास्त्रीय शुभ भावों के अनुसार आँके जाते हैं, जिसमें वेध, "
            "उच्च और नीच, अस्त, चन्द्रमा का बल, ग्रह दृष्टि और चन्द्रमा के साथ के ग्रह भी गिने जाते हैं। चन्द्रमा का भार सबसे "
            "अधिक है क्योंकि दिन वही बदलता है। शुभ रंग, अंक और समय उस ग्रह से हैं जो आज {name} को सबसे अधिक सहारा दे रहा है। "
            "आपकी अपनी कुण्डली, आपकी दशा और जन्म समय के साथ, इससे कहीं अधिक बताती है। स्वास्थ्य के लिए हमेशा अपने डॉक्टर "
            "की सलाह मानें।"),
    "kundali_cta": ("Not sure of your Moon sign? Make your free kundali: it shows your rashi, nakshatra and your own Sade Sati dates.",
                    "अपनी जन्म राशि पता नहीं? अपनी निःशुल्क कुण्डली बनाएँ: इसमें आपकी राशि, नक्षत्र और आपकी साढ़े साती की तिथियाँ हैं।"),
    "other_signs": ("Other rashis", "अन्य राशियाँ"),
    "updated": ("Updated", "अपडेट"),
    "rating": ("Day rating", "दिन की रेटिंग"),
    "parts_h": ("The day in two parts", "दिन के दो भाग"),
    "parts_note": ("The Moon changes sign at {time}, so the day reads differently before and after.",
                   "चन्द्रमा {time} पर राशि बदलते हैं, इसलिए उससे पहले और बाद का फल अलग है।"),
}

ORDINAL = {1: ("1st", "पहले"), 2: ("2nd", "दूसरे"), 3: ("3rd", "तीसरे"), 4: ("4th", "चौथे"), 5: ("5th", "पाँचवें"),
           6: ("6th", "छठे"), 7: ("7th", "सातवें"), 8: ("8th", "आठवें"), 9: ("9th", "नौवें"), 10: ("10th", "दसवें"),
           11: ("11th", "ग्यारहवें"), 12: ("12th", "बारहवें")}

# Nakshatra nature (Muhurta Chintamani) -> the day's "good for" line, same for every sign
NAKSHATRA_NATURE = {
    "dhruva": ({"Rohini", "Uttara Phalguni", "Uttara Ashadha", "Uttara Bhadrapada"},
               ("Fixed (dhruva) nakshatra: good for lasting things such as foundations, planting, buying property and long-term plans.",
                "स्थिर (ध्रुव) नक्षत्र: स्थायी कामों के लिए अच्छा, जैसे नींव, पौधे लगाना, सम्पत्ति खरीदना और लम्बी योजनाएँ।")),
    "chara": ({"Swati", "Punarvasu", "Shravana", "Dhanishta", "Shatabhisha"},
              ("Moving (chara) nakshatra: good for travel, vehicles, change of place and starting a journey.",
               "चर नक्षत्र: यात्रा, वाहन, स्थान परिवर्तन और सफ़र शुरू करने के लिए अच्छा।")),
    "ugra": ({"Bharani", "Magha", "Purva Phalguni", "Purva Ashadha", "Purva Bhadrapada"},
             ("Fierce (ugra) nakshatra: good for bold and competitive work; keep gentle beginnings such as ceremonies for another day.",
              "उग्र नक्षत्र: साहस और प्रतियोगिता के कामों के लिए अच्छा; संस्कार जैसी कोमल शुरुआत किसी और दिन रखें।")),
    "mishra": ({"Krittika", "Vishakha"},
               ("Mixed (mishra) nakshatra: good for routine work and duties; big new beginnings can wait.",
                "मिश्र नक्षत्र: रोज़ के काम और ज़िम्मेदारियों के लिए अच्छा; बड़ी नई शुरुआत रुक सकती है।")),
    "kshipra": ({"Ashwini", "Pushya", "Hasta"},
                ("Swift (kshipra) nakshatra: good for quick tasks, trade, learning, medicine and short trips.",
                 "क्षिप्र नक्षत्र: जल्दी होने वाले काम, व्यापार, पढ़ाई, औषधि और छोटी यात्रा के लिए अच्छा।")),
    "mridu": ({"Mrigashira", "Chitra", "Anuradha", "Revati"},
              ("Soft (mridu) nakshatra: good for friendship, music and arts, new clothes and jewellery, and romance.",
               "मृदु नक्षत्र: मित्रता, संगीत और कला, नए कपड़े और गहने, और प्रेम के लिए अच्छा।")),
    "tikshna": ({"Ardra", "Ashlesha", "Jyeshtha", "Moola"},
                ("Sharp (tikshna) nakshatra: good for clearing obstacles, hard decisions and research; keep new ventures for another day.",
                 "तीक्ष्ण नक्षत्र: बाधाएँ हटाने, कठिन फ़ैसलों और खोज के लिए अच्छा; नए उद्यम किसी और दिन रखें।")),
}


# ---------------------------------------------------------------------------
# Layer 1: the sky
# ---------------------------------------------------------------------------

def sky_at(jd):
    """{planet: {"lon", "sign", "speed", "vakri"}} for all nine grahas (sidereal)."""
    swe.set_sid_mode(pe.SID_MODE)
    out = {}
    for p, body in BODY.items():
        pos = swe.calc_ut(jd, body, pe._FLAGS)[0]
        lon = pos[0] % 360
        out[p] = {"lon": lon, "sign": int(lon // 30), "speed": pos[3], "vakri": pos[3] < 0 and p not in ("Rahu",)}
    k = (out["Rahu"]["lon"] + 180) % 360
    out["Ketu"] = {"lon": k, "sign": int(k // 30), "speed": out["Rahu"]["speed"], "vakri": False}
    return out


def _brightness(sky):
    """0 at Amavasya, 1 at Purnima."""
    elong = (sky["Moon"]["lon"] - sky["Sun"]["lon"]) % 360
    return 1 - abs(180 - elong) / 180


def _combust(sky, p):
    if p not in COMBUST_ORB:
        return False
    d = abs((sky[p]["lon"] - sky["Sun"]["lon"] + 180) % 360 - 180)
    return d < COMBUST_ORB[p]


def _dignity(p, sign):
    if sign == EXALT[p]:
        return "exalted", 1.25
    if sign == (EXALT[p] + 6) % 12:
        return "debilitated", 0.75
    if sign in OWN[p]:
        return "own", 1.1
    return "", 1.0


def _house(sign, rashi):
    return (sign - rashi) % 12 + 1


def _aspects(p, house):
    """Houses (from the rashi) that planet p in `house` casts drishti on."""
    return {(house - 1 + a - 1) % 12 + 1 for a in DRISHTI[p]}


# ---------------------------------------------------------------------------
# Layer 2-3: one rashi
# ---------------------------------------------------------------------------

def score(rashi, sky, moon_sign=None):
    """Weighted gochar score for `rashi` (0-11). moon_sign overrides the Moon's sign (for the evening part)."""
    signs = {p: sky[p]["sign"] for p in PLANETS}
    if moon_sign is not None:
        signs["Moon"] = moon_sign
    houses = {p: _house(signs[p], rashi) for p in PLANETS}
    bright = _brightness(sky)
    parts, notes = {}, []
    for p in PLANETS:
        h = houses[p]
        if p == "Moon":
            base = 1.0 if h in GOOD["Moon"] else (0.0 if h in MOON_MIXED else -1.0)
        else:
            base = 1.0 if h in GOOD[p] else -0.5
        blocked_by = None
        if base > 0 and h in VEDHA.get(p, {}):
            vh = VEDHA[p][h]
            blocked_by = next((q for q in PLANETS if q != p and houses[q] == vh
                               and frozenset({p, q}) not in NO_VEDHA), None)
            if blocked_by:
                base = 0.0
        dig, m = _dignity(p, signs[p])
        s = base * m if base > 0 else base * (2 - m)
        if base > 0 and p != "Moon" and _combust(sky, p):
            s *= 0.6
        if base > 0 and p == "Moon":
            s *= 0.6 + 0.4 * bright
        parts[p] = {"house": h, "base": base, "score": WEIGHT[p] * s, "dignity": dig, "vedha": blocked_by,
                    "combust": _combust(sky, p) if p != "Moon" else False, "vakri": sky[p]["vakri"]}
    # graha drishti on the rashi itself
    rashi_drishti = {p: RASHI_DRISHTI[p] for p in RASHI_DRISHTI if 1 in _aspects(p, houses[p])}
    # the Moon's company (same for every rashi): grahas with the Moon, and drishti on the Moon
    moon_h = houses["Moon"]
    company = [p for p in PLANETS if p != "Moon" and signs[p] == signs["Moon"]]
    on_moon = [p for p in MOON_DRISHTI if p not in company and moon_h in _aspects(p, houses[p])]
    moon_q = sum(MOON_COMPANY[p] for p in company) + sum(MOON_DRISHTI[p] for p in on_moon)
    total = sum(x["score"] for x in parts.values()) + sum(rashi_drishti.values()) + moon_q
    areas = {}
    for a in AREAS:
        v = sum(w * parts[p]["score"] / WEIGHT[p] for p, w in AREA_WEIGHT[a].items())
        v += MOON_HOUSE_AREA[moon_h].get(a, 0) + 0.3 * sum(rashi_drishti.values()) + 0.5 * moon_q
        areas[a] = v
    return {"total": total, "areas": areas, "parts": parts, "houses": houses, "rashi_drishti": rashi_drishti,
            "company": company, "on_moon": on_moon, "moon_q": moon_q, "moon_house": moon_h}


def stars(total):
    a, b, c = STAR_CUTS
    return 2 if total < a else 3 if total < b else 4 if total < c else 5


def level(v):
    lo, hi = AREA_CUTS
    return "care" if v < lo else "mixed" if v < hi else "good"


def _pick(options, *key):
    h = int(hashlib.md5("|".join(str(k) for k in key).encode()).hexdigest(), 16)
    return options[h % len(options)]


def _pair(template, **kw):
    return tuple(template[i].format(**{k: (v[i] if isinstance(v, tuple) else v) for k, v in kw.items()}) for i in (0, 1))


def _lucky_planet(sc, lord):
    best = max(HORA_PLANETS, key=lambda p: sc["parts"][p]["score"])
    return best if sc["parts"][best]["score"] > 0 else lord


def _colour(planet, d, i):
    wear = mu.DAY_COLOURS[COLOUR_KEY[planet]]["wear"]
    name, hexv = wear[(d.toordinal() + i) % len(wear)]          # turns daily, and differs between rashis
    return {"name": (name, COLOUR_HI.get(name, name)), "hex": hexv}


def _good_hora(periods, planet):
    """The planet's first day hora clear of Rahu Kaal, else its first evening hora (ending by 22:00)."""
    r0, r1 = periods["rahu_kaal"]
    for h in periods["hora"]["day"]:
        if h["planet"] == planet and (h["end"] <= r0 or h["start"] >= r1):
            return h
    for h in periods["hora"]["night"]:
        if h["planet"] == planet and h["end"].hour < 22 and h["end"].date() == periods["date"]:
            return h
    return None


def _taras(rashi, today_nak):
    """[(nakshatra, tara number, (English, Hindi) tara name, level)] for the nakshatras that fall in the rashi."""
    naks = []
    for pada in range(rashi * 9, rashi * 9 + 9):
        n = pada // 4
        if n not in naks:
            naks.append(n)
    out = []
    for n in naks:
        t = (today_nak - n) % 27 % 9 + 1
        en, hi, lvl = RT.TARAS[t]
        out.append({"nakshatra": NAKSHATRA_NAMES[n], "tara": t, "name": (en, hi), "level": lvl,
                    "level_label": RT.TARA_LEVEL[lvl]})
    return out


def _influences(sc, d, slug):
    """Up to two supportive and one cautionary line from the faster grahas (Moon, Guru, Shani are shown elsewhere)."""
    fast = [p for p in ("Sun", "Mars", "Mercury", "Venus", "Rahu", "Ketu")]
    ranked = sorted(fast, key=lambda p: -abs(sc["parts"][p]["score"]))
    good = [p for p in ranked if sc["parts"][p]["score"] > 0][:2]
    care = [p for p in ranked if sc["parts"][p]["score"] < 0][:1]
    lines = []
    for p in good + care:
        part = sc["parts"][p]
        line = _pair(RT.PLANET_LINES[p][0 if part["score"] > 0 else 1], n=ORDINAL[part["house"]])
        extra = []
        if part["dignity"] == "exalted":
            extra.append(("(exalted, so stronger)", "(उच्च के, इसलिए अधिक बलवान)"))
        elif part["dignity"] == "debilitated":
            extra.append(("(debilitated, so weaker)", "(नीच के, इसलिए कमज़ोर)"))
        if part["combust"]:
            extra.append(("(close to the Sun, so muted)", "(सूर्य के पास अस्त, इसलिए धीमा)"))
        if extra:
            line = tuple(line[i] + " " + " ".join(e[i] for e in extra) for i in (0, 1))
        lines.append({"planet": p, "kind": "good" if part["score"] > 0 else "care", "text": line})
    return lines


def _longer(sc):
    g, s = sc["parts"]["Jupiter"], sc["parts"]["Saturn"]
    guru = _pair(RT.PLANET_LINES["Jupiter"][0 if g["score"] > 0 else 1], n=ORDINAL[g["house"]])
    sh = s["house"]
    if sh in (12, 1, 2):
        shani = _pair(RT.SHANI["sade"], n=ORDINAL[sh])
    elif sh in (4, 8):
        shani = _pair(RT.SHANI["dhaiya"], n=ORDINAL[sh])
    else:
        shani = _pair(RT.PLANET_LINES["Saturn"][0 if s["score"] > 0 else 1], n=ORDINAL[sh])
    lines = [guru, shani]
    if "Jupiter" in sc["rashi_drishti"]:
        lines.append(RT.JUPITER_ASPECTS_RASHI)
    if "Saturn" in sc["rashi_drishti"]:
        lines.append(RT.SATURN_ASPECTS_RASHI)
    if "Mars" in sc["rashi_drishti"]:
        lines.append(RT.MARS_ASPECTS_RASHI)
    return lines


def _moon_line(sc):
    """The Chandra gochar line, or the vedha line when another graha blocks the Moon's good house."""
    m = sc["parts"]["Moon"]
    if m["vedha"]:
        q = m["vedha"]
        en = f"the {q}" if q in ("Sun", "Moon") else q
        return _pair(RT.MOON_VEDHA, n=ORDINAL[m["house"]], planet=(en, PLANET_HI[q]), v=ORDINAL[sc["houses"][q]])
    return RT.MOON_HOUSE[m["house"]]


def _sky_notes(sc, sky):
    notes = [RT.MOON_WITH[p] for p in sc["company"]]
    if "Jupiter" in sc["on_moon"]:
        notes.append(RT.JUPITER_ASPECTS_MOON)
    for p in ("Mercury", "Venus", "Mars", "Jupiter", "Saturn"):
        if sky[p]["vakri"]:
            notes.append(_pair(RT.VAKRI, planet=(p, PLANET_HI[p])))
    return notes


# ---------------------------------------------------------------------------
# Layer 4: the day
# ---------------------------------------------------------------------------

def compute(d):
    """All 12 readings for local date d (IST)."""
    from . import naamkaran
    from ..templatetags.vp import EXTRA_HI
    periods = day_periods.cached(cities.get("varanasi"), d)
    sunrise, next_sunrise = periods["sunrise"], periods["next_sunrise"]
    jd = pe.dt_to_jd(sunrise)
    sky = sky_at(jd)
    moon_sign = sky["Moon"]["sign"]
    today_nak = pe.index_at(jd, "nakshatra")
    nak = NAKSHATRA_NAMES[today_nak]
    nature = next((k for k, (members, _) in NAKSHATRA_NATURE.items() if nak in members), "mishra")
    change_at = pe.jd_to_local(pe.next_transition(jd, "moon_sign"), IST)
    late = sunrise.replace(hour=22, minute=0, second=0, microsecond=0)
    split = change_at < late
    sign_pair = lambda i: (ZODIAC_SIGNS[i], EXTRA_HI.get(ZODIAC_SIGNS[i], ZODIAC_SIGNS[i]))

    readings = []
    for i, (slug, name, western, lord, symbol) in enumerate(SIGNS):
        sc = score(i, sky)
        parts_of_day = None
        if split:
            sc2 = score(i, sky, moon_sign=(moon_sign + 1) % 12)
            first_longer = (change_at - sunrise) >= (late - change_at)
            if min(change_at - sunrise, late - change_at) >= MIN_PART:      # both parts long enough to read
                parts_of_day = [
                    {"label": _pair(RT.SEGMENT["until"], time=change_at.strftime("%H:%M")), "stars": stars(sc["total"]),
                     "moon": _moon_line(sc)},
                    {"label": _pair(RT.SEGMENT["from"], time=change_at.strftime("%H:%M")), "stars": stars(sc2["total"]),
                     "moon": _moon_line(sc2)},
                ]
            main = sc if first_longer else sc2
        else:
            main = sc
        rating = stars(main["total"])
        lucky = _lucky_planet(main, lord)
        hora = _good_hora(periods, lucky) or _good_hora(periods, lord)
        areas = {}
        for a in AREAS:
            lvl = level(main["areas"][a])
            areas[a] = {"level": lvl, "level_label": TEXT["level"][lvl],
                        "text": _pick(RT.AREAS[a][lvl], d, slug, a)}
        readings.append({
            "slug": slug, "name": name, "western": western, "symbol": symbol, "lord": (lord, PLANET_HI[lord]),
            "rating": rating, "score": round(main["total"], 2),
            "headline": _pick(RT.HEADLINES[rating], d, slug, "headline"),
            "moon_line": _moon_line(main), "moon_house": main["moon_house"],
            "moon_sign": sign_pair((i + main["moon_house"] - 1) % 12),
            "areas": areas, "parts_of_day": parts_of_day,
            "influences": _influences(main, d, slug), "longer": _longer(main),
            "lucky_planet": (lucky, PLANET_HI[lucky]), "colour": _colour(lucky, d, i),
            "lucky_is_lord": main["parts"][lucky]["score"] <= 0,       # no graha supports today: the rashi lord stands in
            "numbers": sorted({NUMBER[lucky], NUMBER[lord]}),
            "hora": hora, "hora_planet": (hora["planet"], PLANET_HI[hora["planet"]]) if hora else None,
            "taras": _taras(i, today_nak),
            "letters": naamkaran.rashi_letters(i),
        })
    base = score(0, sky)
    return {"date": d, "sunrise": sunrise, "nakshatra": nak, "nature": nature,
            "nature_text": NAKSHATRA_NATURE[nature][1], "moon_sign": moon_sign,
            "moves_at": change_at if split else None, "sky_notes": _sky_notes(base, sky),
            "positions": [{"planet": (p, PLANET_HI[p]), "sign": sign_pair(sky[p]["sign"]), "vakri": sky[p]["vakri"]}
                          for p in PLANETS],
            "readings": readings}


def calibrate(year=2026):
    """Print score quantiles over a year (to set STAR_CUTS and AREA_CUTS). Run by hand; ~10 s."""
    totals, areas = [], []
    d = date(year, 1, 1)
    while d.year == year:
        sky = sky_at(pe.dt_to_jd(IST.localize(datetime(d.year, d.month, d.day, 6, 30))))
        for i in range(12):
            sc = score(i, sky)
            totals.append(sc["total"])
            areas += list(sc["areas"].values())
        d += timedelta(days=1)
    totals.sort()
    areas.sort()
    q = lambda xs, f: round(xs[int(f * (len(xs) - 1))], 2)
    return {"stars": [q(totals, f) for f in (0.2, 0.5, 0.8)], "areas": [q(areas, f) for f in (0.25, 0.65)]}


def _key(d):
    return f"rashifal:v{CACHE_VERSION}:{d.isoformat()}"


def build(d, now=None):
    from django.utils import timezone
    data = compute(d)
    data["computed_at"] = (now or timezone.now()).astimezone(IST)
    try:
        from . import rashifal_llm
        rashifal_llm.polish_day(data)
    except Exception:                                    # wording polish is optional; the readings stand without it
        import logging
        logging.getLogger(__name__).exception("Rashifal polish failed; template wording kept")
    cache.set(_key(d), data, 3 * 24 * 3600)
    return data


def day(d):
    data = cache.get(_key(d))
    if data is None:
        data = build(d)
    return data


def stamp_for(d):
    data = cache.get(_key(d))
    return data["computed_at"] if data else None
