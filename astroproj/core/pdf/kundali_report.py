# core/pdf/kundali_report.py
"""The printed Janma Kundali: a book-style PDF built from a saved Kundali."""
from datetime import datetime, timedelta

import pytz
import swisseph as swe

from . import i18n
from .book import (GOLD, GREEN, INK, MAROON, MUTED, PLANET_COLORS, RED, RULE, SAFFRON, SOFT, Book, draw_chart,
                   planet_image, protect)

ORDER = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
SWE_IDS = {"Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS, "Mercury": swe.MERCURY, "Jupiter": swe.JUPITER,
           "Venus": swe.VENUS, "Saturn": swe.SATURN, "Rahu": swe.TRUE_NODE}
SIGN_LORDS = ["Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Saturn",
              "Jupiter"]
EXALTED = {"Sun": 0, "Moon": 1, "Mars": 9, "Mercury": 5, "Jupiter": 3, "Venus": 11, "Saturn": 6}
OWN = {"Sun": {4}, "Moon": {3}, "Mars": {0, 7}, "Mercury": {2, 5}, "Jupiter": {8, 11}, "Venus": {1, 6},
       "Saturn": {9, 10}}
DASHA_ORDER = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
DASHA_YEARS = {"Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7, "Rahu": 18, "Jupiter": 16, "Saturn": 19,
               "Mercury": 17}

KARAKA = {
    "Sun": ("Soul, father, authority, vitality, government", "आत्मा, पिता, अधिकार, ओज, शासन"),
    "Moon": ("Mind, mother, emotions, nourishment", "मन, माता, भावनाएँ, पोषण"),
    "Mars": ("Courage, siblings, land, energy, discipline", "साहस, भाई, भूमि, ऊर्जा, अनुशासन"),
    "Mercury": ("Intellect, speech, trade, learning", "बुद्धि, वाणी, व्यापार, विद्या"),
    "Jupiter": ("Wisdom, guru, children, wealth, dharma", "ज्ञान, गुरु, सन्तान, धन, धर्म"),
    "Venus": ("Love, spouse, comforts, arts, beauty", "प्रेम, जीवनसाथी, सुख, कला, सौन्दर्य"),
    "Saturn": ("Karma, discipline, longevity, service, delays", "कर्म, अनुशासन, आयु, सेवा, विलम्ब"),
    "Rahu": ("Ambition, foreign lands, sudden events", "महत्वाकांक्षा, विदेश, अचानक घटनाएँ"),
    "Ketu": ("Detachment, spirituality, past-life skills", "वैराग्य, अध्यात्म, पूर्वजन्म के संस्कार"),
    "Ascendant": ("Self, body, temperament, the direction of life", "स्वयं, शरीर, स्वभाव, जीवन की दिशा"),
}
DASHA_THEME = {
    "Sun": ("Recognition, authority, government and father; health of heart and eyes.",
            "मान-सम्मान, अधिकार, शासन और पिता; हृदय और नेत्र स्वास्थ्य।"),
    "Moon": ("Mind and emotions, mother, home, travel near water, public dealings.",
             "मन और भावनाएँ, माता, घर, जल यात्रा, जन सम्पर्क।"),
    "Mars": ("Energy, property, siblings, courage, technical work; guard against haste.",
             "ऊर्जा, भूमि-भवन, भाई, साहस, तकनीकी कार्य; जल्दबाज़ी से बचें।"),
    "Rahu": ("Ambition and sudden change, foreign links, technology; keep clarity and ethics.",
             "महत्वाकांक्षा और अचानक परिवर्तन, विदेश, तकनीक; स्पष्टता और नैतिकता रखें।"),
    "Jupiter": ("Growth through wisdom, teachers, children, wealth and dharma.",
                "ज्ञान, गुरु, सन्तान, धन और धर्म से उन्नति।"),
    "Saturn": ("Steady effort and its fruit, responsibility, service, patience.",
               "निरन्तर परिश्रम और उसका फल, उत्तरदायित्व, सेवा, धैर्य।"),
    "Mercury": ("Learning, trade, writing, communication and skill.", "विद्या, व्यापार, लेखन, संवाद और कौशल।"),
    "Ketu": ("Inner turning, detachment, research, spiritual practice.", "अन्तर्मुखता, वैराग्य, शोध, साधना।"),
    "Venus": ("Relationships, comforts, vehicles, arts and prosperity.", "सम्बन्ध, सुख-साधन, वाहन, कला और समृद्धि।"),
}

VARNA = {0: ("Kshatriya", "क्षत्रिय"), 4: ("Kshatriya", "क्षत्रिय"), 8: ("Kshatriya", "क्षत्रिय"),
         1: ("Vaishya", "वैश्य"), 5: ("Vaishya", "वैश्य"), 9: ("Vaishya", "वैश्य"),
         2: ("Shudra", "शूद्र"), 6: ("Shudra", "शूद्र"), 10: ("Shudra", "शूद्र"),
         3: ("Brahmin", "ब्राह्मण"), 7: ("Brahmin", "ब्राह्मण"), 11: ("Brahmin", "ब्राह्मण")}
NADI = [("Adi", "आदि"), ("Madhya", "मध्य"), ("Antya", "अन्त्य"), ("Antya", "अन्त्य"), ("Madhya", "मध्य"),
        ("Adi", "आदि")]
YONI_HI = {"Horse": "अश्व", "Elephant": "गज", "Sheep": "मेष", "Serpent": "सर्प", "Dog": "श्वान", "Cat": "मार्जार",
           "Rat": "मूषक", "Cow": "गौ", "Buffalo": "महिष", "Tiger": "व्याघ्र", "Deer": "मृग", "Monkey": "वानर",
           "Mongoose": "नकुल", "Lion": "सिंह"}
GANA_HI = {"Deva": "देव", "Manushya": "मनुष्य", "Rakshasa": "राक्षस"}

DOSHA_INFO = {
    "mangal": (("Mangal Dosha", "मंगल दोष"),
               ("Mars in the 1st, 4th, 7th, 8th or 12th house from the Lagna, Moon or Venus is said to strain married "
                "life. Every parihara (cancellation) rule is checked below, and the dosha is also weighed against the "
                "partner's chart: two Manglik charts balance each other.",
                "लग्न, चन्द्र या शुक्र से 1, 4, 7, 8 या 12वें भाव में मंगल दाम्पत्य जीवन में तनाव देता है। नीचे प्रत्येक "
                "परिहार (भंग) नियम जाँचा गया है। जीवनसाथी की कुण्डली भी देखी जाती है: दोनों मांगलिक हों तो दोष सम हो जाता है।")),
    "gand_mool": (("Gand Mool Dosha", "गण्ड मूल दोष"),
                  ("Birth with the Moon in Ashwini, Magha, Mula (Ketu) or Ashlesha, Jyeshtha, Revati (Mercury), the "
                   "nakshatras at the junction of water and fire signs. The Mool shanti is done when the Moon returns "
                   "to the same nakshatra, about 27 days after birth.",
                   "चन्द्र अश्विनी, मघा, मूल (केतु) या आश्लेषा, ज्येष्ठा, रेवती (बुध) में हो तो जन्म गण्ड मूल में होता है। ये "
                   "जल और अग्नि राशियों की सन्धि के नक्षत्र हैं। मूल शान्ति जन्म के लगभग 27 दिन बाद, चन्द्र के उसी नक्षत्र में "
                   "लौटने पर की जाती है।")),
    "kaal_sarp": (("Kaal Sarp Dosha", "काल सर्प दोष"),
                  ("All seven planets lie on one side of the Rahu-Ketu axis: effort meets obstacles until the "
                   "dosha is pacified.", "सातों ग्रह राहु-केतु अक्ष के एक ओर हों तो प्रयासों में बाधा आती है।")),
    "pitra": (("Pitra Dosha", "पितृ दोष"),
              ("Afflictions to the Sun or the 9th house, the house of ancestors.",
               "सूर्य या पूर्वजों के नवम भाव पर पीड़ा।")),
    "grahan": (("Grahan Dosha", "ग्रहण दोष"),
               ("The Sun or Moon joined by Rahu or Ketu, as in an eclipse.",
                "सूर्य या चन्द्र के साथ राहु या केतु, जैसे ग्रहण में।")),
    "guru_chandal": (("Guru Chandal Dosha", "गुरु चाण्डाल दोष"),
                     ("Jupiter joined by Rahu or Ketu clouds judgement and guidance.",
                      "गुरु के साथ राहु या केतु विवेक और मार्गदर्शन को धूमिल करते हैं।")),
    "shrapit": (("Shrapit Dosha", "शापित दोष"),
                ("Saturn with Rahu: delays and heavy karmic tests.", "शनि के साथ राहु: विलम्ब और कठिन कर्म परीक्षा।")),
    "angarak": (("Angarak Dosha", "अंगारक दोष"),
                ("Mars with Rahu: anger, haste and accidents need care.",
                 "मंगल के साथ राहु: क्रोध, जल्दबाज़ी और दुर्घटना से सावधानी।")),
    "vish": (("Vish Yoga", "विष योग"),
             ("Saturn with the Moon: a heavy, anxious mind.", "चन्द्र के साथ शनि: भारी और चिन्तित मन।")),
    "kemadruma": (("Kemadruma Yoga", "केमद्रुम योग"),
                  ("No planet beside the Moon: loneliness and unsteady means.",
                   "चन्द्र के दोनों ओर कोई ग्रह नहीं: एकाकीपन और अस्थिर साधन।")),
}
REMEDIES_HI = {
    "mangal": ["विवाह से पहले कुम्भ विवाह या अर्क/पीपल विवाह", "मंगलनाथ (उज्जैन) या नवग्रह मन्दिर में मंगल दोष निवारण पूजा",
               "मंगलवार को हनुमान चालीसा या सुन्दरकाण्ड; 'ॐ क्रां क्रीं क्रौं सः भौमाय नमः' का 10,000 जप",
               "मंगलवार व्रत; मसूर, गुड़ और लाल वस्त्र का दान", "प्रायः मांगलिक से विवाह, या 28 वर्ष की आयु के बाद विवाह की सलाह"],
    "gand_mool": ["जन्म नक्षत्र में चन्द्र के लौटने के दिन (लगभग 27वें दिन) गण्ड मूल (मूल) शान्ति पूजा",
                  "वह दिन छूट जाए तो उसी नक्षत्र के किसी अगले दिन, परम्परा से पहले वर्ष के भीतर",
                  "नक्षत्र स्वामी का जप: अश्विनी, मघा, मूल के लिए केतु ('ॐ कें केतवे नमः'); आश्लेषा, ज्येष्ठा, रेवती के "
                  "लिए बुध ('ॐ बुं बुधाय नमः')",
                  "शान्ति के बाद दान: केतु के लिए तिल और कम्बल, बुध के लिए हरी मूँग और हरा वस्त्र"],
    "kaal_sarp": ["त्र्यम्बकेश्वर (नासिक), उज्जैन या कालहस्ती में काल सर्प दोष निवारण पूजा",
                  "नाग पंचमी या महाशिवरात्रि पर रुद्राभिषेक; चाँदी का नाग-नागिन जोड़ा अर्पित करें",
                  "सर्प सूक्त और महामृत्युंजय मन्त्र का पाठ; पक्षियों और मछलियों को दाना"],
    "pitra": ["गया, वाराणसी (पिशाच मोचन) या त्र्यम्बकेश्वर में नारायण बलि, त्रिपिण्डी श्राद्ध या पिण्ड दान",
              "प्रत्येक अमावस्या को पितरों को जल और काले तिल; पितृ पक्ष में कौए, गाय और ब्राह्मण को भोजन",
              "शनिवार को पीपल में जल और तिल के तेल का दीपक"],
    "grahan": ["ग्रहण या अमावस्या के दिन ग्रहण दोष शान्ति पूजा",
               "सूर्य के लिए आदित्य हृदय स्तोत्र, चन्द्र के लिए 'ॐ सोम सोमाय नमः' का जप",
               "गेहूँ-गुड़ (सूर्य) या चावल-दूध (चन्द्र) का दान; राहु-केतु मन्त्र जप"],
    "guru_chandal": ["गुरु चाण्डाल दोष निवारण पूजा; गुरुवार को 'ॐ बृं बृहस्पतये नमः'",
                     "गुरुवार व्रत, पीली वस्तुएँ, हल्दी और चने की दाल का दान; बड़ों और गुरुजनों का सम्मान"],
    "shrapit": ["शनि-राहु मन्त्र जप ('ॐ शं शनैश्चराय नमः' / 'ॐ रां राहवे नमः')",
                "शनिवार को पीपल के नीचे सरसों के तेल का दीपक; प्रतिदिन हनुमान चालीसा"],
    "angarak": ["मंगलनाथ, उज्जैन में अंगारक दोष पूजा; मंगलवार को हनुमान उपासना",
                "मसूर दान, क्रोध में निर्णय न लें; मंगल और राहु मन्त्र जप"],
    "vish": ["सोमवार को शिवजी का दुग्धाभिषेक और शनिवार को शनि मन्त्र", "हनुमान चालीसा; काले तिल और चावल का दान"],
    "kemadruma": ["सोमवार को शिव-पार्वती पूजन; 'ॐ श्रां श्रीं श्रौं सः चन्द्रमसे नमः' का जप",
                  "चाँदी धारण करें, सोमवार को शिवलिंग पर दूध अर्पित करें"],
}
NOTES = {
    "en": [
        "Planet positions are sidereal (Lahiri ayanamsa) from the Swiss Ephemeris; houses are whole-sign from the Lagna.",
        "Divisional charts follow the Parashari definitions of Brihat Parashara Hora Shastra (the 'Traditional "
        "Parasara' options in Jagannatha Hora), the same as the charts on the website. The Hora (D2) is Jagannatha "
        "Hora's default Uma-Shambhu hora (P.V.R. Narasimha Rao's reading of Parashara); in the older Sun/Moon hora "
        "every planet sits in Leo or Cancer.",
        "The transit chart shows the sky on the printed date over your Lagna; transits change daily.",
        "Vimshottari dasha starts from the Moon's nakshatra at birth; dates depend on an accurate birth time. "
        "A birth time off by a few minutes can move the dasha dates by weeks and change the higher divisional charts.",
        "Dosha checks are rule-based. Mangal Dosha is tested against the parihara rules (own or exalted sign, Leo or "
        "Aquarius, the sign-house exceptions, Cancer or Leo Lagna, Jupiter's conjunction or aspect, Jupiter or Venus "
        "in the Lagna); debility, combustion and the Moon's company only reduce it. Have remedies performed through a "
        "qualified acharya after a full reading. This report is guidance, not a guarantee, and not medical, legal or "
        "financial advice.",
        "Yogas are found by the rules of BPHS, Phaladeepika and Saravali on the D1 chart with whole-sign houses. "
        "A yoga gives its result mainly in the dashas of the planets that form it, and only as far as those planets "
        "are strong; a weak or afflicted planet gives a weaker result.",
    ],
    "hi": [
        "ग्रह स्थिति स्विस एफेमेरिस से निरयण (लाहिरी अयनांश) में है; भाव लग्न से सम्पूर्ण राशि पद्धति में हैं।",
        "वर्ग कुण्डलियाँ बृहत् पाराशर होरा शास्त्र की पाराशरी विधि से हैं (जगन्नाथ होरा के 'Traditional Parasara' "
        "विकल्प), वेबसाइट की कुण्डलियों के समान। होरा (D2) जगन्नाथ होरा की डिफ़ॉल्ट उमा-शम्भु होरा है (पी.वी.आर. "
        "नरसिंह राव द्वारा पराशर की व्याख्या); पुरानी सूर्य-चन्द्र होरा में हर ग्रह सिंह या कर्क में ही आता है।",
        "गोचर कुण्डली मुद्रण तिथि के आकाश को आपके लग्न पर दर्शाती है; गोचर प्रतिदिन बदलता है।",
        "विंशोत्तरी दशा जन्म के चन्द्र नक्षत्र से आरम्भ होती है; तिथियाँ सही जन्म समय पर निर्भर हैं। कुछ मिनट का "
        "अन्तर दशा तिथियों को सप्ताहों तक खिसका सकता है और सूक्ष्म वर्ग कुण्डलियाँ बदल सकता है।",
        "दोष विचार नियमों पर आधारित है। मंगल दोष को परिहार नियमों (स्वराशि या उच्च, सिंह या कुम्भ, राशि-भाव अपवाद, "
        "कर्क या सिंह लग्न, गुरु की युति या दृष्टि, लग्न में गुरु या शुक्र) पर जाँचा गया है; नीच, अस्त या चन्द्र की युति "
        "केवल दोष को न्यून करते हैं। उपाय पूर्ण विचार के बाद योग्य आचार्य से करवाएँ। "
        "यह रिपोर्ट मार्गदर्शन है, गारंटी नहीं, और चिकित्सा, कानूनी या वित्तीय सलाह नहीं।",
        "योग बृहत् पाराशर होरा शास्त्र, फलदीपिका और सारावली के नियमों से लग्न कुण्डली (सम्पूर्ण राशि भाव) पर देखे गए हैं। "
        "योग का फल मुख्यतः उसे बनाने वाले ग्रहों की दशा में और उनके बल के अनुपात में मिलता है; निर्बल या पीड़ित ग्रह "
        "कम फल देता है।",
    ],
}


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

def _dms(deg):
    deg = deg % 30
    d = int(deg)
    m_float = (deg - d) * 60
    m = int(m_float)
    s = int(round((m_float - m) * 60))
    if s == 60:
        m, s = m + 1, 0
    return f"{d}° {m:02d}' {s:02d}\""


def _fmt_date(dt, lang):
    if not dt:
        return "-"
    return dt.strftime("%d.%m.%Y") if lang == "hi" else dt.strftime("%d %b %Y")


def _birth_local(k):
    tz = pytz.timezone(k.birth_timezone or "Asia/Kolkata")
    bd = k.birth_date
    return bd.astimezone(tz) if bd.tzinfo else tz.localize(bd)


def _jd(dt):
    u = dt.astimezone(pytz.utc)
    return swe.julday(u.year, u.month, u.day, u.hour + u.minute / 60 + u.second / 3600)


def _sidereal_positions(jd):
    """{planet: (longitude, speed)} sidereal Lahiri, Ketu opposite the true node, as in the kundali calculator."""
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    ayan = swe.get_ayanamsa_ut(jd)
    out = {}
    for name, pid in SWE_IDS.items():
        pos, _ = swe.calc_ut(jd, pid, swe.FLG_SWIEPH | swe.FLG_SPEED)
        out[name] = ((pos[0] - ayan) % 360, pos[3])
    out["Ketu"] = ((out["Rahu"][0] + 180) % 360, out["Rahu"][1])
    return out


def _fit(pdf, text, width, size, style=""):
    """Set the largest font size (down to 6 pt) at which ``text`` fits in ``width``."""
    while True:
        pdf.font(size, style)
        if pdf.get_string_width(text) <= width or size < 6:
            return
        size -= 0.3


def _dignity(planet, sign, lang):
    if planet not in EXALTED:
        return ""
    if EXALTED[planet] == sign:
        return i18n.w("exalted", lang)
    if (EXALTED[planet] + 6) % 12 == sign:
        return i18n.w("debilitated", lang)
    return i18n.w("own", lang) if sign in OWN[planet] else ""


MANGAL_HI = {
    "own": "मंगल अपनी राशि {sign} में है", "exalted": "मंगल मकर में उच्च का है",
    "leo_aq": "सिंह या कुम्भ ({sign}) में मंगल दोष नहीं देता", "exception": "{house}वें भाव में {sign} का मंगल शास्त्रीय अपवाद है",
    "yogakaraka": "{asc} लग्न के लिए मंगल योगकारक है", "jup_with": "गुरु मंगल के साथ है",
    "jup_aspect": "गुरु की मंगल पर दृष्टि है", "jupiter_lagna": "लग्न में गुरु कुण्डली की रक्षा करता है",
    "venus_lagna": "लग्न में शुक्र कुण्डली की रक्षा करता है", "debilitated": "मंगल कर्क में नीच और निर्बल है",
    "combust": "मंगल सूर्य के समीप अस्त है", "moon_with": "चन्द्र मंगल के साथ है (चन्द्र-मंगल योग)",
}
REF_HI = {"Lagna": "लग्न", "Moon": "चन्द्र", "Venus": "शुक्र"}
REASON_HI = {
    "All seven planets are hemmed between Rahu and Ketu": "सातों ग्रह राहु और केतु के बीच घिरे हैं",
    "Sun conjunct Rahu/Ketu": "सूर्य राहु/केतु के साथ", "Rahu/Ketu in the 9th house (house of ancestors)":
    "राहु/केतु नवम (पितृ) भाव में", "Sun and Saturn together in the 9th house": "नवम भाव में सूर्य और शनि साथ",
    "Sun conjunct Rahu": "सूर्य राहु के साथ", "Sun conjunct Ketu": "सूर्य केतु के साथ",
    "Moon conjunct Rahu": "चन्द्र राहु के साथ", "Moon conjunct Ketu": "चन्द्र केतु के साथ",
    "Jupiter conjunct Rahu/Ketu": "गुरु राहु/केतु के साथ", "Saturn conjunct Rahu": "शनि राहु के साथ",
    "Mars conjunct Rahu": "मंगल राहु के साथ", "Saturn conjunct Moon": "शनि चन्द्र के साथ",
    "No planet in the 2nd or 12th from the Moon (or with it)": "चन्द्र से दूसरे या बारहवें भाव में (या साथ) कोई ग्रह नहीं",
    "Benefic in a kendra cancels Kemadruma": "केन्द्र में शुभ ग्रह केमद्रुम को भंग करता है",
}


def mangal_reasons_text(m, lang):
    if lang != "hi":
        from ..utils.dosha_remedies import mangal_reasons
        return mangal_reasons(m)
    fmt = {"sign": i18n.sign(m["mars_sign"], "hi"), "house": m["mars_house"], "asc": i18n.sign(m["asc_sign"], "hi")}
    lines = [f"{REF_HI[ref]} से {h}वें भाव में मंगल" for ref, h in m["positions"]]
    lines += ["भंग: " + MANGAL_HI[key].format(**fmt) for key, _ in m["parihara"]]
    lines += ["न्यून: " + MANGAL_HI[key].format(**fmt) for key, _ in m["reducers"]]
    return lines


def _nakshatra_return(birth, nak_i):
    """First span after birth (from day 20 on) when the Moon is back in nakshatra ``nak_i``: the Mool shanti day."""
    span = 360 / 27
    t = birth + timedelta(days=20)
    tz = birth.tzinfo
    swe.set_sid_mode(swe.SIDM_LAHIRI)

    def moon_at(dt):
        jd = _jd(dt)
        return (swe.calc_ut(jd, swe.MOON, swe.FLG_SWIEPH)[0][0] - swe.get_ayanamsa_ut(jd)) % 360
    step = timedelta(hours=2)
    for _ in range(12 * 15):
        if int(moon_at(t) // span) == nak_i:
            start = t
            while int(moon_at(start - timedelta(minutes=10)) // span) == nak_i:
                start -= timedelta(minutes=10)
            end = t
            while int(moon_at(end + timedelta(minutes=10)) // span) == nak_i:
                end += timedelta(minutes=10)
            return {"start": start.astimezone(tz) if tz else start, "end": end.astimezone(tz) if tz else end}
        t += step
    return None


def _pratyantar(ad):
    """Pratyantar dashas inside an antardasha: same order from the AD lord, each AD length * years / 120."""
    start, end = ad["start_date"], ad["end_date"]
    total = (end - start).total_seconds()
    i = DASHA_ORDER.index(ad["planet"])
    out, t = [], start
    for n in range(9):
        p = DASHA_ORDER[(i + n) % 9]
        length = timedelta(seconds=total * DASHA_YEARS[p] / 120)
        out.append({"planet": p, "start_date": t, "end_date": t + length})
        t += length
    return out


class _DoshaChart:
    """Adapter so dosha_remedies.individual_doshas can read a saved kundali."""
    def __init__(self, signs, lons, asc_sign):
        from ..utils.dosha_remedies import RASHIS
        self.planets = {n: {"longitude": lons[n], "house": (signs[n] - asc_sign) % 12 + 1,
                            "zodiac_sign": RASHIS[signs[n]]} for n in signs}


def collect(k, now):
    from ..utils.dosha_remedies import GANA, YONI, individual_doshas, nak_index, REMEDIES
    from ..view_kundali import _running_periods, get_structured_dashas

    birth = _birth_local(k)
    jd = _jd(birth)
    live = _sidereal_positions(jd)
    d1 = k.planetary_positions or {}
    planets = {}
    for name in ORDER:
        p = d1.get(name) or {}
        lon = p.get("longitude_sidereal")
        if lon is None:
            lon = live[name][0]
        sign = int(lon // 30)
        planets[name] = {
            "lon": lon, "sign": sign, "nakshatra": i18n.NAK_ALIASES.get(p.get("nakshatra"), p.get("nakshatra")) or
            i18n.NAKSHATRAS[int(lon // (360 / 27))][0],
            "pada": int((lon % (360 / 27)) // (360 / 108)) + 1,
            "retro": name in ("Rahu", "Ketu") or live[name][1] < 0,
        }
    asc_lon = (k.ascendant or {}).get("asc_sidereal")
    if asc_lon is None:
        asc_lon = (i18n.sign_index((k.ascendant or {}).get("sign_sidereal", "Aries")) or 0) * 30
    asc_sign = int(asc_lon // 30)
    moon = planets["Moon"]
    nak_i = int(moon["lon"] // (360 / 27))

    from ..utils import varga
    vargas = {}
    for key, factor in i18n.VARGA_FACTORS.items():
        placements = {name: (varga.varga_sign(planets[name]["lon"], factor), planets[name]["retro"]) for name in ORDER}
        vargas[key] = {"asc": varga.varga_sign(asc_lon, factor), "placements": placements}

    transit = _sidereal_positions(_jd(now))
    transits = {n: {"lon": lon, "sign": int(lon // 30), "retro": n in ("Rahu", "Ketu") or speed < 0}
                for n, (lon, speed) in transit.items()}

    dashas = _running_periods(get_structured_dashas(k))
    current = {}
    naive_now = now.replace(tzinfo=None)
    for block in dashas:
        md = block.get("mahadasha") or {}
        if md.get("start_date") and md["start_date"] <= naive_now < md["end_date"]:
            current["md"] = md
            for ad in block.get("antardashas") or []:
                if ad.get("start_date") and ad["start_date"] <= naive_now < ad["end_date"]:
                    current["ad"] = ad
                    current["pds"] = _pratyantar(ad)
                    current["pd"] = next((p for p in current["pds"] if p["start_date"] <= naive_now < p["end_date"]),
                                         None)

    signs = {n: planets[n]["sign"] for n in ORDER}
    lons = {n: planets[n]["lon"] for n in ORDER}
    doshas = individual_doshas(_DoshaChart(signs, lons, asc_sign))
    from ..utils.kundali_yogas import find_yogas
    yogas = find_yogas(signs, lons, asc_sign)
    from ..utils.dosha_remedies import REMEDIES as _R, gand_mool, mangal_dosha
    mars_house = (planets["Mars"]["sign"] - asc_sign) % 12 + 1
    mangal = mangal_dosha(signs, lons, asc_sign)
    if mangal["present"]:
        doshas = {"mangal": {"present": True, "cancelled": mangal["cancelled"], "mangal": mangal,
                             "reasons": mangal_reasons_text(mangal, "en"),
                             "remedies": [] if mangal["cancelled"] else REMEDIES["mangal"],
                             "severity": mangal["severity"]}, **doshas}
    gm = gand_mool(moon["lon"])
    if gm["present"]:
        gm["shanti"] = _nakshatra_return(birth, gm["nak_index"])
        doshas["gand_mool"] = {"present": True, "cancelled": False, "gm": gm, "reasons": gm["reasons"],
                               "remedies": _R["gand_mool"], "severity": gm["severity"]}

    from ..utils.transits import sade_sati
    nak_name = i18n.NAKSHATRAS[nak_i][0]
    return {
        "birth": birth, "planets": planets, "asc_lon": asc_lon, "asc_sign": asc_sign, "vargas": vargas,
        "transits": transits, "dashas": dashas, "current": current, "doshas": doshas, "yogas": yogas, "mars_house": mars_house,
        "sade_sati": sade_sati(moon["sign"], transits["Saturn"]["sign"]),
        "avakhada": {
            "nak": nak_name, "pada": moon["pada"], "nak_lord": DASHA_ORDER[nak_i % 9], "varna": VARNA[moon["sign"]],
            "nadi": NADI[nak_i % 6], "gana": GANA.get(nak_name.replace("Mula", "Mula"), ""),
            "yoni": YONI[nak_index(nak_name)] if nak_index(nak_name) is not None else "",
        },
    }


def _birth_panchang(k, birth):
    from ..utils.astro_calculations import get_panchang
    try:
        return get_panchang(target_date=birth, lat=k.birth_lat, lon=k.birth_lon, timezone_str=k.birth_timezone,
                            city_name=k.birth_place)
    except Exception:   # the report still prints without it
        return {}


# ---------------------------------------------------------------------------
# Chapters
# ---------------------------------------------------------------------------

def _month_key(k):
    """The owner's lunar month system (profile setting); Purnimanta by default, as in Kashi."""
    profile = getattr(getattr(k, "user", None), "profile", None)
    return "amanta_month" if getattr(profile, "month_system", "") == "amanta" else "purnimanta_month"


def _chapter_birth(pdf, k, data, lang):
    L = lambda key: i18n.w(key, lang)
    pdf.chapter(1, L("ch_birth"))
    b = data["birth"]
    pdf.kv_table([
        (L("name"), k.name),
        (L("birth_date"), _fmt_date(b, lang) + f"  ({i18n.terms(b.strftime('%A'), lang)})"),
        (L("birth_time"), b.strftime("%H:%M") + f"  (UTC{b.strftime('%z')[:3]}:{b.strftime('%z')[3:]})"),
        (L("birth_place"), k.birth_place),
        (L("coords"), f"{k.birth_lat:.4f}°, {k.birth_lon:.4f}°"),
        (L("timezone"), k.birth_timezone),
    ])
    p = _birth_panchang(k, b)
    if p:
        pdf.h2(L("panchang_birth"))
        T = lambda key: i18n.terms(p.get(key, ""), lang)
        pdf.kv_table([(L("weekday"), T("weekday")), (L("tithi"), T("paksha_tithi")),
                      (L("nakshatra"), i18n.nakshatra(p.get("nakshatra", ""), lang)), (L("yoga"), T("yoga")),
                      (L("karana"), T("karana")), (L("masa"), T(_month_key(k))),
                      (L("ritu"), T("ritu")),
                      (f"{L('sunrise')} / {L('sunset')}", f"{p.get('sunrise', '')} / {p.get('sunset', '')}")])
    a = data["avakhada"]
    pdf.h2(L("avakhada"))
    gana = a["gana"]
    pdf.kv_table([
        (L("lagna"), f"{i18n.sign(data['asc_sign'], lang)}  {_dms(data['asc_lon'])}"),
        (L("rashi"), i18n.sign(data["planets"]["Moon"]["sign"], lang)),
        (L("sun_sign"), i18n.sign(data["planets"]["Sun"]["sign"], lang)),
        (L("nakshatra"), f"{i18n.nakshatra(a['nak'], lang)}, {L('pada')} {a['pada']}"),
        (L("nak_lord"), i18n.planet(a["nak_lord"], lang)),
        (L("varna"), i18n.pick(a["varna"], lang)), (L("nadi"), i18n.pick(a["nadi"], lang)),
        (L("gana"), GANA_HI.get(gana, gana) if lang == "hi" else gana),
        (L("yoni"), YONI_HI.get(a["yoni"], a["yoni"]) if lang == "hi" else a["yoni"]),
    ])


def _chapter_planets(pdf, data, lang):
    L = lambda key: i18n.w(key, lang)
    pdf.chapter(2, L("ch_planets"))
    planets = data["planets"]
    asc = data["asc_sign"]
    cards = [("Ascendant", {"lon": data["asc_lon"], "sign": asc, "nakshatra": i18n.NAKSHATRAS[int(data["asc_lon"] // (360 / 27))][0],
                            "pada": int((data["asc_lon"] % (360 / 27)) // (360 / 108)) + 1, "retro": False})]
    cards += [(n, planets[n]) for n in ORDER]
    col_w = (pdf.body_w - 6) / 2
    card_h = 27
    for i, (name, p) in enumerate(cards):
        if i % 2 == 0:
            pdf.need(card_h + 3)
            y = pdf.get_y()
        x = pdf.l_margin + (i % 2) * (col_w + 6)
        color = PLANET_COLORS.get(name, MAROON)
        pdf.set_fill_color(252, 247, 238)
        pdf.set_draw_color(*RULE)
        pdf.set_line_width(0.2)
        pdf.rect(x, y, col_w, card_h, style="DF", round_corners=True, corner_radius=2)
        pdf.set_fill_color(*color)
        pdf.rect(x, y, 1.8, card_h, style="F")
        img = planet_image(name)
        if img:
            pdf.image(img, x=x + 4, y=y + 4, w=14, h=14)
        house = (p["sign"] - asc) % 12 + 1
        pdf.set_xy(x + 21, y + 2.5)
        pdf.font(12, "B")
        pdf.set_text_color(*color)
        other = i18n.PLANETS[name][0 if lang == "hi" else 1]
        pdf.cell(col_w - 24, 6, f"{i18n.planet(name, lang)}  ·  {other}")
        pdf.set_text_color(*INK)
        pdf.font(8.6)
        dign = _dignity(name, p["sign"], lang)
        line1 = f"{i18n.sign(p['sign'], lang)} {_dms(p['lon'])}  ·  {L('house')} {house}"
        line2 = f"{i18n.nakshatra(p['nakshatra'], lang)} {L('pada')} {p['pada']}  ·  {L('lord_short')}: " \
                f"{i18n.planet(SIGN_LORDS[p['sign']], lang)}"
        extra = [s for s in (dign, L("retro") if p["retro"] and name not in ("Rahu", "Ketu", "Ascendant") else "") if s]
        text_w = col_w - 24
        for n, line in enumerate((line1, line2)):
            _fit(pdf, line, text_w, 8.6)
            pdf.set_xy(x + 21, y + 9 + n * 4.6)
            pdf.cell(text_w, 4.6, line)
        pdf.set_xy(x + 21, y + 18.4)
        pdf.set_text_color(*MUTED)
        _fit(pdf, i18n.pick(KARAKA[name], lang), text_w, 7.6, "I")
        pdf.cell(text_w, 4, i18n.pick(KARAKA[name], lang))
        pdf.set_text_color(*INK)
        if extra:
            px = x + col_w - 3
            for label in reversed(extra):
                pdf.font(7.5, "B")
                wdt = pdf.get_string_width(label) + 5
                px -= wdt + 1
                pdf.pill(label, GREEN if label in (L("exalted"), L("own")) else (RED if label == L("debilitated") else SAFFRON),
                         x=px, y=y + 2.6, size=7.5)
        if i % 2 == 1 or i == len(cards) - 1:
            pdf.set_y(y + card_h + 3)
    pdf.h2(L("ch_planets"))
    rows = []
    for name in ORDER:
        p = planets[name]
        rows.append([i18n.planet(name, lang), i18n.sign(p["sign"], lang), _dms(p["lon"]),
                     f"{i18n.nakshatra(p['nakshatra'], lang)} ({p['pada']})", (p["sign"] - asc) % 12 + 1,
                     i18n.planet(SIGN_LORDS[p["sign"]], lang),
                     L("retro") if p["retro"] else L("direct"), _dignity(name, p["sign"], lang)])
    pdf.grid_table([L("planet"), L("sign"), L("degree"), L("nakshatra"), L("house"), L("lord"), L("motion"),
                    L("dignity")], rows, widths=(17, 19, 22, 34, 12, 18, 22, 26), size=8.2)


def _chapter_lagna(pdf, data, lang):
    L = lambda key: i18n.w(key, lang)
    size = 80
    pdf.chapter(3, L("ch_lagna"), min_space=size + 45)
    pdf.need(size + 22)
    placements = {n: (p["sign"], p["retro"]) for n, p in data["planets"].items()}
    y = pdf.get_y() + 2
    draw_chart(pdf, pdf.l_margin, y, size, data["asc_sign"], placements, L("lagna_chart"),
               f"{L('lagna')}: {i18n.sign(data['asc_sign'], lang)}")
    draw_chart(pdf, pdf.l_margin + size + 10, y, size, data["planets"]["Moon"]["sign"], placements, L("moon_chart"),
               f"{i18n.planet('Moon', lang)}: {i18n.sign(data['planets']['Moon']['sign'], lang)}")
    pdf.set_y(y + size + 16)
    pdf.font(8, "I")
    pdf.set_text_color(*MUTED)
    pdf.cell(0, 4, "* " + L("retro") + "  ·  " + ("Numbers are the signs: 1 = Aries ... 12 = Pisces" if lang == "en"
                                                     else "अंक राशि दर्शाते हैं: 1 = मेष ... 12 = मीन"),
             new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(*INK)
    pdf.h2(L("bhava_table"))
    rows = []
    for h in range(1, 13):
        sign = (data["asc_sign"] + h - 1) % 12
        names = [i18n.planet(n, lang) for n in ORDER if data["planets"][n]["sign"] == sign]
        rows.append([h, i18n.sign(sign, lang), i18n.planet(SIGN_LORDS[sign], lang), ", ".join(names) or "-"])
    pdf.grid_table([L("house"), L("sign"), L("lord"), L("planets_in")], rows, widths=(16, 34, 34, 86), size=8.8)


def _chapter_vargas(pdf, data, lang, number=7):
    """Each divisional chart in its own block: the chart on the left, its planet table on the right."""
    from ..utils import varga
    L = lambda key: i18n.w(key, lang)
    intro = ("Each divisional chart magnifies one area of life. Read a planet's strength in the Rashi chart "
             "together with its place in the varga for that subject. A planet in the same sign as in the Rashi "
             "chart is vargottama and gains strength." if lang == "en" else
             "प्रत्येक वर्ग कुण्डली जीवन के एक क्षेत्र को सूक्ष्मता से दिखाती है। ग्रह का बल राशि कुण्डली और "
             "सम्बन्धित वर्ग दोनों में देखें। राशि कुण्डली वाली ही राशि में स्थित ग्रह वर्गोत्तम होकर बली होता है।")
    pdf.chapter(number, L("ch_vargas"), intro)
    keys = [k for k in i18n.VARGAS if k != "d1"]
    size = 66
    gap = 6
    table_x = pdf.l_margin + size + gap
    table_w = pdf.body_w - size - gap
    widths = [0.19, 0.19, 0.18, 0.1, 0.34]
    row_h = 5.6
    block_h = 9 + size + 6
    planets = data["planets"]
    vargottama = "Vargottama" if lang == "en" else "वर्गोत्तम"
    for key in keys:
        factor = i18n.VARGA_FACTORS[key]
        v = data["vargas"][key]
        name_en, name_hi, read = i18n.VARGAS[key]
        pdf.need(block_h)
        top = pdf.get_y()
        pdf.set_fill_color(*MAROON)
        pdf.rect(pdf.l_margin, top, 1.6, 6.5, style="F")
        pdf.set_xy(pdf.l_margin + 3.5, top)
        pdf.font(12, "B")
        pdf.set_text_color(*MAROON)
        title = name_hi if lang == "hi" else name_en
        pdf.cell(pdf.get_string_width(title) + 3, 6.5, title)
        pdf.font(9, "I")
        pdf.set_text_color(*MUTED)
        pdf.cell(0, 6.5, f"{i18n.pick(read, lang)}  ·  {L('lagna')}: {i18n.sign(v['asc'], lang)}")
        pdf.set_text_color(*INK)
        y = top + 9
        draw_chart(pdf, pdf.l_margin, y, size, v["asc"], v["placements"], font_size=7.2)

        heads = [L("planet"), L("sign"), L("degree"), L("house"), L("dignity")]
        rows = [("Lagna" if lang == "en" else "लग्न", v["asc"], varga.varga_degree(data["asc_lon"], factor), 1, "", None)]
        for name in ORDER:
            sign = v["placements"][name][0]
            dign = _dignity(name, sign, lang)
            if sign == planets[name]["sign"]:
                dign = f"{dign}, {vargottama}" if dign else vargottama
            retro = v["placements"][name][1] and name not in ("Rahu", "Ketu")
            rows.append((i18n.planet(name, lang) + ("*" if retro else ""), sign,
                         varga.varga_degree(planets[name]["lon"], factor), (sign - v["asc"]) % 12 + 1, dign, name))
        ty = y + (size - row_h * (len(rows) + 1)) / 2
        pdf.set_fill_color(*MAROON)
        pdf.rect(table_x, ty, table_w, row_h, style="F")
        pdf.set_text_color(255, 255, 255)
        pdf.font(8.4, "B")
        x = table_x
        for h, wf in zip(heads, widths):
            pdf.set_xy(x + 1.2, ty)
            pdf.mixed_cell(table_w * wf - 1.2, row_h, h, 8.4, "B", align="L")
            x += table_w * wf
        for r, (label, sign, deg, house, dign, name) in enumerate(rows):
            ry = ty + row_h * (r + 1)
            pdf.set_fill_color(*((255, 240, 196) if r == 0 else SOFT if r % 2 else (252, 248, 240)))
            pdf.rect(table_x, ry, table_w, row_h, style="F")
            cells = [label, i18n.sign(sign, lang), _dms(deg), str(house), dign]
            x = table_x
            for c, (text, wf) in enumerate(zip(cells, widths)):
                style = "B" if c == 0 else ""
                pdf.set_text_color(*(PLANET_COLORS.get(name, MAROON) if c == 0 else
                                     GREEN if c == 4 and dign else INK))
                _fit(pdf, text, table_w * wf - 1.6, 8.4, style)
                pdf.set_xy(x + 1.2, ry)
                pdf.mixed_cell(table_w * wf - 1.2, row_h, text, pdf.font_size_pt, style, align="L")
                x += table_w * wf
        pdf.set_draw_color(*RULE)
        pdf.set_line_width(0.2)
        bottom = ty + row_h * (len(rows) + 1)
        pdf.line(table_x, bottom, table_x + table_w, bottom)
        pdf.set_text_color(*INK)
        pdf.set_y(top + block_h)
    pdf.font(8, "I")
    pdf.set_text_color(*MUTED)
    pdf.cell(0, 4, "* " + L("retro"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(*INK)


def _chapter_transit(pdf, data, lang, now, number=6):
    L = lambda key: i18n.w(key, lang)
    intro = (f"{L('transit_as_on')} {_fmt_date(now, lang)}, " +
             ("placed on your birth Lagna." if lang == "en" else "आपके जन्म लग्न पर।"))
    size = 92
    pdf.chapter(number, L("ch_transit"), intro, min_space=size + 70)
    pdf.need(size + 14)
    tr = data["transits"]
    x = pdf.l_margin + (pdf.body_w - size) / 2
    y = pdf.get_y()
    draw_chart(pdf, x, y, size, data["asc_sign"], {n: (t["sign"], t["retro"]) for n, t in tr.items()},
               L("ch_transit"), f"{L('lagna')}: {i18n.sign(data['asc_sign'], lang)}")
    pdf.set_y(y + size + 14)
    moon_sign = data["planets"]["Moon"]["sign"]
    rows = []
    for n in ORDER:
        t = tr[n]
        rows.append([i18n.planet(n, lang), i18n.sign(t["sign"], lang), _dms(t["lon"]),
                     (t["sign"] - data["asc_sign"]) % 12 + 1, (t["sign"] - moon_sign) % 12 + 1,
                     L("retro") if t["retro"] else L("direct")])
    pdf.grid_table([L("planet"), L("sign"), L("degree"), L("from_lagna"), L("from_moon"), L("motion")], rows,
                   widths=(28, 30, 30, 28, 28, 26), size=8.8)
    pdf.callout(L("sade_sati"), _sade_sati_text(data["sade_sati"], lang), color=SAFFRON)


def _sade_sati_text(text, lang):
    if lang != "hi":
        return text
    if "Sade Sati is running" in text:
        phase = ("प्रथम (आरोही) चरण" if "rising" in text else "द्वितीय (शिखर) चरण" if "peak" in text
                 else "तृतीय (अवरोही) चरण")
        return f"साढ़ेसाती चल रही है: {phase}"
    if "Kantak" in text:
        return "कण्टक शनि (ढैया): शनि आपके चन्द्र से चौथे भाव में"
    if "Ashtama" in text:
        return "अष्टम शनि (ढैया): शनि आपके चन्द्र से आठवें भाव में"
    return "इस समय साढ़ेसाती या ढैया नहीं है"


def _chapter_dasha(pdf, data, lang, number=5):
    L = lambda key: i18n.w(key, lang)
    intro = ("Vimshottari dasha divides 120 years among the nine planets, beginning with the lord of the Moon's "
             "nakshatra at birth. Each Mahadasha is divided into nine Antardashas, and each of those into nine "
             "Pratyantar dashas." if lang == "en" else
             "विंशोत्तरी दशा 120 वर्षों को नौ ग्रहों में बाँटती है, जो जन्म के चन्द्र नक्षत्र के स्वामी से आरम्भ होती है। "
             "प्रत्येक महादशा में नौ अन्तर्दशाएँ और प्रत्येक अन्तर्दशा में नौ प्रत्यन्तर दशाएँ होती हैं।")
    pdf.chapter(number, L("ch_dasha"), intro)
    cur = data["current"]
    if cur.get("md"):
        md, ad, pd = cur["md"], cur.get("ad"), cur.get("pd")
        text = f"{L('mahadasha')}: {i18n.planet(md['planet'], lang)} ({_fmt_date(md['start_date'], lang)} - " \
               f"{_fmt_date(md['end_date'], lang)})"
        if ad:
            text += f"\n{L('antardasha')}: {i18n.planet(ad['planet'], lang)} ({_fmt_date(ad['start_date'], lang)} - " \
                    f"{_fmt_date(ad['end_date'], lang)})"
        if pd:
            text += f"\n{L('pratyantar')}: {i18n.planet(pd['planet'], lang)} ({_fmt_date(pd['start_date'], lang)} - " \
                    f"{_fmt_date(pd['end_date'], lang)})"
        text += "\n" + i18n.pick(DASHA_THEME[md["planet"]], lang)
        pdf.callout(L("current_period"), text, color=MAROON)
    pdf.h2(L("mahadasha"))
    segs = []
    for block in data["dashas"]:
        md = block.get("mahadasha") or {}
        if md.get("start_date") and md.get("end_date"):
            segs.append(((md["end_date"] - md["start_date"]).days, PLANET_COLORS.get(md.get("planet"), MAROON),
                         i18n.planet_abbr(md["planet"], lang), f"{md['start_date'].year % 100:02d}-{md['end_date'].year % 100:02d}"))   # %y fails before 1900 on Windows
    if segs:
        first, last = data["dashas"][0]["mahadasha"], data["dashas"][-1]["mahadasha"]
        pdf.timeline(segs, _fmt_date(first["start_date"], lang), _fmt_date(last["end_date"], lang))
    rows, hi = [], set()
    for i, block in enumerate(data["dashas"]):
        md = block.get("mahadasha") or {}
        if md.get("is_current"):
            hi.add(i)
        rows.append([i18n.planet(md.get("planet", ""), lang), _fmt_date(md.get("start_date"), lang),
                     _fmt_date(md.get("end_date"), lang), f"{md.get('duration_years', 0):.1f}",
                     i18n.pick(DASHA_THEME.get(md.get("planet"), ("", "")), lang)])
    pdf.grid_table([L("mahadasha"), L("starts"), L("ends"), L("years"), L("read_for")], rows,
                   widths=(22, 24, 24, 13, 87), size=8.2, highlight=hi)

    if cur.get("pds"):
        pdf.h2(f"{L('pratyantar')}: {i18n.planet(cur['md']['planet'], lang)} / {i18n.planet(cur['ad']['planet'], lang)}")
        rows, hi = [], set()
        for i, p in enumerate(cur["pds"]):
            if cur.get("pd") is p:
                hi.add(i)
            rows.append([i18n.planet(p["planet"], lang), _fmt_date(p["start_date"], lang), _fmt_date(p["end_date"], lang)])
        pdf.grid_table([L("pratyantar"), L("starts"), L("ends")], rows, widths=(60, 55, 55), size=8.6, highlight=hi)

    pdf.h2(f"{L('mahadasha')} / {L('antardasha')}")
    birth = data["birth"].replace(tzinfo=None)
    for block in data["dashas"]:
        md = block.get("mahadasha") or {}
        ads = block.get("antardashas") or []
        planet = md.get("planet", "")
        color = PLANET_COLORS.get(planet, MAROON)
        theme = i18n.pick(DASHA_THEME.get(planet, ("", "")), lang)
        pdf.need(16 + 6.2 * (len(ads) + 1) + 6)
        y = pdf.get_y()
        pdf.set_fill_color(*color)
        pdf.rect(pdf.l_margin, y, pdf.body_w, 8, style="F", round_corners=True, corner_radius=1.6)
        pdf.set_text_color(255, 255, 255)
        pdf.font(11, "B")
        pdf.set_xy(pdf.l_margin + 3, y + 0.8)
        label = f"{i18n.planet(planet, lang)} {L('mahadasha')}"
        if md.get("is_current"):
            label += "  ·  " + ("running now" if lang == "en" else "वर्तमान")
        pdf.cell(pdf.body_w * 0.5, 6.4, label)
        pdf.font(9)
        start, end = md.get("start_date"), md.get("end_date")
        age = ""
        if start and end:
            a0, a1 = max(0, (start - birth).days / 365.2425), (end - birth).days / 365.2425
            age = f"  ·  age {a0:.0f} to {a1:.0f}" if lang == "en" else f"  ·  आयु {a0:.0f} से {a1:.0f}"
        pdf.cell(pdf.body_w * 0.5 - 6, 6.4, f"{_fmt_date(start, lang)} - {_fmt_date(end, lang)}{age}", align="R")
        pdf.set_text_color(*MUTED)
        pdf.set_xy(pdf.l_margin + 3, y + 9)
        pdf.font(8.8, "I")
        pdf.cell(0, 5, f"{md.get('duration_years', 0):.1f} " + ("years" if lang == "en" else "वर्ष") + f"  ·  {theme}")
        pdf.set_text_color(*INK)
        pdf.set_y(y + 15)
        rows, hi = [], set()
        for i, ad in enumerate(ads):
            if ad.get("is_current"):
                hi.add(i)
            rows.append([f"{i18n.planet(planet, lang)} / {i18n.planet(ad.get('planet', ''), lang)}",
                         _fmt_date(ad.get("start_date"), lang), _fmt_date(ad.get("end_date"), lang),
                         _span(ad.get("start_date"), ad.get("end_date"), lang)])
        pdf.grid_table([L("antardasha"), L("starts"), L("ends"), "Length" if lang == "en" else "अवधि"], rows,
                       widths=(52, 42, 42, 34), size=9, highlight=hi)
        pdf.ln(2)


def _span(start, end, lang):
    """'1 y 4 m 12 d' between two dates."""
    if not start or not end:
        return ""
    months = (end.year - start.year) * 12 + end.month - start.month
    days = end.day - start.day
    if days < 0:
        months -= 1
        days += (end.replace(day=1) - timedelta(days=1)).day
    y, m = divmod(months, 12)
    units = ("y", "m", "d") if lang == "en" else ("व", "मा", "दि")
    return " ".join(f"{n} {u}" for n, u in zip((y, m, days), units) if n) or "0"


def _chapter_dosha(pdf, data, lang, number=4):
    L = lambda key: i18n.w(key, lang)
    intro = ("Each dosha below is checked in your own chart. A cancelled or absent dosha needs no remedy."
             if lang == "en" else "नीचे प्रत्येक दोष आपकी कुण्डली में जाँचा गया है। भंग या अनुपस्थित दोष के लिए उपाय आवश्यक नहीं।")
    pdf.chapter(number, L("ch_dosha"), intro)
    found = data["doshas"]
    for key, (title, about) in DOSHA_INFO.items():
        d = found.get(key)
        present = bool(d and d.get("present"))
        cancelled = bool(d and d.get("cancelled"))
        pdf.need(30)
        y = pdf.get_y()
        pdf.font(12, "B")
        pdf.set_text_color(*MAROON)
        pdf.cell(110, 7, i18n.pick(title, lang))
        reduced = present and not cancelled and d.get("severity") == "low"
        status = L("cancelled") if cancelled else (L("reduced") if reduced else L("present") if present else L("absent"))
        color = GOLD if cancelled else (SAFFRON if reduced else RED if present else GREEN)
        pdf.pill(status, color, x=pdf.w - pdf.r_margin - pdf.get_string_width(status) - 8, y=y + 1, size=8)
        pdf.set_y(y + 8)
        pdf.para(i18n.pick(about, lang), size=9.4, color=MUTED, align="L")
        if present:
            pdf.font(9.4, "B")
            pdf.cell(0, 5, L("why"), new_x="LMARGIN", new_y="NEXT")
            reasons = d.get("reasons") or []
            if lang == "hi":
                reasons = [REASON_HI.get(r, r) for r in reasons]
            if key == "mangal":
                reasons = mangal_reasons_text(d["mangal"], lang)
            elif key == "gand_mool" and lang == "hi":
                gm = d["gm"]
                reasons = [f"चन्द्र {i18n.nakshatra(gm['nakshatra'], 'hi')} नक्षत्र के {gm['pada']} चरण में, "
                           f"{i18n.planet(gm['lord'], 'hi')} का गण्ड मूल नक्षत्र",
                           "यह चरण राशि सन्धि (गण्डान्त) पर है, दोष का प्रबल रूप" if gm["severity"] == "high" else
                           "यह चरण सन्धि से दूर है, दोष का सौम्य रूप"]
            pdf.bullets(reasons, size=9.2, color=color)
            if key == "gand_mool" and d["gm"].get("shanti"):
                sh = d["gm"]["shanti"]
                pdf.callout(L("mool_shanti"),
                            f"{_fmt_date(sh['start'], lang)} {sh['start'].strftime('%H:%M')} - "
                            f"{_fmt_date(sh['end'], lang)} {sh['end'].strftime('%H:%M')}  ·  " +
                            ("the Moon is back in the birth nakshatra; do the shanti in this window, in daytime."
                             if lang == "en" else "चन्द्र पुनः जन्म नक्षत्र में; इसी अवधि में दिन के समय शान्ति करें।"),
                            color=MAROON)
            if not cancelled:
                pdf.font(9.4, "B")
                pdf.cell(0, 5, L("remedies"), new_x="LMARGIN", new_y="NEXT")
                remedies = REMEDIES_HI.get(key) if lang == "hi" else (d.get("remedies") or [])
                pdf.bullets(remedies or d.get("remedies") or [], size=9.2, color=SAFFRON)
        pdf.set_draw_color(*RULE)
        pdf.line(pdf.l_margin, pdf.get_y() + 1, pdf.w - pdf.r_margin, pdf.get_y() + 1)
        pdf.ln(4)


def _chapter_yoga(pdf, data, lang, number=4):
    L = lambda key: i18n.w(key, lang)
    intro = ("Classical yogas formed in your birth chart, with the placements that form each one. A yoga works "
             "mainly in the dashas of its planets." if lang == "en" else
             "आपकी जन्म कुण्डली में बने शास्त्रीय योग और उन्हें बनाने वाली ग्रह स्थिति। योग का फल मुख्यतः उसके ग्रहों की "
             "दशा में मिलता है।")
    pdf.chapter(number, L("ch_yoga"), intro)
    yogas = data.get("yogas") or []
    if not yogas:
        pdf.para("No classical yoga from our list is formed in this chart." if lang == "en" else
                 "हमारी सूची का कोई शास्त्रीय योग इस कुण्डली में नहीं बनता।", size=10, color=MUTED)
        return
    for y in yogas:
        pdf.need(30)
        top = pdf.get_y()
        pdf.font(12, "B")
        pdf.set_text_color(*MAROON)
        pdf.cell(120, 7, i18n.pick(y["name"], lang))
        if y["strength"] == "cancelled":
            status, color = L("cancelled"), GOLD
        elif not y["good"]:
            status, color = L("challenging"), RED
        elif y["strength"] in ("weak", "partial"):
            status, color = L(y["strength"]), SAFFRON
        else:
            status, color = L("present"), GREEN
        pdf.pill(status, color, x=pdf.w - pdf.r_margin - pdf.get_string_width(status) - 8, y=top + 1, size=8)
        pdf.set_y(top + 8)
        pdf.para(i18n.pick(y["meaning"], lang), size=9.4, color=MUTED, align="L")
        pdf.font(9.4, "B")
        pdf.cell(0, 5, L("why"), new_x="LMARGIN", new_y="NEXT")
        pdf.bullets([i18n.pick(r, lang) for r in y["reasons"]], size=9.2, color=color)
        pdf.set_draw_color(*RULE)
        pdf.line(pdf.l_margin, pdf.get_y() + 1, pdf.w - pdf.r_margin, pdf.get_y() + 1)
        pdf.ln(4)


def build(k, *, lang, licensee, email, order_ref, now=None):
    tz = pytz.timezone(k.birth_timezone or "Asia/Kolkata")
    now = now or datetime.now(tz)
    data = collect(k, now)
    title = i18n.w("kundali_title", lang)
    pdf = Book(lang=lang, title=f"{title} - {k.name}", running_title=f"{title} · {k.name}", licensee=licensee,
               email=email, order_ref=order_ref, printed_on=_fmt_date(now, lang))
    b = data["birth"]
    pdf.cover(title, i18n.w("kundali_sub", lang), k.name, [
        f"{_fmt_date(b, lang)}  ·  {b.strftime('%H:%M')}",
        k.birth_place,
        f"{i18n.w('lagna', lang)}: {i18n.sign(data['asc_sign'], lang)}  ·  {i18n.w('rashi', lang)}: "
        f"{i18n.sign(data['planets']['Moon']['sign'], lang)}  ·  {i18n.w('nakshatra', lang)}: "
        f"{i18n.nakshatra(data['avakhada']['nak'], lang)}",
    ], images=["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"])
    pdf.contents_page()
    _chapter_birth(pdf, k, data, lang)
    _chapter_planets(pdf, data, lang)
    _chapter_lagna(pdf, data, lang)
    _chapter_yoga(pdf, data, lang)       # yogas and doshas straight after the main chart and planets
    _chapter_dosha(pdf, data, lang, number=5)
    _chapter_dasha(pdf, data, lang, number=6)
    _chapter_transit(pdf, data, lang, now, number=7)
    _chapter_vargas(pdf, data, lang, number=8)     # divisional charts last
    pdf.font(10)
    notes_h = sum(len(pdf.multi_cell(pdf.body_w - 5, 5.3, n, dry_run=True, output="LINES")) * 5.3 + 1.6
                  for n in NOTES[lang])
    pdf.chapter(9, i18n.w("ch_notes", lang), min_space=notes_h + 75)   # the notes and colophon stay together
    pdf.bullets(NOTES[lang], size=10)
    pdf.colophon()
    raw = bytes(pdf.output())
    return protect(raw, order_ref, licensee, email)
