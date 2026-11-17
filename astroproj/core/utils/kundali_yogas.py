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
                ("Mars is strong (in its own or exaltation sign) and sits in a kendra, one of the four pillar houses "
                 "of the chart (1st, 4th, 7th, 10th). Mars stands for courage and drive, so this raises the chance "
                 "of boldness, leadership and physical energy, and suits work with land and property, police, army, "
                 "engineering or sport. It shows most in the Mars dasha.",
                 "मंगल बलवान (स्वराशि या उच्च) होकर केन्द्र (1, 4, 7, 10 - कुण्डली के चार स्तम्भ भाव) में है। मंगल साहस "
                 "और ऊर्जा का ग्रह है, अतः साहस, नेतृत्व और शारीरिक बल की सम्भावना बढ़ती है; भूमि-सम्पत्ति, पुलिस, सेना, "
                 "इंजीनियरिंग या खेल के कार्य अनुकूल रहते हैं। इसका फल मुख्यतः मंगल की दशा में दिखता है।")),
    "bhadra": (("Bhadra Yoga", "भद्र योग"), "mahapurusha",
               ("Mercury is strong (in its own or exaltation sign) and sits in a kendra (1st, 4th, 7th, 10th). "
                "Mercury stands for intellect and speech, so this raises the chance of a sharp mind, good speech "
                "and skill in trade, accounts, writing and study. It shows most in the Mercury dasha. This is a "
                "good yoga of Mercury and has nothing to do with the panchang's Bhadra (Vishti karana).",
                "बुध बलवान (स्वराशि या उच्च) होकर केन्द्र (1, 4, 7, 10) में है। बुध बुद्धि और वाणी का ग्रह है, अतः तीक्ष्ण "
                "बुद्धि, अच्छी वाणी और व्यापार, लेखा, लेखन व अध्ययन में कुशलता की सम्भावना बढ़ती है। फल मुख्यतः बुध की दशा "
                "में। यह बुध का शुभ योग है; पंचांग की भद्रा (विष्टि करण) से इसका कोई सम्बन्ध नहीं।")),
    "hamsa": (("Hamsa Yoga", "हंस योग"), "mahapurusha",
              ("Jupiter is strong (in its own or exaltation sign) and sits in a kendra (1st, 4th, 7th, 10th). "
               "Jupiter stands for wisdom and guidance, so this raises the chance of sound judgement, an ethical "
               "nature and respect from others, and suits teaching, law, finance, advice or spiritual work. It "
               "shows most in the Jupiter dasha.",
               "गुरु बलवान (स्वराशि या उच्च) होकर केन्द्र (1, 4, 7, 10) में है। गुरु ज्ञान और मार्गदर्शन का ग्रह है, अतः "
               "अच्छे विवेक, धार्मिक स्वभाव और सम्मान की सम्भावना बढ़ती है; शिक्षा, विधि, वित्त, परामर्श या आध्यात्मिक कार्य "
               "अनुकूल रहते हैं। फल मुख्यतः गुरु की दशा में।")),
    "malavya": (("Malavya Yoga", "मालव्य योग"), "mahapurusha",
                ("Venus is strong (in its own or exaltation sign) and sits in a kendra (1st, 4th, 7th, 10th). "
                 "Venus stands for comfort, relationships and art, so this raises the chance of comforts, vehicles, "
                 "harmony in married life and a taste for art, music, design and beauty. It shows most in the "
                 "Venus dasha.",
                 "शुक्र बलवान (स्वराशि या उच्च) होकर केन्द्र (1, 4, 7, 10) में है। शुक्र सुख, सम्बन्ध और कला का ग्रह है, अतः "
                 "सुख-सुविधा, वाहन, दाम्पत्य में सामंजस्य और कला, संगीत, डिज़ाइन व सौन्दर्य में रुचि की सम्भावना बढ़ती है। "
                 "फल मुख्यतः शुक्र की दशा में।")),
    "shasha": (("Shasha Yoga", "शश योग"), "mahapurusha",
               ("Saturn is strong (in its own or exaltation sign) and sits in a kendra (1st, 4th, 7th, 10th). "
                "Saturn stands for discipline and endurance, so this raises the chance of patience, organising "
                "ability and authority over many people. Rewards tend to come later in life but last. It shows "
                "most in the Saturn dasha.",
                "शनि बलवान (स्वराशि या उच्च) होकर केन्द्र (1, 4, 7, 10) में है। शनि अनुशासन और धैर्य का ग्रह है, अतः धैर्य, "
                "संगठन क्षमता और अनेक लोगों पर अधिकार की सम्भावना बढ़ती है। फल प्रायः देर से पर स्थायी मिलता है; मुख्यतः "
                "शनि की दशा में।")),
    "gaja_kesari": (("Gaja Kesari Yoga", "गजकेसरी योग"), "chandra",
                    ("Jupiter is in a kendra (1st, 4th, 7th or 10th sign) counted from the Moon. Jupiter, the planet "
                     "of wisdom, supports the Moon, the mind, so this raises the chance of good judgement, a "
                     "respected name and help from others when it is needed. A strong Jupiter gives more; a "
                     "debilitated Jupiter gives little.",
                     "चन्द्र से गिनने पर गुरु केन्द्र (1, 4, 7 या 10वीं राशि) में है। ज्ञान का ग्रह गुरु मन (चन्द्र) को सहारा "
                     "देता है, अतः अच्छे विवेक, सम्मानित नाम और आवश्यकता पर दूसरों की सहायता की सम्भावना बढ़ती है। बलवान "
                     "गुरु अधिक फल देता है, नीच गुरु बहुत कम।")),
    "sunapha": (("Sunapha Yoga", "सुनफा योग"), "chandra",
                ("A planet (not the Sun, Rahu or Ketu) is in the sign just after the Moon. Planets next to the Moon "
                 "support the mind, so this raises the chance of self-earned means, confidence and a good name. "
                 "The planet gives its own colour to the result: see below whether yours is gentle or harsh.",
                 "चन्द्र से अगली (दूसरी) राशि में कोई ग्रह (सूर्य, राहु, केतु के अतिरिक्त) है। चन्द्र के पास के ग्रह मन को "
                 "सहारा देते हैं, अतः स्वअर्जित साधन, आत्मविश्वास और अच्छी प्रतिष्ठा की सम्भावना बढ़ती है। फल उस ग्रह के "
                 "स्वभाव पर निर्भर है: नीचे देखें कि आपका ग्रह सौम्य है या क्रूर।")),
    "anapha": (("Anapha Yoga", "अनफा योग"), "chandra",
               ("A planet (not the Sun, Rahu or Ketu) is in the sign just before the Moon. This raises the chance "
                "of good health, pleasing manners, comforts and a self-content nature. The planet gives its own "
                "colour to the result: see below whether yours is gentle or harsh.",
                "चन्द्र से पिछली (बारहवीं) राशि में कोई ग्रह (सूर्य, राहु, केतु के अतिरिक्त) है। इससे अच्छे स्वास्थ्य, सौम्य "
                "व्यवहार, सुख और सन्तोषी स्वभाव की सम्भावना बढ़ती है। फल उस ग्रह के स्वभाव पर निर्भर है: नीचे देखें कि "
                "आपका ग्रह सौम्य है या क्रूर।")),
    "durudhara": (("Durudhara Yoga", "दुरुधरा योग"), "chandra",
                  ("Planets (not the Sun, Rahu or Ketu) sit in the signs on both sides of the Moon. The mind is "
                   "well supported, which raises the chance of steady resources, comforts, vehicles and a generous "
                   "nature. See below whether the planets are gentle or harsh.",
                   "चन्द्र के दोनों ओर की राशियों में ग्रह (सूर्य, राहु, केतु के अतिरिक्त) हैं। मन को दोनों ओर से सहारा मिलता "
                   "है, अतः स्थिर साधन, सुख, वाहन और उदार स्वभाव की सम्भावना बढ़ती है। नीचे देखें कि ग्रह सौम्य हैं या क्रूर।")),
    "adhi": (("Adhi Yoga", "अधि योग"), "chandra",
             ("Gentle planets (Mercury, Jupiter, Venus) sit in the 6th, 7th and 8th signs from the Moon with no harsh "
              "planet there. This raises the chance of a position of trust, leading others, a comfortable life and "
              "the upper hand over opponents.",
              "चन्द्र से छठी, सातवीं और आठवीं राशि में सौम्य ग्रह (बुध, गुरु, शुक्र) हैं और वहाँ कोई क्रूर ग्रह नहीं। इससे "
              "विश्वास के पद, नेतृत्व, सुखी जीवन और विरोधियों पर बढ़त की सम्भावना बढ़ती है।")),
    "chandra_mangala": (("Chandra-Mangala Yoga", "चन्द्र-मंगल योग"), "chandra",
                        ("The Moon (mind) and Mars (drive) are in the same sign. This raises the chance of "
                         "enterprise, quick decisions and earning through trade or one's own business. The mind can "
                         "also be restless or quick to anger, so patience helps.",
                         "चन्द्र (मन) और मंगल (ऊर्जा) एक ही राशि में हैं। इससे उद्यम, शीघ्र निर्णय और व्यापार या अपने काम से "
                         "धनार्जन की सम्भावना बढ़ती है। मन अस्थिर या क्रोधी भी हो सकता है, अतः धैर्य लाभ देता है।")),
    "amala": (("Amala Yoga", "अमला योग"), "other",
              ("Only gentle planets (Mercury, Jupiter, Venus) are in the 10th sign, the house of work, from the "
               "Lagna or the Moon. This raises the chance of a clean reputation, honest work and good deeds that "
               "people remember.",
               "लग्न या चन्द्र से दसवीं राशि (कर्म भाव) में केवल सौम्य ग्रह (बुध, गुरु, शुक्र) हैं। इससे निर्मल यश, ईमानदार "
               "कार्य और स्मरणीय सत्कर्म की सम्भावना बढ़ती है।")),
    "budha_aditya": (("Budha-Aditya Yoga", "बुधादित्य योग"), "surya",
                     ("The Sun and Mercury are in the same sign, and Mercury is far enough from the Sun not to be "
                      "burnt (combust). This raises the chance of a sharp intellect, clear communication and success "
                      "in study, accounts and administration.",
                      "सूर्य और बुध एक ही राशि में हैं और बुध सूर्य से इतना दूर है कि अस्त नहीं। इससे तीक्ष्ण बुद्धि, स्पष्ट "
                      "वाणी और अध्ययन, लेखा व प्रशासन में सफलता की सम्भावना बढ़ती है।")),
    "vesi": (("Vesi Yoga", "वेशि योग"), "surya",
             ("A planet (not the Moon, Rahu or Ketu) is in the sign just after the Sun. The Sun shows self and "
              "status; this planet shapes how you pursue them. A gentle planet raises the chance of a truthful, "
              "balanced nature and good fortune; a harsh planet gives hard work and bluntness. See below which "
              "kind yours is.",
              "सूर्य से अगली (दूसरी) राशि में कोई ग्रह (चन्द्र, राहु, केतु के अतिरिक्त) है। सूर्य आत्मा और प्रतिष्ठा है; यह "
              "ग्रह बताता है कि आप उन्हें कैसे पाते हैं। सौम्य ग्रह हो तो सत्यनिष्ठ, सन्तुलित स्वभाव और भाग्य की सम्भावना; "
              "क्रूर ग्रह हो तो कठोर परिश्रम और रूखापन। नीचे देखें आपका ग्रह किस प्रकार का है।")),
    "vasi": (("Vasi Yoga", "वाशि योग"), "surya",
             ("A planet (not the Moon, Rahu or Ketu) is in the sign just before the Sun. A gentle planet raises the "
              "chance of generosity, skill and respect; a harsh planet gives success only through strain and some "
              "loss. See below which kind yours is.",
              "सूर्य से पिछली (बारहवीं) राशि में कोई ग्रह (चन्द्र, राहु, केतु के अतिरिक्त) है। सौम्य ग्रह हो तो उदारता, "
              "कुशलता और सम्मान की सम्भावना; क्रूर ग्रह हो तो सफलता परिश्रम और कुछ हानि के साथ। नीचे देखें आपका ग्रह "
              "किस प्रकार का है।")),
    "ubhayachari": (("Ubhayachari Yoga", "उभयचरी योग"), "surya",
                    ("Planets (not the Moon, Rahu or Ketu) sit on both sides of the Sun. With gentle planets this "
                     "raises the chance of a capable, balanced person who rises in status; with harsh planets the "
                     "rise comes through struggle. See below which kind yours are.",
                     "सूर्य के दोनों ओर ग्रह (चन्द्र, राहु, केतु के अतिरिक्त) हैं। सौम्य ग्रह हों तो समर्थ, सन्तुलित व्यक्ति और "
                     "पद में उन्नति की सम्भावना; क्रूर ग्रह हों तो उन्नति संघर्ष से। नीचे देखें आपके ग्रह किस प्रकार के हैं।")),
    "dharma_karma": (("Dharma-Karmadhipati Yoga", "धर्म-कर्माधिपति योग"), "raj",
                     ("The lord of the 9th house (fortune, dharma) and the lord of the 10th house (career, karma) are "
                      "connected. BPHS ranks this the finest of the Raj Yogas: fortune backs your work, which raises "
                      "the chance of a respected career, steady promotion and recognition. It acts most in the dashas "
                      "of these two planets, and more when they are strong.",
                      "नवम भाव (भाग्य, धर्म) का स्वामी और दशम भाव (कर्म, पद) का स्वामी आपस में जुड़े हैं। बृहत् पाराशर होरा "
                      "शास्त्र इसे राज योगों में श्रेष्ठ मानता है: भाग्य आपके कर्म का साथ देता है, जिससे सम्मानजनक करियर, "
                      "नियमित उन्नति और मान्यता की सम्भावना बढ़ती है। फल मुख्यतः इन दोनों ग्रहों की दशा में, और ग्रह बलवान "
                      "हों तो अधिक।")),
    "raj": (("Raj Yoga", "राज योग"), "raj",
            ("The lord (ruling planet) of a kendra house - 1st, 4th, 7th, 10th: self, home, partner, career - is "
             "connected with the lord of a trikona house - 1st, 5th, 9th: intelligence and fortune - by sitting "
             "together, exchanging signs or looking at each other. Effort meets luck, which raises the chance of "
             "promotion, responsibility and recognition. It acts most in the dashas of the planets named below, "
             "and more when they are strong.",
             "किसी केन्द्र भाव (1, 4, 7, 10: स्वयं, घर, जीवनसाथी, कर्म) का स्वामी ग्रह किसी त्रिकोण भाव (1, 5, 9: बुद्धि "
             "और भाग्य) के स्वामी से जुड़ा है: साथ बैठकर, राशि परिवर्तन से या परस्पर दृष्टि से। परिश्रम और भाग्य मिलते हैं, "
             "जिससे पदोन्नति, उत्तरदायित्व और मान्यता की सम्भावना बढ़ती है। फल मुख्यतः नीचे लिखे ग्रहों की दशा में, और "
             "ग्रह बलवान हों तो अधिक।")),
    "yogakaraka": (("Yogakaraka", "योगकारक"), "raj",
                   ("For your Lagna one planet rules both a kendra and a trikona, so it alone joins effort with luck, "
                    "and it sits in a good house (kendra or trikona). Its dasha tends to be one of the most "
                    "productive periods of life.",
                    "आपके लग्न के लिए एक ही ग्रह केन्द्र और त्रिकोण दोनों का स्वामी है, अतः अकेले ही परिश्रम और भाग्य को "
                    "जोड़ता है, और वह शुभ भाव (केन्द्र या त्रिकोण) में है। इसकी दशा प्रायः जीवन के सबसे फलदायी समयों में "
                    "होती है।")),
    "dhana": (("Dhana Yoga", "धन योग"), "dhana",
              ("The lords of the money houses - 2nd (savings) and 11th (income) - are connected with each other or "
               "with the lords of the 1st, 5th or 9th (self, intelligence, fortune), or a money-house lord is strong in its "
               "own or exaltation sign. This raises the chance of "
               "earning and saving well, mostly in the dashas of the planets named below.",
               "धन भावों - दूसरा (संचय) और ग्यारहवाँ (आय) - के स्वामी आपस में या 1, 5, 9 (स्वयं, बुद्धि, भाग्य) के "
               "स्वामी से जुड़े हैं, या धन भाव का स्वामी स्वराशि या उच्च में बलवान है। इससे अच्छी कमाई और बचत की सम्भावना बढ़ती है, मुख्यतः नीचे लिखे ग्रहों की दशा में।")),
    "harsha": (("Harsha Yoga (Viparita Raj)", "हर्ष योग (विपरीत राज)"), "raj",
               ("The lord of the 6th house (debts, illness, rivals) sits in another difficult house (6th, 8th or "
                "12th), so one trouble cancels another. This raises the chance of resilience, good health and "
                "winning over opponents, often after a hard phase.",
                "छठे भाव (ऋण, रोग, शत्रु) का स्वामी किसी दूसरे कठिन भाव (6, 8, 12) में है, अतः एक कष्ट दूसरे को काटता है। "
                "इससे सहनशक्ति, अच्छे स्वास्थ्य और विरोधियों पर विजय की सम्भावना बढ़ती है, प्रायः एक कठिन दौर के बाद।")),
    "sarala": (("Sarala Yoga (Viparita Raj)", "सरल योग (विपरीत राज)"), "raj",
               ("The lord of the 8th house (sudden events, obstacles) sits in a difficult house (6th, 8th or 12th), "
                "so one trouble cancels another. This raises the chance of long life, fearlessness and recovering "
                "well from setbacks.",
                "आठवें भाव (आकस्मिक घटनाएँ, बाधाएँ) का स्वामी कठिन भाव (6, 8, 12) में है, अतः एक कष्ट दूसरे को काटता है। "
                "इससे दीर्घायु, निर्भयता और बाधाओं से अच्छी तरह उबरने की सम्भावना बढ़ती है।")),
    "vimala": (("Vimala Yoga (Viparita Raj)", "विमल योग (विपरीत राज)"), "raj",
               ("The lord of the 12th house (expenses, losses) sits in a difficult house (6th, 8th or 12th), so one "
                "trouble cancels another. This raises the chance of careful spending, savings, independence and "
                "good conduct.",
                "बारहवें भाव (व्यय, हानि) का स्वामी कठिन भाव (6, 8, 12) में है, अतः एक कष्ट दूसरे को काटता है। इससे "
                "सोच-समझकर खर्च, बचत, स्वतन्त्रता और सदाचार की सम्भावना बढ़ती है।")),
    "neecha_bhanga": (("Neecha Bhanga Raj Yoga", "नीचभंग राज योग"), "raj",
                      ("A planet is in its sign of weakness (debilitated), but its weakness is cancelled because "
                       "the lord of that sign, or the planet exalted there, sits in a kendra. The matters of that "
                       "planet can be a struggle early on and tend to turn into a strength later.",
                       "कोई ग्रह अपनी नीच राशि में है, पर उस राशि का स्वामी या वहाँ उच्च होने वाला ग्रह केन्द्र में है, अतः "
                       "नीचत्व भंग होता है। उस ग्रह के विषयों में आरम्भ में संघर्ष और बाद में वही शक्ति बनने की सम्भावना।")),
    "maha_parivartana": (("Maha Parivartana Yoga", "महा परिवर्तन योग"), "raj",
                         ("Two planets sit in each other's signs and both houses involved are good ones (not the "
                          "3rd, 6th, 8th or 12th). The two areas of life named below support each other, which "
                          "raises the chance of growth in both.",
                          "दो ग्रह एक-दूसरे की राशि में हैं और दोनों भाव शुभ हैं (3, 6, 8, 12 नहीं)। नीचे लिखे जीवन के दोनों "
                          "क्षेत्र एक-दूसरे को बल देते हैं, जिससे दोनों में उन्नति की सम्भावना बढ़ती है।")),
    "khala_parivartana": (("Khala Parivartana Yoga", "खल परिवर्तन योग"), "other",
                          ("Two planets sit in each other's signs and one of the houses is the 3rd (effort, "
                           "courage). Results are mixed: gains come through your own effort, with ups and downs.",
                           "दो ग्रह एक-दूसरे की राशि में हैं और एक भाव तीसरा (परिश्रम, साहस) है। फल मिश्रित: लाभ अपने "
                           "प्रयास से, उतार-चढ़ाव के साथ।")),
    "dainya_parivartana": (("Dainya Parivartana Yoga", "दैन्य परिवर्तन योग"), "challenge",
                           ("Two planets sit in each other's signs and one of the houses is the 6th, 8th or 12th "
                            "(difficulties). The matters of the other house can face delays or obstacles; steady "
                            "effort and patience reduce them.",
                            "दो ग्रह एक-दूसरे की राशि में हैं और एक भाव छठा, आठवाँ या बारहवाँ (कठिनाई) है। दूसरे भाव के "
                            "विषयों में विलम्ब या बाधा की सम्भावना; निरन्तर प्रयास और धैर्य से कम होती है।")),
    "lakshmi": (("Lakshmi Yoga", "लक्ष्मी योग"), "dhana",
                ("The lord of the 9th (fortune) is strong in its own or exaltation sign and sits in a kendra or "
                 "trikona, and the Lagna lord (you) is also well placed. This raises the chance of wealth, grace, "
                 "a good family life and luck.",
                 "नवम भाव (भाग्य) का स्वामी स्वराशि या उच्च होकर केन्द्र या त्रिकोण में है और लग्नेश (आप) भी अच्छी स्थिति में "
                 "है। इससे धन, श्री, सुखी पारिवारिक जीवन और भाग्य की सम्भावना बढ़ती है।")),
    "saraswati": (("Saraswati Yoga", "सरस्वती योग"), "other",
                  ("Jupiter, Venus and Mercury, the planets of learning, art and speech, are all in good houses "
                   "(kendra, trikona or the 2nd) and Jupiter is strong. This raises the chance of success in "
                   "learning, arts, writing, music and speech.",
                   "विद्या, कला और वाणी के ग्रह गुरु, शुक्र और बुध सभी शुभ भावों (केन्द्र, त्रिकोण या दूसरे) में हैं और गुरु "
                   "बलवान है। इससे विद्या, कला, लेखन, संगीत और वाणी में सफलता की सम्भावना बढ़ती है।")),
    "shakata": (("Shakata Yoga", "शकट योग"), "challenge",
                ("The Moon is in the 6th or 8th sign from Jupiter. Fortune tends to rise and fall like a cart wheel: "
                 "gains and setbacks alternate, so savings and steady habits matter. It is cancelled when the Moon "
                 "is in a kendra from the Lagna.",
                 "चन्द्र गुरु से छठी या आठवीं राशि में है। भाग्य गाड़ी के पहिये की तरह ऊपर-नीचे हो सकता है: लाभ और हानि "
                 "बारी-बारी आते हैं, अतः बचत और नियमित आदतें महत्वपूर्ण हैं। लग्न से केन्द्र में चन्द्र हो तो यह भंग होता है।")),
}
SOURCES = ("BPHS", "Phaladeepika", "Saravali")
ORDER = list(INFO)


def _entry(key, reasons, strength="full", planets=()):
    title, kind, meaning = INFO[key]
    return {"key": key, "name": title, "kind": kind, "good": kind != "challenge", "meaning": meaning,
            "reasons": reasons, "strength": strength, "planets": list(dict.fromkeys(planets))}


GENTLE = ("Mercury", "Jupiter", "Venus")
HARSH = ("Mars", "Saturn")


def _nature(planets):
    """For yogas whose result takes the colour of the planets (Sunapha ... Ubhayachari): one plain sentence saying
    whether they are natural benefics (gentle) or malefics (harsh), and the strength label that follows."""
    gentle = [p for p in planets if p in GENTLE]
    harsh = [p for p in planets if p in HARSH]
    g = (", ".join(_p(p)[0] for p in gentle), ", ".join(_p(p)[1] for p in gentle))
    h = (", ".join(_p(p)[0] for p in harsh), ", ".join(_p(p)[1] for p in harsh))
    if not harsh:
        return (f"{g[0]}: natural benefic (gentle planet), so this is the favourable form of the yoga",
                f"{g[1]}: नैसर्गिक शुभ (सौम्य ग्रह), अतः यह योग का शुभ रूप है"), "full"
    if not gentle:
        return (f"{h[0]}: natural malefic (harsh planet), so results come through hard work and can bring friction",
                f"{h[1]}: नैसर्गिक पाप (क्रूर ग्रह), अतः फल कठोर परिश्रम से और कुछ खिंचाव के साथ"), "mixed"
    return (f"{g[0]} gentle (benefic) and {h[0]} harsh (malefic): a mixed form, good results with some effort",
            f"{g[1]} सौम्य (शुभ) और {h[1]} क्रूर (पाप): मिश्रित रूप, कुछ परिश्रम के साथ शुभ फल"), "mixed"


def planet_strength(ch, planet):
    """(label, (English, Hindi) sentence) for one planet's plain dignity: strong, good, average or weak."""
    s = ch.sign[planet]
    pe, ph = _p(planet)
    se, sh = _s(s)
    gap = abs((ch.lon[planet] - ch.lon["Sun"] + 180) % 360 - 180) if planet != "Sun" else 99
    if EXALT.get(planet) == s:
        return "strong", (f"{pe}: strong (exalted in {se})", f"{ph}: बलवान ({sh} में उच्च)")
    if DEBIL.get(planet) == s:
        return "weak", (f"{pe}: weak (debilitated in {se})", f"{ph}: निर्बल ({sh} में नीच)")
    if planet in COMBUST and gap < COMBUST[planet] and (s in OWN.get(planet, ()) or EXALT.get(planet) == s):
        return "mixed", (f"{pe}: mixed ({'exalted' if EXALT.get(planet) == s else 'own sign'} {se} gives strength, "
                         f"but it is combust, {gap:.0f}° from the Sun)",
                         f"{ph}: मिश्रित ({'उच्च' if EXALT.get(planet) == s else 'स्वराशि'} {sh} बल देती है, पर सूर्य से "
                         f"{gap:.0f}° पर अस्त है)")
    if planet in COMBUST and gap < COMBUST[planet]:
        return "weak", (f"{pe}: weak (combust, {gap:.0f}° from the Sun)", f"{ph}: निर्बल (अस्त, सूर्य से {gap:.0f}°)")
    if s in OWN.get(planet, ()):
        return "strong", (f"{pe}: strong (own sign {se})", f"{ph}: बलवान (स्वराशि {sh})")
    if LORD[s] in FRIENDS.get(planet, ()):
        return "good", (f"{pe}: good (in a friend's sign, {se})", f"{ph}: अच्छा (मित्र राशि {sh} में)")
    return "average", (f"{pe}: average (in {se})", f"{ph}: सामान्य ({sh} में)")


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
                reasons.append((f"{_p(planet)[0]} is combust ({gap:.0f}° from the Sun): its sign gives strength but "
                                f"combustion reduces the results, so this yoga is mixed",
                                f"{_p(planet)[1]} अस्त है (सूर्य से {gap:.0f}°): राशि बल देती है पर अस्त होने से फल घटता "
                                f"है, अतः यह योग मिश्रित है"))
            out.append(_entry(key, reasons, "mixed" if weak else "full", [planet]))
    return out


def moon_yogas(ch):
    out = []
    j = ch.from_moon("Jupiter")
    if j in KENDRA:
        weak = ch.sign["Jupiter"] == DEBIL["Jupiter"]
        r = [(f"Jupiter is in the {_ord(j)} from the Moon", f"गुरु चन्द्र से {HI_ORD[j]} भाव में")]
        if weak:
            r.append(("Jupiter is debilitated, so the yoga is weak", "गुरु नीच राशि में है, इसलिए योग निर्बल है"))
        out.append(_entry("gaja_kesari", r, "weak" if weak else "full", ["Jupiter", "Moon"]))
    five = ("Mars", "Mercury", "Jupiter", "Venus", "Saturn")
    second = [p for p in five if ch.from_moon(p) == 2]
    twelfth = [p for p in five if ch.from_moon(p) == 12]
    names = lambda ps: (", ".join(_p(p)[0] for p in ps), ", ".join(_p(p)[1] for p in ps))
    m = ch.sign["Moon"]
    moon, nxt, prv = _s(m), _s((m + 1) % 12), _s((m - 1) % 12)
    if second or twelfth:
        note, level = _nature(second + twelfth)
    if second and twelfth:
        a, b = names(second), names(twelfth)
        out.append(_entry("durudhara", [(f"Moon in {moon[0]}; {a[0]} in the next sign ({nxt[0]}) and {b[0]} in the "
                                         f"sign before it ({prv[0]})",
                                         f"चन्द्र {moon[1]} में; अगली राशि ({nxt[1]}) में {a[1]} और पिछली राशि "
                                         f"({prv[1]}) में {b[1]}"), note], level, second + twelfth))
    elif second:
        a = names(second)
        out.append(_entry("sunapha", [(f"Moon in {moon[0]}; {a[0]} in the next sign ({nxt[0]})",
                                       f"चन्द्र {moon[1]} में; अगली राशि ({nxt[1]}) में {a[1]}"), note], level, second))
    elif twelfth:
        b = names(twelfth)
        out.append(_entry("anapha", [(f"Moon in {moon[0]}; {b[0]} in the sign before it ({prv[0]})",
                                      f"चन्द्र {moon[1]} में; पिछली राशि ({prv[1]}) में {b[1]}"), note], level, twelfth))
    adhi = [p for p in BENEFICS if ch.from_moon(p) in (6, 7, 8)]
    spoilt = [p for p in MALEFICS if p in ch.sign and ch.from_moon(p) in (6, 7, 8)]
    if len(adhi) >= 2 and not spoilt:
        a = names(adhi)
        out.append(_entry("adhi", [(f"{a[0]} in the 6th-8th from the Moon, with no malefic there",
                                    f"चन्द्र से छठे-आठवें भावों में {a[1]}, वहाँ कोई पाप ग्रह नहीं")],
                          "full" if len(adhi) == 3 else "partial", adhi))
    if ch.sign["Moon"] == ch.sign["Mars"]:
        out.append(_entry("chandra_mangala", [_in("Moon", ch), _in("Mars", ch)], planets=["Moon", "Mars"]))
    return out


def amala(ch):
    for base, (be, bh) in ((ch.asc, ("the Lagna", "लग्न")), (ch.sign["Moon"], ("the Moon", "चन्द्र"))):
        tenth = (base + 9) % 12
        there = [p for p, s in ch.sign.items() if s == tenth and p != "Moon"]
        if there and all(p in BENEFICS for p in there):
            n = (", ".join(_p(p)[0] for p in there), ", ".join(_p(p)[1] for p in there))
            return [_entry("amala", [(f"Only {n[0]} in the 10th from {be}", f"{bh} से दसवें भाव में केवल {n[1]}")],
                           planets=there)]
    return []


def sun_yogas(ch):
    out = []
    if ch.sign["Sun"] == ch.sign["Mercury"]:
        gap = abs((ch.lon["Mercury"] - ch.lon["Sun"] + 180) % 360 - 180)
        if gap > COMBUST_MERCURY:
            out.append(_entry("budha_aditya", [(f"Sun and Mercury together in {_s(ch.sign['Sun'])[0]}, Mercury "
                                                f"{gap:.0f}° from the Sun",
                                                f"सूर्य और बुध {_s(ch.sign['Sun'])[1]} राशि में साथ, बुध सूर्य से "
                                                f"{gap:.0f}° दूर")], planets=["Sun", "Mercury"]))
    five = ("Mars", "Mercury", "Jupiter", "Venus", "Saturn")
    second = [p for p in five if _count(ch.sign["Sun"], ch.sign[p]) == 2]
    twelfth = [p for p in five if _count(ch.sign["Sun"], ch.sign[p]) == 12]
    names = lambda ps: (", ".join(_p(p)[0] for p in ps), ", ".join(_p(p)[1] for p in ps))
    m = ch.sign["Sun"]
    sun, nxt, prv = _s(m), _s((m + 1) % 12), _s((m - 1) % 12)
    if second or twelfth:
        note, level = _nature(second + twelfth)
    if second and twelfth:
        a, b = names(second), names(twelfth)
        out.append(_entry("ubhayachari", [(f"Sun in {sun[0]}; {a[0]} in the next sign ({nxt[0]}) and {b[0]} in the "
                                           f"sign before it ({prv[0]})",
                                           f"सूर्य {sun[1]} में; अगली राशि ({nxt[1]}) में {a[1]} और पिछली राशि "
                                           f"({prv[1]}) में {b[1]}"), note], level, second + twelfth))
    elif second:
        a = names(second)
        out.append(_entry("vesi", [(f"Sun in {sun[0]}; {a[0]} in the next sign ({nxt[0]})",
                                    f"सूर्य {sun[1]} में; अगली राशि ({nxt[1]}) में {a[1]}"), note], level, second))
    elif twelfth:
        b = names(twelfth)
        out.append(_entry("vasi", [(f"Sun in {sun[0]}; {b[0]} in the sign before it ({prv[0]})",
                                    f"सूर्य {sun[1]} में; पिछली राशि ({prv[1]}) में {b[1]}"), note], level, twelfth))
    return out


HOUSE_TOPIC = {1: ("self", "स्वयं"), 2: ("savings, family", "धन, कुटुम्ब"), 3: ("effort, siblings", "पराक्रम, भाई-बहन"),
               4: ("home, mother, comforts", "घर, माता, सुख"), 5: ("intelligence, children", "बुद्धि, सन्तान"),
               6: ("debts, illness, rivals", "ऋण, रोग, शत्रु"), 7: ("partner, partnerships", "जीवनसाथी, साझेदारी"),
               8: ("sudden events, longevity", "आकस्मिक घटनाएँ, आयु"), 9: ("fortune, father, dharma", "भाग्य, पिता, धर्म"),
               10: ("career, status", "कर्म, पद"), 11: ("income, gains", "आय, लाभ"), 12: ("expenses, foreign lands", "व्यय, विदेश")}


def _houses_text(hs):
    return (" and ".join(f"{_ord(h)} house: {HOUSE_TOPIC[h][0]}" for h in hs),
            " और ".join(f"{h}वें भाव: {HOUSE_TOPIC[h][1]}" for h in hs))


def _lord_pair_reason(ch, a, ha, b, hb, how):
    la, lb = _p(a), _p(b)
    ta, tb = _houses_text(ha), _houses_text(hb)
    where_en = (f"both in {_house_en(ch.house(a))}" if how == "conj" else
                f"{la[0]} in {_house_en(ch.house(a))}, {lb[0]} in {_house_en(ch.house(b))}")
    where_hi = (f"दोनों {_house_hi(ch.house(a))} में" if how == "conj" else
                f"{la[1]} {_house_hi(ch.house(a))} में, {lb[1]} {_house_hi(ch.house(b))} में")
    return (f"{la[0]} [lord of the {ta[0]}] and {lb[0]} [lord of the {tb[0]}] are {LINK_TEXT[how][0]}; {where_en}",
            f"{la[1]} [{ta[1]} का स्वामी] और {lb[1]} [{tb[1]} का स्वामी] {LINK_TEXT[how][1]}; {where_hi}")


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
                out.append((_lord_pair_reason(ch, a, ra, b, rb, how), (a, b)))
    return out


def raj_dhana(ch):
    out = []
    raj = _linked_pairs(ch, KENDRA, TRIKONA)
    dk = [x for x in raj if {ch.lord(9), ch.lord(10)} == set(x[1]) and ch.lord(9) != ch.lord(10)]
    if dk:
        out.append(_entry("dharma_karma", [r for r, _ in dk], planets=[p for _, pair in dk for p in pair]))
    raj = [x for x in raj if x not in dk]
    if raj:
        out.append(_entry("raj", [r for r, _ in raj], planets=[p for _, pair in raj for p in pair]))
    for p in SEVEN:
        ruled = _houses_ruled(ch, p)
        if p in ("Sun", "Moon") or not (set(ruled) & {4, 7, 10} and set(ruled) & {5, 9}):
            continue
        if ch.house(p) in KENDRA | TRIKONA:
            en, hi = _in(p, ch)
            out.append(_entry("yogakaraka", [(f"{_p(p)[0]} rules the {_ord(ruled[0])} and {_ord(ruled[1])}; {en}",
                                              f"{_p(p)[1]} {ruled[0]} और {ruled[1]} भाव का स्वामी; {hi}")],
                              planets=[p]))
    dhana = _linked_pairs(ch, {2, 11}, TRIKONA)
    pair_2_11 = _linked_pairs(ch, {2}, {11})
    both = dhana + [r for r in pair_2_11 if r not in dhana]
    reasons, planets, good = [r for r, _ in both], [p for _, pair in both for p in pair], bool(both)
    for h in dict.fromkeys(h for h in (2, 11) if ch.own_or_exalted(ch.lord(h))):
        lord = ch.lord(h)
        if h == 11 and ch.lord(2) == lord:
            continue                    # one planet ruling both: said once, under the 2nd
        dig = ("exalted in", "उच्च") if EXALT.get(lord) == ch.sign[lord] else ("in its own sign", "स्वराशि")
        at = ch.house(lord)
        se, sh = _s(ch.sign[lord])
        pe, ph = _p(lord)
        t, ta = HOUSE_TOPIC[h], HOUSE_TOPIC[at]
        if at in DUSTHANA:
            reasons.append((f"{pe}, lord of the {_ord(h)} house ({t[0]}), is strong {dig[0]} {se} but sits in "
                            f"{_house_en(at)} ({ta[0]}): money comes through effort, service or competition rather "
                            f"than easily",
                            f"{ph}, {HI_ORD[h]} भाव ({t[1]}) का स्वामी, {sh} में {dig[1]} होकर बलवान है पर "
                            f"{_house_hi(at)} ({ta[1]}) में है: धन परिश्रम, सेवा या प्रतिस्पर्धा से मिलता है, सहजता से नहीं"))
        else:
            good = True
            reasons.append((f"{pe}, lord of the {_ord(h)} house ({t[0]}), is strong {dig[0]} {se} in "
                            f"{_house_en(at)} ({ta[0]})",
                            f"{ph}, {HI_ORD[h]} भाव ({t[1]}) का स्वामी, {sh} में {dig[1]} होकर {_house_hi(at)} "
                            f"({ta[1]}) में बलवान"))
            sharing = [x for x, sg in ch.sign.items() if sg == ch.sign[lord] and x in MALEFICS and x != lord]
            if sharing:
                n = (", ".join(_p(x)[0] for x in sharing), ", ".join(_p(x)[1] for x in sharing))
                reasons.append((f"{n[0]} in the same house adds a harsher influence, so wealth may build steadily "
                                f"but not smoothly",
                                f"उसी भाव में {n[1]} कठोर प्रभाव जोड़ता है, अतः धन धीरे-धीरे बढ़ सकता है पर सहजता से नहीं"))
        planets.append(lord)
    if reasons:
        out.append(_entry("dhana", reasons, "full" if good else "partial", planets))
    for key, h in (("harsha", 6), ("sarala", 8), ("vimala", 12)):
        lord = ch.lord(h)
        if ch.house(lord) in DUSTHANA:
            en, hi = _in(lord, ch)
            r = [(f"Lord of the {_ord(h)}: {en}", f"{HI_ORD[h]} भाव का स्वामी: {hi}")]
            also = [x for x in _houses_ruled(ch, lord) if x != h]
            if also:
                t = _houses_text(also)
                r.append((f"{_p(lord)[0]} also rules the {t[0]}, so those matters too tend to come through effort "
                          f"and overcoming difficulty",
                          f"{_p(lord)[1]} {t[1]} का भी स्वामी है, अतः ये विषय भी परिश्रम और कठिनाई पार करके मिलते हैं"))
            out.append(_entry(key, r, planets=[lord]))
    return out


def neecha_bhanga(ch):
    reasons, planets = [], []
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
            planets.append(p)
    return [_entry("neecha_bhanga", reasons, planets=planets)] if reasons else []


def parivartana(ch):
    out = {}
    for i, a in enumerate(SEVEN):
        for b in SEVEN[i + 1:]:
            if LORD[ch.sign[a]] == b and LORD[ch.sign[b]] == a and ch.sign[a] != ch.sign[b]:
                ha, hb = ch.house(a), ch.house(b)
                key = ("dainya_parivartana" if {ha, hb} & DUSTHANA else
                       "khala_parivartana" if 3 in (ha, hb) else "maha_parivartana")
                ta, tb = HOUSE_TOPIC[ha], HOUSE_TOPIC[hb]
                out.setdefault(key, []).append((
                    (f"{_p(a)[0]} in {_house_en(ha)} ({ta[0]}) and {_p(b)[0]} in {_house_en(hb)} ({tb[0]}) "
                     f"have exchanged signs",
                     f"{_p(a)[1]} {_house_hi(ha)} ({ta[1]}) में और {_p(b)[1]} {_house_hi(hb)} ({tb[1]}) में, "
                     f"परस्पर राशि परिवर्तन"), (a, b)))
    return [_entry(k, [x for x, _ in r], planets=[p for _, pair in r for p in pair]) for k, r in out.items()]


def lakshmi(ch):
    nine, one = ch.lord(9), ch.lord(1)
    if ch.own_or_exalted(nine) and ch.house(nine) in KENDRA | TRIKONA:
        if ch.own_or_exalted(one) or ch.house(one) in KENDRA | TRIKONA:
            return [_entry("lakshmi", [(f"9th lord {_in(nine, ch)[0]}; Lagna lord {_in(one, ch)[0]}",
                                        f"भाग्येश {_in(nine, ch)[1]}; लग्नेश {_in(one, ch)[1]}")],
                           planets=[nine, one])]
    return []


def saraswati(ch):
    good = KENDRA | TRIKONA | {2}
    if all(ch.house(p) in good for p in ("Jupiter", "Venus", "Mercury")):
        js = ch.sign["Jupiter"]
        if ch.own_or_exalted("Jupiter") or LORD[js] in FRIENDS["Jupiter"]:
            return [_entry("saraswati", [_in(p, ch) for p in ("Jupiter", "Venus", "Mercury")],
                           planets=["Jupiter", "Venus", "Mercury"])]
    return []


def shakata(ch):
    n = _count(ch.sign["Jupiter"], ch.sign["Moon"])
    if n in (6, 8):
        r = [(f"Moon is in the {_ord(n)} from Jupiter", f"चन्द्र गुरु से {HI_ORD[n]} भाव में")]
        if ch.house("Moon") in KENDRA:
            r.append(("Moon in a kendra from the Lagna cancels it", "लग्न से केन्द्र में चन्द्र इसे भंग करता है"))
            return [_entry("shakata", r, "cancelled", ["Moon", "Jupiter"])]
        return [_entry("shakata", r, planets=["Moon", "Jupiter"])]
    return []


def find_yogas(signs, lons, asc):
    """All yogas in the chart, in ORDER. signs/lons need the seven planets plus Rahu and Ketu."""
    if any(p not in signs or p not in lons for p in SEVEN):
        return []
    ch = Chart(signs, lons, asc)
    found = (mahapurusha(ch) + moon_yogas(ch) + amala(ch) + sun_yogas(ch) + raj_dhana(ch) + neecha_bhanga(ch)
             + parivartana(ch) + lakshmi(ch) + saraswati(ch) + shakata(ch))
    for y in found:
        y["strength_notes"] = [planet_strength(ch, p)[1] for p in y["planets"] if p in SEVEN]
    return sorted(found, key=lambda y: ORDER.index(y["key"]))


THEMES = (
    (("Career and status", "करियर और पद"),
     ("dharma_karma", "raj", "yogakaraka", "ruchaka", "shasha", "amala", "lakshmi", "maha_parivartana", "neecha_bhanga")),
    (("Money and savings", "धन और बचत"), ("dhana", "lakshmi", "sunapha", "durudhara", "adhi", "chandra_mangala")),
    (("Mind, skill and learning", "बुद्धि, कौशल और विद्या"),
     ("bhadra", "budha_aditya", "saraswati", "hamsa", "gaja_kesari")),
    (("Overcoming difficulty", "कठिनाई पर विजय"), ("harsha", "sarala", "vimala")),
    (("Initiative and character", "पहल और स्वभाव"), ("anapha", "vesi", "vasi", "ubhayachari", "malavya")),
    (("Watch out for", "सावधानी"), ("shakata", "khala_parivartana", "dainya_parivartana")),
)


def overview(signs, lons, asc, yogas):
    """Plain lines (English, Hindi) that read the chart as a whole: planets in strong or weak signs, houses where
    planets gather, and what the yogas found add up to by theme."""
    if any(p not in signs for p in SEVEN):
        return []
    ch = Chart(signs, lons, asc)
    out = []
    for label, test in ((("Planets in their own or exaltation sign", "स्वराशि या उच्च राशि के ग्रह"),
                         lambda p: ch.own_or_exalted(p)),
                        (("Planets in their debilitation sign", "नीच राशि के ग्रह"),
                         lambda p: DEBIL[p] == ch.sign[p])):
        ps = [p for p in SEVEN if test(p)]
        if ps:
            out.append((f"{label[0]}: " + "; ".join(f"{_p(p)[0]} ({_s(ch.sign[p])[0]}, {_ord(ch.house(p))} house)"
                                                    for p in ps),
                        f"{label[1]}: " + "; ".join(f"{_p(p)[1]} ({_s(ch.sign[p])[1]}, {HI_ORD[ch.house(p)]} भाव में)"
                                                    for p in ps)))
    by_house = {}
    for p in SEVEN + ("Rahu", "Ketu"):
        if p in ch.sign:
            by_house.setdefault(ch.house(p), []).append(p)
    for h, ps in sorted(by_house.items()):
        if len(ps) >= 3:
            n = (", ".join(_p(p)[0] for p in ps), ", ".join(_p(p)[1] for p in ps))
            t = HOUSE_TOPIC[h]
            out.append((f"{n[0]} together in {_house_en(h)} ({t[0]}): this area of life is a main stage of the chart",
                        f"{n[1]} एक साथ {_house_hi(h)} ({t[1]}) में: जीवन का यह क्षेत्र इस कुण्डली का मुख्य मंच है"))
    by_key = {y["key"]: y for y in yogas if y["strength"] != "cancelled"}
    for (te, th), keys in THEMES:
        found = [by_key[k] for k in keys if k in by_key]
        if not found:
            continue
        names = (", ".join(y["name"][0] for y in found), ", ".join(y["name"][1] for y in found))
        planets = list(dict.fromkeys(p for y in found for p in y["planets"] if p in SEVEN))
        soft = [p for p in planets if planet_strength(ch, p)[0] in ("weak", "mixed")]
        line = (f"{te}: {names[0]}", f"{th}: {names[1]}")
        if planets:
            pn = (", ".join(_p(p)[0] for p in planets), ", ".join(_p(p)[1] for p in planets))
            line = (line[0] + f" (through {pn[0]})", line[1] + f" ({pn[1]} के द्वारा)")
        if soft:
            sn = (", ".join(_p(p)[0] for p in soft), ", ".join(_p(p)[1] for p in soft))
            line = (line[0] + f". {sn[0]} {'is' if len(soft) == 1 else 'are'} not at full strength, so expect "
                              f"results with some delay or effort",
                    line[1] + f"। {sn[1]} पूर्ण बल में नहीं, अतः फल कुछ देरी या परिश्रम से")
        out.append(line)
    if yogas:
        out.append(("Together these are classical indications that raise or lower the chance of results in each "
                    "area; they do not fix an income, a job or any outcome.",
                    "ये सब मिलकर शास्त्रीय संकेत हैं जो हर क्षेत्र में फल की सम्भावना बढ़ाते या घटाते हैं; ये किसी आय, नौकरी "
                    "या परिणाम को निश्चित नहीं करते।"))
    return out


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
