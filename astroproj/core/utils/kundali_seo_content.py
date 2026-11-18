# core/utils/kundali_seo_content.py
"""
Reading text for the Kundali Milan and Janam Kundali pages: what each page does, in plain words, and an FAQ that is
also sent to Google as FAQPage structured data. Every entry is an (English, Hindi) pair, shown with the |pick filter.

Tone (owner's rule): explain, never frighten. A low score or a dosha is something to look at with the family pandit,
not a verdict; most doshas have classical cancellations, and the page says so.
"""
import json

from django.utils.safestring import mark_safe
from django.utils.translation import get_language

# ---------------------------------------------------------------- Kundali Milan

MILAN_INTRO = (
    "Kundali Milan (also called Gun Milan or kundali matching) compares the birth charts of a bride and groom before "
    "marriage. The Ashtakoot method looks at eight aspects of the Moon in both charts, from temperament and health to "
    "mutual affection, and adds them up to a score out of 36 gunas. Families in Kashi and across North India have used "
    "it for centuries as a starting point for a conversation, not as a final word.",
    "कुंडली मिलान (गुण मिलान या कुंडली मैचिंग) विवाह से पहले वर और वधू की जन्म कुंडलियों को मिलाकर देखने की "
    "परम्परा है। अष्टकूट पद्धति दोनों कुंडलियों में चन्द्रमा से जुड़े आठ पहलुओं को देखती है, स्वभाव और स्वास्थ्य "
    "से लेकर आपसी स्नेह तक, और इन्हें जोड़कर 36 गुणों में से अंक देती है। काशी और पूरे उत्तर भारत में परिवार "
    "सदियों से इसे बातचीत की शुरुआत मानते आए हैं, अन्तिम निर्णय नहीं।",
)

# (name, max points, what it looks at)
KOOTAS = [
    (("Varna", "वर्ण"), 1, ("Outlook and approach to work and duty.", "काम और कर्तव्य के प्रति दृष्टिकोण।")),
    (("Vashya", "वश्य"), 2, ("Mutual attraction and how the two influence each other.",
                             "आपसी आकर्षण और एक-दूसरे पर प्रभाव।")),
    (("Tara", "तारा"), 3, ("Health and well-being, from the distance between the two birth nakshatras.",
                           "दोनों जन्म नक्षत्रों की दूरी से स्वास्थ्य और कुशलता।")),
    (("Yoni", "योनि"), 4, ("Physical compatibility and intimacy.", "शारीरिक अनुकूलता और निकटता।")),
    (("Graha Maitri", "ग्रह मैत्री"), 5, ("Friendship between the lords of the two Moon signs: how well minds meet.",
                                         "दोनों चन्द्र राशियों के स्वामियों की मित्रता: मन कितना मिलता है।")),
    (("Gana", "गण"), 6, ("Temperament: Deva, Manushya or Rakshasa nature.",
                         "स्वभाव: देव, मनुष्य या राक्षस गण।")),
    (("Bhakoot", "भकूट"), 7, ("The relative position of the two Moon signs: family life, prosperity and affection.",
                              "दोनों चन्द्र राशियों की आपसी स्थिति: पारिवारिक जीवन, समृद्धि और स्नेह।")),
    (("Nadi", "नाड़ी"), 8, ("Constitution and health of the family line, from the nakshatra's nadi.",
                            "नक्षत्र की नाड़ी से शारीरिक प्रकृति और सन्तान से जुड़ा स्वास्थ्य।")),
]

SCORE_BANDS = [
    (("30 to 36: Uttam", "30 से 36: उत्तम"), ("An excellent match on all eight kootas.",
                                            "आठों कूटों पर बहुत अच्छा मेल।")),
    (("25 to 29: Shubh", "25 से 29: शुभ"), ("A good match; most families go ahead with confidence.",
                                          "अच्छा मेल; अधिकतर परिवार विश्वास के साथ आगे बढ़ते हैं।")),
    (("18 to 24: Madhyam", "18 से 24: मध्यम"), ("An acceptable match. 18 gunas is the traditional minimum, and many "
                                              "happy marriages fall in this range.",
                                              "स्वीकार्य मेल। 18 गुण परम्परागत न्यूनतम है, और बहुत से सुखी विवाह "
                                              "इसी सीमा में आते हैं।")),
    (("Below 18: discuss with your pandit", "18 से कम: पंडित जी से चर्चा करें"),
     ("Not a rejection. Look at which kootas scored low and whether the full charts balance them; a pandit reads "
      "both kundalis together before advising.",
      "यह अस्वीकृति नहीं है। देखें कि कौन से कूट कम रहे और क्या पूरी कुंडलियाँ उनकी भरपाई करती हैं; पंडित जी "
      "सलाह देने से पहले दोनों कुंडलियाँ साथ में देखते हैं।")),
]

MILAN_DOSHAS = [
    (("Nadi and Bhakoot dosha", "नाड़ी और भकूट दोष"),
     ("When Nadi or Bhakoot scores zero the tradition calls it a dosha, but the texts also list clear exceptions. "
      "Same Moon sign with different nakshatras, the same nakshatra in different signs or padas, or friendly lords "
      "of the two Moon signs cancel it. This report checks those exceptions for you and says when they apply.",
      "जब नाड़ी या भकूट में शून्य अंक आते हैं तो परम्परा इसे दोष कहती है, पर शास्त्र इसके स्पष्ट अपवाद भी "
      "बताते हैं। एक ही चन्द्र राशि पर अलग नक्षत्र, एक ही नक्षत्र पर अलग राशि या चरण, या दोनों चन्द्र "
      "राशियों के स्वामी मित्र हों तो दोष नहीं माना जाता। यह रिपोर्ट इन अपवादों को स्वयं जाँचकर बताती है।")),
    (("Mangal dosha (Manglik)", "मंगल दोष (मांगलिक)"),
     ("Mars in the 1st, 4th, 7th, 8th or 12th house is called Manglik, and roughly every second person has it from "
      "at least one reference point, so it is very common. It is cancelled when both partners are Manglik, and by "
      "several sign and house placements of Mars. When you match by birth details, we check it from the Lagna, "
      "Moon and Venus and list every cancellation that applies.",
      "पहले, चौथे, सातवें, आठवें या बारहवें भाव में मंगल हो तो व्यक्ति मांगलिक कहलाता है, और लगभग हर दूसरे "
      "व्यक्ति की कुंडली में किसी न किसी सन्दर्भ से यह योग होता है, यानी यह बहुत सामान्य है। दोनों साथी मांगलिक "
      "हों, या मंगल कुछ विशेष राशियों और भावों में हो, तो यह दोष निरस्त हो जाता है। जन्म विवरण से मिलान करने पर हम "
      "लग्न, चन्द्र और शुक्र तीनों से इसे जाँचते हैं और लागू होने वाला हर परिहार बताते हैं।")),
]

MILAN_BY_NAME = (
    "No birth time? You can still match by name. In the tradition the first syllable of the name (naam akshar) "
    "points to a nakshatra and its pada, and from that to the Moon sign. Choose \"Match by name\" above, or pick the "
    "janma nakshatra if the family knows it. Name matching gives the eight-koota score; doshas, lagna and planets "
    "need the full birth details.",
    "जन्म समय पता नहीं? तब भी नाम से मिलान हो सकता है। परम्परा में नाम का पहला अक्षर (नाम अक्षर) एक नक्षत्र "
    "और उसके चरण की ओर संकेत करता है, और उससे चन्द्र राशि पता चलती है। ऊपर \"नाम से मिलान\" चुनें, या परिवार "
    "को जन्म नक्षत्र पता हो तो वह चुनें। नाम से मिलान में आठ कूटों के अंक मिलते हैं; दोष, लग्न और ग्रहों के लिए "
    "पूरा जन्म विवरण चाहिए।",
)

MILAN_FAQ = [
    (("How many gunas are needed for marriage?", "विवाह के लिए कितने गुण मिलने चाहिए?"),
     ("Traditionally 18 of 36 is the minimum, 25 or more is considered good, and 30 or more excellent. The score is "
      "one part of the picture: a pandit also looks at doshas, their cancellations and the two charts as a whole.",
      "परम्परा के अनुसार 36 में से 18 गुण न्यूनतम माने जाते हैं, 25 या अधिक अच्छे और 30 या अधिक उत्तम। अंक "
      "पूरी तस्वीर का एक हिस्सा हैं: पंडित जी दोष, उनके परिहार और दोनों कुंडलियों को समग्र रूप से भी देखते हैं।")),
    (("Is kundali milan free here?", "क्या यहाँ कुंडली मिलान मुफ्त है?"),
     ("Yes. The full gun milan report, with dosha checks, cancellations and both charts' planets, is free and needs "
      "no sign-up.",
      "हाँ। दोष जाँच, परिहार और दोनों कुंडलियों के ग्रहों सहित पूरी गुण मिलान रिपोर्ट मुफ्त है और इसके लिए "
      "साइन-अप की ज़रूरत नहीं है।")),
    (("Can we match kundali by name only?", "क्या केवल नाम से कुंडली मिलान हो सकता है?"),
     ("Yes. The first syllable of each name gives a nakshatra, and the eight kootas are scored from it. For Mangal "
      "dosha and the planets, use date, time and place of birth.",
      "हाँ। हर नाम का पहला अक्षर एक नक्षत्र बताता है और उसी से आठों कूटों के अंक निकलते हैं। मंगल दोष और ग्रहों "
      "के लिए जन्म तिथि, समय और स्थान दें।")),
    (("What if the score is low or a dosha shows up?", "अगर अंक कम आएँ या कोई दोष दिखे तो क्या करें?"),
     ("Do not worry. Many doshas are cancelled by rules in the classical texts, and the report shows when that "
      "happens. A low score is a reason to look closer with your family pandit, not a sign that the marriage will "
      "fail.",
      "चिन्ता न करें। बहुत से दोष शास्त्रों के नियमों से निरस्त हो जाते हैं, और रिपोर्ट यह भी बताती है। कम अंक "
      "का अर्थ है कि परिवार के पंडित जी के साथ ध्यान से देखा जाए, यह नहीं कि विवाह असफल होगा।")),
    (("Which system do you follow?", "आप कौन सी पद्धति अपनाते हैं?"),
     ("North Indian Ashtakoot gun milan as used by Kashi (Varanasi) pandits, with sidereal positions from the Swiss "
      "Ephemeris.",
      "काशी (वाराणसी) के पंडितों द्वारा प्रयुक्त उत्तर भारतीय अष्टकूट गुण मिलान, स्विस एफेमेरिस से निरयन ग्रह "
      "स्थितियों के साथ।")),
]

# ---------------------------------------------------------------- Janam Kundali

KUNDALI_INTRO = (
    "A janam kundali (birth chart) is a map of the sky at the moment you were born, drawn for your birth place. It "
    "shows the lagna (the sign rising in the east), the twelve houses, and where the Sun, Moon and planets stood. "
    "Enter your date, time and place of birth and the chart is calculated in a few seconds, free.",
    "जन्म कुंडली आपके जन्म के क्षण का, आपके जन्म स्थान से दिखने वाला आकाश का नक्शा है। इसमें लग्न (पूर्व में "
    "उदित राशि), बारह भाव, और सूर्य, चन्द्र तथा ग्रहों की स्थिति दिखती है। अपनी जन्म तिथि, समय और स्थान "
    "डालें, कुछ ही सेकंड में आपकी कुंडली मुफ्त बन जाएगी।",
)

KUNDALI_FEATURES = [
    (("Lagna chart and all divisional charts", "लग्न कुंडली और सभी वर्ग कुंडलियाँ"),
     ("The D1 lagna chart in North Indian style, with Navamsa (D9) and every divisional chart up to D60.",
      "उत्तर भारतीय शैली में D1 लग्न कुंडली, साथ में नवांश (D9) और D60 तक की हर वर्ग कुंडली।")),
    (("Planets, nakshatras and houses", "ग्रह, नक्षत्र और भाव"),
     ("Each planet's sign, degree, nakshatra and pada, and the house it sits in.",
      "हर ग्रह की राशि, अंश, नक्षत्र, चरण और वह किस भाव में है।")),
    (("Vimshottari dasha", "विंशोत्तरी दशा"),
     ("Your Mahadasha, Antardasha and Pratyantar dasha timeline, with what is running today.",
      "महादशा, अन्तर्दशा और प्रत्यन्तर दशा का क्रम, और आज कौन सी दशा चल रही है।")),
    (("Yogas and doshas, explained plainly", "योग और दोष, सरल भाषा में"),
     ("Raj yogas, Dhana yogas, Mangal dosha and others, each with what cancels or softens it.",
      "राज योग, धन योग, मंगल दोष आदि, और हर एक के साथ यह भी कि क्या उसे निरस्त या हल्का करता है।")),
    (("Sade Sati and transits", "साढ़ेसाती और गोचर"),
     ("Shani Sade Sati and Dhaiya across your life, so you can plan ahead, and where the planets are now.",
      "जीवन भर की शनि साढ़ेसाती और ढैया, ताकि आप पहले से योजना बना सकें, और अभी ग्रह कहाँ हैं।")),
]

KUNDALI_ACCURACY = (
    "Birth time matters most: the lagna changes about every two hours, and divisional charts change within minutes. "
    "Use the time on the birth certificate or hospital record if you have it. Pick your birth place from the "
    "suggestions, and the correct historical time zone is applied for you, including India's 1942 to 1945 war time.",
    "जन्म समय सबसे महत्वपूर्ण है: लग्न लगभग हर दो घंटे में बदलता है, और वर्ग कुंडलियाँ कुछ ही मिनटों में। "
    "जन्म प्रमाणपत्र या अस्पताल के रिकॉर्ड में लिखा समय हो तो वही डालें। जन्म स्थान सुझावों में से चुनें, "
    "सही ऐतिहासिक समय क्षेत्र अपने आप लग जाएगा, भारत का 1942 से 1945 का युद्धकालीन समय भी।",
)

KUNDALI_FAQ = [
    (("Is this kundali really free?", "क्या यह कुंडली सच में मुफ्त है?"),
     ("Yes. The full online kundali, with all charts, dashas, yogas and Sade Sati, is free. A free account keeps "
      "your kundalis saved so you can open them again. A printable PDF with remedies is optional.",
      "हाँ। सभी कुंडलियाँ, दशा, योग और साढ़ेसाती सहित पूरी ऑनलाइन कुंडली मुफ्त है। मुफ्त खाते में आपकी "
      "कुंडलियाँ सहेजी रहती हैं ताकि आप उन्हें फिर खोल सकें। उपायों सहित प्रिंट करने योग्य PDF वैकल्पिक है।")),
    (("Can I make a kundali by date of birth only?", "क्या केवल जन्म तिथि से कुंडली बन सकती है?"),
     ("The planets' signs come from the date, but the lagna and houses need the birth time and place. If the time "
      "is not known, use your best estimate and treat the lagna and houses as approximate.",
      "ग्रहों की राशियाँ तिथि से पता चल जाती हैं, पर लग्न और भावों के लिए जन्म समय और स्थान चाहिए। समय पता न "
      "हो तो अनुमानित समय डालें और लग्न तथा भावों को अनुमानित मानें।")),
    (("Which ayanamsa and chart style do you use?", "आप कौन सा अयनांश और कुंडली शैली अपनाते हैं?"),
     ("Sidereal positions from the Swiss Ephemeris with the True Chitrapaksha ayanamsa (Chitra/Spica fixed at 180°, "
      "very close to Lahiri), drawn in the North Indian chart style used in Kashi.",
      "स्विस एफेमेरिस से निरयन ग्रह स्थिति, सत्य चित्रापक्ष अयनांश के साथ (चित्रा तारा ठीक 180° पर, "
      "लाहिड़ी के बहुत निकट), काशी में प्रचलित उत्तर भारतीय शैली में।")),
    (("Can I see my kundali in Hindi?", "क्या मैं अपनी कुंडली हिंदी में देख सकता हूँ?"),
     ("Yes. Switch to हिंदी at the top of the page and the kundali, planet names and explanations appear in Hindi.",
      "हाँ। पेज के ऊपर हिंदी चुनें, कुंडली, ग्रहों के नाम और विवरण हिंदी में दिखेंगे।")),
    (("Does a dosha in my chart mean something bad will happen?", "क्या कुंडली में दोष होने का अर्थ है कि कुछ बुरा होगा?"),
     ("No. A dosha describes a tendency, often a mild one, and many are cancelled by other placements in the same "
      "chart. Your kundali page shows these cancellations alongside each dosha.",
      "नहीं। दोष केवल एक प्रवृत्ति बताता है, अक्सर हल्की, और बहुत से दोष उसी कुंडली के दूसरे योगों से निरस्त हो "
      "जाते हैं। आपके कुंडली पेज पर हर दोष के साथ ये परिहार भी दिखाए जाते हैं।")),
]


def _pick(pair):
    return pair[1] if (get_language() or "").startswith("hi") and pair[1] else pair[0]


def faq_jsonld(faq):
    """FAQPage structured data for ``faq`` in the active language, safe to place inside a <script> tag."""
    data = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": _pick(q), "acceptedAnswer": {"@type": "Answer", "text": _pick(a)}}
        for q, a in faq]}
    text = json.dumps(data, ensure_ascii=False)
    return mark_safe(text.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026"))


def milan_context():
    return {"intro": MILAN_INTRO, "kootas": KOOTAS, "bands": SCORE_BANDS, "doshas": MILAN_DOSHAS,
            "by_name": MILAN_BY_NAME, "faq": MILAN_FAQ, "faq_jsonld": faq_jsonld(MILAN_FAQ)}


def kundali_context():
    return {"intro": KUNDALI_INTRO, "features": KUNDALI_FEATURES, "accuracy": KUNDALI_ACCURACY,
            "faq": KUNDALI_FAQ, "faq_jsonld": faq_jsonld(KUNDALI_FAQ)}
