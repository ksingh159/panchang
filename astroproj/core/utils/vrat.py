# core/utils/vrat.py
"""
Monthly vrat date lists (/vrat/ and /vrat/<kind>/<year>/), read from the festival engine (Kashi rules, Varanasi times).

    KINDS                 kind -> how to find its rows and its (English, Hindi) text
    rows(kind, year)      the year's dates, with tithi start/end, parana (Ekadashi), moonrise (Sankashti) ...
    next_date(kind, d)    the next row on or after d (for the /vrat/ hub)

Dates come from festival_calculations, so they always agree with /festivals/<year>/ and each festival page.
"""
from datetime import date, datetime, timedelta

from . import festival_calculations as fc

# kind -> {"category" | "slugs", "name", "short", "about", "deity", "rule"}
KINDS = {
    "ekadashi": {
        "category": "Ekadashi",
        "name": ("Ekadashi", "एकादशी"),
        "about": ("Ekadashi is the 11th tithi of each paksha, the fast of Bhagwan Vishnu, twice a month. An Adhik Maas "
                  "adds two more, Padmini and Parama Ekadashi. The fast is broken (parana) the next morning, after "
                  "sunrise and within Dwadashi.",
                  "एकादशी हर पक्ष की ग्यारहवीं तिथि है, भगवान विष्णु का व्रत, महीने में दो बार। अधिक मास में दो और एकादशी होती "
                  "हैं, पद्मिनी और परमा। व्रत का पारण अगली सुबह सूर्योदय के बाद, द्वादशी के भीतर किया जाता है।"),
        "rule": ("Smarta date: Ekadashi at sunrise. Where Vaishnavas (ISKCON and others) fast a day later, the date is noted.",
                 "स्मार्त तिथि: सूर्योदय के समय एकादशी। जहाँ वैष्णव (इस्कॉन आदि) एक दिन बाद व्रत रखते हैं, वह तिथि भी दी गई है।"),
    },
    "pradosh": {
        "slugs": ["pradosh-vrat"],
        "name": ("Pradosh Vrat", "प्रदोष व्रत"),
        "about": ("Pradosh Vrat falls on Trayodashi (13th tithi) of both pakshas, two a month. Bhagwan Shiva is worshipped "
                  "at twilight (pradosh kaal). On a Monday it is Som Pradosh, on a Tuesday Bhaum Pradosh and on a Saturday "
                  "Shani Pradosh.",
                  "प्रदोष व्रत दोनों पक्षों की त्रयोदशी को होता है, महीने में दो बार। भगवान शिव की पूजा सन्ध्या के समय (प्रदोष काल) में "
                  "होती है। सोमवार को सोम प्रदोष, मंगलवार को भौम प्रदोष और शनिवार को शनि प्रदोष कहलाता है।"),
        "rule": ("The day on which Trayodashi covers pradosh kaal (the first part of the night after sunset).",
                 "वह दिन जब त्रयोदशी प्रदोष काल (सूर्यास्त के बाद रात का पहला भाग) में हो।"),
    },
    "sankashti-chaturthi": {
        "slugs": ["sankashti-chaturthi"],
        "name": ("Sankashti Chaturthi", "संकष्टी चतुर्थी"),
        "about": ("Sankashti Chaturthi is Krishna paksha Chaturthi, the monthly fast of Bhagwan Ganesha. The fast is broken "
                  "after sighting the Moon, so the moonrise time matters. On a Tuesday it is Angaraki Chaturthi.",
                  "संकष्टी चतुर्थी कृष्ण पक्ष की चतुर्थी है, भगवान गणेश का मासिक व्रत। चन्द्र दर्शन के बाद व्रत खोला जाता है, इसलिए "
                  "चन्द्रोदय का समय महत्वपूर्ण है। मंगलवार को हो तो अंगारकी चतुर्थी कहलाती है।"),
        "rule": ("The day on which Chaturthi is running at moonrise. Moonrise shown for Varanasi.",
                 "वह दिन जब चन्द्रोदय के समय चतुर्थी हो। चन्द्रोदय वाराणसी का है।"),
    },
    "vinayaka-chaturthi": {
        "slugs": ["vinayaka-chaturthi"],
        "name": ("Vinayaka Chaturthi", "विनायक चतुर्थी"),
        "about": ("Vinayaka Chaturthi is Shukla paksha Chaturthi, the monthly Ganesha puja done at midday.",
                  "विनायक चतुर्थी शुक्ल पक्ष की चतुर्थी है, भगवान गणेश की मासिक पूजा जो मध्याह्न में होती है।"),
        "rule": ("The day on which Chaturthi covers madhyahna (midday).", "वह दिन जब चतुर्थी मध्याह्न में हो।"),
    },
    "purnima": {
        "slugs": ["purnima"],
        "name": ("Purnima", "पूर्णिमा"),
        "about": ("Purnima is the full Moon day: snan-daan, Satyanarayan katha and the Purnima vrat. When the vrat (kept "
                  "with moonrise) falls a day before the snan-daan day, both dates are shown.",
                  "पूर्णिमा पूरे चन्द्रमा का दिन है: स्नान-दान, सत्यनारायण कथा और पूर्णिमा व्रत। जब व्रत (चन्द्रोदय के साथ) स्नान-दान "
                  "के दिन से एक दिन पहले हो, तो दोनों तिथियाँ दी गई हैं।"),
        "rule": ("Snan-daan: Purnima at sunrise. Vrat: Purnima at moonrise.",
                 "स्नान-दान: सूर्योदय के समय पूर्णिमा। व्रत: चन्द्रोदय के समय पूर्णिमा।"),
    },
    "amavasya": {
        "slugs": ["amavasya"],
        "name": ("Amavasya", "अमावस्या"),
        "about": ("Amavasya is the new Moon day, for pitru tarpan, shraddha and daan. On a Monday it is Somvati Amavasya "
                  "and on a Saturday Shani Amavasya.",
                  "अमावस्या नए चन्द्रमा का दिन है, पितृ तर्पण, श्राद्ध और दान के लिए। सोमवार को हो तो सोमवती अमावस्या और शनिवार को "
                  "शनि अमावस्या कहलाती है।"),
        "rule": ("Amavasya at sunrise.", "सूर्योदय के समय अमावस्या।"),
    },
    "masik-shivaratri": {
        "slugs": ["masik-shivaratri"],
        "name": ("Masik Shivaratri", "मासिक शिवरात्रि"),
        "about": ("Masik Shivaratri is Krishna paksha Chaturdashi each month; Shiva puja is done at midnight (nishita kaal). "
                  "The one in Phalguna is Mahashivratri.",
                  "मासिक शिवरात्रि हर महीने की कृष्ण पक्ष चतुर्दशी है; शिव पूजा मध्यरात्रि (निशीथ काल) में होती है। फाल्गुन की "
                  "शिवरात्रि महाशिवरात्रि है।"),
        "rule": ("The night on which Chaturdashi covers nishita kaal (midnight).",
                 "वह रात जब चतुर्दशी निशीथ काल (मध्यरात्रि) में हो।"),
    },
    "masik-durgashtami": {
        "slugs": ["masik-durgashtami"],
        "name": ("Masik Durgashtami", "मासिक दुर्गाष्टमी"),
        "about": ("Masik Durgashtami is Shukla paksha Ashtami each month, for the worship of Maa Durga.",
                  "मासिक दुर्गाष्टमी हर महीने की शुक्ल पक्ष अष्टमी है, माँ दुर्गा की पूजा के लिए।"),
        "rule": ("Ashtami at sunrise.", "सूर्योदय के समय अष्टमी।"),
    },
}

TEXT = {
    "hub_h1": ("Vrat Calendar: Ekadashi, Pradosh, Sankashti, Purnima, Amavasya", "व्रत कैलेंडर: एकादशी, प्रदोष, संकष्टी, पूर्णिमा, अमावस्या"),
    "hub_lede": ("Every monthly vrat of the year with its date, the tithi's start and end and, where it matters, the "
                 "parana or moonrise time. Dates follow Kashi (Varanasi) panchang rules; times are IST for Varanasi.",
                 "साल के हर मासिक व्रत की तिथि, तिथि के शुरू और समाप्त होने का समय और जहाँ ज़रूरी हो वहाँ पारण या चन्द्रोदय का "
                 "समय। तिथियाँ काशी (वाराणसी) पंचांग के नियमों से हैं; समय वाराणसी के, IST में।"),
    "next": ("Next", "अगली"), "list": ("Full list", "पूरी सूची"),
    "h1": ("{name} {year}: All Dates", "{name} {year}: सभी तिथियाँ"),
    "date": ("Date", "तिथि"), "vrat": ("Vrat", "व्रत"), "tithi": ("Tithi timing", "तिथि का समय"),
    "begins": ("begins", "शुरू"), "ends": ("ends", "समाप्त"),
    "parana": ("Parana (break the fast)", "पारण (व्रत खोलना)"), "parana_from": ("from", "से"),
    "dwadashi_ends": ("Dwadashi ends", "द्वादशी समाप्त"),
    "vaishnava": ("Vaishnava (ISKCON) fast", "वैष्णव (इस्कॉन) व्रत"),
    "moonrise": ("Moonrise (Varanasi)", "चन्द्रोदय (वाराणसी)"),
    "vrat_date": ("Purnima vrat", "पूर्णिमा व्रत"),
    "how": ("How the date is chosen", "तिथि कैसे तय होती है"),
    "next_one": ("Next {name}", "अगली {name}"),
    "passed": ("passed", "बीत गई"), "today": ("today", "आज"),
    "other_years": ("Other years", "अन्य वर्ष"), "other_vrats": ("Other vrats", "अन्य व्रत"),
    "count": ("{n} dates in {year}", "{year} में {n} तिथियाँ"),
    "times_note": ("Times are IST for Varanasi. Tithi times are the same moment everywhere; moonrise and parana differ a "
                   "little by city.", "समय वाराणसी के, IST में। तिथि का समय हर जगह एक ही क्षण होता है; चन्द्रोदय और पारण शहर के "
                   "अनुसार थोड़ा बदलते हैं।"),
    "details": ("Details", "विवरण"),
}

HI_MONTHS = ["जनवरी", "फ़रवरी", "मार्च", "अप्रैल", "मई", "जून", "जुलाई", "अगस्त", "सितम्बर", "अक्टूबर", "नवम्बर", "दिसम्बर"]
HI_DAYS = ["सोमवार", "मंगलवार", "बुधवार", "गुरुवार", "शुक्रवार", "शनिवार", "रविवार"]


def _moment(text):
    """'25 Nov 2026, 02:14 PM' (festival engine format) -> naive datetime, or None."""
    try:
        return datetime.strptime(text, "%d %b %Y, %I:%M %p")
    except (TypeError, ValueError):
        return None


def label(x, hindi, time=False, weekday=False):
    """'Wed, 25 Nov 2026, 14:14' / 'बुधवार, 25 नवम्बर 2026, 14:14'."""
    if x is None:
        return ""
    if hindi:
        out = f"{x.day} {HI_MONTHS[x.month - 1]} {x.year}"
        if weekday:
            out = f"{HI_DAYS[x.weekday()]}, {out}"
    else:
        out = f"{x.day} {x:%b %Y}"                      # no %-d: it does not exist on Windows
        if weekday:
            out = f"{x:%a}, {out}"
    if time and isinstance(x, datetime):
        out += f", {x:%H:%M}"
    return out


def _rows(kind, year):
    k = KINDS[kind]
    if "category" in k:
        return fc.get_festivals_for_year(year, [k["category"]])
    out = []
    for slug in k["slugs"]:
        out += fc.get_festival_by_slug(slug, year)
    return sorted(out, key=lambda f: f["date"])


def rows(kind, year, today=None, hindi=False):
    out = []
    for f in _rows(kind, year):
        d = f["details"] or {}
        parana = d.get("parana") or {}
        vd = d.get("vaishnava_date")
        pv = d.get("vrat_date")
        out.append({
            "date": f["date"], "name": f["name"], "slug": f["slug"], "masa": d.get("masa", ""),
            "date_label": label(f["date"], hindi, weekday=True),
            "tithi_start": label(_moment(d.get("tithi_start")), hindi, time=True),
            "tithi_end": label(_moment(d.get("tithi_end")), hindi, time=True),
            "parana_from": label(_moment(parana.get("from")), hindi, time=True),
            "dwadashi_ends": label(_moment(parana.get("dwadashi_ends")), hindi, time=True),
            "vaishnava": label(date.fromisoformat(vd), hindi, weekday=True) if vd else "",
            "moonrise": f"{_moment(d.get('moonrise')):%H:%M}" if _moment(d.get("moonrise")) else "",
            "vrat_date": label(date.fromisoformat(pv), hindi, weekday=True) if pv else "",
            "past": today is not None and f["date"] < today,
            "today": today is not None and f["date"] == today,
        })
    return out


def next_date(kind, d):
    """The next row on or after d (looks into next year in December)."""
    for y in (d.year, d.year + 1):
        for f in _rows(kind, y):
            if f["date"] >= d:
                return f
    return None
