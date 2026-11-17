# core/utils/dosha_page.py
"""
Doshas for the kundali page, told for this chart: which planets form each one and where they sit, what it can
mean in plain words, and whether a cancellation applies. The remedies themselves are in the paid PDF report.

Every text is an (English, Hindi) pair.
"""
from ..pdf import i18n

MEANING = {
    "mangal": ("Mars, the planet of energy and temper, sits in a house that classical texts link with married "
               "life. It can bring arguments, impatience or delays in marriage, mostly in the dashas of Mars. It is "
               "usually weighed against the partner's chart: when both charts have it, it balances out.",
               "ऊर्जा और क्रोध का ग्रह मंगल उस भाव में है जिसे शास्त्र दाम्पत्य से जोड़ते हैं। इससे विवाह में विवाद, अधीरता या "
               "विलम्ब की सम्भावना रहती है, मुख्यतः मंगल की दशा में। इसे जीवनसाथी की कुण्डली के साथ देखा जाता है: दोनों में "
               "हो तो सम हो जाता है।"),
    "gand_mool": ("The Moon was in one of the six nakshatras that sit where a water sign meets a fire sign. "
                  "Tradition asks for a Mool shanti puja for the child; it is not a lifelong defect. The PDF gives "
                  "the exact shanti dates for this birth.",
                  "जन्म के समय चन्द्र उन छह नक्षत्रों में से एक में था जो जल और अग्नि राशि की सन्धि पर हैं। परम्परा में बालक के "
                  "लिए मूल शान्ति पूजा की जाती है; यह जीवनभर का दोष नहीं। PDF में इस जन्म की शान्ति की सही तिथियाँ हैं।"),
    "kaal_sarp": ("All seven planets lie on one side of the Rahu-Ketu axis. It can show as effort that meets "
                  "repeated obstacles or delays before results come, mostly in the dashas of Rahu and Ketu. Many "
                  "texts do not count it at all, so read it as a tendency, not a verdict.",
                  "सातों ग्रह राहु-केतु अक्ष के एक ओर हैं। इससे प्रयासों में बार-बार बाधा या फल में विलम्ब की सम्भावना रहती है, "
                  "मुख्यतः राहु-केतु की दशा में। कई ग्रन्थ इसे मानते ही नहीं, अतः इसे प्रवृत्ति समझें, निर्णय नहीं।"),
    "pitra": ("The Sun (father, ancestors) or the 9th house (ancestors, fortune) is touched by Rahu, Ketu or "
              "Saturn. Tradition reads it as unfinished duties to the ancestors; it can show as delays in fortune or "
              "strain with the father.",
              "सूर्य (पिता, पूर्वज) या नवम भाव (पूर्वज, भाग्य) पर राहु, केतु या शनि का प्रभाव है। परम्परा में इसे पितरों के प्रति "
              "अधूरे कर्तव्य माना जाता है; भाग्य में विलम्ब या पिता से तनाव के रूप में दिख सकता है।"),
    "grahan": ("The Sun or the Moon sits in the same sign as Rahu or Ketu in your birth chart, the pairing that "
               "causes eclipses in the sky. It does NOT mean you were born during an eclipse. It can show as "
               "self-doubt or confusion (Sun) or worry and mood swings (Moon), mostly in the dashas of these planets.",
               "आपकी जन्म कुण्डली में सूर्य या चन्द्र राहु या केतु के साथ एक ही राशि में है, वही जोड़ी जो आकाश में ग्रहण बनाती "
               "है। इसका अर्थ यह नहीं कि आपका जन्म ग्रहण के समय हुआ। इससे आत्मविश्वास में कमी या भ्रम (सूर्य) अथवा चिन्ता और "
               "मन की अस्थिरता (चन्द्र) की सम्भावना रहती है, मुख्यतः इन ग्रहों की दशा में।"),
    "guru_chandal": ("Jupiter (wisdom, teachers) is in the same sign as Rahu or Ketu. It can cloud judgement, bring "
                     "unusual beliefs or friction with teachers and elders, mostly in the dashas of these planets.",
                     "गुरु (ज्ञान, गुरुजन) राहु या केतु के साथ एक ही राशि में है। इससे विवेक धूमिल होने, असामान्य मान्यताओं या "
                     "गुरुजनों और बड़ों से मतभेद की सम्भावना रहती है, मुख्यतः इन ग्रहों की दशा में।"),
    "shrapit": ("Saturn (delay, karma) is in the same sign as Rahu. It can show as delays and heavy "
                "responsibilities in the matters of that house, mostly in the dashas of Saturn and Rahu.",
                "शनि (विलम्ब, कर्म) राहु के साथ एक ही राशि में है। इससे उस भाव के विषयों में विलम्ब और भारी उत्तरदायित्व की "
                "सम्भावना रहती है, मुख्यतः शनि और राहु की दशा में।"),
    "angarak": ("Mars (energy, anger) is in the same sign as Rahu. It can show as anger, haste and a higher "
                "chance of accidents or injuries, so care with fire, vehicles and machines helps.",
                "मंगल (ऊर्जा, क्रोध) राहु के साथ एक ही राशि में है। इससे क्रोध, जल्दबाज़ी और दुर्घटना या चोट की सम्भावना बढ़ती "
                "है, अतः अग्नि, वाहन और मशीनों में सावधानी लाभ देती है।"),
    "vish": ("Saturn (heaviness) is in the same sign as the Moon (mind). It can show as worry, low mood or a "
             "serious, cautious nature, mostly in the dashas of the Moon and Saturn and during Sade Sati.",
             "शनि (भारीपन) चन्द्र (मन) के साथ एक ही राशि में है। इससे चिन्ता, उदासी या गम्भीर, सतर्क स्वभाव की सम्भावना रहती "
             "है, मुख्यतः चन्द्र और शनि की दशा में और साढ़े साती में।"),
    "kemadruma": ("No planet sits in the sign before or after the Moon, or with it, so the mind has no support "
                  "from neighbours. It can show as loneliness or unsteady means in some periods. It is cancelled "
                  "when Jupiter or Venus is in a kendra.",
                  "चन्द्र के साथ, उससे पहले या बाद की राशि में कोई ग्रह नहीं, अतः मन को आसपास से सहारा नहीं। इससे कुछ समय एकाकीपन "
                  "या अस्थिर साधन की सम्भावना रहती है। गुरु या शुक्र केन्द्र में हो तो यह भंग होता है।"),
}


def _ord(n):
    return f"{n}{'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"


def _house(signs, asc, p):
    return (signs[p] - asc) % 12 + 1


def _together(signs, asc, a, b):
    """'The Sun and Rahu are both in Leo, in the 5th house.'"""
    pa, pb = (i18n.planet(a, "en"), i18n.planet(a, "hi")), (i18n.planet(b, "en"), i18n.planet(b, "hi"))
    s = signs[a]
    h = _house(signs, asc, a)
    return (f"{pa[0]} and {pb[0]} are both in {i18n.sign(s, 'en')}, in the {_ord(h)} house",
            f"{pa[1]} और {pb[1]} दोनों {i18n.sign(s, 'hi')} राशि में, {h}वें भाव में")


def _at(signs, asc, p):
    h = _house(signs, asc, p)
    return (f"{i18n.planet(p, 'en')} in {i18n.sign(signs[p], 'en')} ({_ord(h)} house)",
            f"{i18n.planet(p, 'hi')} {i18n.sign(signs[p], 'hi')} में ({h}वाँ भाव)")


def facts(key, signs, lons, asc, extra=None):
    """'In your chart' lines for one dosha."""
    pairs = {"grahan": [("Sun", "Rahu"), ("Sun", "Ketu"), ("Moon", "Rahu"), ("Moon", "Ketu")],
             "guru_chandal": [("Jupiter", "Rahu"), ("Jupiter", "Ketu")], "shrapit": [("Saturn", "Rahu")],
             "angarak": [("Mars", "Rahu")], "vish": [("Moon", "Saturn")]}
    if key in pairs:
        return [_together(signs, asc, a, b) for a, b in pairs[key] if signs[a] == signs[b]]
    if key == "pitra":
        out = [_together(signs, asc, "Sun", n) for n in ("Rahu", "Ketu") if signs["Sun"] == signs[n]]
        for n in ("Rahu", "Ketu"):
            if _house(signs, asc, n) == 9:
                e, h = _at(signs, asc, n)
                out.append((f"{e}, the house of ancestors", f"{h}, पितृ भाव"))
        if _house(signs, asc, "Sun") == 9 and signs["Sun"] == signs["Saturn"]:
            out.append(_together(signs, asc, "Sun", "Saturn"))
        return out
    if key == "kaal_sarp":
        r, k = _at(signs, asc, "Rahu"), _at(signs, asc, "Ketu")
        return [(f"Rahu: {r[0]}; Ketu: {k[0]}; all seven planets lie on one side between them",
                 f"राहु: {r[1]}; केतु: {k[1]}; सातों ग्रह इनके बीच एक ओर")]
    if key == "kemadruma":
        m = signs["Moon"]
        out = [(f"Moon in {i18n.sign(m, 'en')}; nothing in {i18n.sign((m - 1) % 12, 'en')} or "
                f"{i18n.sign((m + 1) % 12, 'en')}",
                f"चन्द्र {i18n.sign(m, 'hi')} में; {i18n.sign((m - 1) % 12, 'hi')} या {i18n.sign((m + 1) % 12, 'hi')} "
                f"में कोई ग्रह नहीं")]
        for p in ("Jupiter", "Venus"):
            if _house(signs, asc, p) in (1, 4, 7, 10):
                e, h = _at(signs, asc, p)
                out.append((f"Cancelled: {e}, a kendra", f"भंग: {h}, केन्द्र"))
        return out
    if key == "mangal" and extra:
        from ..pdf.kundali_report import mangal_reasons_text
        return list(zip(mangal_reasons_text(extra, "en"), mangal_reasons_text(extra, "hi")))
    if key == "gand_mool" and extra:
        hi = [f"चन्द्र {i18n.nakshatra(extra['nakshatra'], 'hi')} नक्षत्र के {extra['pada']} चरण में, "
              f"{i18n.planet(extra['lord'], 'hi')} का गण्ड मूल नक्षत्र",
              "यह चरण राशि सन्धि (गण्डान्त) पर है, दोष का प्रबल रूप" if extra["severity"] == "high" else
              "यह चरण सन्धि से दूर है, दोष का सौम्य रूप"]
        return list(zip(extra["reasons"], hi))
    return []


PLANETS = {"mangal": ["Mars"], "kaal_sarp": ["Rahu", "Ketu"], "pitra": ["Sun"], "grahan": ["Rahu", "Ketu"],
           "guru_chandal": ["Jupiter"], "shrapit": ["Saturn", "Rahu"], "angarak": ["Mars", "Rahu"],
           "vish": ["Moon", "Saturn"], "kemadruma": ["Moon"]}


def planets_of(key, signs):
    """Planets whose dashas bring the dosha out most."""
    if key == "grahan":
        return [p for p in ("Sun", "Moon") if signs[p] in (signs["Rahu"], signs["Ketu"])] + \
               [n for n in ("Rahu", "Ketu") if signs[n] in (signs["Sun"], signs["Moon"])]
    if key == "guru_chandal":
        return ["Jupiter"] + [n for n in ("Rahu", "Ketu") if signs[n] == signs["Jupiter"]]
    return PLANETS.get(key, [])
