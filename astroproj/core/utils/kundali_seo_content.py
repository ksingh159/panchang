# core/utils/kundali_seo_content.py
"""
Reading text for the Kundali Milan and Janam Kundali pages: what each page does, in plain words, and an FAQ that is
also sent to Google as FAQPage structured data. Every entry is an (English, Hindi) pair, shown with the |pick filter.
English wording of the Kundali Milan text and the Janam Kundali intro is the owner's (2026-11-18).

Tone (owner's rule): explain, never frighten. A low score or a dosha is something to look at with the family pandit,
not a verdict; most doshas have classical cancellations, and the page says so.
"""
import json

from django.utils.safestring import mark_safe
from django.utils.translation import get_language

# ---------------------------------------------------------------- Kundali Milan

MILAN_HEADINGS = {
    "intro": ("Kundali Milan – Marriage Compatibility by Birth Chart", "कुंडली मिलान – जन्म कुंडली से विवाह अनुकूलता"),
    "kootas": ("The Eight Kootas and Their 36 Gunas", "आठ कूट और उनके 36 गुण"),
    "bands": ("How Many Gunas Should Match?", "कितने गुण मिलने चाहिए?"),
    "doshas": ("Doshas in Kundali Matching and Their Cancellations", "कुंडली मिलान में दोष और उनके परिहार"),
    "by_name": ("Kundali Milan by Name", "नाम से कुंडली मिलान"),
    "faq": ("Frequently Asked Questions About Kundali Milan", "कुंडली मिलान से जुड़े सामान्य प्रश्न"),
    "koota": ("Koota", "कूट"),
    "gunas": ("Gunas", "गुण"),
    "evaluates": ("What It Evaluates", "क्या देखता है"),
    "total": ("Total", "कुल"),
    "more_q": ("Want to understand your complete birth chart?", "अपनी पूरी जन्म कुंडली समझना चाहते हैं?"),
    "more_link": ("Create your free Janam Kundali", "अपनी मुफ्त जन्म कुंडली बनाएँ"),
}

MILAN_INTRO = [
    ("Kundali Milan, also known as Gun Milan or Kundali Matching, is a traditional Vedic astrology method used to "
     "assess compatibility between prospective bride and groom. The Ashtakoota system evaluates eight aspects of "
     "compatibility based primarily on the Moon's position in both birth charts, covering temperament, mutual "
     "understanding, attraction and other traditional considerations.",
     "कुंडली मिलान, जिसे गुण मिलान या कुंडली मैचिंग भी कहते हैं, भावी वर और वधू की अनुकूलता देखने की "
     "पारम्परिक वैदिक ज्योतिष पद्धति है। अष्टकूट पद्धति मुख्य रूप से दोनों जन्म कुंडलियों में चन्द्रमा की स्थिति "
     "के आधार पर अनुकूलता के आठ पहलुओं को देखती है, जिनमें स्वभाव, आपसी समझ, आकर्षण और अन्य पारम्परिक बातें "
     "शामिल हैं।"),
    ("Each koota carries a specific weight, adding up to a maximum of 36 gunas. The resulting score provides a "
     "traditional framework for assessing compatibility and is considered alongside other factors in both birth "
     "charts.",
     "हर कूट का एक निश्चित भार होता है, और सब मिलाकर अधिकतम 36 गुण होते हैं। इससे मिलने वाले अंक अनुकूलता "
     "देखने का एक पारम्परिक ढाँचा देते हैं, और इन्हें दोनों जन्म कुंडलियों की अन्य बातों के साथ देखा जाता है।"),
    ("In Kashi (Varanasi) and across North India, Kundali Milan has long been an important part of traditional "
     "marriage consultations. It serves as a guide for further consideration rather than the sole basis for a "
     "marriage decision.",
     "काशी (वाराणसी) और पूरे उत्तर भारत में कुंडली मिलान लम्बे समय से विवाह सम्बन्धी पारम्परिक परामर्श का "
     "महत्वपूर्ण हिस्सा रहा है। यह आगे विचार करने के लिए एक मार्गदर्शक है, विवाह के निर्णय का एकमात्र आधार नहीं।"),
]

# (name, gunas, what it evaluates)
KOOTAS = [
    (("Varna", "वर्ण"), 1, ("Spiritual outlook, values and traditional compatibility.",
                            "आध्यात्मिक दृष्टिकोण, मूल्य और पारम्परिक अनुकूलता।")),
    (("Vashya", "वश्य"), 2, ("Mutual influence, attraction and interpersonal dynamics.",
                             "आपसी प्रभाव, आकर्षण और आपसी व्यवहार।")),
    (("Tara", "तारा"), 3, ("Traditional assessment of well-being and compatibility based on the distance between "
                           "birth nakshatras.",
                           "जन्म नक्षत्रों के बीच की दूरी के आधार पर कुशलता और अनुकूलता का पारम्परिक आकलन।")),
    (("Yoni", "योनि"), 4, ("Physical compatibility, attraction and intimacy.",
                           "शारीरिक अनुकूलता, आकर्षण और निकटता।")),
    (("Graha Maitri", "ग्रह मैत्री"), 5, ("Mental compatibility and friendship between the lords of the two Moon "
                                         "signs.",
                                         "मानसिक अनुकूलता और दोनों चन्द्र राशियों के स्वामियों की मित्रता।")),
    (("Gana", "गण"), 6, ("Temperamental compatibility based on Deva, Manushya and Rakshasa classifications.",
                         "देव, मनुष्य और राक्षस गण के आधार पर स्वभाव की अनुकूलता।")),
    (("Bhakoot", "भकूट"), 7, ("Compatibility based on the relative positions of the Moon signs, traditionally "
                              "associated with family life, prosperity and emotional harmony.",
                              "चन्द्र राशियों की आपसी स्थिति के आधार पर अनुकूलता, जो परम्परा में पारिवारिक जीवन, "
                              "समृद्धि और भावनात्मक सामंजस्य से जुड़ी है।")),
    (("Nadi", "नाड़ी"), 8, ("Traditional compatibility based on the Nadi classification of the birth nakshatras, "
                            "associated with health and progeny considerations.",
                            "जन्म नक्षत्रों की नाड़ी के आधार पर पारम्परिक अनुकूलता, जो स्वास्थ्य और सन्तान से जुड़ी "
                            "मानी जाती है।")),
]

BANDS_INTRO = (
    "The Ashtakoota system awards a maximum of 36 gunas. The following ranges are commonly used in North Indian "
    "Kundali Milan:",
    "अष्टकूट पद्धति में अधिकतम 36 गुण होते हैं। उत्तर भारतीय कुंडली मिलान में सामान्यतः ये सीमाएँ मानी जाती हैं:",
)

SCORE_BANDS = [
    (("30–36 Gunas: Uttam (Excellent)", "30–36 गुण: उत्तम"),
     ("A highly favourable score under the Ashtakoota system, indicating strong compatibility across its evaluated "
      "factors.",
      "अष्टकूट पद्धति में बहुत अनुकूल अंक, जो देखे गए सभी पहलुओं पर अच्छी अनुकूलता दर्शाते हैं।")),
    (("25–29 Gunas: Shubh (Favourable)", "25–29 गुण: शुभ"),
     ("A generally favourable match, with a good level of compatibility according to the Ashtakoota assessment.",
      "सामान्यतः अनुकूल मेल, अष्टकूट आकलन के अनुसार अच्छी अनुकूलता।")),
    (("18–24 Gunas: Madhyam (Moderate)", "18–24 गुण: मध्यम"),
     ("An acceptable score under the traditional system. Eighteen gunas is commonly considered the minimum "
      "benchmark, although the individual kootas and complete birth charts should also be examined.",
      "पारम्परिक पद्धति में स्वीकार्य अंक। अठारह गुण सामान्यतः न्यूनतम माने जाते हैं, फिर भी अलग-अलग कूटों और "
      "पूरी जन्म कुंडलियों को भी देखना चाहिए।")),
    (("Below 18 Gunas: Further Assessment Recommended", "18 से कम गुण: आगे और विचार करें"),
     ("A lower score does not automatically mean a marriage is unsuitable. The individual koota scores, relevant "
      "doshas, possible cancellations and overall compatibility of both birth charts should be considered before "
      "reaching a conclusion.",
      "कम अंक का अर्थ अपने आप यह नहीं है कि विवाह उपयुक्त नहीं है। किसी निष्कर्ष से पहले अलग-अलग कूटों के अंक, "
      "सम्बन्धित दोष, सम्भावित परिहार और दोनों जन्म कुंडलियों की समग्र अनुकूलता देखनी चाहिए।")),
]

MILAN_DOSHAS = [
    (("Nadi Dosha and Bhakoot Dosha", "नाड़ी दोष और भकूट दोष"), [
        ("When Nadi or Bhakoot receives zero points, the corresponding dosha is traditionally identified in the "
         "Ashtakoota system. However, certain traditional calculation methods also recognise exceptions and "
         "cancellation conditions.",
         "जब नाड़ी या भकूट में शून्य अंक आते हैं, तो अष्टकूट पद्धति में परम्परा से वह दोष माना जाता है। फिर भी कुछ "
         "पारम्परिक गणना पद्धतियाँ इसके अपवाद और परिहार की स्थितियाँ भी मानती हैं।"),
        ("These may involve the relationship between the Moon signs, their ruling planets, and the nakshatras and "
         "padas of the individuals. The applicable rules can vary across astrological traditions.",
         "इनमें चन्द्र राशियों का आपसी सम्बन्ध, उनके स्वामी ग्रह, और दोनों व्यक्तियों के नक्षत्र और चरण शामिल हो "
         "सकते हैं। लागू होने वाले नियम अलग-अलग ज्योतिष परम्पराओं में भिन्न हो सकते हैं।"),
        ("Our report evaluates the relevant cancellation conditions and indicates which ones apply to the matched "
         "birth charts, helping you understand the result beyond the basic guna score.",
         "हमारी रिपोर्ट सम्बन्धित परिहार की स्थितियाँ जाँचती है और बताती है कि मिलाई गई कुंडलियों पर कौन सी लागू "
         "होती हैं, ताकि आप केवल गुण अंकों से आगे परिणाम को समझ सकें।"),
    ]),
    (("Mangal Dosha (Manglik Dosha)", "मंगल दोष (मांगलिक दोष)"), [
        ("Mangal Dosha is traditionally assessed when Mars occupies the 1st, 4th, 7th, 8th or 12th house from a "
         "specified reference point in the birth chart.",
         "जब जन्म कुंडली में किसी निर्धारित सन्दर्भ बिन्दु से मंगल पहले, चौथे, सातवें, आठवें या बारहवें भाव में हो, "
         "तब परम्परा से मंगल दोष का आकलन किया जाता है।"),
        ("Its interpretation also depends on the sign and house placement of Mars, aspects, conjunctions and "
         "recognised cancellation conditions. In certain traditions, the presence of Mangal Dosha in both partners "
         "is considered a mitigating or balancing factor.",
         "इसका अर्थ मंगल की राशि और भाव, दृष्टि, युति और मान्य परिहार की स्थितियों पर भी निर्भर करता है। कुछ "
         "परम्पराओं में दोनों साथियों में मंगल दोष होना इसे कम करने या सन्तुलित करने वाला माना जाता है।"),
        ("Our Kundali Matching report checks Mangal Dosha from the Lagna (Ascendant), Moon and Venus reference "
         "points and identifies the applicable cancellation conditions according to the calculation rules used.",
         "हमारी कुंडली मिलान रिपोर्ट लग्न, चन्द्र और शुक्र, तीनों सन्दर्भ बिन्दुओं से मंगल दोष जाँचती है और "
         "प्रयुक्त गणना नियमों के अनुसार लागू होने वाले परिहार बताती है।"),
    ]),
]

MILAN_BY_NAME = [
    ("Do you want to match horoscopes but don't know the exact birth time? You can also perform a traditional "
     "name-based Kundali Milan.",
     "कुंडली मिलाना चाहते हैं पर सही जन्म समय पता नहीं? आप पारम्परिक रूप से नाम से भी कुंडली मिलान कर सकते हैं।"),
    ("In this method, the first syllable of a person's name is associated with a nakshatra (birth star) and its "
     "pada according to traditional Naam Akshar conventions. This association is then used to derive the "
     "corresponding Moon sign for the matching calculation.",
     "इस पद्धति में पारम्परिक नाम अक्षर नियमों के अनुसार व्यक्ति के नाम का पहला अक्षर एक नक्षत्र और उसके चरण से "
     "जोड़ा जाता है। फिर उसी से मिलान की गणना के लिए चन्द्र राशि निकाली जाती है।"),
    ("Select Match by Name above, or enter the Janma Nakshatra if it is already known.",
     "ऊपर \"नाम से मिलान\" चुनें, या जन्म नक्षत्र पहले से पता हो तो वह चुनें।"),
    ("Name-based matching provides an approximate Ashtakoota score. However, it cannot replace a complete "
     "birth-chart comparison. Accurate birth date, time and place are required to assess Lagna, planetary "
     "positions and Mangal Dosha comprehensively.",
     "नाम से मिलान लगभग अष्टकूट अंक देता है, पर यह पूरी जन्म कुंडली के मिलान का स्थान नहीं ले सकता। लग्न, ग्रह "
     "स्थिति और मंगल दोष को पूरी तरह देखने के लिए सही जन्म तिथि, समय और स्थान चाहिए।"),
]

MILAN_FAQ = [
    (("How many gunas should match for marriage?", "विवाह के लिए कितने गुण मिलने चाहिए?"),
     ("Traditionally, 18 out of 36 gunas is considered the minimum benchmark. A score of 25 or more is generally "
      "considered favourable, while 30 or more is regarded as excellent. However, the guna score is only one part "
      "of Kundali Milan. A comprehensive assessment also considers doshas, cancellation conditions and the overall "
      "compatibility of both birth charts.",
      "परम्परा से 36 में से 18 गुण न्यूनतम माने जाते हैं। 25 या अधिक गुण सामान्यतः अनुकूल और 30 या अधिक उत्तम "
      "माने जाते हैं। फिर भी गुण अंक कुंडली मिलान का केवल एक हिस्सा हैं। पूरे आकलन में दोष, परिहार की स्थितियाँ "
      "और दोनों जन्म कुंडलियों की समग्र अनुकूलता भी देखी जाती है।")),
    (("Is Kundali Milan free on Varanasi Panchang?", "क्या वाराणसी पंचांग पर कुंडली मिलान मुफ्त है?"),
     ("Yes. You can generate a complete Kundali Milan report free of charge, including the Ashtakoota guna score, "
      "dosha assessment, applicable cancellation conditions and planetary details of both birth charts. No sign-up "
      "is required.",
      "हाँ। आप पूरी कुंडली मिलान रिपोर्ट मुफ्त बना सकते हैं, जिसमें अष्टकूट गुण अंक, दोष आकलन, लागू होने वाले "
      "परिहार और दोनों जन्म कुंडलियों के ग्रहों का विवरण शामिल है। साइन-अप की ज़रूरत नहीं है।")),
    (("Can I match Kundalis using names alone?", "क्या केवल नाम से कुंडली मिलान हो सकता है?"),
     ("Yes. Traditional name-based matching uses the first syllable of each person's name to identify an "
      "associated nakshatra and pada. The eight kootas are then evaluated using the resulting astrological details. "
      "However, a name-based match cannot provide a complete assessment of Mangal Dosha, Lagna or planetary "
      "placements. For that, complete birth details are required.",
      "हाँ। पारम्परिक नाम मिलान में हर व्यक्ति के नाम के पहले अक्षर से सम्बन्धित नक्षत्र और चरण पहचाना जाता है, "
      "फिर उसी से आठों कूट देखे जाते हैं। पर नाम से मिलान में मंगल दोष, लग्न या ग्रह स्थिति का पूरा आकलन नहीं हो "
      "सकता। उसके लिए पूरा जन्म विवरण चाहिए।")),
    (("What if the guna score is low or a dosha is present?", "अगर गुण कम हों या कोई दोष हो तो क्या करें?"),
     ("A low guna score or the presence of a dosha should not be treated as a final verdict. Traditional astrology "
      "recognises various exceptions and cancellation conditions, depending on the specific dosha and the rules "
      "being followed. Both birth charts should be examined together before drawing conclusions. The report helps "
      "identify these factors so that you can discuss them further with your family pandit or astrologer.",
      "कम गुण या किसी दोष को अन्तिम निर्णय नहीं मानना चाहिए। पारम्परिक ज्योतिष, दोष और अपनाए गए नियमों के "
      "अनुसार, कई अपवाद और परिहार मानता है। निष्कर्ष से पहले दोनों जन्म कुंडलियाँ साथ में देखनी चाहिए। रिपोर्ट "
      "इन बातों को पहचानने में मदद करती है, ताकि आप अपने परिवार के पंडित जी या ज्योतिषी से आगे चर्चा कर सकें।")),
    (("Which Kundali Matching system does Varanasi Panchang follow?",
      "वाराणसी पंचांग कौन सी कुंडली मिलान पद्धति अपनाता है?"),
     ("Varanasi Panchang follows the North Indian Ashtakoota Guna Milan framework, drawing on traditional Kundali "
      "Matching practices associated with Kashi (Varanasi). Planetary calculations use the Swiss Ephemeris with "
      "sidereal zodiac settings. The interpretation of certain doshas and their cancellations may differ across "
      "regional and astrological traditions.",
      "वाराणसी पंचांग उत्तर भारतीय अष्टकूट गुण मिलान पद्धति अपनाता है, जो काशी (वाराणसी) की पारम्परिक कुंडली "
      "मिलान रीति पर आधारित है। ग्रहों की गणना स्विस एफेमेरिस से निरयन राशिचक्र में होती है। कुछ दोषों और उनके "
      "परिहारों का अर्थ अलग-अलग क्षेत्रीय और ज्योतिष परम्पराओं में भिन्न हो सकता है।")),
]

# ---------------------------------------------------------------- Janam Kundali

KUNDALI_INTRO = [
    ("A Janam Kundali (Birth Chart) is a celestial map of the sky at the exact moment and location of your birth. "
     "It represents your Lagna (Ascendant), the twelve astrological houses, and the positions of the Sun, Moon, and "
     "planets across the zodiac.",
     "जन्म कुंडली आपके जन्म के ठीक उसी क्षण और स्थान पर आकाश का नक्शा है। इसमें आपका लग्न, बारह भाव, और "
     "राशिचक्र में सूर्य, चन्द्र तथा ग्रहों की स्थिति दिखाई देती है।"),
    ("Simply enter your date, time, and place of birth to generate your Vedic birth chart in seconds — completely "
     "free.",
     "बस अपनी जन्म तिथि, समय और स्थान डालें, और कुछ ही सेकंड में अपनी वैदिक जन्म कुंडली बनाएँ — पूरी तरह मुफ्त।"),
]

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

KUNDALI_ACCURACY = [
    ("Birth time matters most: the lagna changes about every two hours, and divisional charts change within "
     "minutes. Use the time on the birth certificate or hospital record if you have it.",
     "जन्म समय सबसे महत्वपूर्ण है: लग्न लगभग हर दो घंटे में बदलता है, और वर्ग कुंडलियाँ कुछ ही मिनटों में। जन्म "
     "प्रमाणपत्र या अस्पताल के रिकॉर्ड में लिखा समय हो तो वही डालें।"),
    ("Select your birthplace from the suggested locations, and the correct historical time zone will be applied "
     "automatically — including India's wartime clock changes between 1942 and 1945.",
     "सुझाए गए स्थानों में से अपना जन्म स्थान चुनें, सही ऐतिहासिक समय क्षेत्र अपने आप लग जाएगा — 1942 से 1945 के "
     "बीच भारत में युद्धकाल के दौरान बदली गई घड़ी का समय भी।"),
]

KUNDALI_FAQ = [
    (("Is this kundali really free?", "क्या यह कुंडली सच में मुफ्त है?"),
     ("Yes. The full online kundali, with all charts, dashas, yogas and Sade Sati, is free, and no sign-up is "
      "needed. Sign in with Google or email if you want your kundalis saved to your account and opened from any "
      "device. A printable PDF with remedies is optional.",
      "हाँ। सभी कुंडलियाँ, दशा, योग और साढ़ेसाती सहित पूरी ऑनलाइन कुंडली मुफ्त है, और साइन-अप की ज़रूरत नहीं "
      "है। अपनी कुंडलियाँ खाते में सहेजकर किसी भी डिवाइस से खोलनी हों तो Google या ईमेल से साइन इन करें। उपायों "
      "सहित प्रिंट करने योग्य PDF वैकल्पिक है।")),
    (("Can I make a kundali by date of birth only?", "क्या केवल जन्म तिथि से कुंडली बन सकती है?"),
     ("The planets' signs come from the date, but the lagna and houses need the birth time and place. If the time "
      "is not known, use your best estimate and treat the lagna and houses as approximate.",
      "ग्रहों की राशियाँ तिथि से पता चल जाती हैं, पर लग्न और भावों के लिए जन्म समय और स्थान चाहिए। समय पता न "
      "हो तो अनुमानित समय डालें और लग्न तथा भावों को अनुमानित मानें।")),
    (("Which ayanamsa and chart style do you use?", "आप कौन सा अयनांश और कुंडली शैली अपनाते हैं?"),
     ("Sidereal positions from the Swiss Ephemeris with the True Chitrapaksha ayanamsa (Chitra/Spica fixed at "
      "180°, very close to Lahiri), drawn in the North Indian chart style used in Kashi.",
      "स्विस एफेमेरिस से निरयन ग्रह स्थिति, सत्य चित्रापक्ष अयनांश के साथ (चित्रा तारा ठीक 180° पर, लाहिड़ी के "
      "बहुत निकट), काशी में प्रचलित उत्तर भारतीय शैली में।")),
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
    return {"h": MILAN_HEADINGS, "intro": MILAN_INTRO, "kootas": KOOTAS, "bands_intro": BANDS_INTRO,
            "bands": SCORE_BANDS, "doshas": MILAN_DOSHAS, "by_name": MILAN_BY_NAME, "faq": MILAN_FAQ,
            "faq_jsonld": faq_jsonld(MILAN_FAQ)}


def kundali_context():
    return {"intro": KUNDALI_INTRO, "features": KUNDALI_FEATURES, "accuracy": KUNDALI_ACCURACY,
            "faq": KUNDALI_FAQ, "faq_jsonld": faq_jsonld(KUNDALI_FAQ)}
