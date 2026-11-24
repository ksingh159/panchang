# core/utils/kumbh.py
"""Kumbh Mela: the next melas with their snan dates, the Guru (Jupiter) sign windows behind them, and reading text.

    MELAS                  upcoming melas; snan dates are the organisers' announced lists ("official") or the
                           expected year where nothing is announced yet ("expected")
    upcoming(d)            melas not yet over on date d, each snan tagged past/next and linked to our festival page
    snans_on(slug, d)      Kumbh snans that fall on a festival (a day either side, for lists that differ by a day)
    calendar_events(year)  rows for the festival calendar (mela windows and Amrit snans)
    guru_windows(d)        when Guru is next in each Kumbh sign (Swiss Ephemeris, Lahiri), merged over retrograde dips
    SECTIONS / FAQ         reading text as (English, Hindi) pairs, shown with |pick

Owner's tone rule: reading text reassures, never frightens.
"""
from datetime import date, datetime, timedelta
from functools import lru_cache

import swisseph as swe

P = lambda en, hi: (en, hi)  # noqa: E731 - (English, Hindi) pair

SITES = {
    "haridwar": {"name": P("Haridwar", "हरिद्वार"), "river": P("Ganga", "गंगा"),
                 "guru": 10, "sun": P("Sun in Mesha (Aries)", "सूर्य मेष में")},
    "prayagraj": {"name": P("Prayagraj", "प्रयागराज"), "river": P("Triveni Sangam: Ganga, Yamuna and Saraswati",
                                                               "त्रिवेणी संगम: गंगा, यमुना और सरस्वती"),
                  "guru": 1, "sun": P("Sun in Makara (Capricorn), in Magha", "सूर्य मकर में, माघ मास में")},
    "nashik": {"name": P("Nashik-Trimbakeshwar", "नासिक-त्र्यम्बकेश्वर"), "river": P("Godavari", "गोदावरी"),
               "guru": 4, "sun": P("Sun in Simha (Leo)", "सूर्य सिंह में")},
    "ujjain": {"name": P("Ujjain", "उज्जैन"), "river": P("Kshipra", "क्षिप्रा"),
               "guru": 4, "sun": P("Sun in Mesha (Aries)", "सूर्य मेष में")},
}
GURU_SIGN = {1: P("Vrishabha (Taurus)", "वृषभ"), 4: P("Simha (Leo)", "सिंह"), 10: P("Kumbha (Aquarius)", "कुम्भ")}


def _s(d, name, slug=None, amrit=False, note=None):
    return {"date": date.fromisoformat(d), "name": name, "slug": slug, "amrit": amrit, "note": note}


MELAS = [
    {
        "key": "haridwar-2027", "site": "haridwar", "kind": P("Ardh Kumbh", "अर्ध कुम्भ"), "year": 2027,
        "title": P("Haridwar Ardh Kumbh 2027", "हरिद्वार अर्ध कुम्भ 2027"),
        "start": date(2027, 1, 14), "end": date(2027, 4, 20), "status": "official",
        "note": P("Ten snan days announced by the Uttarakhand government; the Shahi Snans are now called Amrit Snans.",
                  "उत्तराखण्ड सरकार ने दस स्नान तिथियाँ घोषित की हैं; शाही स्नान को अब अमृत स्नान कहा जाता है।"),
        "snans": [
            _s("2027-01-14", P("Makar Sankranti", "मकर संक्रान्ति"), "makar-sankranti",
               note=P("The Sun enters Makara on the evening of 14 January, so by Kashi rules the punya kaal is on "
                      "15 January; bathing on either day is fine.",
                      "सूर्य 14 जनवरी की शाम मकर में प्रवेश करते हैं, इसलिए काशी नियम से पुण्य काल 15 जनवरी को है; "
                      "दोनों में से किसी भी दिन स्नान उत्तम है।")),
            _s("2027-02-06", P("Mauni Amavasya", "मौनी अमावस्या"), "mauni-amavasya"),
            _s("2027-02-11", P("Vasant Panchami", "वसन्त पंचमी"), "vasant-panchami"),
            _s("2027-02-20", P("Magha Purnima", "माघ पूर्णिमा"), "magha-purnima"),
            _s("2027-03-06", P("Maha Shivaratri", "महाशिवरात्रि"), "maha-shivaratri", amrit=True),
            _s("2027-03-08", P("Somvati Amavasya (Phalguna)", "सोमवती अमावस्या (फाल्गुन)"), amrit=True),
            _s("2027-04-07", P("Nav Samvatsar (Chaitra Pratipada)", "नव संवत्सर (चैत्र प्रतिपदा)"), "chaitra-navratri"),
            _s("2027-04-14", P("Mesha Sankranti (Baisakhi)", "मेष संक्रान्ति (बैसाखी)"), "mesha-sankranti", amrit=True),
            _s("2027-04-15", P("Rama Navami", "राम नवमी"), "rama-navami"),
            _s("2027-04-20", P("Chaitra Purnima", "चैत्र पूर्णिमा"), "hanuman-jayanti",
               note=P("Closing snan; some lists also count it as an Amrit Snan.",
                      "समापन स्नान; कुछ सूचियाँ इसे भी अमृत स्नान मानती हैं।")),
        ],
    },
    {
        "key": "nashik-2027", "site": "nashik", "kind": P("Simhastha Kumbh", "सिंहस्थ कुम्भ"), "year": 2027,
        "title": P("Nashik-Trimbakeshwar Simhastha Kumbh 2027", "नासिक-त्र्यम्बकेश्वर सिंहस्थ कुम्भ 2027"),
        "start": date(2026, 10, 31), "end": date(2028, 7, 24), "status": "official",
        "note": P("Opened with the dhwajarohan (flag hoisting) at Ramkund and Trimbakeshwar on 31 October 2026; the "
                  "flags come down on 24 July 2028. The three Amrit Snans fall in August and September 2027.",
                  "31 अक्टूबर 2026 को रामकुण्ड और त्र्यम्बकेश्वर में ध्वजारोहण से आरम्भ; 24 जुलाई 2028 को ध्वज उतरेंगे। "
                  "तीनों अमृत स्नान अगस्त और सितम्बर 2027 में हैं।"),
        "snans": [
            _s("2027-08-02", P("First Amrit Snan (Amavasya)", "पहला अमृत स्नान (अमावस्या)"), amrit=True),
            _s("2027-08-31", P("Second Amrit Snan (Amavasya)", "दूसरा अमृत स्नान (अमावस्या)"), amrit=True),
            _s("2027-09-11", P("Third Amrit Snan at Nashik (Ramkund)", "तीसरा अमृत स्नान, नासिक (रामकुण्ड)"), amrit=True),
            _s("2027-09-12", P("Third Amrit Snan at Trimbakeshwar (Kushavarta)",
                               "तीसरा अमृत स्नान, त्र्यम्बकेश्वर (कुशावर्त)"), amrit=True),
        ],
    },
    {
        "key": "ujjain-2028", "site": "ujjain", "kind": P("Simhastha Kumbh", "सिंहस्थ कुम्भ"), "year": 2028,
        "title": P("Ujjain Simhastha 2028", "उज्जैन सिंहस्थ 2028"),
        "start": date(2028, 3, 27), "end": date(2028, 5, 27), "status": "announced",
        "note": P("Dates as announced so far by Madhya Pradesh; the final snan list comes nearer the mela.",
                  "मध्य प्रदेश द्वारा अब तक घोषित तिथियाँ; अन्तिम स्नान सूची मेले के निकट आएगी।"),
        "snans": [
            _s("2028-04-09", P("First Shahi Snan (Chaitra Purnima)", "पहला शाही स्नान (चैत्र पूर्णिमा)"),
               "hanuman-jayanti", amrit=True),
            _s("2028-04-24", P("Second Shahi Snan (Vaishakha Amavasya)", "दूसरा शाही स्नान (वैशाख अमावस्या)"), amrit=True,
               note=P("Some lists give 23 April; the Amavasya is at sunrise on 24 April.",
                      "कुछ सूचियों में 23 अप्रैल है; सूर्योदय पर अमावस्या 24 अप्रैल को है।")),
            _s("2028-05-08", P("Third Shahi Snan (Vaishakha Purnima)", "तीसरा शाही स्नान (वैशाख पूर्णिमा)"),
               "buddha-purnima", amrit=True),
        ],
    },
    {
        "key": "prayagraj-2031", "site": "prayagraj", "kind": P("Ardh Kumbh", "अर्ध कुम्भ"), "year": 2031,
        "title": P("Prayagraj Ardh Kumbh 2031", "प्रयागराज अर्ध कुम्भ 2031"),
        "start": date(2031, 1, 1), "end": date(2031, 3, 31), "status": "expected",
        "note": P("Six years after the 2025 Maha Kumbh, in Magha (January-February). Dates are not announced yet.",
                  "2025 के महाकुम्भ के छह वर्ष बाद, माघ मास (जनवरी-फ़रवरी) में। तिथियाँ अभी घोषित नहीं हुई हैं।"),
        "snans": [],
    },
    {
        "key": "haridwar-2033", "site": "haridwar", "kind": P("Purna Kumbh", "पूर्ण कुम्भ"), "year": 2033,
        "title": P("Haridwar Purna Kumbh 2033", "हरिद्वार पूर्ण कुम्भ 2033"),
        "start": date(2033, 1, 1), "end": date(2033, 4, 30), "status": "expected",
        "note": P("Twelve years after the 2021 Kumbh, when Guru is in Kumbha and the Sun enters Mesha. Dates are not "
                  "announced yet.",
                  "2021 के कुम्भ के बारह वर्ष बाद, जब गुरु कुम्भ में और सूर्य मेष में हों। तिथियाँ अभी घोषित नहीं हुई हैं।"),
        "snans": [],
    },
    {
        "key": "prayagraj-2037", "site": "prayagraj", "kind": P("Purna (Maha) Kumbh", "पूर्ण (महा) कुम्भ"), "year": 2037,
        "title": P("Prayagraj Maha Kumbh 2037", "प्रयागराज महाकुम्भ 2037"),
        "start": date(2037, 1, 1), "end": date(2037, 3, 31), "status": "expected",
        "note": P("Twelve years after the 2025 Maha Kumbh. Dates are not announced yet.",
                  "2025 के महाकुम्भ के बारह वर्ष बाद। तिथियाँ अभी घोषित नहीं हुई हैं।"),
        "snans": [],
    },
]

STATUS = {
    "official": P("Official dates", "आधिकारिक तिथियाँ"),
    "announced": P("Announced, may change", "घोषित, बदल सकती हैं"),
    "expected": P("Expected year, dates not announced", "सम्भावित वर्ष, तिथियाँ घोषित नहीं"),
}

# Prayagraj Magh Mela: every year, snans by our own Kashi panchang (not a government list)
MAGH_MELA_SNANS = [
    ("makar-sankranti", P("Makar Sankranti", "मकर संक्रान्ति")),
    ("mauni-amavasya", P("Mauni Amavasya", "मौनी अमावस्या")),
    ("vasant-panchami", P("Vasant Panchami", "वसन्त पंचमी")),
    ("magha-purnima", P("Magha Purnima", "माघ पूर्णिमा")),
    ("maha-shivaratri", P("Maha Shivaratri", "महाशिवरात्रि")),
]


def upcoming(d):
    """Melas not over on ``d``; each snan dict gets "past" and the next one "next"."""
    out = []
    for m in MELAS:
        if m["end"] < d:
            continue
        snans = [dict(s, past=s["date"] < d, next=False) for s in m["snans"]]
        for s in snans:
            if not s["past"]:
                s["next"] = True
                break
        out.append(dict(m, snans=snans, site_info=SITES[m["site"]],
                        running=m["start"] <= d and m["status"] != "expected"))
    return out


def next_snan(d):
    """(mela, snan) of the first announced Kumbh snan on or after ``d``, or None."""
    best = None
    for m in MELAS:
        for s in m["snans"]:
            if s["date"] >= d and (best is None or s["date"] < best[1]["date"]):
                best = (m, s)
    return best


def snans_on(slug, d):
    """[(mela, snan)] for Kumbh snans that are this festival (same slug, within a day) or on this very date."""
    out = []
    for m in MELAS:
        for s in m["snans"]:
            if (s["slug"] == slug and abs((s["date"] - d).days) <= 1) or s["date"] == d:
                out.append((m, s))
    return out


def calendar_events(year):
    """Festival-calendar rows: each mela's window (in the year it opens) and its Amrit/Shahi snans."""
    from .festival_calculations import WEEKDAY_NAMES, _format_event_range
    out = []

    def row(name, start, end, note, anchor):
        return {"slug": "kumbh-mela", "date": start, "end_date": end, "date_display": _format_event_range(start, end),
                "name": name, "category": "Kumbh", "month": "", "tithi": "", "rule": "Mela organisers' announcement",
                "note": note, "importance": "high", "weekday": WEEKDAY_NAMES[start.weekday()], "details": {},
                "url_name": "kumbh_mela", "anchor": anchor}

    for m in MELAS:
        if m["status"] == "expected":
            continue
        if m["start"].year == year:
            out.append(row(m["title"][0], m["start"], m["end"], "Kumbh mela window.", m["key"]))
        for s in m["snans"]:
            if s["date"].year == year and s["amrit"]:
                out.append(row(f"{m['title'][0]}: {s['name'][0]}", s["date"], s["date"], "Kumbh Amrit Snan.", m["key"]))
    return out


@lru_cache(maxsize=1)
def hindi_names():
    """{English calendar-row name: Hindi} for the rows calendar_events() makes."""
    out = {}
    for m in MELAS:
        out[m["title"][0]] = m["title"][1]
        for s in m["snans"]:
            out[f"{m['title'][0]}: {s['name'][0]}"] = f"{m['title'][1]}: {s['name'][1]}"
    return out


# ---------------------------------------------------------------------------
# Guru (Jupiter) sign windows
# ---------------------------------------------------------------------------

STEP_DAYS = 5
MERGE_GAP_DAYS = 250   # a retrograde step back out of the sign shorter than this is not the end of the stay


def _guru_sign(jd):
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    pos, _ = swe.calc_ut(jd, swe.JUPITER, swe.FLG_SWIEPH)
    return int(((pos[0] - swe.get_ayanamsa_ut(jd)) % 360) // 30)


def _edge(a, b):
    s = _guru_sign(a)
    while b - a > 0.04:
        mid = (a + b) / 2
        if _guru_sign(mid) == s:
            a = mid
        else:
            b = mid
    return b


def _to_date(jd):
    y, m, d, h = swe.revjul(jd)
    return (datetime(y, m, d) + timedelta(hours=h)).date()


@lru_cache(maxsize=8)
def _guru_spans(start_year, years):
    from .panchang_engine import EPHE_PATH
    if EPHE_PATH:
        swe.set_ephe_path(EPHE_PATH)
    jd = swe.julday(start_year, 1, 1, 0.0)
    jd_end = jd + years * 365.25
    cur, start, out = _guru_sign(jd), jd, []
    while jd < jd_end:
        nxt = min(jd + STEP_DAYS, jd_end)
        s = _guru_sign(nxt)
        if s != cur:
            e = _edge(jd, nxt)
            out.append((cur, _to_date(start), _to_date(e)))
            cur, start = _guru_sign(e), e
        jd = nxt
    out.append((cur, _to_date(start), _to_date(jd_end)))
    return tuple(out)


def guru_windows(d, years=16):
    """{sign: [(start, end)]} for the Kumbh signs, from the stay in force on ``d`` onward, retrograde dips merged."""
    spans = _guru_spans(d.year - 2, years + 2)
    out = {}
    for sign in GURU_SIGN:
        merged = []
        for s, a, b in spans:
            if s != sign:
                continue
            if merged and (a - merged[-1][1]).days < MERGE_GAP_DAYS:
                merged[-1] = (merged[-1][0], b)
            else:
                merged.append((a, b))
        out[sign] = [(a, b) for a, b in merged if b >= d]
    return out


def guru_rows(d):
    """One row per site: its rule and the next Guru window."""
    win = guru_windows(d)
    rows = []
    for key in ("prayagraj", "haridwar", "nashik", "ujjain"):
        site = SITES[key]
        spans = win.get(site["guru"]) or []
        rows.append({"key": key, "site": site, "guru_sign": GURU_SIGN[site["guru"]], "windows": spans[:2]})
    return rows


# ---------------------------------------------------------------------------
# Reading text
# ---------------------------------------------------------------------------

SECTIONS = [
    (P("What is the Kumbh Mela?", "कुम्भ मेला क्या है?"),
     P("The Kumbh Mela is the largest gathering of pilgrims on earth: crores of people come to bathe in a sacred "
       "river at an hour the panchang marks as especially purifying. It is held at four places - Prayagraj, "
       "Haridwar, Ujjain and Nashik-Trimbakeshwar - and each place has its turn when Guru (Jupiter) and the Sun "
       "reach particular signs. Sadhus of the thirteen akhadas, kalpavasis who live on the river bank for a month, "
       "and families from every corner of India all come for the same thing: a dip at the right moment, darshan of "
       "saints, katha, daan and seva.",
       "कुम्भ मेला धरती पर श्रद्धालुओं का सबसे बड़ा समागम है: करोड़ों लोग पवित्र नदी में उस मुहूर्त पर स्नान करने आते हैं "
       "जिसे पंचांग विशेष पुण्यदायी बताता है। यह चार स्थानों पर होता है - प्रयागराज, हरिद्वार, उज्जैन और "
       "नासिक-त्र्यम्बकेश्वर - और हर स्थान की बारी तब आती है जब गुरु (बृहस्पति) और सूर्य विशेष राशियों में पहुँचते हैं। "
       "तेरह अखाड़ों के साधु, महीने भर नदी तट पर रहने वाले कल्पवासी और देश के हर कोने से आए परिवार - सब एक ही "
       "उद्देश्य से आते हैं: सही समय पर डुबकी, सन्तों के दर्शन, कथा, दान और सेवा।")),
    (P("The story: why these four places", "कथा: ये चार स्थान ही क्यों"),
     P("At the Samudra Manthan, the churning of the ocean, Dhanvantari rose holding a kumbh (pot) of amrit. Devas "
       "and asuras struggled over it for twelve divine days, which are twelve human years, and as the pot was "
       "carried away, drops of amrit fell at Prayag, Haridwar, Ujjain and Nashik. Surya, Chandra, Guru and Shani "
       "guarded the pot during the struggle, which is why the mela follows their positions in the sky: when they "
       "return to the same places, the river at that tirtha is held to carry the same amrit again.",
       "समुद्र मन्थन में धन्वन्तरि अमृत का कुम्भ (कलश) लेकर प्रकट हुए। उस कलश के लिए देवों और असुरों में बारह दिव्य दिन, "
       "यानी बारह मानव वर्ष, संघर्ष चला, और कलश ले जाते समय अमृत की बूँदें प्रयाग, हरिद्वार, उज्जैन और नासिक में गिरीं। "
       "संघर्ष के समय सूर्य, चन्द्र, गुरु और शनि ने कलश की रक्षा की, इसलिए मेला आकाश में इन्हीं ग्रहों की स्थिति से "
       "तय होता है: जब वे फिर उन्हीं स्थानों पर आते हैं, तब उस तीर्थ की नदी में वही अमृत फिर से माना जाता है।")),
    (P("Kumbh, Ardh Kumbh, Purna Kumbh, Maha Kumbh and Simhastha", "कुम्भ, अर्ध कुम्भ, पूर्ण कुम्भ, महाकुम्भ और सिंहस्थ"),
     P("Purna Kumbh is the full Kumbh, held at each of the four places once in about twelve years, the time Guru "
       "takes to go round the zodiac. Ardh Kumbh, the 'half' Kumbh, is held only at Haridwar and Prayagraj, about "
       "six years after the Purna Kumbh. Maha Kumbh is the name for the Purna Kumbh at Prayagraj; many saints use it "
       "especially for the one that comes after twelve Purna Kumbhs, once in 144 years, and the 2025 Prayagraj mela "
       "was celebrated as that Maha Kumbh. Simhastha is the Kumbh at Ujjain and Nashik, so named because Guru is "
       "then in Simha (Leo). And every year in Magha, Prayagraj holds the Magh Mela, a smaller mela with the same "
       "snan days and kalpavas.",
       "पूर्ण कुम्भ हर स्थान पर लगभग बारह वर्ष में एक बार होता है, जितने समय में गुरु राशिचक्र का एक चक्कर पूरा करते हैं। "
       "अर्ध कुम्भ केवल हरिद्वार और प्रयागराज में, पूर्ण कुम्भ के लगभग छह वर्ष बाद होता है। महाकुम्भ प्रयागराज के पूर्ण "
       "कुम्भ का नाम है; अनेक सन्त इसे विशेष रूप से बारह पूर्ण कुम्भों के बाद, 144 वर्ष में एक बार आने वाले कुम्भ के लिए "
       "कहते हैं, और 2025 का प्रयागराज मेला उसी महाकुम्भ के रूप में मनाया गया। सिंहस्थ उज्जैन और नासिक का कुम्भ है, "
       "क्योंकि तब गुरु सिंह राशि में होते हैं। और हर वर्ष माघ मास में प्रयागराज में माघ मेला लगता है - वही स्नान पर्व "
       "और कल्पवास, छोटे रूप में।")),
    (P("Amrit Snan (Shahi Snan) and the akhadas", "अमृत स्नान (शाही स्नान) और अखाड़े"),
     P("On the chief snan days the akhadas go to the river first, in a fixed order, in grand processions - the "
       "Naga sadhus, then the other orders - and only after them do the public bathe at the main ghats. These days "
       "were long called Shahi Snan; the organisers now call them Amrit Snan. The other snan days are open to "
       "everyone from early morning. Bathing during Brahma muhurta, before sunrise, is held best.",
       "मुख्य स्नान पर्वों पर अखाड़े भव्य शोभायात्राओं के साथ निश्चित क्रम में सबसे पहले नदी पर जाते हैं - पहले नागा "
       "साधु, फिर अन्य सम्प्रदाय - और उनके बाद ही आम श्रद्धालु मुख्य घाटों पर स्नान करते हैं। इन दिनों को पहले शाही "
       "स्नान कहा जाता था; अब आयोजक इन्हें अमृत स्नान कहते हैं। बाकी स्नान पर्व सुबह से ही सबके लिए खुले रहते हैं। "
       "सूर्योदय से पहले, ब्रह्म मुहूर्त में स्नान सबसे उत्तम माना गया है।")),
    (P("How to make the most of a Kumbh snan", "कुम्भ स्नान का पूरा लाभ कैसे लें"),
     P("Take a sankalp before the dip with your name, gotra and the day's tithi; bathe facing the Sun or the "
       "current, take three or five dips, and offer arghya to Surya. Afterwards give daan - til, gur, grain, warm "
       "clothes or a meal to someone in need - and if you can, sit for katha or darshan of a saint. Keep the day "
       "sattvik. On the busiest days, smaller ghats away from the main one carry the same river and the same "
       "punya, with far less crowd.",
       "डुबकी से पहले अपने नाम, गोत्र और उस दिन की तिथि के साथ संकल्प लें; सूर्य या धारा की ओर मुख करके तीन या पाँच "
       "डुबकी लें और सूर्य को अर्घ्य दें। इसके बाद दान दें - तिल, गुड़, अन्न, गरम कपड़े या किसी ज़रूरतमन्द को भोजन - "
       "और हो सके तो कथा सुनें या किसी सन्त के दर्शन करें। दिन सात्विक रखें। सबसे भीड़ वाले दिनों में मुख्य घाट से दूर "
       "के छोटे घाटों पर भी वही नदी और वही पुण्य है, और भीड़ बहुत कम।")),
    (P("If you cannot go", "यदि आप जा न सकें"),
     P("The punya of the day is not only for those at the river. On a Kumbh snan day, add a few drops of Ganga jal "
       "to your bath water at home before sunrise, remember the tirtha with the sankalp, offer arghya to Surya and "
       "give daan. The scriptures praise the bhava more than the distance travelled, so elderly family members and "
       "anyone unwell can join in this way with a full heart.",
       "उस दिन का पुण्य केवल नदी तट पर पहुँचे लोगों के लिए नहीं है। कुम्भ स्नान के दिन घर पर सूर्योदय से पहले नहाने के "
       "पानी में गंगाजल की कुछ बूँदें मिलाएँ, संकल्प में उस तीर्थ का स्मरण करें, सूर्य को अर्घ्य दें और दान करें। शास्त्र "
       "दूरी से अधिक भाव की प्रशंसा करते हैं, इसलिए घर के बुज़ुर्ग और अस्वस्थ सदस्य भी इसी तरह पूरे मन से जुड़ सकते हैं।")),
]

FAQ = [
    (P("When is the next Kumbh Mela?", "अगला कुम्भ मेला कब है?"),
     P("The next Kumbh snans are at the Haridwar Ardh Kumbh, from Makar Sankranti on 14 January to Chaitra Purnima on "
       "20 April 2027. The Nashik-Trimbakeshwar Simhastha is already open, with its Amrit Snans on 2 August, 31 August "
       "and 11-12 September 2027, and the Ujjain Simhastha follows from 27 March to 27 May 2028.",
       "अगले कुम्भ स्नान हरिद्वार अर्ध कुम्भ में हैं, 14 जनवरी (मकर संक्रान्ति) से 20 अप्रैल 2027 (चैत्र पूर्णिमा) तक। "
       "नासिक-त्र्यम्बकेश्वर सिंहस्थ आरम्भ हो चुका है, जिसके अमृत स्नान 2 अगस्त, 31 अगस्त और 11-12 सितम्बर 2027 को "
       "हैं, और उसके बाद उज्जैन सिंहस्थ 27 मार्च से 27 मई 2028 तक है।")),
    (P("When is the next Maha Kumbh at Prayagraj?", "प्रयागराज में अगला महाकुम्भ कब है?"),
     P("The next Purna (Maha) Kumbh at Prayagraj is expected in 2037, twelve years after 2025, and the Ardh Kumbh "
       "there in 2031. The Magh Mela is held at Prayagraj every year in January-February.",
       "प्रयागराज में अगला पूर्ण (महा) कुम्भ 2037 में, 2025 के बारह वर्ष बाद, और वहाँ का अर्ध कुम्भ 2031 में अपेक्षित "
       "है। माघ मेला प्रयागराज में हर वर्ष जनवरी-फ़रवरी में लगता है।")),
    (P("What is the difference between Kumbh, Ardh Kumbh and Maha Kumbh?", "कुम्भ, अर्ध कुम्भ और महाकुम्भ में क्या अन्तर है?"),
     P("Purna Kumbh comes at each of the four places about every twelve years; Ardh Kumbh is held at Haridwar and "
       "Prayagraj about six years after it; Maha Kumbh is the Purna Kumbh at Prayagraj, and for many saints "
       "especially the one after twelve Purna Kumbhs (144 years).",
       "पूर्ण कुम्भ चारों स्थानों पर लगभग हर बारह वर्ष में आता है; अर्ध कुम्भ हरिद्वार और प्रयागराज में उसके लगभग छह वर्ष "
       "बाद होता है; महाकुम्भ प्रयागराज का पूर्ण कुम्भ है, और अनेक सन्तों के लिए विशेष रूप से बारह पूर्ण कुम्भों (144 "
       "वर्ष) के बाद आने वाला कुम्भ।")),
    (P("Why is the Kumbh not always exactly twelve years apart?", "कुम्भ हमेशा ठीक बारह वर्ष के अन्तर पर क्यों नहीं होता?"),
     P("Because it follows Guru, and Guru takes about 11.86 years to go round the zodiac, not exactly twelve. Every "
       "few cycles the Kumbh therefore comes a year early: Haridwar held its Kumbh in 2021 instead of 2022 for this "
       "reason.",
       "क्योंकि यह गुरु की स्थिति से चलता है, और गुरु राशिचक्र का चक्कर ठीक बारह नहीं, लगभग 11.86 वर्ष में पूरा करते हैं। "
       "इसलिए कुछ चक्रों के बाद कुम्भ एक वर्ष पहले आ जाता है: इसी कारण हरिद्वार में कुम्भ 2022 के बजाय 2021 में हुआ।")),
    (P("What is Simhastha?", "सिंहस्थ क्या है?"),
     P("The Kumbh at Ujjain (on the Kshipra) and at Nashik-Trimbakeshwar (on the Godavari). It is named after Simha "
       "(Leo), the sign Guru is in at the time.",
       "उज्जैन (क्षिप्रा तट) और नासिक-त्र्यम्बकेश्वर (गोदावरी तट) का कुम्भ। इसका नाम सिंह राशि से है, जिसमें उस समय गुरु "
       "होते हैं।")),
    (P("Which snan day is the most important?", "कौन सा स्नान पर्व सबसे महत्वपूर्ण है?"),
     P("At Prayagraj, Mauni Amavasya in Magha draws the largest crowds; at Haridwar it is Mesha Sankranti and the "
       "Amrit Snans around Maha Shivaratri. Any announced snan day is complete in itself, so choose the one your "
       "family can reach comfortably.",
       "प्रयागराज में माघ की मौनी अमावस्या पर सबसे अधिक भीड़ होती है; हरिद्वार में मेष संक्रान्ति और महाशिवरात्रि के "
       "आसपास के अमृत स्नान। हर घोषित स्नान पर्व अपने आप में पूर्ण है, इसलिए वह दिन चुनें जब आपका परिवार आराम से पहुँच "
       "सके।")),
]
