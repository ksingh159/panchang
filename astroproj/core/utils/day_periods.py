# core/utils/day_periods.py
"""
Choghadiya and Hora for one place and date (/aaj-ka-choghadiya/, /aaj-ki-hora/).

Both split sunrise -> sunset into equal day parts and sunset -> next sunrise into equal night parts:
8 choghadiyas (sequence from the weekday, helpers.get_choghadiya) and 12 horas each (Chaldean order from the
weekday's lord), the same sequences the full /panchang/ page uses.

    periods(place, d)     {"sunrise", "sunset", "next_sunrise", "choghadiya": {"day", "night"}, "hora": {"day", "night"},
                           "rahu_kaal": (start, end)}; every time an aware datetime in the place's zone
    cached(place, d)      the same, kept for three days (pages for the listed cities are built at 05:30 IST)

Text is (English, Hindi) pairs, shown with |pick. Owner's tone rule: reassure, never frighten.
"""
from datetime import timedelta

import pytz
from django.core.cache import cache

from . import panchang_engine as pe
from .constants import RAHU_KAAL
from .helpers import get_choghadiya

CACHE_VERSION = 1

# name -> (kind, planet, good for, Hindi name, Hindi good for); kind: good / neutral / avoid
CHOGHADIYA = {
    "Amrit": ("good", ("Moon", "चन्द्र"), ("The best of all: any good work, puja, starting something new.",
                                          "सबसे उत्तम: हर शुभ कार्य, पूजा, नई शुरुआत।"), "अमृत"),
    "Shubh": ("good", ("Jupiter", "गुरु"), ("Marriage talks, ceremonies, education, religious work.",
                                           "विवाह की बात, संस्कार, शिक्षा, धार्मिक कार्य।"), "शुभ"),
    "Labh": ("good", ("Mercury", "बुध"), ("Business, trade, money matters, study, buying.",
                                         "व्यापार, लेन-देन, धन के काम, पढ़ाई, खरीदारी।"), "लाभ"),
    "Char": ("neutral", ("Venus", "शुक्र"), ("Also called Chal (moving): good for travel, vehicles and luxury or comfort purchases; "
                                            "not favourable for work that needs stability, such as griha pravesh, laying a foundation "
                                            "or long-term commitments.",
                                            "चल भी कहते हैं: यात्रा, वाहन और विलासिता या आराम की खरीदारी के लिए अच्छा; स्थिरता चाहने "
                                            "वाले कामों के लिए अनुकूल नहीं, जैसे गृह प्रवेश, नींव रखना या लम्बी प्रतिबद्धताएँ।"), "चर"),
    "Udveg": ("avoid", ("Sun", "सूर्य"), ("Keep new beginnings for another slot; government and official work is traditionally allowed.",
                                         "नई शुरुआत दूसरे समय रखें; सरकारी और दफ़्तरी काम परम्परा से किए जाते हैं।"), "उद्वेग"),
    "Rog": ("avoid", ("Mars", "मंगल"), ("Keep new beginnings, travel and agreements for another slot.",
                                       "नई शुरुआत, यात्रा और समझौते दूसरे समय रखें।"), "रोग"),
    "Kaal": ("avoid", ("Saturn", "शनि"), ("Keep new beginnings for another slot; routine and hard work go on as usual.",
                                         "नई शुरुआत दूसरे समय रखें; रोज़ का और मेहनत का काम सामान्य रूप से चलता रहे।"), "काल"),
}

# planet -> (Hindi name, good for, Hindi good for)
HORA = {
    "Sun": ("सूर्य", "Government work, meeting seniors, job interviews, matters of authority and health.",
            "सरकारी काम, बड़ों से मिलना, नौकरी का साक्षात्कार, अधिकार और स्वास्थ्य के काम।"),
    "Moon": ("चन्द्र", "Travel, meeting people, home and family matters, water and milk, creative work.",
             "यात्रा, लोगों से मिलना, घर-परिवार के काम, जल और दूध से जुड़े काम, रचनात्मक कार्य।"),
    "Mars": ("मंगल", "Property and land, sports, courage and physical work, surgery; avoid arguments.",
             "भूमि और सम्पत्ति, खेल, साहस और शारीरिक काम, शल्य चिकित्सा; विवाद से बचें।"),
    "Mercury": ("बुध", "Business, study, writing, accounts, phone calls and messages, signing papers.",
                "व्यापार, पढ़ाई, लेखन, हिसाब-किताब, फ़ोन और सन्देश, काग़ज़ों पर हस्ताक्षर।"),
    "Jupiter": ("गुरु", "The most auspicious hora: puja, education, marriage talks, finance, advice from elders.",
                "सबसे शुभ होरा: पूजा, शिक्षा, विवाह की बात, धन के काम, बड़ों की सलाह।"),
    "Venus": ("शुक्र", "Buying clothes, jewellery and vehicles, arts and music, romance, beauty.",
              "कपड़े, गहने और वाहन खरीदना, कला और संगीत, प्रेम, सौन्दर्य।"),
    "Saturn": ("शनि", "Hard work, machinery, iron and oil, old pending matters; keep new beginnings for another hora.",
               "मेहनत का काम, मशीनें, लोहा और तेल, पुराने अटके काम; नई शुरुआत दूसरी होरा में रखें।"),
}
CHALDEAN = ["Saturn", "Jupiter", "Mars", "Sun", "Venus", "Mercury", "Moon"]
WEEKDAY_LORD = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]     # Sunday first


def _sunday_index(d):
    return (d.weekday() + 1) % 7


def _horas(start, end, first):
    step = (end - start) / 12
    i0 = CHALDEAN.index(first)
    return [{"n": i + 1, "planet": CHALDEAN[(i0 + i) % 7], "start": start + step * i, "end": start + step * (i + 1)}
            for i in range(12)]


def periods(place, d):
    tz = pytz.timezone(place["tz"])
    sr, ss = pe.sun_times(d, place["lat"], place["lon"], tz)
    nsr, _ = pe.sun_times(d + timedelta(days=1), place["lat"], place["lon"], tz)
    wd = _sunday_index(d)
    chog = get_choghadiya(sr, ss, nsr, wd)
    for part in ("day", "night"):
        for p in chog[part]:
            kind, planet, good, hi = CHOGHADIYA[p["name"]]
            p.update(kind=kind, planet=planet, good=good, name_hi=hi)
    day = _horas(sr, ss, WEEKDAY_LORD[wd])
    night = _horas(ss, nsr, CHALDEAN[(CHALDEAN.index(day[-1]["planet"]) + 1) % 7])
    for h in day + night:
        hi, good, good_hi = HORA[h["planet"]]
        h.update(planet_hi=hi, good=(good, good_hi))
    eighth = (ss - sr) / 8
    rahu = sr + eighth * RAHU_KAAL[wd]
    return {"date": d, "sunrise": sr, "sunset": ss, "next_sunrise": nsr, "weekday_index": wd,
            "choghadiya": chog, "hora": {"day": day, "night": night}, "rahu_kaal": (rahu, rahu + eighth)}


def cached(place, d):
    key = f"day-periods:v{CACHE_VERSION}:{place.get('key', '')}:{place['lat']:.4f}:{place['lon']:.4f}:{d.isoformat()}"
    data = cache.get(key)
    if data is None:
        data = periods(place, d)
        cache.set(key, data, 3 * 24 * 3600)
    return data
