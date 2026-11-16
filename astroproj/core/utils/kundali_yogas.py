# core/utils/kundali_yogas.py
"""
Classical yogas found in one birth chart (D1, whole-sign houses from the Lagna).

Rules follow Brihat Parashara Hora Shastra (BPHS), Phaladeepika and Saravali in their commonly taught form:
    Pancha Mahapurusha  - Ruchaka, Bhadra, Hamsa, Malavya, Shasha
    Moon yogas          - Gaja Kesari, Sunapha, Anapha, Durudhara, Adhi, Chandra-Mangala, Amala
    Sun yogas           - Budha-Aditya, Vesi, Vasi, Ubhayachari
    Raj / Dhana yogas   - kendra-trikona lords linked, yogakaraka, 2nd/11th lords linked with 1/5/9 lords,
                          Viparita (Harsha, Sarala, Vimala), Neecha Bhanga, Parivartana, Lakshmi, Saraswati
    Challenging         - Shakata (Guru Chandal, Kemadruma, Vish etc. are in dosha_remedies.individual_doshas)

A "link" (sambandha) between two planets is conjunction in one sign, exchange of signs, or mutual full aspect.
Every entry is a pair (English, Hindi) so the page and the PDF can print either language.
"""
from ..pdf import i18n

SEVEN = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
LORD = ["Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter"]
OWN = {"Sun": {4}, "Moon": {3}, "Mars": {0, 7}, "Mercury": {2, 5}, "Jupiter": {8, 11}, "Venus": {1, 6},
       "Saturn": {9, 10}}
EXALT = {"Sun": 0, "Moon": 1, "Mars": 9, "Mercury": 5, "Jupiter": 3, "Venus": 11, "Saturn": 6}
EXALTED_IN = {s: p for p, s in EXALT.items()}
DEBIL = {p: (s + 6) % 12 for p, s in EXALT.items()}
FRIENDS = {"Sun": {"Moon", "Mars", "Jupiter"}, "Moon": {"Sun", "Mercury"}, "Mars": {"Sun", "Moon", "Jupiter"},
           "Mercury": {"Sun", "Venus"}, "Jupiter": {"Sun", "Moon", "Mars"}, "Venus": {"Mercury", "Saturn"},
           "Saturn": {"Mercury", "Venus"}}
SPECIAL_ASPECTS = {"Mars": {4, 8}, "Jupiter": {5, 9}, "Saturn": {3, 10}}
BENEFICS = ("Mercury", "Jupiter", "Venus")
MALEFICS = ("Sun", "Mars", "Saturn", "Rahu", "Ketu")
KENDRA, TRIKONA, DUSTHANA = {1, 4, 7, 10}, {1, 5, 9}, {6, 8, 12}
COMBUST_MERCURY = 14     # degrees from the Sun (BPHS)
COMBUST = {"Mars": 17, "Mercury": 14, "Jupiter": 11, "Venus": 10, "Saturn": 15}   # combustion orbs, BPHS

HI_ORD = {1: "पहले", 2: "दूसरे", 3: "तीसरे", 4: "चौथे", 5: "पाँचवें", 6: "छठे", 7: "सातवें", 8: "आठवें",
          9: "नौवें", 10: "दसवें", 11: "ग्यारहवें", 12: "बारहवें"}


def _ord(n):
    return f"{n}{'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"


def _house_en(n):
    return f"the {_ord(n)} house"


def _house_hi(n):
    return f"{HI_ORD[n]} भाव"


def _p(name):
    return i18n.planet(name, "en"), i18n.planet(name, "hi")


def _s(sign):
    return i18n.sign(sign, "en"), i18n.sign(sign, "hi")


def _count(frm, to):
    """House number of sign ``to`` counted from sign ``frm`` (1-12)."""
    return (to - frm) % 12 + 1


def _aspects(planet, frm, to):
    n = _count(frm, to)
    return n == 7 or n in SPECIAL_ASPECTS.get(planet, ())


class Chart:
    """signs: {planet: sign index 0-11}, lons: {planet: sidereal longitude}, asc: Lagna sign index."""

    def __init__(self, signs, lons, asc):
        self.sign, self.lon, self.asc = dict(signs), dict(lons), asc

    def house(self, planet):
        return _count(self.asc, self.sign[planet])

    def lord(self, house):
        return LORD[(self.asc + house - 1) % 12]

    def from_moon(self, planet):
        return _count(self.sign["Moon"], self.sign[planet])

    def own_or_exalted(self, planet):
        s = self.sign[planet]
        return s in OWN.get(planet, ()) or EXALT.get(planet) == s

    def link(self, a, b):
        """How two planets are linked (Parashari sambandha), or None."""
        sa, sb = self.sign[a], self.sign[b]
        if sa == sb:
            return "conj"
        if LORD[sa] == b and LORD[sb] == a:
            return "exchange"
        if _aspects(a, sa, sb) and _aspects(b, sb, sa):
            return "aspect"
        return None


LINK_TEXT = {"conj": ("together in one sign", "एक ही राशि में साथ"),
             "exchange": ("in each other's signs (exchange)", "परस्पर राशि परिवर्तन में"),
             "aspect": ("in mutual aspect", "परस्पर दृष्टि में")}

INFO = {
    "ruchaka": (("Ruchaka Yoga", "रुचक योग"), "mahapurusha",
                ("One of the five Mahapurusha yogas: courage, leadership, a strong body, success in work with land, "
                 "police, army or sport.",
                 "पंच महापुरुष योगों में एक: साहस, नेतृत्व, सुदृढ़ शरीर; भूमि, पुलिस, सेना या खेल में सफलता।")),
    "bhadra": (("Bhadra Yoga", "भद्र योग"), "mahapurusha",
               ("One of the five Mahapurusha yogas: sharp intellect, fine speech, skill in trade, writing and "
                "learning. This is a good yoga of Mercury and has nothing to do with the panchang's Bhadra "
                "(Vishti karana).",
                "पंच महापुरुष योगों में एक: तीक्ष्ण बुद्धि, मधुर वाणी, व्यापार, लेखन और विद्या में कुशलता। यह बुध का शुभ "
                "योग है; पंचांग की भद्रा (विष्टि करण) से इसका कोई सम्बन्ध नहीं।")),
    "hamsa": (("Hamsa Yoga", "हंस योग"), "mahapurusha",
              ("One of the five Mahapurusha yogas: wisdom, a righteous nature, respect from learned people, "
               "success in teaching, law or spiritual life.",
               "पंच महापुरुष योगों में एक: ज्ञान, धार्मिक स्वभाव, विद्वानों में सम्मान; शिक्षा, विधि या आध्यात्म में सफलता।")),
    "malavya": (("Malavya Yoga", "मालव्य योग"), "mahapurusha",
                ("One of the five Mahapurusha yogas: comforts, vehicles, a happy married life, taste for art, "
                 "music and beauty.",
                 "पंच महापुरुष योगों में एक: सुख-सुविधा, वाहन, सुखी दाम्पत्य, कला, संगीत और सौन्दर्य में रुचि।")),
    "shasha": (("Shasha Yoga", "शश योग"), "mahapurusha",
               ("One of the five Mahapurusha yogas: authority over many people, discipline, patience, and "
                "rewards that come from steady long effort.",
                "पंच महापुरुष योगों में एक: अनेक लोगों पर अधिकार, अनुशासन, धैर्य; लम्बे परिश्रम का स्थायी फल।")),
    "gaja_kesari": (("Gaja Kesari Yoga", "गजकेसरी योग"), "chandra",
                    ("Jupiter in a kendra from the Moon: intelligence, a good name that lasts, wealth and the "
                     "respect of others.",
                     "चन्द्र से केन्द्र में गुरु: बुद्धि, स्थायी यश, धन और समाज में सम्मान।")),
    "sunapha": (("Sunapha Yoga", "सुनफा योग"), "chandra",
                ("A planet in the 2nd from the Moon: self-earned wealth and a good reputation.",
                 "चन्द्र से दूसरे भाव में ग्रह: स्वअर्जित धन और अच्छी प्रतिष्ठा।")),
    "anapha": (("Anapha Yoga", "अनफा योग"), "chandra",
               ("A planet in the 12th from the Moon: good health, pleasing manners and comforts.",
                "चन्द्र से बारहवें भाव में ग्रह: अच्छा स्वास्थ्य, सौम्य व्यवहार और सुख।")),
    "durudhara": (("Durudhara Yoga", "दुरुधरा योग"), "chandra",
                  ("Planets on both sides of the Moon: wealth, vehicles and a generous nature.",
                   "चन्द्र के दोनों ओर ग्रह: धन, वाहन और उदार स्वभाव।")),
    "adhi": (("Adhi Yoga", "अधि योग"), "chandra",
             ("Benefics in the 6th, 7th and 8th from the Moon: a high position, leadership and a comfortable life.",
              "चन्द्र से छठे, सातवें और आठवें भाव में शुभ ग्रह: उच्च पद, नेतृत्व और सुखी जीवन।")),
    "chandra_mangala": (("Chandra-Mangala Yoga", "चन्द्र-मंगल योग"), "chandra",
                        ("Moon and Mars together: earning through enterprise and trade.",
                         "चन्द्र और मंगल साथ: उद्यम और व्यापार से धनार्जन।")),
    "amala": (("Amala Yoga", "अमला योग"), "other",
              ("Only benefics in the 10th from the Lagna or Moon: a clean reputation and good deeds that are "
               "remembered.",
               "लग्न या चन्द्र से दसवें भाव में केवल शुभ ग्रह: निर्मल यश और स्मरणीय सत्कर्म।")),
    "budha_aditya": (("Budha-Aditya Yoga", "बुधादित्य योग"), "surya",
                     ("Sun and Mercury together with Mercury not combust: intelligence and skill with words.",
                      "सूर्य और बुध साथ, बुध अस्त नहीं: बुद्धि और वाणी की कुशलता।")),
    "vesi": (("Vesi Yoga", "वेशि योग"), "surya",
             ("A planet in the 2nd from the Sun: steady nature and good fortune (best when the planet is a benefic).",
              "सूर्य से दूसरे भाव में ग्रह: स्थिर स्वभाव और भाग्य (शुभ ग्रह हो तो उत्तम)।")),
    "vasi": (("Vasi Yoga", "वाशि योग"), "surya",
             ("A planet in the 12th from the Sun: generosity and success (best when the planet is a benefic).",
              "सूर्य से बारहवें भाव में ग्रह: उदारता और सफलता (शुभ ग्रह हो तो उत्तम)।")),
    "ubhayachari": (("Ubhayachari Yoga", "उभयचरी योग"), "surya",
                    ("Planets on both sides of the Sun: a balanced, capable person who rises like a king.",
                     "सूर्य के दोनों ओर ग्रह: सन्तुलित, समर्थ व्यक्ति, राजा समान उन्नति।")),
    "raj": (("Raj Yoga", "राज योग"), "raj",
            ("Lords of a kendra (1, 4, 7, 10) and a trikona (1, 5, 9) are linked: status, authority and a rise "
             "in life, felt most in the dashas of these planets. Most charts have at least one; its result "
             "depends on the strength of the planets involved.",
             "केन्द्र (1, 4, 7, 10) और त्रिकोण (1, 5, 9) के स्वामियों का सम्बन्ध: पद, अधिकार और उन्नति, विशेषकर इन "
             "ग्रहों की दशा में। अधिकांश कुण्डलियों में कम से कम एक होता है; फल ग्रहों के बल पर निर्भर है।")),
    "yogakaraka": (("Yogakaraka", "योगकारक"), "raj",
                   ("One planet rules both a kendra and a trikona for this Lagna and sits in a kendra or trikona: "
                    "a Raj yoga by itself.",
                    "इस लग्न के लिए एक ही ग्रह केन्द्र और त्रिकोण दोनों का स्वामी है और केन्द्र या त्रिकोण में है: "
                    "अपने आप में राज योग।")),
    "dhana": (("Dhana Yoga", "धन योग"), "dhana",
              ("Lords of the houses of wealth (2, 11) linked with lords of 1, 5 or 9: earning and saving wealth.",
               "धन भावों (2, 11) के स्वामी का 1, 5 या 9 के स्वामी से सम्बन्ध: धन का अर्जन और संचय।")),
    "harsha": (("Harsha Yoga (Viparita Raj)", "हर्ष योग (विपरीत राज)"), "raj",
               ("Lord of the 6th in a dusthana: victory over rivals and good health, a rise that comes out of "
                "difficulty.",
                "षष्ठेश दुःस्थान में: शत्रुओं पर विजय, अच्छा स्वास्थ्य; कठिनाई से निकली उन्नति।")),
    "sarala": (("Sarala Yoga (Viparita Raj)", "सरल योग (विपरीत राज)"), "raj",
               ("Lord of the 8th in a dusthana: long life, fearlessness and success after setbacks.",
                "अष्टमेश दुःस्थान में: दीर्घायु, निर्भयता और बाधाओं के बाद सफलता।")),
    "vimala": (("Vimala Yoga (Viparita Raj)", "विमल योग (विपरीत राज)"), "raj",
               ("Lord of the 12th in a dusthana: careful with money, independent and of good conduct.",
                "द्वादशेश दुःस्थान में: धन में मितव्ययी, स्वतन्त्र और सदाचारी।")),
    "neecha_bhanga": (("Neecha Bhanga Raj Yoga", "नीचभंग राज योग"), "raj",
                      ("A debilitated planet whose weakness is cancelled: struggle early, then a strong rise.",
                       "नीच ग्रह का नीचत्व भंग: आरम्भ में संघर्ष, फिर प्रबल उन्नति।")),
    "maha_parivartana": (("Maha Parivartana Yoga", "महा परिवर्तन योग"), "raj",
                         ("Two good houses exchange lords: the matters of both houses support each other and prosper.",
                          "दो शुभ भावों के स्वामियों का परिवर्तन: दोनों भावों के फल एक-दूसरे को बल देते हैं।")),
    "khala_parivartana": (("Khala Parivartana Yoga", "खल परिवर्तन योग"), "other",
                          ("An exchange that involves the 3rd house: mixed results, ups and downs through own effort.",
                           "तीसरे भाव से जुड़ा परिवर्तन: मिश्रित फल, अपने प्रयास से उतार-चढ़ाव।")),
    "dainya_parivartana": (("Dainya Parivartana Yoga", "दैन्य परिवर्तन योग"), "challenge",
                           ("An exchange that involves the 6th, 8th or 12th house: obstacles in the matters of the "
                            "other house until effort pays off.",
                            "छठे, आठवें या बारहवें भाव से जुड़ा परिवर्तन: दूसरे भाव के विषयों में बाधा, प्रयास से सुधार।")),
    "lakshmi": (("Lakshmi Yoga", "लक्ष्मी योग"), "dhana",
                ("A strong 9th lord in its own or exalted sign in a kendra or trikona, with a strong Lagna lord: "
                 "wealth, grace and good fortune.",
                 "भाग्येश स्वराशि या उच्च होकर केन्द्र या त्रिकोण में और लग्नेश बलवान: धन, श्री और सौभाग्य।")),
    "saraswati": (("Saraswati Yoga", "सरस्वती योग"), "other",
                  ("Jupiter, Venus and Mercury in kendras, trikonas or the 2nd with Jupiter strong: learning, "
                   "arts, poetry and fine speech.",
                   "गुरु, शुक्र और बुध केन्द्र, त्रिकोण या दूसरे भाव में और गुरु बलवान: विद्या, कला, काव्य और वाणी।")),
    "shakata": (("Shakata Yoga", "शकट योग"), "challenge",
                ("Moon in the 6th or 8th from Jupiter: fortune rises and falls like a cart wheel.",
                 "गुरु से छठे या आठवें भाव में चन्द्र: भाग्य गाड़ी के पहिये की तरह ऊपर-नीचे।")),
}
SOURCES = ("BPHS", "Phaladeepika", "Saravali")
ORDER = list(INFO)


def _entry(key, reasons, strength="full"):
    title, kind, meaning = INFO[key]
    return {"key": key, "name": title, "kind": kind, "good": kind != "challenge", "meaning": meaning,
            "reasons": reasons, "strength": strength}


def _in(planet, ch):
    """'Mars in Capricorn in the 10th house' in both languages."""
    h = ch.house(planet)
    pe, ph = _p(planet)
    se, sh = _s(ch.sign[planet])
    return f"{pe} in {se} in {_house_en(h)}", f"{ph} {sh} राशि में, {_house_hi(h)} में"


def mahapurusha(ch):
    out = []
    for key, planet in (("ruchaka", "Mars"), ("bhadra", "Mercury"), ("hamsa", "Jupiter"), ("malavya", "Venus"),
                        ("shasha", "Saturn")):
        if ch.house(planet) in KENDRA and ch.own_or_exalted(planet):
            dig = ("exalted", "उच्च") if EXALT[planet] == ch.sign[planet] else ("in its own sign", "स्वराशि")
            en, hi = _in(planet, ch)
            reasons = [(f"{en} (a kendra), {dig[0]} (BPHS ch. 75)", f"{hi} (केन्द्र), {dig[1]} (बृ.पा.हो.शा. अ. 75)")]
            gap = abs((ch.lon[planet] - ch.lon["Sun"] + 180) % 360 - 180)
            weak = gap < COMBUST[planet]
            if weak:
                reasons.append((f"{_p(planet)[0]} is combust ({gap:.0f}° from the Sun), so the yoga gives weaker results",
                                f"{_p(planet)[1]} अस्त है (सूर्य से {gap:.0f}°), अतः योग का फल निर्बल रहेगा"))
            out.append(_entry(key, reasons, "weak" if weak else "full"))
    return out


def moon_yogas(ch):
    out = []
    j = ch.from_moon("Jupiter")
    if j in KENDRA:
        weak = ch.sign["Jupiter"] == DEBIL["Jupiter"]
        r = [(f"Jupiter is in the {_ord(j)} from the Moon", f"गुरु चन्द्र से {HI_ORD[j]} भाव में")]
        if weak:
            r.append(("Jupiter is debilitated, so the yoga is weak", "गुरु नीच राशि में है, इसलिए योग निर्बल है"))
        out.append(_entry("gaja_kesari", r, "weak" if weak else "full"))
    five = ("Mars", "Mercury", "Jupiter", "Venus", "Saturn")
    second = [p for p in five if ch.from_moon(p) == 2]
    twelfth = [p for p in five if ch.from_moon(p) == 12]
    names = lambda ps: (", ".join(_p(p)[0] for p in ps), ", ".join(_p(p)[1] for p in ps))
    if second and twelfth:
        a, b = names(second), names(twelfth)
        out.append(_entry("durudhara", [(f"{a[0]} in the 2nd and {b[0]} in the 12th from the Moon",
                                         f"चन्द्र से दूसरे भाव में {a[1]} और बारहवें में {b[1]}")]))
    elif second:
        a = names(second)
        out.append(_entry("sunapha", [(f"{a[0]} in the 2nd from the Moon", f"चन्द्र से दूसरे भाव में {a[1]}")]))
    elif twelfth:
        b = names(twelfth)
        out.append(_entry("anapha", [(f"{b[0]} in the 12th from the Moon", f"चन्द्र से बारहवें भाव में {b[1]}")]))
    adhi = [p for p in BENEFICS if ch.from_moon(p) in (6, 7, 8)]
    spoilt = [p for p in MALEFICS if p in ch.sign and ch.from_moon(p) in (6, 7, 8)]
    if len(adhi) >= 2 and not spoilt:
        a = names(adhi)
        out.append(_entry("adhi", [(f"{a[0]} in the 6th-8th from the Moon, with no malefic there",
                                    f"चन्द्र से छठे-आठवें भावों में {a[1]}, वहाँ कोई पाप ग्रह नहीं")],
                          "full" if len(adhi) == 3 else "partial"))
    if ch.sign["Moon"] == ch.sign["Mars"]:
        out.append(_entry("chandra_mangala", [_in("Moon", ch)]))
    return out


def amala(ch):
    for base, (be, bh) in ((ch.asc, ("the Lagna", "लग्न")), (ch.sign["Moon"], ("the Moon", "चन्द्र"))):
        tenth = (base + 9) % 12
        there = [p for p, s in ch.sign.items() if s == tenth and p != "Moon"]
        if there and all(p in BENEFICS for p in there):
            n = (", ".join(_p(p)[0] for p in there), ", ".join(_p(p)[1] for p in there))
            return [_entry("amala", [(f"Only {n[0]} in the 10th from {be}", f"{bh} से दसवें भाव में केवल {n[1]}")])]
    return []


def sun_yogas(ch):
    out = []
    if ch.sign["Sun"] == ch.sign["Mercury"]:
        gap = abs((ch.lon["Mercury"] - ch.lon["Sun"] + 180) % 360 - 180)
        if gap > COMBUST_MERCURY:
            out.append(_entry("budha_aditya", [(f"Sun and Mercury together in {_s(ch.sign['Sun'])[0]}, Mercury "
                                                f"{gap:.0f}° from the Sun",
                                                f"सूर्य और बुध {_s(ch.sign['Sun'])[1]} राशि में साथ, बुध सूर्य से "
                                                f"{gap:.0f}° दूर")]))
    five = ("Mars", "Mercury", "Jupiter", "Venus", "Saturn")
    second = [p for p in five if _count(ch.sign["Sun"], ch.sign[p]) == 2]
    twelfth = [p for p in five if _count(ch.sign["Sun"], ch.sign[p]) == 12]
    names = lambda ps: (", ".join(_p(p)[0] for p in ps), ", ".join(_p(p)[1] for p in ps))
    if second and twelfth:
        a, b = names(second), names(twelfth)
        out.append(_entry("ubhayachari", [(f"{a[0]} in the 2nd and {b[0]} in the 12th from the Sun",
                                           f"सूर्य से दूसरे भाव में {a[1]} और बारहवें में {b[1]}")]))
    elif second:
        a = names(second)
        out.append(_entry("vesi", [(f"{a[0]} in the 2nd from the Sun", f"सूर्य से दूसरे भाव में {a[1]}")]))
    elif twelfth:
        b = names(twelfth)
        out.append(_entry("vasi", [(f"{b[0]} in the 12th from the Sun", f"सूर्य से बारहवें भाव में {b[1]}")]))
    return out


def _lord_pair_reason(ch, a, ha, b, hb, how):
    la, lb = _p(a), _p(b)
    hae = "/".join(_ord(h) for h in ha)
    hbe = "/".join(_ord(h) for h in hb)
    hah = "/".join(str(h) for h in ha)
    hbh = "/".join(str(h) for h in hb)
    return (f"{la[0]} (lord of {hae}) and {lb[0]} (lord of {hbe}) are {LINK_TEXT[how][0]}",
            f"{la[1]} ({hah} भाव का स्वामी) और {lb[1]} ({hbh} भाव का स्वामी) {LINK_TEXT[how][1]}")


def _houses_ruled(ch, planet):
    return [h for h in range(1, 13) if ch.lord(h) == planet]


def _linked_pairs(ch, group_a, group_b):
    """Distinct planet pairs where one rules a house in group_a, the other one in group_b, and they are linked."""
    seen, out = set(), []
    for ha in sorted(group_a):
        for hb in sorted(group_b):
            a, b = ch.lord(ha), ch.lord(hb)
            if a == b or frozenset((a, b)) in seen:
                continue
            how = ch.link(a, b)
            if how:
                seen.add(frozenset((a, b)))
                ra = [h for h in _houses_ruled(ch, a) if h in group_a | group_b]
                rb = [h for h in _houses_ruled(ch, b) if h in group_a | group_b]
                out.append(_lord_pair_reason(ch, a, ra, b, rb, how))
    return out


def raj_dhana(ch):
    out = []
    raj = _linked_pairs(ch, KENDRA, TRIKONA)
    if raj:
        out.append(_entry("raj", raj))
    for p in SEVEN:
        ruled = _houses_ruled(ch, p)
        if p in ("Sun", "Moon") or not (set(ruled) & {4, 7, 10} and set(ruled) & {5, 9}):
            continue
        if ch.house(p) in KENDRA | TRIKONA:
            en, hi = _in(p, ch)
            out.append(_entry("yogakaraka", [(f"{_p(p)[0]} rules the {_ord(ruled[0])} and {_ord(ruled[1])}; {en}",
                                              f"{_p(p)[1]} {ruled[0]} और {ruled[1]} भाव का स्वामी; {hi}")]))
    dhana = _linked_pairs(ch, {2, 11}, TRIKONA)
    pair_2_11 = _linked_pairs(ch, {2}, {11})
    if dhana or pair_2_11:
        out.append(_entry("dhana", dhana + [r for r in pair_2_11 if r not in dhana]))
    for key, h in (("harsha", 6), ("sarala", 8), ("vimala", 12)):
        lord = ch.lord(h)
        if ch.house(lord) in DUSTHANA:
            en, hi = _in(lord, ch)
            out.append(_entry(key, [(f"Lord of the {_ord(h)}: {en}", f"{HI_ORD[h]} भाव का स्वामी: {hi}")]))
    return out


def neecha_bhanga(ch):
    reasons = []
    for p in SEVEN:
        s = ch.sign[p]
        if DEBIL[p] != s:
            continue
        helpers = []
        for helper, what in ((LORD[s], ("lord of its sign", "राशि स्वामी")),
                             (EXALTED_IN.get(s), ("planet exalted in that sign", "उस राशि में उच्च होने वाला ग्रह"))):
            if not helper or helper == p:
                continue
            for base, (be, bh) in ((ch.asc, ("Lagna", "लग्न")), (ch.sign["Moon"], ("Moon", "चन्द्र"))):
                n = _count(base, ch.sign[helper])
                if n in KENDRA:
                    helpers.append((f"{_p(helper)[0]} ({what[0]}) is in a kendra from the {be}",
                                    f"{_p(helper)[1]} ({what[1]}) {bh} से केन्द्र में"))
                    break
        if helpers:
            pe, ph = _p(p)
            se, sh = _s(s)
            reasons.append((f"{pe} is debilitated in {se}; " + "; ".join(h[0] for h in helpers),
                            f"{ph} {sh} में नीच; " + "; ".join(h[1] for h in helpers)))
    return [_entry("neecha_bhanga", reasons)] if reasons else []


def parivartana(ch):
    out = {}
    for i, a in enumerate(SEVEN):
        for b in SEVEN[i + 1:]:
            if LORD[ch.sign[a]] == b and LORD[ch.sign[b]] == a and ch.sign[a] != ch.sign[b]:
                ha, hb = ch.house(a), ch.house(b)
                key = ("dainya_parivartana" if {ha, hb} & DUSTHANA else
                       "khala_parivartana" if 3 in (ha, hb) else "maha_parivartana")
                out.setdefault(key, []).append(
                    (f"{_p(a)[0]} in {_house_en(ha)} and {_p(b)[0]} in {_house_en(hb)} have exchanged signs",
                     f"{_p(a)[1]} {_house_hi(ha)} में और {_p(b)[1]} {_house_hi(hb)} में, परस्पर राशि परिवर्तन"))
    return [_entry(k, r) for k, r in out.items()]


def lakshmi(ch):
    nine, one = ch.lord(9), ch.lord(1)
    if ch.own_or_exalted(nine) and ch.house(nine) in KENDRA | TRIKONA:
        if ch.own_or_exalted(one) or ch.house(one) in KENDRA | TRIKONA:
            return [_entry("lakshmi", [(f"9th lord {_in(nine, ch)[0]}; Lagna lord {_in(one, ch)[0]}",
                                        f"भाग्येश {_in(nine, ch)[1]}; लग्नेश {_in(one, ch)[1]}")])]
    return []


def saraswati(ch):
    good = KENDRA | TRIKONA | {2}
    if all(ch.house(p) in good for p in ("Jupiter", "Venus", "Mercury")):
        js = ch.sign["Jupiter"]
        if ch.own_or_exalted("Jupiter") or LORD[js] in FRIENDS["Jupiter"]:
            return [_entry("saraswati", [_in(p, ch) for p in ("Jupiter", "Venus", "Mercury")])]
    return []


def shakata(ch):
    n = _count(ch.sign["Jupiter"], ch.sign["Moon"])
    if n in (6, 8):
        r = [(f"Moon is in the {_ord(n)} from Jupiter", f"चन्द्र गुरु से {HI_ORD[n]} भाव में")]
        if ch.house("Moon") in KENDRA:
            r.append(("Moon in a kendra from the Lagna cancels it", "लग्न से केन्द्र में चन्द्र इसे भंग करता है"))
            return [_entry("shakata", r, "cancelled")]
        return [_entry("shakata", r)]
    return []


def find_yogas(signs, lons, asc):
    """All yogas in the chart, in ORDER. signs/lons need the seven planets plus Rahu and Ketu."""
    if any(p not in signs or p not in lons for p in SEVEN):
        return []
    ch = Chart(signs, lons, asc)
    found = (mahapurusha(ch) + moon_yogas(ch) + amala(ch) + sun_yogas(ch) + raj_dhana(ch) + neecha_bhanga(ch)
             + parivartana(ch) + lakshmi(ch) + saraswati(ch) + shakata(ch))
    return sorted(found, key=lambda y: ORDER.index(y["key"]))


def chart_from_kundali(k):
    """(signs, lons, asc) from a saved Kundali, or None when its positions are missing."""
    d1 = k.planetary_positions or {}
    lons = {}
    for name in SEVEN + ("Rahu", "Ketu"):
        lon = (d1.get(name) or {}).get("longitude_sidereal")
        if lon is None:
            return None
        lons[name] = float(lon) % 360
    asc_lon = (k.ascendant or {}).get("asc_sidereal")
    if asc_lon is not None:
        asc = int(float(asc_lon) // 30) % 12
    else:
        asc = i18n.sign_index((k.ascendant or {}).get("sign_sidereal", ""))
        if asc is None:
            return None
    return {n: int(l // 30) for n, l in lons.items()}, lons, asc
