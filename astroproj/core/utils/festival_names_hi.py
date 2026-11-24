# core/utils/festival_names_hi.py
"""Hindi festival names for the Hindi site. Phrases first (longest match wins), then single words, so names that
appear only in some years (Adhik Shravana Purnima, Somvati Pausha Amavasya ...) still come out in Hindi."""
import re

PHRASES = {
    "Purushottam Maas": "पुरुषोत्तम मास", "Bhai Dooj": "भाई दूज", "Yama Dwitiya": "यम द्वितीया",
    "Nahay Khay": "नहाय खाय", "Usha Arghya": "उषा अर्घ्य", "Sandhya Arghya": "सन्ध्या अर्घ्य",
    "Dev Deepawali": "देव दीपावली", "Lakshmi Puja": "लक्ष्मी पूजा", "Ganesh Chaturthi": "गणेश चतुर्थी",
    "Ganga Dussehra": "गंगा दशहरा", "Ganga Saptami": "गंगा सप्तमी", "Govardhan Puja": "गोवर्धन पूजा",
    "Guru Purnima": "गुरु पूर्णिमा", "Hanuman Jayanti": "हनुमान जयन्ती", "Hariyali Teej": "हरियाली तीज",
    "Hartalika Teej": "हरतालिका तीज", "Kajari Teej": "कजरी तीज", "Holika Dahan": "होलिका दहन",
    "Jagannath Rath Yatra": "जगन्नाथ रथ यात्रा", "Karwa Chauth": "करवा चौथ", "Krishna Janmashtami": "कृष्ण जन्माष्टमी",
    "Maha Shivaratri": "महाशिवरात्रि", "Masik Shivaratri": "मासिक शिवरात्रि", "Masik Durgashtami": "मासिक दुर्गाष्टमी",
    "Maha Navami": "महानवमी", "Durga Ashtami": "दुर्गा अष्टमी", "Nag Panchami": "नाग पंचमी",
    "Narak Chaturdashi": "नरक चतुर्दशी", "Narasimha Jayanti": "नृसिंह जयन्ती", "Pitru Paksha": "पितृ पक्ष",
    "Raksha Bandhan": "रक्षा बन्धन", "Rama Navami": "राम नवमी", "Ratha Saptami": "रथ सप्तमी",
    "Rishi Panchami": "ऋषि पंचमी", "Sankashti Chaturthi": "संकष्टी चतुर्थी", "Sarva Pitru Amavasya": "सर्व पितृ अमावस्या",
    "Sawan Somvar": "सावन सोमवार", "Sharad Navratri": "शारदीय नवरात्रि", "Chaitra Navratri": "चैत्र नवरात्रि",
    "Sharad Purnima": "शरद पूर्णिमा", "Sita Navami": "सीता नवमी", "Tulsi Vivah": "तुलसी विवाह",
    "Vasant Panchami": "वसन्त पंचमी", "Vat Savitri Vrat": "वट सावित्री व्रत", "Vijaya Dashami": "विजयादशमी",
    "Vinayaka Chaturthi": "विनायक चतुर्थी", "Vivah Panchami": "विवाह पंचमी", "Pradosh Vrat": "प्रदोष व्रत",
    "Bhaum Pradosh": "भौम प्रदोष", "Shani Pradosh": "शनि प्रदोष", "Som Pradosh": "सोम प्रदोष",
    "Bhishma Ashtami": "भीष्म अष्टमी", "Buddha Purnima": "बुद्ध पूर्णिमा", "Akshaya Tritiya": "अक्षय तृतीया",
    "Akshaya Navami": "अक्षय नवमी", "Ahoi Ashtami": "अहोई अष्टमी", "Anant Chaturdashi": "अनन्त चतुर्दशी",
    "Annapurna Jayanti": "अन्नपूर्णा जयन्ती", "Datta Jayanti": "दत्त जयन्ती", "Kalabhairav Jayanti": "कालभैरव जयन्ती",
    "Makar Sankranti": "मकर संक्रान्ति", "Mauni Amavasya": "मौनी अमावस्या", "Kartik Purnima": "कार्तिक पूर्णिमा",
    "Holi (Rangwali / Dhulandi)": "होली (रंगवाली / धुलण्डी)", "Kharmas (Malmas)": "खरमास (मलमास)",
    "Pitru Paksha (Shraddh)": "पितृ पक्ष (श्राद्ध)", "Pitru Paksha begins": "पितृ पक्ष आरम्भ",
    "Chhath Puja": "छठ पूजा",
    "Yamunotri Dham Kapat": "यमुनोत्री धाम कपाट", "Gangotri Dham Kapat": "गंगोत्री धाम कपाट",
    "Kedarnath Dham Kapat": "केदारनाथ धाम कपाट", "Badrinath Dham Kapat": "बद्रीनाथ धाम कपाट",
    "Shri Amarnath Ji Yatra": "श्री अमरनाथ जी यात्रा", "Char Dham": "चार धाम",
}

WORDS = {
    "Adhik": "अधिक", "Maas": "मास", "Purnima": "पूर्णिमा", "Amavasya": "अमावस्या", "Ekadashi": "एकादशी",
    "Sankranti": "संक्रान्ति", "Navratri": "नवरात्रि", "Ghatasthapana": "घटस्थापना", "Chhath": "छठ", "Kharna": "खरना",
    "Diwali": "दीपावली", "Dhanteras": "धनतेरस", "Dussehra": "दशहरा", "Annakut": "अन्नकूट", "Holashtak": "होलाष्टक",
    "Lohri": "लोहड़ी", "Kharmas": "खरमास", "Somvati": "सोमवती", "Shani": "शनि", "Angaraki": "अंगारकी", "Vrat": "व्रत",
    "Total": "पूर्ण", "Annular": "वलयाकार", "Partial": "खण्ड", "Hybrid": "संकर", "Penumbral": "उपच्छाया",
    "Surya": "सूर्य", "Chandra": "चन्द्र", "Grahan": "ग्रहण",
    "India": "भारत", "Nepal": "नेपाल", "Sri": "श्री", "Lanka": "लंका", "UAE": "संयुक्त अरब अमीरात", "Singapore": "सिंगापुर",
    "Japan": "जापान", "Australia": "ऑस्ट्रेलिया", "East": "पूर्व", "West": "पश्चिम", "Africa": "अफ़्रीका", "Egypt": "मिस्र",
    "UK": "ब्रिटेन", "Germany": "जर्मनी", "Canada": "कनाडा", "USA": "अमेरिका", "Brazil": "ब्राज़ील", "Mauritius": "मॉरीशस",
    "Fiji": "फ़िजी",
    "Jayanti": "जयन्ती", "Puja": "पूजा", "Teej": "तीज", "Som": "सोम", "Bhaum": "भौम",
    # months and signs
    "Chaitra": "चैत्र", "Vaishakha": "वैशाख", "Jyeshtha": "ज्येष्ठ", "Ashadha": "आषाढ़", "Shravana": "श्रावण",
    "Bhadrapada": "भाद्रपद", "Ashwina": "आश्विन", "Kartika": "कार्तिक", "Margashirsha": "मार्गशीर्ष", "Pausha": "पौष",
    "Magha": "माघ", "Phalguna": "फाल्गुन", "Mesha": "मेष", "Vrishabha": "वृषभ", "Mithuna": "मिथुन", "Karka": "कर्क",
    "Simha": "सिंह", "Kanya": "कन्या", "Tula": "तुला", "Vrishchika": "वृश्चिक", "Dhanu": "धनु", "Makar": "मकर",
    "Kumbha": "कुम्भ", "Meena": "मीन",
    # Ekadashi names
    "Aja": "अजा", "Amalaki": "आमलकी", "Apara": "अपरा", "Devshayani": "देवशयनी", "Devutthana": "देवउठनी",
    "Indira": "इन्दिरा", "Jaya": "जया", "Kamada": "कामदा", "Kamika": "कामिका", "Mohini": "मोहिनी", "Mokshada": "मोक्षदा",
    "Nirjala": "निर्जला", "Padmini": "पद्मिनी", "Papankusha": "पापांकुशा", "Papmochani": "पापमोचनी", "Parama": "परमा",
    "Parivartini": "परिवर्तिनी", "Rama": "रमा", "Shattila": "षटतिला", "Putrada": "पुत्रदा", "Utpanna": "उत्पन्ना",
    "Varuthini": "वरूथिनी", "Vijaya": "विजया", "Yogini": "योगिनी", "Saphala": "सफला",
}

CATEGORIES = {
    "Amavasya": "अमावस्या", "Ekadashi": "एकादशी", "Festival": "त्योहार", "Major Festival": "प्रमुख त्योहार",
    "Period": "अवधि", "Purnima": "पूर्णिमा", "Regional Festival": "क्षेत्रीय त्योहार", "Sankranti": "संक्रान्ति",
    "Shraddha": "श्राद्ध", "Snan-Daan": "स्नान-दान", "Vrat": "व्रत", "Yatra": "यात्रा", "Char Dham": "चार धाम",
    "Kumbh": "कुम्भ",
}


def hindi_name(name):
    if not name:
        return name
    if name in CATEGORIES:
        return CATEGORIES[name]
    from .kumbh import hindi_names
    if name in hindi_names():
        return hindi_names()[name]
    text = name
    for en in sorted(PHRASES, key=len, reverse=True):
        text = text.replace(en, PHRASES[en])
    return re.sub(r"[A-Za-z]+", lambda m: WORDS.get(m.group(0), m.group(0)), text)
