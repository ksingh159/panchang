# core/pdf/i18n.py
"""Words used in the printed reports, in English and Hindi. Add a language by adding a column."""
LANGS = ("en", "hi")

PLANETS = {
    "Sun": ("Sun", "सूर्य"), "Moon": ("Moon", "चन्द्र"), "Mars": ("Mars", "मंगल"), "Mercury": ("Mercury", "बुध"),
    "Jupiter": ("Jupiter", "गुरु"), "Venus": ("Venus", "शुक्र"), "Saturn": ("Saturn", "शनि"),
    "Rahu": ("Rahu", "राहु"), "Ketu": ("Ketu", "केतु"), "Ascendant": ("Lagna", "लग्न"),
}
PLANET_ABBR = {
    "Sun": ("Su", "सू"), "Moon": ("Mo", "च"), "Mars": ("Ma", "मं"), "Mercury": ("Me", "बु"), "Jupiter": ("Ju", "गु"),
    "Venus": ("Ve", "शु"), "Saturn": ("Sa", "श"), "Rahu": ("Ra", "रा"), "Ketu": ("Ke", "के"),
}
SIGNS = [("Aries", "मेष"), ("Taurus", "वृषभ"), ("Gemini", "मिथुन"), ("Cancer", "कर्क"), ("Leo", "सिंह"),
         ("Virgo", "कन्या"), ("Libra", "तुला"), ("Scorpio", "वृश्चिक"), ("Sagittarius", "धनु"),
         ("Capricorn", "मकर"), ("Aquarius", "कुम्भ"), ("Pisces", "मीन")]
NAKSHATRAS = [("Ashwini", "अश्विनी"), ("Bharani", "भरणी"), ("Krittika", "कृत्तिका"), ("Rohini", "रोहिणी"),
              ("Mrigashira", "मृगशिरा"), ("Ardra", "आर्द्रा"), ("Punarvasu", "पुनर्वसु"), ("Pushya", "पुष्य"),
              ("Ashlesha", "आश्लेषा"), ("Magha", "मघा"), ("Purva Phalguni", "पूर्वा फाल्गुनी"),
              ("Uttara Phalguni", "उत्तरा फाल्गुनी"), ("Hasta", "हस्त"), ("Chitra", "चित्रा"), ("Swati", "स्वाति"),
              ("Vishakha", "विशाखा"), ("Anuradha", "अनुराधा"), ("Jyeshtha", "ज्येष्ठा"), ("Mula", "मूल"),
              ("Purva Ashadha", "पूर्वाषाढ़ा"), ("Uttara Ashadha", "उत्तराषाढ़ा"), ("Shravana", "श्रवण"),
              ("Dhanishta", "धनिष्ठा"), ("Shatabhisha", "शतभिषा"), ("Purva Bhadrapada", "पूर्वा भाद्रपद"),
              ("Uttara Bhadrapada", "उत्तरा भाद्रपद"), ("Revati", "रेवती")]
NAK_ALIASES = {"Moola": "Mula", "Dhanishtha": "Dhanishta", "Shatabhishak": "Shatabhisha", "Jyestha": "Jyeshtha"}

VARGAS = {
    # key: (English name, Hindi name, what it is read for)
    "d1": ("Rashi (D1)", "राशि (D1)", ("Body, life as a whole", "शरीर और सम्पूर्ण जीवन")),
    "d2": ("Hora (D2)", "होरा (D2)", ("Wealth and family resources", "धन और कुटुम्ब")),
    "d3": ("Drekkana (D3)", "द्रेष्काण (D3)", ("Siblings, courage", "भाई-बहन, पराक्रम")),
    "d4": ("Chaturthamsha (D4)", "चतुर्थांश (D4)", ("Property, home, fortune", "भूमि, भवन, भाग्य")),
    "d5": ("Panchamsha (D5)", "पंचमांश (D5)", ("Fame, authority, mantra", "यश, अधिकार, मन्त्र")),
    "d7": ("Saptamsha (D7)", "सप्तमांश (D7)", ("Children and progeny", "सन्तान")),
    "d9": ("Navamsha (D9)", "नवमांश (D9)", ("Marriage, dharma, inner strength of planets", "विवाह, धर्म, ग्रह बल")),
    "d10": ("Dashamsha (D10)", "दशमांश (D10)", ("Career and status", "कर्म और पद")),
    "d12": ("Dwadashamsha (D12)", "द्वादशांश (D12)", ("Parents and lineage", "माता-पिता और वंश")),
    "d16": ("Shodashamsha (D16)", "षोडशांश (D16)", ("Vehicles, comforts", "वाहन और सुख")),
    "d20": ("Vimshamsha (D20)", "विंशांश (D20)", ("Spiritual practice, upasana", "उपासना और साधना")),
    "d24": ("Chaturvimshamsha (D24)", "चतुर्विंशांश (D24)", ("Learning and education", "विद्या")),
    "d27": ("Saptavimshamsha (D27)", "सप्तविंशांश (D27)", ("Strengths and weaknesses", "बलाबल")),
    "d30": ("Trimshamsha (D30)", "त्रिंशांश (D30)", ("Misfortune, health troubles", "अरिष्ट और रोग")),
    "d40": ("Khavedamsha (D40)", "खवेदांश (D40)", ("Maternal legacy, auspicious effects", "मातृ पक्ष, शुभाशुभ")),
    "d45": ("Akshavedamsha (D45)", "अक्षवेदांश (D45)", ("Paternal legacy, character", "पितृ पक्ष, चरित्र")),
    "d60": ("Shashtiamsha (D60)", "षष्ट्यंश (D60)", ("Past karma, the finest reading of all", "पूर्व कर्म, सूक्ष्मतम फल")),
}
VARGA_FACTORS = {k: int(k[1:]) for k in VARGAS}

WORDS = {
    # key: (English, Hindi)
    "site": ("Varanasi Panchang", "वाराणसी पंचांग"),
    "tagline": ("Know Your Time", "अपना समय जानें"),
    "kundali_title": ("Janma Kundali", "जन्म कुण्डली"),
    "kundali_sub": ("A complete Vedic birth chart report", "सम्पूर्ण वैदिक जन्म पत्रिका"),
    "aahaar_title": ("Aahaar and Ritucharya", "आहार और ऋतुचर्या"),
    "aahaar_sub": ("Eating with the seasons, the day and your age", "ऋतु, दिनचर्या और आयु के अनुसार आहार"),
    "prepared_for": ("Prepared for", "के लिए तैयार"),
    "printed_on": ("Printed on", "मुद्रण तिथि"),
    "order": ("Order", "ऑर्डर"),
    "licensed_to": ("Licensed to", "अधिकृत"),
    "page": ("Page", "पृष्ठ"),
    "contents": ("Contents", "विषय सूची"),
    "colophon": ("May this guide you well. Prepared with care from the Swiss Ephemeris and the classical texts.",
                 "यह आपका शुभ मार्गदर्शन करे। स्विस एफेमेरिस और शास्त्रीय ग्रन्थों के आधार पर सावधानी से तैयार।"),
    "region": ("Region", "क्षेत्र"),
    "reduced": ("Present, reduced", "उपस्थित, न्यून"),
    "mool_shanti": ("Mool shanti window", "मूल शान्ति का समय"),
    "personal_copy": ("Personal copy. Not for resale or redistribution.",
                      "व्यक्तिगत प्रति। पुनर्विक्रय या वितरण वर्जित।"),
    # kundali chapters
    "ch_birth": ("Birth Details", "जन्म विवरण"),
    "ch_planets": ("Planetary Positions", "ग्रह स्थिति"),
    "ch_lagna": ("Lagna and Chandra Charts", "लग्न और चन्द्र कुण्डली"),
    "ch_vargas": ("Divisional Charts (Shodashavarga)", "षोडशवर्ग कुण्डलियाँ"),
    "ch_transit": ("Transit Chart (Gochar)", "गोचर कुण्डली"),
    "ch_dasha": ("Vimshottari Dasha", "विंशोत्तरी दशा"),
    "ch_dosha": ("Dosha Analysis and Remedies", "दोष विचार और उपाय"),
    "ch_yoga": ("Yogas in Your Chart", "आपकी कुण्डली के योग"),
    "partial": ("Partial", "आंशिक"),
    "weak": ("Weak", "निर्बल"),
    "challenging": ("Challenging", "कष्टकारी"),
    "ch_notes": ("Notes on this Report", "रिपोर्ट सम्बन्धी टिप्पणी"),
    # fields
    "name": ("Name", "नाम"), "birth_date": ("Date of birth", "जन्म तिथि"), "birth_time": ("Time of birth", "जन्म समय"),
    "birth_place": ("Place of birth", "जन्म स्थान"), "coords": ("Latitude, longitude", "अक्षांश, देशान्तर"),
    "timezone": ("Time zone", "समय क्षेत्र"), "weekday": ("Weekday", "वार"), "tithi": ("Tithi", "तिथि"),
    "nakshatra": ("Nakshatra", "नक्षत्र"), "yoga": ("Yoga", "योग"), "karana": ("Karana", "करण"),
    "sunrise": ("Sunrise", "सूर्योदय"), "sunset": ("Sunset", "सूर्यास्त"), "masa": ("Lunar month", "मास"),
    "ritu": ("Ritu", "ऋतु"), "lagna": ("Lagna (Ascendant)", "लग्न"), "rashi": ("Rashi (Moon sign)", "राशि"),
    "sun_sign": ("Sun sign", "सूर्य राशि"), "nak_lord": ("Nakshatra lord", "नक्षत्र स्वामी"),
    "varna": ("Varna", "वर्ण"), "yoni": ("Yoni", "योनि"), "gana": ("Gana", "गण"), "nadi": ("Nadi", "नाड़ी"),
    "avakhada": ("Avakhada Chakra", "अवकहड़ा चक्र"), "panchang_birth": ("Panchang at Birth", "जन्म समय का पंचांग"),
    "planet": ("Planet", "ग्रह"), "sign": ("Sign", "राशि"), "degree": ("Degree", "अंश"), "house": ("House", "भाव"),
    "lord": ("Sign lord", "राशि स्वामी"), "lord_short": ("Lord", "स्वामी"), "dignity": ("Dignity", "स्थिति"), "pada": ("Pada", "पद"),
    "retro": ("Retrograde", "वक्री"), "direct": ("Direct", "मार्गी"), "motion": ("Motion", "गति"),
    "exalted": ("Exalted", "उच्च"), "debilitated": ("Debilitated", "नीच"), "own": ("Own sign", "स्वराशि"),
    "lagna_chart": ("Lagna Chart (D1)", "लग्न कुण्डली (D1)"), "moon_chart": ("Chandra Chart", "चन्द्र कुण्डली"),
    "bhava_table": ("Houses at a Glance", "भाव सारणी"), "planets_in": ("Planets", "ग्रह"),
    "read_for": ("Read for", "विचार"),
    "transit_as_on": ("Planets in the sky on", "आकाश में ग्रह स्थिति, दिनांक"),
    "from_lagna": ("From Lagna", "लग्न से"), "from_moon": ("From Moon", "चन्द्र से"),
    "sade_sati": ("Shani Sade Sati", "शनि साढ़ेसाती"),
    "mahadasha": ("Mahadasha", "महादशा"), "antardasha": ("Antardasha", "अन्तर्दशा"),
    "pratyantar": ("Pratyantar Dasha", "प्रत्यन्तर दशा"), "starts": ("Starts", "आरम्भ"), "ends": ("Ends", "समाप्ति"),
    "years": ("Years", "वर्ष"), "running_now": ("Running now", "वर्तमान"),
    "current_period": ("Your Current Period", "वर्तमान दशा"),
    "present": ("Present", "उपस्थित"), "absent": ("Not present", "नहीं है"), "cancelled": ("Cancelled", "भंग"),
    "remedies": ("Remedies (Upaya)", "उपाय"), "why": ("Why", "कारण"),
    "mangal_dosha": ("Mangal Dosha", "मंगल दोष"),
    # aahaar chapters
    "ch_today": ("Your Day at a Glance", "आज का दिन"),
    "ch_rhythm": ("Daily Rhythm by Pahar", "प्रहर अनुसार दिनचर्या"),
    "ch_ritu": ("This Season", "वर्तमान ऋतु"),
    "ch_regions": ("Foods of India by Region", "क्षेत्र अनुसार भारतीय आहार"),
    "ch_foods": ("Ingredients and their Nature", "खाद्य पदार्थ और उनकी प्रकृति"),
    "ch_age": ("Diet by Age and Stage of Life", "आयु अनुसार आहार"),
    "ch_fitness": ("Weight Loss, Gym and Yoga", "वज़न घटाना, जिम और योग"),
    "ch_dosha_guide": ("Vata, Pitta, Kapha", "वात, पित्त, कफ"),
    "ch_calendar": ("Month by Month, Day by Day", "मास और वार अनुसार"),
    "ch_sayings": ("Sayings of our Elders", "बुज़ुर्गों की कहावतें"),
    "eat": ("Favour", "लें"), "avoid": ("Reduce", "कम करें"), "city": ("City", "नगर"), "date": ("Date", "दिनांक"),
    "pahar": ("Pahar", "प्रहर"), "time": ("Time", "समय"), "dosha": ("Dosha", "दोष"), "what_to_do": ("What to do", "क्या करें"),
    "meals": ("Meal Times for your City", "आपके नगर के अनुसार भोजन समय"),
    "staples": ("Grains", "अनाज"), "vegetables": ("Vegetables", "सब्ज़ियाँ"), "fruits": ("Fruits", "फल"),
    "dals": ("Dals and pulses", "दालें"), "spices": ("Spices", "मसाले"), "dishes": ("Seasonal dishes", "मौसमी व्यंजन"),
    "dry_fruits": ("Dry fruits and nuts", "मेवे"), "grains": ("Grains and millets", "अनाज और मोटा अनाज"),
    "nature": ("Nature", "प्रकृति"), "ingredient": ("Ingredient", "खाद्य पदार्थ"), "use": ("Use", "उपयोग"), "best_season": ("Best season", "उत्तम ऋतु"),
    "cooling": ("Cooling", "शीतल"), "heating": ("Heating", "उष्ण"), "neutral": ("Balanced", "सम"),
    "sample_day": ("A Sample Day", "एक दिन का नमूना"), "principles": ("Principles", "सिद्धान्त"),
    "limit": ("Limit", "सीमित करें"), "before_workout": ("Before workout", "व्यायाम से पहले"),
    "after_workout": ("After workout", "व्यायाम के बाद"),
    "disclaimer_title": ("Please Note", "कृपया ध्यान दें"),
}


def w(key, lang):
    en, hi = WORDS[key]
    return hi if lang == "hi" else en


def pick(pair, lang):
    """(English, Hindi) tuple to the requested language."""
    if isinstance(pair, (tuple, list)):
        return pair[1] if lang == "hi" and len(pair) > 1 and pair[1] else pair[0]
    return pair


def planet(name, lang):
    return pick(PLANETS.get(name, (name, name)), lang)


def planet_abbr(name, lang):
    return pick(PLANET_ABBR.get(name, (name[:2], name[:2])), lang)


def sign(index, lang):
    return pick(SIGNS[index % 12], lang)


def sign_index(name):
    for i, (en, _) in enumerate(SIGNS):
        if en == name:
            return i
    return None


def nakshatra(name, lang):
    name = NAK_ALIASES.get(name, name)
    for en, hi in NAKSHATRAS:
        if en == name:
            return hi if lang == "hi" else en
    return name


# Panchang words as the calculators print them, for the Hindi edition
TERMS_HI = {
    "Raviwar": "रविवार", "Somawar": "सोमवार", "Mangalwar": "मंगलवार", "Budhwar": "बुधवार", "Guruwar": "गुरुवार",
    "Shukrawar": "शुक्रवार", "Shaniwar": "शनिवार", "Sunday": "रविवार", "Monday": "सोमवार", "Tuesday": "मंगलवार",
    "Wednesday": "बुधवार", "Thursday": "गुरुवार", "Friday": "शुक्रवार", "Saturday": "शनिवार",
    "Shukla Paksha": "शुक्ल पक्ष", "Krishna Paksha": "कृष्ण पक्ष", "Shukla": "शुक्ल", "Krishna": "कृष्ण",
    "Pratipada": "प्रतिपदा", "Dvitiya": "द्वितीया", "Dwitiya": "द्वितीया", "Tritiya": "तृतीया", "Chaturthi": "चतुर्थी",
    "Panchami": "पंचमी", "Shashthi": "षष्ठी", "Shashti": "षष्ठी", "Saptami": "सप्तमी", "Ashtami": "अष्टमी",
    "Navami": "नवमी", "Dashami": "दशमी", "Ekadashi": "एकादशी", "Dvadashi": "द्वादशी", "Dwadashi": "द्वादशी",
    "Trayodashi": "त्रयोदशी", "Chaturdashi": "चतुर्दशी", "Purnima": "पूर्णिमा", "Amavasya": "अमावस्या",
    "Vishkumbha": "विष्कुम्भ", "Priti": "प्रीति", "Ayushman": "आयुष्मान", "Saubhagya": "सौभाग्य", "Shobhana": "शोभन",
    "Atiganda": "अतिगण्ड", "Sukarma": "सुकर्मा", "Dhriti": "धृति", "Shula": "शूल", "Ganda": "गण्ड", "Vriddhi": "वृद्धि",
    "Dhruva": "ध्रुव", "Vyaghata": "व्याघात", "Harshana": "हर्षण", "Vajra": "वज्र", "Siddhi": "सिद्धि",
    "Vyatipata": "व्यतीपात", "Variyan": "वरीयान", "Parigha": "परिघ", "Shiva": "शिव", "Siddha": "सिद्ध",
    "Sadhya": "साध्य", "Shubha": "शुभ", "Brahma": "ब्रह्म", "Indra": "ऐन्द्र", "Vaidhriti": "वैधृति",
    "Bava": "बव", "Balava": "बालव", "Kaulava": "कौलव", "Taitila": "तैतिल", "Garaja": "गर", "Vanija": "वणिज",
    "Vishti": "विष्टि (भद्रा)", "Shakuni": "शकुनि", "Chatushpada": "चतुष्पद", "Naga": "नाग", "Kimstughna": "किंस्तुघ्न",
    "Chaitra": "चैत्र", "Vaishakha": "वैशाख", "Jyeshtha": "ज्येष्ठ", "Ashadha": "आषाढ़", "Shravana": "श्रावण",
    "Bhadrapada": "भाद्रपद", "Ashwina": "आश्विन", "Kartika": "कार्तिक", "Margashirsha": "मार्गशीर्ष", "Pausha": "पौष",
    "Magha": "माघ", "Phalguna": "फाल्गुन", "Adhik": "अधिक", "Purnimanta": "पूर्णिमान्त", "Amanta": "अमान्त",
    "Vasanta": "वसन्त", "Grishma": "ग्रीष्म", "Varsha": "वर्षा", "Sharad": "शरद", "Hemanta": "हेमन्त", "Shishira": "शिशिर",
}


def terms(text, lang):
    """Translate panchang words in ``text`` for the Hindi edition; drops English glosses in brackets."""
    import re
    if lang != "hi" or not text:
        return text
    text = re.sub(r"\s*\((?:Spring|Summer|Monsoon|Autumn|Pre-winter|Winter|Late winter|Early winter)\)", "", str(text))
    for en in sorted(TERMS_HI, key=len, reverse=True):
        text = re.sub(rf"\b{en}\b", TERMS_HI[en], text)
    return text
