# core/utils/aahaar.py
"""
Ritucharya and Aahaar: what to eat and avoid to keep Vata, Pitta and Kapha in balance.

Sources (reviewed November 2026 against the classical texts; see CLASSICAL_SOURCES):
  Charaka Samhita, Sutrasthana 6 (Tasyashitiya), Ashtanga Hridaya, Sutrasthana 3 and Sushruta Samhita,
  Sutrasthana 6 - ritu regimen
  Ashtanga Hridaya, Sutrasthana 1 and 12 - doshas, their seasons and times of day
  Bhavaprakasha - Ritu Haritaki
  Brahma Vaivarta Purana, Brahma Khanda 27 - foods avoided by tithi
  Skanda Purana (Chaturmas vrata) and the Hindi folk verse of the twelve months
Weekday items are lok-parampara and are labelled as such on the page.
"""

# Ayurveda's solar ritus; each spans two solar months.
RITU = {
    "Shishira": {
        "hindi": "शिशिर", "months": "Sun in sayana Makara and Kumbha, about 21 Dec to 18 Feb (late winter)", "named": "Tapas and Tapasya (Magha, Phalguna)", "kaal": "Adana (Sun draws strength from the body)",
        "agni": "Strong", "bala": "Good but starting to fall", "rasa": "Tikta (bitter)",
        "dosha": "Kapha gathers (sanchaya)", "focus": "Kapha",
        "eat": ["Same as Hemanta, with a little more warmth", "Wheat, urad, new rice, ghee and sesame",
                "Ginger, black pepper, long pepper", "Warm soups, milk preparations, jaggery"],
        "avoid": ["Very light or cold food", "Pungent, bitter and astringent excess", "Cold water and cold wind",
                  "Skipping breakfast"],
        "lifestyle": ["Oil massage and warm bath", "Stay out of cold wind", "Exercise to full capacity"],
        "haritaki": "Haritaki with pippali",
    },
    "Vasanta": {
        "hindi": "वसन्त", "months": "Sun in sayana Meena and Mesha, about 18 Feb to 20 Apr (spring)", "named": "Madhu and Madhava (Chaitra, Vaishakha)", "kaal": "Adana",
        "agni": "Weak (melting Kapha dims it)", "bala": "Moderate", "rasa": "Kashaya (astringent)",
        "dosha": "Kapha aggravates (prakopa)", "focus": "Kapha",
        "eat": ["Old barley and wheat", "Honey in warm water", "Moong, masoor", "Bitter greens, neem and karela",
                "Ginger water, buttermilk in moderation"],
        "avoid": ["Heavy, oily, sweet and sour food", "Curd", "New grains", "Sleeping by day", "Cold drinks"],
        "lifestyle": ["Vigorous exercise", "Dry powder massage (udvartana)", "Morning walks in gardens",
                      "Vamana under a vaidya for high Kapha"],
        "haritaki": "Haritaki with honey",
    },
    "Grishma": {
        "hindi": "ग्रीष्म", "months": "Sun in sayana Vrishabha and Mithuna, about 20 Apr to 21 Jun (summer)", "named": "Shukra and Shuchi (Jyeshtha, Ashadha)", "kaal": "Adana",
        "agni": "Mild", "bala": "Low", "rasa": "Katu (pungent)",
        "dosha": "Vata gathers, Kapha settles", "focus": "Vata",
        "eat": ["Sweet, cool, liquid and light food", "Rice with ghee and milk", "Sattu, panna, sherbet with mishri",
                "Melons, cucumber, gourds", "Plenty of water kept in an earthen pot"],
        "avoid": ["Salty, sour and pungent food", "Hot spices", "Alcohol", "Heavy exercise",
                  "Midday sun without cover"],
        "lifestyle": ["Short afternoon rest is allowed in this ritu only", "Light cotton clothes",
                      "Moonlit evenings and cool rooms", "Sandal paste on the skin"],
        "haritaki": "Haritaki with jaggery",
    },
    "Varsha": {
        "hindi": "वर्षा", "months": "Sun in sayana Karka and Simha, about 21 Jun to 23 Aug (monsoon)", "named": "Nabhas and Nabhasya (Shravana, Bhadrapada)", "kaal": "Visarga (Moon returns strength)",
        "agni": "Weakest of the year", "bala": "Low", "rasa": "Amla (sour)",
        "dosha": "Vata aggravates, Pitta gathers", "focus": "Vata",
        "eat": ["Old barley, wheat and rice", "Moong soup with ginger", "Boiled and cooled water",
                "Ghee, a little salt and sour to keep Vata calm", "Honey in small amounts"],
        "avoid": ["Leafy greens (folk and Chaturmas custom; they carry insects and silt)", "Stale or street food",
                  "River water",
                  "Curd at night", "Overeating and sleeping by day"],
        "lifestyle": ["Stay dry, and keep the feet clean", "Light fumigation of the home with herbs",
                      "Avoid strenuous exertion", "Basti under a vaidya for high Vata"],
        "haritaki": "Haritaki with rock salt",
    },
    "Sharad": {
        "hindi": "शरद", "months": "Sun in sayana Kanya and Tula, about 23 Aug to 23 Oct (autumn)", "named": "Isha and Urja (Ashwina, Kartika)", "kaal": "Visarga",
        "agni": "Moderate", "bala": "Moderate", "rasa": "Lavana (salty)",
        "dosha": "Pitta aggravates (prakopa)", "focus": "Pitta",
        "eat": ["Sweet, bitter and light food", "Rice, wheat, barley, moong", "Ghee, amla, pomegranate, parwal",
                "Hamsodaka: water warmed by day and cooled by moonlight", "Mishri, kheer on Sharad Purnima"],
        "avoid": ["Curd, hot spices, sour pickles", "Fried food", "Fish and heavy meats",
                  "Sun exposure and sleeping by day", "Alcohol"],
        "lifestyle": ["Evening moonlight", "Light clothes and flower garlands", "Blood-cooling foods",
                      "Virechana under a vaidya for high Pitta"],
        "haritaki": "Haritaki with sugar",
    },
    "Hemanta": {
        "hindi": "हेमन्त", "months": "Sun in sayana Vrishchika and Dhanu, about 23 Oct to 21 Dec (early winter)", "named": "Sahas and Sahasya (Margashirsha, Pausha)", "kaal": "Visarga",
        "agni": "Strongest of the year", "bala": "Highest", "rasa": "Madhura (sweet)",
        "dosha": "Pitta settles (prashamana) after its Sharad peak", "focus": "Vata",
        "eat": ["Sweet, sour and salty food in full measure", "New rice, wheat, urad", "Ghee, sesame, dry fruits, jaggery",
                "Milk, sugarcane products", "Warm water"],
        "avoid": ["Light, dry or cold food", "Very small meals, even when losing weight: strong agni needs real food", "Fasting for long hours",
                  "Cold drinks"],
        "lifestyle": ["Oil massage, sunbathing, exercise", "Warm clothes and warm rooms",
                      "This is the season to build strength"],
        "haritaki": "Haritaki with dry ginger",
    },
}

RITU_NAMES_NOTE = (
    "The texts name each ritu by two months (Hemanta: Sahas and Sahasya, that is Margashirsha and Pausha). Since then "
    "the equinoxes have slipped about 24 degrees, so the real seasons now begin roughly a month before those names: the "
    "lunar month on a given day can carry the name of the previous ritu. This guide follows the Sun's real (sayana) "
    "position, as the weather does; lunar months are used only for the month verse, Chaturmas and tithi rules.")

# Folk verse: चैते गुड़ बैसाखे तेल, जेठे पंथ असाढ़े बेल ...
MAAS = {
    "Chaitra": ("गुड़ (jaggery)", "Jaggery and heavy sweets feed the Kapha that is melting in spring.",
                "Neem leaves, the classic Chaitra Navratri tonic"),
    "Vaishakha": ("तेल (oily food)", "Rising heat makes oily, fried food hard to digest.", "Bel sherbet and light food"),
    "Jyeshtha": ("पंथ (long journeys on foot)", "The hottest month: not a food rule but rest from exertion in the sun.",
                 "Water, panna, and rest at noon"),
    "Ashadha": ("बेल (bael fruit)", "Ripe bael is heavy and hard to digest (Charaka Su 27); as the rains near and agni falls, "
                "the summer bel sherbet is stopped.",
                "Light, warm and freshly cooked food"),
    "Shravana": ("साग (leafy greens)", "Monsoon greens carry insects and silt, and digestion is at its weakest.",
                 "Harad, moong and old grains"),
    "Bhadrapada": ("दही (curd)", "Curd feeds Pitta and blocks channels when digestion is low.", "Til and light meals"),
    "Ashwina": ("करेला (bitter gourd)", "Folk tradition rests it this month, and milk is avoided too (see Chaturmas).",
                "Jaggery in small amounts, amla and sweet fruits"),
    "Kartika": ("मही (buttermilk)", "Sour buttermilk is held to stir the Pitta that is still settling after Sharad (folk custom).",
                "Radish in moderation, amla"),
    "Margashirsha": ("जीरा (cumin excess)", "Heating spices are kept in moderation.", "Oil, ghee and warm food"),
    "Pausha": ("धनिया (coriander)", "A cooling herb is set aside in the coldest weeks.", "Milk and sesame"),
    "Magha": ("मिश्री (rock sugar)", "Excess sugar feeds gathering Kapha.", "Ghee and khichdi"),
    "Phalguna": ("चना (chickpea)", "Dry, Vata-raising chana is rested as Kapha turns.",
                 "Rising early, and light breakfasts"),
}
MAAS_VERSE = ("चैते गुड़ बैसाखे तेल, जेठे पंथ असाढ़े बेल। सावन साग न भादों दही, क्वार करेला न कातिक मही। "
              "अगहन जीरा पूसे धना, माघे मिश्री फागुन चना। ई बारह जो देय बचाय, वहि घर बैद कबौं न जाय॥")
# Sayings kept in the Hindi belt (many credited to Ghagh), with one line from Vagbhata. Wording varies by region.
SAYINGS = [
    {"key": "maas_avoid", "title": "What to leave out, month by month", "source": "Folk saying, Awadh and Bhojpur",
     "text": MAAS_VERSE,
     "meaning": "Twelve things to give up in twelve months. Keep to them, and the vaidya need never visit your home."},
    {"key": "maas_take", "title": "What to take, month by month", "source": "Folk saying, attributed to Ghagh",
     "text": "सावन हर्रे भादों चीत, क्वार मास गुड़ खायउ मीत। कातिक मूली अगहन तेल, पूस में करै दूध से मेल। "
             "माघ मास घिउ खींचरी खाय, फागुन उठि के प्रात नहाय। चैत मास में नीम बेसहनी, बैसाखे में खाय जड़हनी। "
             "जेठ मास जो दिन में सोवै, ओकर जर असाढ़ में रोवै॥",
     "meaning": "The other half of the first verse: harad in Shravana, jaggery in Ashwina, radish in Kartika, milk in "
                "Pausha, ghee and khichdi in Magha, an early bath in Phalguna, neem in Chaitra. Rest in the heat of "
                "Jyeshtha, and fever will not trouble you in Ashadha."},
    {"key": "after_meal", "title": "After the meal", "source": "Folk saying, Bhojpur and Awadh",
     "text": "खाय के मूतै, सूतै बाम, काहे बैद बसावै गाम॥",
     "meaning": "Pass urine after eating and rest on your left side. Then why would a village need a vaidya?"},
    {"key": "on_waking", "title": "On waking", "source": "Folk saying, attributed to Ghagh",
     "text": "प्रातःकाल खटिया से उठि के, पियै तुरन्तै पानी। वा घर में वैद न आवै, बात घाघ की जानी॥",
     "meaning": "Drink water as soon as you rise, and the vaidya stays away."},
    {"key": "three_words", "title": "Three words for good health", "source": "Attributed to Acharya Vagbhata",
     "text": "हितभुक् मितभुक् ऋतभुक्",
     "meaning": "Eat what is good for you, eat in measure, and eat with the season."},
]
SAYINGS_BY_KEY = {x["key"]: x for x in SAYINGS}


def sayings_for(region_key):
    """The region's own sayings (in its script) plus the pan-Indian Sanskrit line; never another region's."""
    from .aahaar_regions import PAN_INDIAN_SAYINGS, SAYINGS as REGIONAL
    out = []
    for item in REGIONAL.get(region_key, []) + [{"key": k} for k in PAN_INDIAN_SAYINGS]:
        if "key" in item:
            base = SAYINGS_BY_KEY[item["key"]]
            out.append({"lang": "sa" if item["key"] == "three_words" else "hi", "text": base["text"], "roman": "",
                        "title": base["title"], "meaning": base["meaning"], "source": base["source"]})
        else:
            out.append({"title": "", **item})
    return out


CHATURMAS = {"Shravana": "leafy greens", "Bhadrapada": "curd", "Ashwina": "milk", "Kartika": "dals (dvidala)"}


def chaturmas_item(masa, paksha_tithi):
    """What the Chaturmas vrata gives up today, or None. It ends on Devutthana Ekadashi (Kartika Shukla 11)."""
    item = CHATURMAS.get(masa)
    n = tithi_number(paksha_tithi) or 0
    if item and masa == "Kartika" and n != 30 and n > 11 and ("shukla" in (paksha_tithi or "").lower() or n == 15):
        return None
    return item


# Which rule wins when two of today's rules disagree. Health first, then the season (classical, for everyone),
# then observances (only for those who keep them), then folk customs.
PRECEDENCE = [
    ("Your own health", "A vaidya's or doctor's advice, and any dosha imbalance you already have, come before "
                        "everything below."),
    ("Season (ritu)", "The classical base for everyone, every day (Charaka, Ashtanga Hridaya, Sushruta)."),
    ("Observances you keep", "Chaturmas, Ekadashi and the tithi rules bind only those who keep them. When kept, they "
                             "take a food out for that day; they do not add new staples."),
    ("Folk customs", "The month verse and weekday foods are gentle suggestions. Drop them whenever they clash with "
                     "the rules above."),
]

# Food words that tie together the different rule lists; the first name is the one shown.
_FOOD_WORDS = {
    "radish": ("radish", "mooli", "मूली"), "curd": ("curd", "dahi", "दही"),
    "buttermilk": ("buttermilk", "मही", "chaas", "chhach"), "milk": ("milk", "दूध"),
    "dals": ("dal", "dvidala", "urad", "masoor", "moong", "chana", "chickpea", "arhar"),
    "brinjal": ("brinjal", "baingan"), "bael": ("bael", "bel ", "बेल"), "coconut": ("coconut",),
    "sesame": ("sesame", "til"), "bottle gourd": ("bottle gourd", "lauki"), "parwal": ("parwal",),
    "leafy greens": ("leafy greens", "साग"), "jaggery": ("jaggery", "गुड़"), "beans": ("beans", "sem)"),
}


def _foods_in(text):
    low = f" {(text or '').lower()} "
    return {name for name, words in _FOOD_WORDS.items()
            if any((f" {w}" in low or f"({w}" in low) if w.isascii() else w in low for w in words)}


def day_guidance(ritu_name, masa, paksha_tithi, weekday, lang="en"):
    """Today's rules split into their frames (rank 1 = season ... 4 = weekday), and how each clash is resolved.
    The clash detection reads the English text; ``lang="hi"`` renders the result in Hindi."""
    ritu, maas, vaar = RITU.get(ritu_name), MAAS.get(masa), VAAR[weekday]
    chaturmas, tithi_avoid = chaturmas_item(masa, paksha_tithi), TITHI_AVOID.get(tithi_number(paksha_tithi))
    layers = []
    if ritu:
        layers.append({"key": "ritu", "rank": 1, "label": f"{ritu_name} (season)", "who": "Everyone",
                       "favour": "; ".join(ritu["eat"]), "avoid": "; ".join(ritu["avoid"]), "note": ""})
    if chaturmas:
        layers.append({"key": "chaturmas", "rank": 2, "label": "Chaturmas vrata", "who": "Only if you keep it",
                       "favour": "", "avoid": chaturmas, "span": "until Devutthana Ekadashi",
                       "note": "A vrata observance until Devutthana Ekadashi, not a seasonal rule."})
    if tithi_avoid:
        layers.append({"key": "tithi", "rank": 2, "label": f"{paksha_tithi} (tithi)", "who": "Only if you keep it",
                       "favour": "", "avoid": tithi_avoid, "span": "today", "note": "Brahma Vaivarta Purana; for this tithi only."})
    if maas:
        layers.append({"key": "maas", "rank": 3, "label": f"{masa} (month verse)", "who": "Folk custom",
                       "favour": maas[2], "avoid": maas[0], "note": maas[1]})
    layers.append({"key": "vaar", "rank": 4, "label": f"{weekday} · {vaar['planet']} (weekday)", "who": "Folk custom",
                   "favour": vaar["favour"], "avoid": vaar["avoid"], "note": ""})

    clashes = []
    for fav in layers:
        for food in sorted(_foods_in(fav["favour"])):
            for avd in layers:
                if avd is fav or food not in _foods_in(avd["avoid"]):
                    continue
                clashes.append(_resolve(food, fav, avd))
    foods_out = set().union(*(_foods_in(x["avoid"]) for x in layers))
    foods_in = set().union(*(_foods_in(x["favour"]) for x in layers))
    if "buttermilk" in foods_out and "curd" in foods_in and "curd" not in foods_out:
        clashes.append({"food": "curd", "dairy": True, "text": "Curd and buttermilk are both sour dairy. On a day "
                        "buttermilk is set aside, take curd only by day, fresh and not sour, or leave it out."})
    out = {"layers": layers, "clashes": clashes, "precedence": PRECEDENCE}
    if lang == "hi":
        out = _guidance_hi(out, ritu_name, masa, paksha_tithi, weekday)
    return out


FOOD_HI = {"radish": "मूली", "curd": "दही", "buttermilk": "छाछ", "milk": "दूध", "dals": "दालें", "brinjal": "बैंगन",
           "bael": "बेल", "coconut": "नारियल", "sesame": "तिल", "bottle gourd": "लौकी", "parwal": "परवल",
           "leafy greens": "साग", "jaggery": "गुड़", "beans": "सेम"}
WHO_HI = {"Everyone": "सबके लिए", "Only if you keep it": "केवल व्रत रखने वालों के लिए", "Folk custom": "लोक-परम्परा"}
NOTE_HI = {"A vrata observance until Devutthana Ekadashi, not a seasonal rule.": "देवउठनी एकादशी तक का व्रत-नियम, ऋतु का नियम नहीं।",
           "Brahma Vaivarta Purana; for this tithi only.": "ब्रह्म वैवर्त पुराण; केवल इस तिथि के लिए।"}


def _guidance_hi(g, ritu_name, masa, paksha_tithi, weekday):
    from .aahaar_hi import hi
    from ..pdf.i18n import terms
    labels = {"ritu": f"{terms(ritu_name, 'hi')} (ऋतु)", "chaturmas": "चातुर्मास व्रत",
              "tithi": f"{terms(paksha_tithi or '', 'hi')} (तिथि)", "maas": f"{terms(masa or '', 'hi')} (मास-दोहा)",
              "vaar": f"{terms(weekday, 'hi')} · {hi(VAAR[weekday]['planet'])} (वार)"}
    spans = {"chaturmas": "देवउठनी एकादशी तक", "tithi": "आज"}
    layers = []
    for x in g["layers"]:
        if x["key"] == "ritu":
            ritu = RITU[ritu_name]
            favour, avoid = "; ".join(hi(e) for e in ritu["eat"]), "; ".join(hi(e) for e in ritu["avoid"])
        else:
            favour, avoid = hi(x["favour"]), hi(x["avoid"])
        layers.append({**x, "label": labels[x["key"]], "who": WHO_HI.get(x["who"], x["who"]), "favour": favour,
                       "avoid": avoid, "note": NOTE_HI.get(x["note"], hi(x["note"])), "span": spans.get(x["key"], "")})
    by_key = {x["key"]: x for x in layers}
    clashes = []
    for c in g["clashes"]:
        if c.get("dairy"):
            clashes.append({**c, "text": "दही और छाछ दोनों खट्टे दुग्ध पदार्थ हैं। जिस दिन छाछ छोड़ी जाए, उस दिन दही केवल दिन में, "
                                         "ताज़ा और बिना खट्टा, लें या न लें।"})
            continue
        food, fav, avd = FOOD_HI.get(c["food"], c["food"]), by_key[c["fav"]], by_key[c["avd"]]
        if avd["rank"] == 1:
            text = f"{food}: कम करें। ऋतु का नियम पहले है; {fav['label']} की सलाह इसे नहीं बदलती।"
        elif avd["rank"] == 2:
            text = (f"{food}: {fav['label']} इसे अच्छा बताता है, {avd['label']} इसे छोड़ता है। यदि आप वह व्रत रखते हैं तो "
                    f"{food} {avd['span']} न लें; अन्यथा {fav['label']} मानें।")
        elif fav["rank"] < avd["rank"]:
            text = f"{food}: {fav['label']} इसे अच्छा बताता है; {avd['label']} की इसे छोड़ने की परम्परा वैकल्पिक है।"
        else:
            text = (f"{food}: {avd['label']} की परम्परा इसे छोड़ती है और {fav['label']} से ऊपर है, इसलिए लोक-परम्परा मानते हों "
                    f"तो आज इसे छोड़ें।")
        clashes.append({**c, "text": text})
    precedence = [(hi(a), hi(b)) for a, b in g["precedence"]]
    return {"layers": layers, "clashes": clashes, "precedence": precedence}


def _resolve(food, fav, avd):
    name = food.capitalize()
    if avd["rank"] == 1:
        text = f"{name}: reduce it. The season comes first; the {fav['label']} favour does not override it."
    elif avd["rank"] == 2:
        text = (f"{name}: {fav['label']} favours it, {avd['label']} sets it aside. If you keep that observance, "
                f"leave {food} out {avd['span']}; if not, follow {fav['label']}.")
    elif fav["rank"] < avd["rank"]:
        text = f"{name}: {fav['label']} favours it; the {avd['label']} custom to skip it is optional."
    else:
        text = (f"{name}: the {avd['label']} custom sets it aside and outranks the {fav['label']} favour, so skip it "
                f"today if you follow folk customs at all.")
    return {"food": food, "fav": fav["key"], "avd": avd["key"], "text": text}

# Index: tithi number within a paksha, 1-based. 15 = Purnima, 30 = Amavasya.
TITHI_AVOID = {
    1: "kushmanda (ash gourd, petha)", 2: "small brinjal (brihati)", 3: "parwal", 4: "radish (mooli)",
    5: "bael", 6: "neem", 7: "palm fruit (taad)", 8: "coconut", 9: "bottle gourd (lauki)",
    10: "kalambi (water spinach)", 11: "beans (sem), and all grains on Ekadashi vrata", 12: "poi (Malabar spinach)",
    13: "brinjal (baingan)", 14: "urad dal", 15: "sesame oil and kansa (bell metal) vessels",
    30: "sesame oil and kansa (bell metal) vessels",
}

VAAR = {
    "Sunday": {"planet": "Surya", "favour": "Wheat, jaggery, ghee, red lentils", "avoid": "Excess salt, oil massage, meat"},
    "Monday": {"planet": "Chandra", "favour": "Rice, milk, kheer, curd, white foods", "avoid": "Very sour or heating food"},
    "Tuesday": {"planet": "Mangal", "favour": "Jaggery, masoor, boondi; many keep a sweet-only vrat", "avoid": "Salt (on vrat), alcohol, meat"},
    "Wednesday": {"planet": "Budh", "favour": "Moong, green vegetables, ghee", "avoid": "Very heavy meals"},
    "Thursday": {"planet": "Guru", "favour": "Chana dal, besan, banana, ghee, turmeric", "avoid": "Banana for those on Guruwar vrat, excess salt"},
    "Friday": {"planet": "Shukra", "favour": "Curd, kheer, sweets, white foods", "avoid": "Sour food, for those on Santoshi vrat"},
    "Saturday": {"planet": "Shani", "favour": "Urad, black til, mustard oil, khichdi", "avoid": "Alcohol, meat"},
}

DOSHA = {
    "Vata": {
        "hindi": "वात", "element": "Air and space", "qualities": "dry, light, cold, rough, moving",
        "signs": "Gas, constipation, dry skin, joint pain, anxiety, poor sleep",
        "pacify": "Sweet, sour and salty tastes; warm, moist, oily food",
        "eat": ["Warm cooked meals on time", "Ghee, sesame oil", "Rice, wheat, moong", "Sweet ripe fruit, dates",
                "Warm milk with nutmeg", "Ginger, cumin, ajwain, hing"],
        "avoid": ["Dry snacks and raw salads", "Cold drinks and ice cream", "Beans and chana in excess",
                  "Skipping meals", "Late nights"],
    },
    "Pitta": {
        "hindi": "पित्त", "element": "Fire and water", "qualities": "hot, sharp, oily, light, sour",
        "signs": "Acidity, skin rashes, anger, loose motions, burning, excess heat",
        "pacify": "Sweet, bitter and astringent tastes; cool, mildly heavy food",
        "eat": ["Rice, wheat, barley", "Ghee, milk, coconut water", "Gourds, cucumber, leafy greens",
                "Pomegranate, amla, sweet grapes", "Coriander, fennel, cardamom"],
        "avoid": ["Chilli and hot spices", "Sour pickles, vinegar, sour curd", "Fried food, tea and coffee excess",
                  "Alcohol", "Missing lunch"],
    },
    "Kapha": {
        "hindi": "कफ", "element": "Earth and water", "qualities": "heavy, cold, oily, slow, sticky",
        "signs": "Heaviness, cough and cold, weight gain, sluggishness, excess sleep",
        "pacify": "Pungent, bitter and astringent tastes; light, warm, dry food",
        "eat": ["Barley, millets, old rice", "Moong, masoor, chana", "Bitter greens, karela, radish",
                "Ginger, black pepper, turmeric", "Honey (never heated) in warm water"],
        "avoid": ["Curd, cheese, cold milk", "Sweets and bakery food", "Fried food", "Sleeping by day",
                  "Heavy dinners"],
    },
}

# A modern approximation of Ashtanga Hridaya Sutrasthana 1.8: the doshas rule the first, middle and last thirds
# of the day and of the night. daily_rhythm() uses the real thirds from sunrise and sunset instead of clock hours.
DOSHA_CLOCK = [
    ("6 am - 10 am", "Kapha", "Move your body; keep breakfast light."),
    ("10 am - 2 pm", "Pitta", "Agni peaks: make this the main meal."),
    ("2 pm - 6 pm", "Vata", "Good for thinking and creative work."),
    ("6 pm - 10 pm", "Kapha", "Eat a light early dinner, then wind down."),
    ("10 pm - 2 am", "Pitta", "The body repairs itself: be asleep."),
    ("2 am - 6 am", "Vata", "Brahma muhurta: wake and meditate."),
]

MEAL_RULES = [
    "Eat only when the previous meal has been digested and hunger is real (Charaka Vimana 1.24).",
    "Fill the stomach one third with solid food, one third with liquid, and leave one third for the doshas "
    "(Charaka Vimana 2.3; Ashtanga Hridaya Sutrasthana 8 gives half solid, a quarter liquid, a quarter empty).",
    "Do not take milk with fish or sour fruit, ghee and honey in equal amounts, or heated honey "
    "(Charaka Sutrasthana 26 and 27; Sushruta Sutrasthana 20).",
    "Eat warm, unctuous food in measure, in a pleasant place, neither too fast nor too slow, without talking or "
    "laughing, with attention on the meal (Charaka Vimana 1.24).",
    "Sip water during the meal: taken before it weakens agni, after it adds weight (Ashtanga Hridaya Sutrasthana 8).",
]

# What each part of the guide rests on, after review against the four texts the owner named. Vangasena Samhita
# (Cikitsasara Samgraha) is arranged disease by disease with pathya-apathya inside each chapter; it has no separate
# dinacharya or ritucharya chapter to check this general guidance against, so it is not cited here.
CLASSICAL_SOURCES = [
    ("Ritu regimen (six seasons, rasa, strength, dosha cycle, eat and avoid)",
     "Ashtanga Hridaya Sutrasthana 3; Charaka Sutrasthana 6; Sushruta Sutrasthana 6", "Agrees"),
    ("Doshas by time of day and stage of life", "Ashtanga Hridaya Sutrasthana 1.8", "Agrees (thirds of day and night)"),
    ("Waking in Brahma muhurta, daily routine, exercise to half strength",
     "Ashtanga Hridaya Sutrasthana 2; Charaka Sutrasthana 5 and 7; Sushruta Chikitsa 24", "Agrees"),
    ("Rules of eating and the three parts of the stomach", "Charaka Vimana 1.24 and 2.3; Ashtanga Hridaya Sutrasthana 8",
     "Agrees"),
    ("Incompatible food (viruddha ahara)", "Charaka Sutrasthana 26; Sushruta Sutrasthana 20; Ashtanga Hridaya "
     "Sutrasthana 7", "Agrees"),
    ("Nature of grains, pulses, vegetables, fruits, milk, honey, ghee",
     "Charaka Sutrasthana 27; Sushruta Sutrasthana 46; Ashtanga Hridaya Sutrasthana 5 and 6", "Agrees; ripe bael "
     "corrected"),
    ("Pregnancy month by month", "Charaka Sharira 8; Sushruta Sharira 10", "Agrees; modern additions marked"),
    ("Obesity: barley, honey water, exercise", "Charaka Sutrasthana 21", "Agrees"),
    ("Ingredients unknown to the samhitas (potato, tomato, chilli, papaya, guava, cashew, peanut, chikoo, "
     "custard apple, cauliflower, cabbage)", "Later Nighantus and everyday practice", "Not classical"),
    ("Regional dishes, gym and protein targets, month verse, tithi and weekday foods",
     "Folk tradition, Brahma Vaivarta Purana, modern nutrition", "Not Ayurvedic samhita"),
]

DISCLAIMER = ("General guidance from classical Ayurveda and Hindu tradition, not medical advice. Your prakriti, age, "
              "health and medicines matter: consult a qualified vaidya or doctor before changing your diet, especially "
              "if you are pregnant, diabetic, or under treatment.")


def tithi_number(paksha_tithi):
    """1-15 for Shukla, 16-30 style names mapped back: returns 1-15, or 30 for Amavasya."""
    text = (paksha_tithi or "").lower()
    names = ["pratipada", "dvitiya", "tritiya", "chaturthi", "panchami", "shashthi", "saptami", "ashtami", "navami",
             "dashami", "ekadashi", "dvadashi", "trayodashi", "chaturdashi"]
    alt = {"dwitiya": 2, "dwadashi": 12, "shashti": 6, "pratipat": 1}
    if "amavasya" in text:
        return 30
    if "purnima" in text:
        return 15
    for i, n in enumerate(names, 1):
        if n in text:
            return i
    for n, i in alt.items():
        if n in text:
            return i
    return None


# ---------------------------------------------------------------------------
# Daily rhythm by pahar (a quarter of the day or of the night, from the real sunrise and sunset)
# ---------------------------------------------------------------------------

PAHARS = [
    # (English, Hindi, guidance)
    ("1st pahar of the day (morning)", "दिन का पहला पहर (प्रातः)",
     "Sandhya, exercise or yoga, bath. A light breakfast once you feel hungry."),
    ("2nd pahar of the day (forenoon)", "दिन का दूसरा पहर (पूर्वाह्न)",
     "Best hours for focused work. The main meal falls at its end, when digestion peaks."),
    ("3rd pahar of the day (afternoon)", "दिन का तीसरा पहर (अपराह्न)",
     "Let lunch digest: a short walk, no long nap (except in Grishma). Sip warm water."),
    ("4th pahar of the day (late afternoon)", "दिन का चौथा पहर (सायाह्न)",
     "Creative and social work. A light snack if needed; sandhya at sunset."),
    ("1st pahar of the night (evening)", "रात का पहला पहर (प्रदोष)",
     "A light dinner early in this pahar, family time, then wind down."),
    ("2nd pahar of the night (to midnight)", "रात का दूसरा पहर (निशीथ तक)",
     "Get to sleep early in this pahar, before the Kapha third ends: the body then digests the day and repairs itself."),
    ("3rd pahar of the night (after midnight)", "रात का तीसरा पहर",
     "Deep sleep. Waking now often points to excess Pitta or late meals."),
    ("4th pahar of the night (before dawn)", "रात का चौथा पहर (उषा काल)",
     "Brahma muhurta at its end: wake, drink water, meditate or study."),
]
DOSHA_HI = {"Kapha": "कफ", "Pitta": "पित्त", "Vata": "वात"}


def _doshas_between(a, b, thirds):
    names = []
    for start, end, name in thirds:
        if start < b and end > a and name not in names:
            names.append(name)
    return names


def daily_rhythm(d, lat, lon, tz_name):
    """Eight pahars with times and doshas, the three dosha periods of day and night, and meal times."""
    from datetime import timedelta
    import pytz
    from . import panchang_engine as pe
    tz = pytz.timezone(tz_name)
    sr, ss = pe.sun_times(d, lat, lon, tz)
    nsr, _ = pe.sun_times(d + timedelta(days=1), lat, lon, tz)
    if not (sr and ss and nsr):      # polar day or night: no pahars
        return None
    day, night = ss - sr, nsr - ss
    thirds = [(sr, sr + day / 3, "Kapha"), (sr + day / 3, sr + day * 2 / 3, "Pitta"), (sr + day * 2 / 3, ss, "Vata"),
              (ss, ss + night / 3, "Kapha"), (ss + night / 3, ss + night * 2 / 3, "Pitta"),
              (ss + night * 2 / 3, nsr, "Vata")]
    pahars = []
    for i, (name, hindi, tip) in enumerate(PAHARS):
        base, span = (sr, day) if i < 4 else (ss, night)
        a = base + span * (i % 4) / 4
        b = base + span * (i % 4 + 1) / 4
        doshas = _doshas_between(a, b, thirds)
        pahars.append({"n": i % 4 + 1, "is_day": i < 4, "name": name, "hindi": hindi, "tip": tip, "start": a, "end": b,
                       "doshas": doshas, "doshas_hi": [DOSHA_HI[x] for x in doshas],
                       "dosha_class": doshas[0].lower()})
    total = (nsr - sr).total_seconds()
    for p in pahars:                 # widths for the timeline bar (percent of the 24-hour cycle from sunrise)
        p["width"] = round((p["end"] - p["start"]).total_seconds() / total * 100, 2)
    meals = [
        ("Brahma muhurta: wake", "ब्रह्म मुहूर्त: जागरण", sr - timedelta(minutes=96), sr - timedelta(minutes=48)),
        ("Breakfast (light)", "नाश्ता (हल्का)", sr + timedelta(minutes=90), sr + timedelta(minutes=180)),
        ("Main meal (madhyahna)", "मुख्य भोजन (मध्याह्न)", sr + day * 2 / 5, sr + day * 3 / 5),
        ("Evening snack (optional)", "शाम का अल्पाहार (वैकल्पिक)", ss - timedelta(minutes=120), ss - timedelta(minutes=60)),
        ("Dinner (light, early)", "रात्रि भोजन (हल्का, जल्दी)", ss + timedelta(minutes=30), ss + timedelta(minutes=120)),
        ("Sleep by", "सोने का समय", ss + night / 3 - timedelta(minutes=30), ss + night / 3),
    ]
    return {"sunrise": sr, "sunset": ss, "next_sunrise": nsr, "pahars": pahars,
            "thirds": [{"start": a, "end": b, "dosha": n, "hindi": DOSHA_HI[n]} for a, b, n in thirds],
            "meals": [{"name": n, "hindi": h, "start": a, "end": b} for n, h, a, b in meals],
            "day_length": day, "night_length": night}
