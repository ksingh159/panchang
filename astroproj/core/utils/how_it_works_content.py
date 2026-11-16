# core/utils/how_it_works_content.py
"""How It Works: every feature, how it is calculated, in English and Hindi. One entry per feature.

Each point is ((term_en, term_hi), (text_en, text_hi)). ``url`` is a URL name for the "Open" button.
"""

SECTIONS = [
    {"key": "panchang", "icon": "🕉", "url": "panchang",
     "title": ("Daily panchang", "दैनिक पंचांग"), "cta": ("Open today's panchang", "आज का पंचांग देखें"),
     "intro": ("The five limbs of the day, computed for the exact place you choose from the Swiss Ephemeris, with "
               "Chitrapaksha ayanamsa. The day runs from sunrise to the next sunrise.",
               "चुने हुए स्थान के लिए दिन के पाँच अंग, स्विस एफ़ेमेरिस और चित्रापक्ष अयनांश से गणना। दिन एक सूर्योदय से "
               "अगले सूर्योदय तक माना जाता है।"),
     "points": [
         (("Tithi", "तिथि"), ("Each 12° that the Moon gains on the Sun. Thirty tithis make a lunar month.",
                              "चन्द्रमा सूर्य से जितने 12° आगे बढ़ता है, उतनी तिथियाँ। तीस तिथियों का एक चान्द्र मास।")),
         (("Nakshatra", "नक्षत्र"), ("The Moon's place among 27 equal parts of 13°20′ of the sidereal zodiac.",
                                    "निरयण राशिचक्र के 13°20′ के 27 बराबर भागों में चन्द्रमा की स्थिति।")),
         (("Yoga", "योग"), ("The sum of the Sun's and Moon's longitudes, divided into 27 parts.",
                            "सूर्य और चन्द्र के भोगांश का योग, 27 भागों में बँटा।")),
         (("Karana", "करण"), ("Half a tithi. Vishti karana is Bhadra, avoided for auspicious work.",
                              "आधी तिथि। विष्टि करण ही भद्रा है, जिसमें शुभ कार्य टाले जाते हैं।")),
         (("Rahu Kaal, choghadiya, hora", "राहुकाल, चौघड़िया, होरा"),
          ("Day and night are each split from the real sunrise and sunset, so the timings change with the season and "
           "the city, not with the clock.",
           "दिन और रात को वास्तविक सूर्योदय और सूर्यास्त से बाँटा जाता है, इसलिए समय ऋतु और शहर के साथ बदलता है, "
           "घड़ी के साथ नहीं।")),
     ]},
    {"key": "months", "icon": "🌙", "url": "panchang",
     "title": ("Lunar months, Adhik maas and ritu", "चान्द्र मास, अधिक मास और ऋतु"), "cta": ("", ""),
     "intro": ("A lunar month is named after the sign the Sun enters during it. A month in which the Sun enters no new "
               "sign is Adhik (Purushottam) maas.",
               "चान्द्र मास का नाम उस राशि से होता है जिसमें उस मास में सूर्य प्रवेश करता है। जिस मास में सूर्य किसी नई "
               "राशि में प्रवेश नहीं करता, वह अधिक (पुरुषोत्तम) मास होता है।"),
     "points": [
         (("Amanta or Purnimanta", "अमान्त या पूर्णिमान्त"),
          ("Kashi and North India end the month on Purnima; Maharashtra, Gujarat and the South on Amavasya. Pick one "
           "in your profile and every page follows it.",
           "काशी और उत्तर भारत में मास पूर्णिमा पर, महाराष्ट्र, गुजरात और दक्षिण में अमावस्या पर पूरा होता है। "
           "प्रोफ़ाइल में एक चुनें, हर पृष्ठ उसी के अनुसार दिखेगा।")),
         (("Two ritus", "दो ऋतुएँ"),
          ("The Vedic (nirayana) ritu follows the sidereal Sun and is used for puja and vrata. The Drik (sayana) ritu "
           "follows the Sun against the solstices, as the weather does, and is used for Ayurveda's seasonal diet.",
           "वैदिक (निरयण) ऋतु निरयण सूर्य से चलती है और पूजा-व्रत में मानी जाती है। दृक् (सायन) ऋतु अयनान्त के सापेक्ष "
           "सूर्य से चलती है, जैसे मौसम चलता है; आयुर्वेद का ऋतु-आहार इसी से है।")),
     ]},
    {"key": "festivals", "icon": "🪔", "url": "festival_calendar",
     "title": ("Festivals and vrats by Kashi rules", "काशी के नियमों से त्योहार और व्रत"),
     "cta": ("Open the festival calendar", "त्योहार कैलेंडर देखें"),
     "intro": ("A tithi rarely begins at sunrise, so it often touches two days. Each festival names the part of the day "
               "its tithi must cover, following Nirnaya Sindhu and Dharma Sindhu, and we compute that window for Varanasi.",
               "तिथि शायद ही सूर्योदय पर शुरू होती है, इसलिए वह प्रायः दो दिनों को छूती है। निर्णय सिन्धु और धर्म सिन्धु "
               "के अनुसार हर त्योहार के लिए दिन का वह भाग तय है जिसमें तिथि होनी चाहिए; हम वाराणसी के लिए वही काल "
               "निकालते हैं।"),
     "points": [
         (("The deciding kaal", "निर्णायक काल"),
          ("Diwali in Pradosh, Janmashtami at Nishita (midnight), Rama Navami at Madhyahna, Karva Chauth at moonrise, "
           "and so on. Every festival page names the rule that decided its date.",
           "दीपावली प्रदोष में, जन्माष्टमी निशीथ (अर्धरात्रि) में, राम नवमी मध्याह्न में, करवा चौथ चन्द्रोदय पर, इत्यादि। "
           "हर त्योहार पृष्ठ पर वह नियम लिखा है जिससे तिथि तय हुई।")),
         (("Smarta and Vaishnava", "स्मार्त और वैष्णव"),
          ("Where the traditions differ, as for Ekadashi and Janmashtami, both dates are shown.",
           "जहाँ परम्पराएँ अलग हैं, जैसे एकादशी और जन्माष्टमी, वहाँ दोनों तिथियाँ दी जाती हैं।")),
         (("Puja muhurat for your city", "आपके शहर का पूजा मुहूर्त"),
          ("The date follows Kashi; the puja window is worked out again for the city you select.",
           "तिथि काशी के अनुसार है; पूजा का समय आपके चुने शहर के लिए अलग से निकाला जाता है।")),
     ]},
    {"key": "finder", "icon": "🔎", "url": "panchang_finder",
     "title": ("Panchang Finder, any date 1900 to 2200", "पंचांग खोज, 1900 से 2200 तक कोई भी तिथि"),
     "cta": ("Try the Panchang Finder", "पंचांग खोज आज़माएँ"),
     "intro": ("The exact start and end of every tithi, nakshatra, yoga and karana is computed once per year and stored. "
               "The first request for a year takes about a second; after that every answer is instant.",
               "हर तिथि, नक्षत्र, योग और करण का सटीक आरम्भ और अन्त वर्ष में एक बार गणना करके सहेजा जाता है। किसी वर्ष "
               "का पहला अनुरोध लगभग एक सेकण्ड लेता है; उसके बाद हर उत्तर तुरन्त मिलता है।"),
     "points": [
         (("Places", "स्थान"),
          ("More than 170,000 towns from GeoNames with their historical time zones, so old dates before Indian "
           "Standard Time, or with war-time and daylight-saving clocks, come out right.",
           "जियोनेम्स के 1,70,000 से अधिक नगर, उनके ऐतिहासिक समय-क्षेत्रों सहित, ताकि भारतीय मानक समय से पहले की "
           "या युद्धकालीन और डेलाइट-सेविंग घड़ियों वाली तिथियाँ भी सही आएँ।")),
     ]},
    {"key": "muhurat", "icon": "✨", "url": "shubh_muhurat",
     "title": ("Shubh muhurat and auspicious yogas", "शुभ मुहूर्त और शुभ योग"),
     "cta": ("See today's shubh muhurat", "आज का शुभ मुहूर्त देखें"),
     "intro": ("For each purpose (marriage, gold, vehicle, property, investment, loans) we take the nakshatras, weekdays "
               "and tithis recommended in Muhurta Chintamani, then remove Bhadra, Rahu Kaal and Rikta tithis, and for "
               "big events Kharmas, Adhik maas, Pitru Paksha and Holashtak.",
               "हर कार्य (विवाह, सोना, वाहन, सम्पत्ति, निवेश, ऋण) के लिए मुहूर्त चिन्तामणि में बताए नक्षत्र, वार और तिथियाँ "
               "ली जाती हैं, फिर भद्रा, राहुकाल और रिक्ता तिथियाँ हटाई जाती हैं, और बड़े कार्यों के लिए खरमास, अधिक मास, "
               "पितृ पक्ष और होलाष्टक भी।"),
     "points": [
         (("Your own stars", "आपके अपने तारे"),
          ("With your birth details saved, only times with good Tarabalam (your nakshatra) and Chandrabalam (your Moon "
           "sign) are kept.",
           "जन्म विवरण सहेजने पर केवल वही समय रखे जाते हैं जिनमें ताराबल (आपका नक्षत्र) और चन्द्रबल (आपकी चन्द्र राशि) "
           "शुभ हों।")),
         (("Auspicious yogas", "शुभ योग"),
          ("Sarvartha Siddhi, Amrit Siddhi, Guru Pushya, Ravi Pushya and Pushkar yogas are found from the weekday, "
           "nakshatra and tithi combinations in the texts.",
           "सर्वार्थ सिद्धि, अमृत सिद्धि, गुरु पुष्य, रवि पुष्य और पुष्कर योग शास्त्रों में दिए वार, नक्षत्र और तिथि के "
           "मेल से निकाले जाते हैं।")),
     ]},
    {"key": "grahan", "icon": "🌑", "url": "grahan_calendar",
     "title": ("Surya and Chandra grahan", "सूर्य और चन्द्र ग्रहण"), "cta": ("See upcoming grahan", "आगामी ग्रहण देखें"),
     "intro": ("Eclipses from 1900 to 2200 are found with the Swiss Ephemeris. For your city we compute sparsha, madhya "
               "and moksha, whether it is visible, and a map of where it can be seen.",
               "1900 से 2200 तक के ग्रहण स्विस एफ़ेमेरिस से निकाले जाते हैं। आपके शहर के लिए स्पर्श, मध्य और मोक्ष का "
               "समय, ग्रहण दिखेगा या नहीं, और जहाँ दिखेगा उसका नक्शा।"),
     "points": [
         (("Sutak", "सूतक"),
          ("Four prahar (12 hours) before sparsha for a Surya grahan and three prahar (9 hours) for a Chandra grahan, "
           "and only where the grahan is visible.",
           "सूर्य ग्रहण में स्पर्श से चार प्रहर (12 घण्टे) और चन्द्र ग्रहण में तीन प्रहर (9 घण्टे) पहले, और केवल "
           "वहीं जहाँ ग्रहण दिखाई दे।")),
     ]},
    {"key": "aahaar", "icon": "🍲", "url": "aahaar",
     "title": ("Aahaar: eating with the season", "आहार: ऋतु के साथ भोजन"), "cta": ("Open Aahaar", "आहार देखें"),
     "intro": ("The ritu regimen of Charaka Samhita, Ashtanga Hridaya and Sushruta Samhita for the current Drik ritu, "
               "with the day split into pahars from your city's real sunrise and sunset.",
               "चरक संहिता, अष्टांग हृदय और सुश्रुत संहिता की ऋतुचर्या, वर्तमान दृक् ऋतु के लिए, और आपके शहर के वास्तविक "
               "सूर्योदय-सूर्यास्त से दिन के पहर।"),
     "points": [
         (("Which rule wins", "कौन-सा नियम ऊपर"),
          ("Your health first, then the season, then observances you keep (Chaturmas, Ekadashi, tithi), then folk "
           "customs. Clashes on the day are listed and resolved.",
           "पहले आपका स्वास्थ्य, फिर ऋतु, फिर आपके रखे व्रत-नियम (चातुर्मास, एकादशी, तिथि), फिर लोक-परम्परा। उस दिन के "
           "टकराव सूचीबद्ध करके सुलझाए जाते हैं।")),
         (("Regional food", "क्षेत्रीय भोजन"),
          ("Seasonal dishes of your native state first, then of the city you live in, then every other region.",
           "पहले आपके मूल राज्य के ऋतु-व्यंजन, फिर जिस शहर में आप रहते हैं, फिर अन्य सभी क्षेत्र।")),
     ]},
    {"key": "naamkaran", "icon": "👶", "url": "naamkaran",
     "title": ("Naamkaran: baby names", "नामकरण: शिशु के नाम"), "cta": ("Find name letters", "नाम के अक्षर खोजें"),
     "intro": ("The first syllable comes from the Moon's nakshatra pada at birth (the Avakahada chakra), with names that "
               "begin with that sound and the rashi letters.",
               "पहला अक्षर जन्म के समय चन्द्रमा के नक्षत्र-चरण (अवकहड़ा चक्र) से आता है, साथ में उस ध्वनि से शुरू होने वाले "
               "नाम और राशि के अक्षर।"),
     "points": []},
    {"key": "kundali", "icon": "🪐", "url": "create_kundali",
     "title": ("Kundali, Kundali Milan and gochar", "कुण्डली, कुण्डली मिलान और गोचर"),
     "cta": ("Create a kundali", "कुण्डली बनाएँ"),
     "intro": ("Birth charts use Lahiri ayanamsa and the historical time zone of the birthplace.",
               "जन्म कुण्डली लाहिरी अयनांश और जन्मस्थान के ऐतिहासिक समय-क्षेत्र से बनती है।"),
     "points": [
         (("Divisional charts", "वर्ग कुण्डलियाँ"),
          ("D1 to D60 by traditional Parashari rules, matching Jagannatha Hora; D2 is the Uma-Shambhu hora.",
           "D1 से D60 तक पारम्परिक पाराशरी नियमों से, जगन्नाथ होरा से मेल खाते हुए; D2 उमा-शम्भु होरा है।")),
         (("Dasha and doshas", "दशा और दोष"),
          ("Vimshottari Mahadasha, Antardasha and Pratyantar dasha; Mangal dosha with its cancellations, and Gand Mool.",
           "विंशोत्तरी महादशा, अन्तर्दशा और प्रत्यन्तर दशा; मंगल दोष और उसका परिहार, और गण्ड मूल।")),
         (("Kundali Milan", "कुण्डली मिलान"),
          ("Ashtakoot guna milan out of 36, with Nadi, Bhakoot and Mangal dosha and the classical cancellations.",
           "36 में से अष्टकूट गुण मिलान, नाड़ी, भकूट और मंगल दोष तथा शास्त्रीय परिहार सहित।")),
         (("Gochar", "गोचर"), ("Today's planets drawn over the chart, sign by sign.",
                              "आज के ग्रह कुण्डली पर, राशि-दर-राशि।")),
     ]},
    {"key": "pdf", "icon": "📘", "url": "refund_policy",
     "title": ("PDF reports", "PDF रिपोर्ट"), "cta": ("Prices and refund policy", "मूल्य और रिफ़ंड नीति"),
     "intro": ("Every page is free to read. The Kundali report and the Aahaar guide can also be bought as a printed-book "
               "PDF in English or Hindi.",
               "हर पृष्ठ पढ़ना निःशुल्क है। कुण्डली रिपोर्ट और आहार मार्गदर्शिका अंग्रेज़ी या हिन्दी में छपी पुस्तक जैसी PDF के "
               "रूप में भी ली जा सकती हैं।"),
     "points": [
         (("Delivery", "डिलीवरी"),
          ("The PDF is made the moment the payment is confirmed, carries the buyer's name and order number, and can be "
           "downloaded 10 times in 30 days.",
           "भुगतान की पुष्टि होते ही PDF बनती है, उस पर क्रेता का नाम और ऑर्डर संख्या रहती है, और इसे 30 दिनों में "
           "10 बार डाउनलोड किया जा सकता है।")),
     ]},
]
