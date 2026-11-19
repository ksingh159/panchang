# core/utils/muhurat.py
"""
Shubh muhurat for purchases and sales ("what to buy, when - and what not to").

Everything is derived from the shared PanchangEvent cache, so finding every
vehicle-purchase window of a year for any city is a few DB queries plus
in-memory interval maths - no ephemeris scanning per request.

Rules follow Muhurta Chintamani / common panchang practice:
  * Kraya (buying) nakshatras and Vikraya (selling) nakshatras
  * Rikta tithis (4, 9, 14) and Amavasya avoided for purchases
  * Bhadra (Vishti karana), Rahu Kaal avoided; the day's cautions name Bhadra's loka (Moon sign)
  * The nine inauspicious nitya yogas: Vyatipata and Vaidhriti in full, Parigha's first half and the first
    ghatis of Vishkumbha and Vajra (3), Shoola (5), Ganda and Atiganda (6) and Vyaghata (9), for every purpose
  * Panchak avoided for wood / furniture / roofing
  * Blackout periods by level (see BLOCKS): Kharmas, Adhik maas, Pitru Paksha, Holashtak,
    Chaturmas, Guru/Shukra Asta and a visible Grahan
  * Saturday, Tuesday and Sunday carry no capital-goods muhurat, matching the weekday lists below
  * Personal filter: Tarabalam + Chandrabalam from the natal Moon
"""
from datetime import date, datetime, timedelta

import pytz
import swisseph as swe

from . import grahan as gr
from . import panchang_engine as pe
from . import panchang_store as ps
from .constants import NAKSHATRA_NAMES, ZODIAC_SIGNS

N = {name: i for i, name in enumerate(NAKSHATRA_NAMES)}
WEEKDAY_EN = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
WEEKDAY_HI = ["Raviwar", "Somawar", "Mangalwar", "Budhwar", "Guruwar", "Shukrawar", "Shaniwar"]
RAHU_KAAL_PART = [7, 1, 6, 4, 5, 3, 2]   # 1/8th part of daytime, Sunday first

GOOD_TARAS = {2, 4, 6, 8, 9}
TARA_NAMES = ["Janma", "Sampat", "Vipat", "Kshema", "Pratyari", "Sadhana", "Naidhana", "Mitra", "Param Mitra"]
GOOD_CHANDRA_HOUSES = {1, 3, 6, 7, 10, 11}
GANDA_MOOL = {N["Ashwini"], N["Ashlesha"], N["Magha"], N["Jyeshtha"], N["Moola"], N["Revati"]}
RIKTA = {3, 8, 13, 18, 23, 28}          # Chaturthi, Navami, Chaturdashi (0-based tithi index)
AMAVASYA = 29


def _ns(*names):
    return {N[n] for n in names}


# Classical kraya / vikraya nakshatras (Muhurta Chintamani)
KRAYA = _ns("Ashwini", "Chitra", "Swati", "Shravana", "Shatabhisha", "Revati")
VIKRAYA = _ns("Bharani", "Krittika", "Ashlesha", "Vishakha", "Purva Phalguni", "Purva Ashadha", "Purva Bhadrapada")
CHARA = _ns("Punarvasu", "Swati", "Shravana", "Dhanishta", "Shatabhisha")   # movable - vehicles
STHIRA = _ns("Rohini", "Uttara Phalguni", "Uttara Ashadha", "Uttara Bhadrapada")   # fixed - property
MRIDU = _ns("Mrigashira", "Chitra", "Anuradha", "Revati")
LAGHU = _ns("Ashwini", "Pushya", "Hasta")

VIVAH_NAKSHATRAS = _ns("Rohini", "Mrigashira", "Magha", "Uttara Phalguni", "Hasta", "Swati", "Anuradha", "Moola",
                       "Uttara Ashadha", "Uttara Bhadrapada", "Revati")
VIVAH_TITHIS = {1, 2, 4, 6, 9, 10, 11, 12, 16, 17, 19, 21, 24, 25, 26, 27}   # 2, 3, 5, 7, 10-13 of either paksha (0-based)
VIVAH_SOLAR_MONTHS = {0, 1, 2, 7, 9, 10}     # Sun in Mesha, Vrishabha, Mithuna, Vrischika, Makara, Kumbha
VIVAH_BAD_YOGAS = {"Vyatipata", "Vaidhriti"}
# Griha pravesh and sanskars (0-based tithi index: 0-14 Shukla Pratipada-Purnima, 15-29 Krishna Pratipada-Amavasya)
GRIHA_PRAVESH_TITHIS = {1, 2, 4, 5, 6, 9, 10, 11, 12, 16, 17, 19}   # Shukla 2, 3, 5, 6, 7, 10-13; Krishna 2, 3, 5
SANSKAR_TITHIS = {1, 2, 4, 6, 9, 10, 12, 16, 17, 19}                # Shukla 2, 3, 5, 7, 10, 11, 13; Krishna 2, 3, 5
UPANAYAN_TITHIS = {1, 2, 4, 9, 10, 11, 16, 17, 19}                  # Shukla 2, 3, 5, 10, 11, 12; Krishna 2, 3, 5
SANSKAR_NAKSHATRAS = STHIRA | MRIDU | LAGHU | CHARA                 # fixed, soft, swift and movable
UTTARAYANA_MONTHS = {9, 10, 0, 1, 2}                                 # Sun in Makara, Kumbha, Mesha, Vrishabha, Mithuna

# Tyajya (avoided) part of the inauspicious nitya yogas, in ghatis of 24 minutes from the yoga's start instant.
# Muhurta Chintamani 1.34: Vyatipata, Vaidhriti and the first 3 ghatis of Vishkambha and Vajra; 1.35: half of
# Parigha (read as the first half), 5 ghatis of Shoola, 6 of Ganda and Atiganda, 9 of Vyaghata, "varjyah sarveshu
# karmasu" (avoided in all work). Applying them to every purpose is the classical rule; exceptions an acharya may
# weigh (1.42: a good yoga overcoming a bad one, a strong Lagna) are not modelled.
GHATI = timedelta(minutes=24)
YOGA_TYAJYA = {"Vishkumbha": 3, "Vajra": 3, "Shoola": 5, "Atiganda": 6, "Ganda": 6, "Vyaghata": 9,
               "Parigha": "half", "Vyatipata": "whole", "Vaidhriti": "whole"}
YOGA_TYAJYA_NOTE = {
    3: "The first 3 ghatis (72 minutes) of this yoga are avoided in all work (Muhurta Chintamani 1.34).",
    5: "The first 5 ghatis (2 hours) of this yoga are avoided in all work (Muhurta Chintamani 1.35).",
    6: "The first 6 ghatis (2 hours 24 minutes) of this yoga are avoided in all work (Muhurta Chintamani 1.35).",
    9: "The first 9 ghatis (3 hours 36 minutes) of this yoga are avoided in all work (Muhurta Chintamani 1.35).",
    "half": "Half of this yoga is avoided in all work (Muhurta Chintamani 1.35); we take the first half, the usual "
            "reading.",
    "whole": "The whole yoga is avoided for auspicious work (Muhurta Chintamani 1.34).",
}

# Bhadra's loka by the Moon's sign, Muhurta Chintamani 1.45: "kumbhakarkadvaye martye svarge'bje'jattraye'lige /
# stridhanurjukanakre'dho bhadra tatraiva tatphalam" - Bhadra gives her result in the world where she is. The loka is
# read per segment, so it changes at the Moon's sign ingress, not at the start of the karana.
BHADRA_LOKA = {3: "mrityu", 4: "mrityu", 10: "mrityu", 11: "mrityu",
               0: "swarga", 1: "swarga", 2: "swarga", 7: "swarga",
               5: "patala", 6: "patala", 8: "patala", 9: "patala"}
BHADRA_CAUTION = {
    "mrityu": ("Bhadra on earth (Mrityu lok)",
               "The Moon is in Karka, Simha, Kumbha or Meena, so Bhadra is on earth and her effect falls here "
               "(Muhurta Chintamani 1.45). Avoid auspicious work, purchases, new starts and travel."),
    "swarga": ("Bhadra in Swarga lok",
               "The Moon is in Mesha, Vrishabha, Mithuna or Vrishchika, so Bhadra's influence is assigned to heaven "
               "(Muhurta Chintamani 1.45). Our muhurats still leave all Bhadra out, as a cautious policy."),
    "patala": ("Bhadra in Patala lok",
               "The Moon is in Kanya, Tula, Dhanu or Makara, so Bhadra's influence is assigned to the lower world "
               "(Muhurta Chintamani 1.45). Our muhurats still leave all Bhadra out, as a cautious policy."),
}


def yoga_tyajya(seg):
    """(start, end) of the avoided part of the segment's nitya yoga, or None."""
    part = YOGA_TYAJYA.get(seg["yoga"])
    if part is None:
        return None
    ys, ye = seg["yoga_start"], seg["yoga_end"]
    if part == "whole":
        return ys, ye
    if part == "half":
        return ys, ys + (ye - ys) / 2
    return ys, min(ye, ys + GHATI * part)

PURPOSES = {
    "vivah": {
        "title": "Vivah (Marriage)",
        "items": "wedding ceremony, phere, saptapadi",
        "group": "ceremony",
        "nakshatras": VIVAH_NAKSHATRAS,
        "weekdays": {0, 1, 3, 4, 5, 6},
        "best_weekdays": {1, 3, 4, 5},
        "tithis": VIVAH_TITHIS, "solar_months": VIVAH_SOLAR_MONTHS, "bad_yogas": VIVAH_BAD_YOGAS,
        "avoid_panchak": False, "major": True, "level": "vivah", "night": True,
        "why": "The eleven vivah nakshatras, with the Sun in Mesha, Vrishabha, Mithuna, Vrischika, Makara or Kumbha. "
               "Chaturmas, Kharmas, Adhik maas, Pitru Paksha, Holashtak, Guru and Shukra Asta and a visible grahan are "
               "excluded, as are Bhadra, Rikta tithis, Amavasya and the Vyatipata and Vaidhriti yogas. Always confirm "
               "the final lagna with your family pandit: this list does not check the couple's own charts.",
    },
    # Griha pravesh and the sanskars. Rules as commonly read from Muhurta Chintamani (Griha Pravesha and Sanskara
    # prakaranas); lists differ between panchangs, so an acharya should confirm them. None of them checks the Lagna
    # or the family's own charts.
    "griha-pravesh": {
        "title": "Griha Pravesh (Housewarming)",
        "items": "entering a new house, vastu shanti, griha shanti, kalash sthapana",
        "group": "ceremony",
        "nakshatras": STHIRA | MRIDU | _ns("Dhanishta", "Shatabhisha"),
        "weekdays": {1, 3, 4, 5}, "best_weekdays": {3, 4},
        "tithis": GRIHA_PRAVESH_TITHIS, "bad_yogas": VIVAH_BAD_YOGAS,
        # Owner's acharya, 2026-11-19: only the first half of Dhanishta (Moon in Makara) - the second half (Moon in
        # Kumbha) is Panchak and is avoided for griha pravesh.
        "nak_moon_signs": {N["Dhanishta"]: {9}},
        "avoid_panchak": False, "major": True, "level": "sanskar",
        "why": "Sthira (fixed) and Mridu (soft) nakshatras with Dhanishta and Shatabhisha, on Monday, Wednesday, "
               "Thursday or Friday, in a waxing Moon or the first days of the waning one. Only the first half of "
               "Dhanishta (Moon in Makara) is used: its second half falls in Panchak. Chaturmas, Kharmas, Adhik "
               "maas, Pitru Paksha, Holashtak, Guru and Shukra Asta and a visible grahan are left out. Your pandit will "
               "fix the lagna for the moment of entry.",
    },
    "mundan": {
        "title": "Mundan (Chudakarma)",
        "items": "first haircut, mundan sanskar, chaula",
        "group": "ceremony",
        "nakshatras": _ns("Ashwini", "Mrigashira", "Punarvasu", "Pushya", "Hasta", "Chitra", "Swati", "Jyeshtha",
                          "Shravana", "Dhanishta", "Shatabhisha", "Revati"),
        "weekdays": {1, 3, 4, 5},
        "tithis": SANSKAR_TITHIS, "bad_yogas": VIVAH_BAD_YOGAS,
        "avoid_panchak": False, "major": True, "level": "sanskar",
        "why": "Laghu, Chara and Mridu nakshatras with Jyeshtha, on Monday, Wednesday, Thursday or Friday. Most "
               "families do mundan in the child's first, third or fifth year; follow your family's custom for the age "
               "and the place (many go to a temple or a tirtha).",
    },
    "namkaran": {
        "title": "Namkaran (Naming Ceremony)",
        "items": "naming ceremony, namkaran sanskar",
        "group": "ceremony",
        "nakshatras": SANSKAR_NAKSHATRAS,
        "weekdays": {1, 3, 4, 5},
        "bad_yogas": VIVAH_BAD_YOGAS,
        "avoid_panchak": False, "major": True, "level": "sanskar",
        "why": "Many families name the child on the 11th or 12th day after birth, and that custom needs no other "
               "date. When the ceremony is held later, these days have a gentle nakshatra (fixed, soft, swift or "
               "movable) and a good weekday, outside Rikta tithis, Amavasya and Bhadra.",
    },
    "annaprashan": {
        "title": "Annaprashan (First Solid Food)",
        "items": "first rice or kheer, annaprashan sanskar",
        "group": "ceremony",
        "nakshatras": SANSKAR_NAKSHATRAS,
        "weekdays": {1, 3, 4, 5},
        "tithis": SANSKAR_TITHIS, "bad_yogas": VIVAH_BAD_YOGAS,
        "avoid_panchak": False, "major": True, "level": "sanskar",
        "why": "Fixed, soft, swift and movable nakshatras on Monday, Wednesday, Thursday or Friday. Custom is the "
               "sixth or eighth month for a boy and the fifth or seventh for a girl; check the child's age with your "
               "pandit.",
    },
    "upanayan": {
        "title": "Upanayan (Sacred Thread)",
        "items": "janeu, yagnopavit, upanayan sanskar",
        "group": "ceremony",
        "nakshatras": SANSKAR_NAKSHATRAS - _ns("Rohini", "Anuradha"),
        "weekdays": {0, 1, 3, 4, 5}, "best_weekdays": {3, 4},
        "tithis": UPANAYAN_TITHIS, "solar_months": UTTARAYANA_MONTHS, "bad_yogas": VIVAH_BAD_YOGAS,
        "avoid_panchak": False, "major": True, "level": "sanskar",
        "why": "Upanayan is held in Uttarayana, with the Sun in Makara, Kumbha, Mesha, Vrishabha or Mithuna (Kharmas "
               "in Meena is left out), so there are no dates from the middle of July to the middle of January. Thursday "
               "(Guru) and Wednesday are best. The boy's age and the family's gotra customs are for your pandit.",
    },
    "vehicle": {
        "title": "Vehicle Purchase",
        "items": "car, bike, scooter, tractor, any vehicle",
        "nakshatras": CHARA | LAGHU | MRIDU,
        "weekdays": {1, 3, 4, 5},
        "avoid_panchak": False, "major": True,
        "why": "Chara (movable) and Laghu nakshatras suit things that move; Monday, Wednesday, "
               "Thursday and Friday are preferred.",
    },
    "property": {
        "title": "Property / Land Purchase",
        "items": "house, flat, plot, land, shop",
        "nakshatras": STHIRA | MRIDU | _ns("Punarvasu", "Pushya", "Vishakha", "Moola"),
        "weekdays": {1, 3, 4, 5},
        "avoid_panchak": True, "major": True,
        "why": "Sthira (fixed) nakshatras give stability to what is bought for the long term.",
    },
    "gold": {
        "title": "Gold, Silver & Jewellery",
        "items": "gold, silver, diamonds, gemstones, jewellery, coins",
        "nakshatras": KRAYA | LAGHU | STHIRA | _ns("Rohini", "Mrigashira", "Punarvasu", "Anuradha", "Dhanishta"),
        "weekdays": {0, 1, 3, 4, 5},
        "avoid_panchak": False, "major": False, "level": "durable",
        "why": "Pushya is the king of nakshatras for gold; Guru-Pushya and Ravi-Pushya days, "
               "Akshaya Tritiya and Dhanteras are the most sought after.",
    },
    "electronics": {
        "title": "Electronics & Gadgets",
        "items": "mobile, laptop, tablet, TV, camera, printer",
        "nakshatras": KRAYA | LAGHU | MRIDU | _ns("Rohini", "Punarvasu", "Uttara Phalguni", "Dhanishta"),
        "weekdays": {1, 3, 4, 5},
        "avoid_panchak": False, "major": False, "level": "durable",
        "why": "Mercury rules electronics and communication - Wednesday and Mercury hora are favoured.",
    },
    "furniture": {
        "title": "Furniture & Wooden Items",
        "items": "bed, sofa, wardrobe, doors, wooden items",
        "nakshatras": STHIRA | MRIDU | LAGHU,
        "weekdays": {1, 3, 4, 5},
        "avoid_panchak": True, "major": False, "level": "durable",
        "why": "Buying wood, beds or making a roof during Panchak is specifically prohibited.",
    },
    "clothes": {
        "title": "New Clothes (Vastra Dharana)",
        "items": "clothes, wedding attire, sarees",
        "nakshatras": _ns("Ashwini", "Rohini", "Punarvasu", "Pushya", "Uttara Phalguni", "Hasta", "Chitra", "Swati",
                          "Vishakha", "Anuradha", "Uttara Ashadha", "Dhanishta", "Uttara Bhadrapada", "Revati"),
        "weekdays": {3, 4, 5},
        "avoid_panchak": False, "major": False, "level": "durable",
        "why": "Wednesday, Thursday and Friday are best for wearing or buying new clothes.",
    },
    "business": {
        "title": "Start Business / New Venture",
        "items": "shop opening, new firm, new account, signing an agreement",
        "nakshatras": LAGHU | MRIDU | STHIRA | _ns("Punarvasu", "Swati", "Shravana", "Dhanishta"),
        "weekdays": {1, 3, 4, 5},
        "avoid_panchak": False, "major": True,
        "why": "Laghu, Mridu and Sthira nakshatras with Jupiter, Mercury or Venus hora.",
    },
    "groceries": {
        "title": "Monthly Grocery & FMCG Stock",
        "items": "atta, rice, dal, oil, spices, tea, soap, detergent, packaged food, big online grocery orders",
        "nakshatras": KRAYA | LAGHU | _ns("Rohini", "Punarvasu", "Anuradha"),
        "weekdays": {1, 3, 4, 5},
        "avoid_panchak": False, "major": False,
        "why": "Filling the kitchen is treated as Annapurna's blessing: kraya and Laghu nakshatras, avoiding "
               "Rikta tithis, Amavasya and Bhadra.",
    },
    "beauty": {
        "title": "Beauty, Skin Care & Personal Care",
        "items": "cosmetics, perfume, skin care, hair care, grooming kits, salon packages",
        "nakshatras": MRIDU | LAGHU | _ns("Rohini", "Uttara Phalguni", "Shravana"),
        "weekdays": {1, 3, 4, 5},
        "avoid_panchak": False, "major": False, "level": "durable",
        "why": "Venus governs beauty: Mridu (soft) nakshatras and Friday are preferred.",
    },
    "appliances": {
        "title": "Home Appliances & Consumer Durables",
        "items": "refrigerator, AC, washing machine, TV, kitchen appliances, inverter, water purifier",
        "nakshatras": KRAYA | LAGHU | STHIRA | _ns("Punarvasu", "Anuradha", "Dhanishta"),
        "weekdays": {1, 3, 4, 5},
        "avoid_panchak": False, "major": False, "level": "durable",
        "why": "Long-life goods favour Sthira nakshatras alongside the kraya list.",
    },
    "machinery": {
        "title": "Machinery & Capital Goods",
        "items": "plant and machinery, generator, tractor, CNC, solar panels, commercial kitchen, office equipment",
        "nakshatras": STHIRA | LAGHU | _ns("Punarvasu", "Swati", "Shravana", "Dhanishta", "Revati"),
        "weekdays": {1, 3, 4, 5},
        "avoid_panchak": False, "major": True,
        "why": "Machinery is iron, and iron is not bought on Saturday, so Shani's day is used for servicing and not "
               "for purchase. Sthira nakshatras suit assets meant to last.",
    },
    "investment": {
        "title": "Investment (SIP, Shares, FD, Bonds, Insurance)",
        "items": "starting a SIP, buying shares or mutual funds, fixed deposit, gold bonds, PPF, insurance policy",
        "nakshatras": LAGHU | MRIDU | STHIRA | _ns("Punarvasu", "Swati", "Shravana", "Dhanishta"),
        "weekdays": {1, 3, 4, 5}, "best_weekdays": {3, 4},
        "bad_yogas": {"Vyatipata", "Vaidhriti"},
        "avoid_panchak": False, "major": False, "level": "durable",
        "why": "Sthira nakshatras for money meant to stay and grow, Laghu and Mridu for a smooth start. Wednesday "
               "(Budh, trade) and Thursday (Guru, wealth) are best. This is traditional timing, not financial advice.",
    },
    "loan": {
        "title": "Taking a Loan (Rin Grahan)",
        "items": "home loan, car loan, personal or business loan, borrowing from family",
        "nakshatras": (CHARA | LAGHU | MRIDU) - _ns("Hasta"),
        "weekdays": {1, 3, 4, 5},
        "bad_yogas": {"Vriddhi", "Vyatipata", "Vaidhriti"}, "avoid_sankranti": True,
        "avoid_panchak": False, "major": False, "level": "durable",
        "why": "Tradition says never to borrow on a Tuesday, on a Sankranti, in Vriddhi yoga or in Hasta nakshatra: "
               "a debt taken then grows and is hard to clear. Chara and Laghu nakshatras suit money that should move on "
               "and be repaid quickly.",
    },
    "lending": {
        "title": "Lending Money (Rin Dena)",
        "items": "lending to friends or family, giving credit, advancing payment",
        "nakshatras": STHIRA | MRIDU | _ns("Ashwini", "Pushya", "Punarvasu", "Shravana", "Dhanishta"),
        "weekdays": {1, 4, 5},
        "bad_yogas": {"Vyatipata", "Vaidhriti"}, "avoid_sankranti": True,
        "avoid_panchak": False, "major": False, "level": "durable",
        "why": "Sthira (fixed) nakshatras are chosen so that the money comes back. Folk custom avoids lending on "
               "Tuesday and Wednesday, when money given is said not to return.",
    },
    "repay": {
        "title": "Repaying a Loan (Rin Mukti)",
        "items": "paying back a loan or EMI in full, closing a credit card or debt",
        "nakshatras": set(range(27)),
        "weekdays": {0, 1, 2, 3, 4, 5, 6}, "best_weekdays": {2},
        "avoid_panchak": False, "major": False, "allow_rikta": True,
        "why": "Mangal is the remover of debt: Tuesday is the classical day to repay, and reciting the Rin Mochana "
               "Mangala Stotra is customary. Any day outside Rahu Kaal and Bhadra will do.",
    },
    "buy": {
        "title": "General Buying (Kraya)",
        "items": "shopping, stock or commodity purchase, raw material",
        "nakshatras": KRAYA | LAGHU,
        "weekdays": {1, 3, 4, 5},
        "avoid_panchak": False, "major": False,
        "why": "Muhurta Chintamani lists Ashwini, Chitra, Swati, Shravana, Shatabhisha and Revati for buying.",
    },
    "sell": {
        "title": "Selling (Vikraya)",
        "items": "selling goods, property, vehicle, booking profit",
        "nakshatras": VIKRAYA,
        "weekdays": {0, 1, 2, 3, 4, 5, 6},
        "avoid_panchak": False, "major": False,
        "allow_rikta": True,
        "why": "The three Purvas, Bharani, Krittika, Ashlesha and Vishakha are the classical selling nakshatras.",
    },
}

# Popular weekday guidance by the day's ruling planet (traditional; varies by region)
WEEKDAY_GUIDE = {
    0: {"planet": "Sun", "buy": "copper, wheat, red or saffron items, medicines, government papers",
        "avoid": "new footwear and hardware purchases are avoided by many families"},
    1: {"planet": "Moon", "buy": "silver, pearls, rice, milk products, white clothes, water purifiers",
        "avoid": "large loans; travel East (Disha Shool)"},
    2: {"planet": "Mars", "buy": "red items, medicines, kitchen utensils of copper",
        "avoid": "lending money, cosmetics, new clothes; travel North (Disha Shool)"},
    3: {"planet": "Mercury", "buy": "books, stationery, electronics, mobiles, green items, investments",
        "avoid": "travel North (Disha Shool)"},
    4: {"planet": "Jupiter", "buy": "gold, yellow items, religious books, education, property",
        "avoid": "travel South (Disha Shool)"},
    5: {"planet": "Venus", "buy": "vehicles, clothes, cosmetics, perfume, jewellery, home decor",
        "avoid": "travel West (Disha Shool)"},
    6: {"planet": "Saturn", "buy": "urad, black chana, and servicing of what you already own",
        "avoid": "iron, mustard oil, salt, black sesame, leather and black items (donate them instead); "
                 "travel East (Disha Shool)"},
}

# What to put in the cart each weekday, from each graha's traditional significations (karakatva).
# Associations are customary and regional, not shastric rules for individual products.
WEEKDAY_SHOPPING = {
    0: {"fmcg": "wheat atta, jaggery, honey, saffron, ghee, red lentils (masoor), oranges, herbal tea, sunscreen",
        "home": "copper bottles and vessels, red or orange linen, sun-facing decor, wall clocks",
        "capital": "gold and silver only, best on Ravi Pushya; other big purchases wait for Monday",
        "avoid": "iron and hardware, new footwear, tools"},
    1: {"fmcg": "rice, milk, curd, paneer, sugar, mishri, bottled water, white flour, face wash, moisturiser, baby care",
        "home": "silver items, white bedsheets, crockery, glassware, mattress, pillows",
        "capital": "water purifier, refrigerator, RO plant, aquarium, pumps and plumbing, dairy equipment",
        "avoid": "large new loans, sharp or iron tools"},
    2: {"fmcg": "red chilli, masoor, jaggery, spices, tea, coffee, energy drinks, first-aid supplies",
        "home": "copper utensils, fire safety kit, red linen",
        "capital": "no big purchase today: vehicles, property and machinery wait for Wednesday",
        "avoid": "lending money, cosmetics, new clothes, milk products in bulk, major purchases"},
    3: {"fmcg": "moong, green vegetables, green tea, cardamom, pens and stationery, printer ink, school supplies",
        "home": "books, educational toys, green plants and planters, bags, wallets",
        "capital": "laptop, mobile, tablet, printer, networking gear, software licences, office equipment, SIP or investment",
        "avoid": "large cash lending"},
    4: {"fmcg": "chana dal, besan, turmeric, ghee, banana, bakery items, yellow sweets, kesar, dry fruits",
        "home": "brass vessels, puja items, religious books, yellow linen, school and college supplies",
        "capital": "gold, house or flat booking, education fees, furniture, long-term insurance, business expansion",
        "avoid": "soap, detergent, shampoo, hair oil, brooms (many homes skip washing and hair care on Thursday)"},
    5: {"fmcg": "perfume, cosmetics, skin and hair care, sugar, mishri, curd, sweets, rose water, dairy products",
        "home": "clothes, sarees, jewellery, curtains, sofa covers, home decor, kitchen appliances, wall art",
        "capital": "car, bike, scooter, AC, TV, music system, luxury furniture, mattress",
        "avoid": "sour items such as lemon, tamarind and vinegar in bulk (Santoshi Maa vrat homes)"},
    6: {"fmcg": "urad, black chana, tea, packaged staples, cleaning supplies for the workplace",
        "home": "storage boxes, work wear, old-furniture restoration supplies",
        "capital": "no purchase today: machinery, tractors, vehicles and property wait. Service and repair what you own",
        "avoid": "iron and steel, machinery, vehicles, mustard oil, salt, black sesame, leather shoes, ink, scissors (donate them instead)"},
}

DISHA_SHOOL = {
    0: ("West", "Eat ghee, daliya or a paan before leaving"),
    1: ("East", "Drink milk or look into a mirror before leaving"),
    2: ("North", "Eat jaggery (gud) before leaving"),
    3: ("North", "Eat sesame (til) or coriander before leaving"),
    4: ("South", "Eat curd before leaving"),
    5: ("West", "Eat barley or curd before leaving"),
    6: ("East", "Eat ginger or urad dal before leaving"),
}


# Colours to wear: the day's graha, the season and the month's festivals. Customary, not shastric rules.
DAY_COLOURS = {
    0: {"planet": "Surya", "wear": [("Red", "#c62828"), ("Orange", "#ef6c00"), ("Saffron", "#f4a300"), ("Gold", "#c9a227")],
        "avoid": "black and dark blue", "why": "Surya's colours of fire and dawn bring confidence and authority."},
    1: {"planet": "Chandra", "wear": [("White", "#ffffff"), ("Silver", "#c0c0c0"), ("Cream", "#f3e9d2"), ("Light blue", "#9ecbea")],
        "avoid": "very dark shades", "why": "Chandra's soft, cool colours calm the mind."},
    2: {"planet": "Mangal", "wear": [("Red", "#c62828"), ("Maroon", "#7b1f1f"), ("Coral", "#ff7f50"), ("Orange", "#ef6c00")],
        "avoid": "black", "why": "Mangal's red gives energy and courage; Hanuman devotees wear red or saffron."},
    3: {"planet": "Budh", "wear": [("Green", "#2e7d32"), ("Emerald", "#00897b"), ("Light green", "#9ccc65"), ("Turquoise", "#26a69a")],
        "avoid": "nothing in particular", "why": "Budh's green helps speech, study and trade."},
    4: {"planet": "Guru", "wear": [("Yellow", "#f9c80e"), ("Gold", "#c9a227"), ("Saffron", "#f4a300"), ("Cream", "#f3e9d2")],
        "avoid": "black and dark blue", "why": "Guru's yellow is worn for learning, worship and the Guruwar vrat."},
    5: {"planet": "Shukra", "wear": [("White", "#ffffff"), ("Pink", "#f48fb1"), ("Pastel blue", "#b3d4f0"), ("Silver", "#c0c0c0")],
        "avoid": "very dark shades", "why": "Shukra's bright whites and pastels bring charm and harmony."},
    6: {"planet": "Shani", "wear": [("Black", "#212121"), ("Navy", "#1a237e"), ("Dark blue", "#283593"), ("Purple", "#5e35b1")],
        "avoid": "bright red", "why": "Shani's dark blue and black are worn to please him; many donate black items."},
}
RITU_COLOURS = {
    "Vasanta": ([("Basanti yellow", "#f9d71c"), ("Spring green", "#8bc34a")], "Yellow of mustard fields, worn from Vasant Panchami."),
    "Grishma": ([("White", "#ffffff"), ("Cream", "#f3e9d2"), ("Pastels", "#cfe8d5")], "Light colours in cotton reflect the heat."),
    "Varsha": ([("Green", "#2e7d32"), ("Light colours", "#d8ecf3")], "Hariyali green of the rains; quick-drying fabric."),
    "Sharad": ([("White", "#ffffff"), ("Red", "#c62828"), ("Cream", "#f3e9d2")], "White for the clear autumn moon; red for Navratri."),
    "Hemanta": ([("Maroon", "#7b1f1f"), ("Saffron", "#f4a300"), ("Mustard", "#d4a017")], "Warm shades in wool as the cold sets in."),
    "Shishira": ([("Deep red", "#8e1b1b"), ("Black", "#212121"), ("Brown", "#6d4c41")],
                 "Dark warm colours hold the sun's heat; black is worn on Makar Sankranti in Maharashtra and Karnataka."),
}
MAAS_COLOURS = {
    "Chaitra": ([("Red", "#c62828"), ("Yellow", "#f9c80e")], "Navratri and new year (Gudi Padwa, Ugadi): new clothes in red and yellow."),
    "Vaishakha": ([("White", "#ffffff"), ("Gold", "#c9a227")], "Light clothes in the heat; gold for Akshaya Tritiya."),
    "Jyeshtha": ([("White", "#ffffff"), ("Light blue", "#9ecbea")], "The hottest month: white cotton."),
    "Ashadha": ([("Yellow", "#f9c80e"), ("White", "#ffffff")], "Yellow for Guru Purnima and the Rath Yatra."),
    "Shravana": ([("Green", "#2e7d32"), ("Saffron", "#f4a300")], "Green bangles and clothes for Sawan and Hariyali Teej; saffron for Kanwar."),
    "Bhadrapada": ([("Yellow", "#f9c80e"), ("Red", "#c62828")], "Krishna's pitambar yellow for Janmashtami; red for Teej and Ganesh Chaturthi."),
    "Ashwina": ([("Red", "#c62828"), ("White", "#ffffff")], "Red for Durga during Navratri; white for Sharad Purnima."),
    "Kartika": ([("Red", "#c62828"), ("Gold", "#c9a227"), ("Yellow", "#f9c80e")], "Red and gold for Karwa Chauth and Diwali; yellow for Chhath."),
    "Margashirsha": ([("Yellow", "#f9c80e"), ("Saffron", "#f4a300")], "Vishnu's month: yellow and saffron."),
    "Pausha": ([("Saffron", "#f4a300"), ("Red", "#c62828")], "Surya's month: warm saffron and red."),
    "Magha": ([("Yellow", "#f9c80e"), ("White", "#ffffff")], "Yellow for Vasant Panchami; white for the Magha snan."),
    "Phalguna": ([("White", "#ffffff"), ("Pink", "#f48fb1")], "White for Mahashivratri and for playing Holi."),
}


def colour_guide(vaar, ritu, masa):
    """What to wear: the weekday's graha colours, then the season's and the month's."""
    r = RITU_COLOURS.get(ritu)
    m = MAAS_COLOURS.get((masa or "").replace("Adhik", "").strip())
    return {"day": DAY_COLOURS[vaar], "ritu": ritu, "ritu_wear": r[0] if r else [], "ritu_why": r[1] if r else "",
            "masa": masa, "maas_wear": m[0] if m else [], "maas_why": m[1] if m else ""}


MONEY_KEYS = ("investment", "loan", "lending", "repay")

# What each weekday means for money, in the order Sunday..Saturday. Folk and Muhurta tradition, not financial advice.
MONEY_DAY = {
    "investment": [
        "Sunday is not among the days used for starting an investment.",
        "Monday is acceptable for starting an investment if the nakshatra is right.",
        "Tuesday is not used for starting an investment; Mangal's day is kept for clearing debts.",
        "Wednesday (Budh, the planet of trade) is one of the two best days to invest.",
        "Thursday (Guru, the giver of wealth) is the best day to start an investment meant to grow.",
        "Friday (Shukra) is acceptable, and favoured for gold and jewellery.",
        "Saturday is not among the days used for starting an investment.",
    ],
    "loan": [
        "Sunday is not among the days used for borrowing.",
        "Monday is acceptable for borrowing if the nakshatra is right.",
        "Tuesday: never borrow on Mangalvar. A loan taken today is said to keep growing.",
        "Wednesday is acceptable for borrowing if the nakshatra is right.",
        "Thursday is acceptable for borrowing if the nakshatra is right.",
        "Friday is acceptable for borrowing if the nakshatra is right.",
        "Saturday is not among the days used for borrowing.",
    ],
    "lending": [
        "Sunday is not among the days used for lending.",
        "Monday is good for lending when the nakshatra is fixed (sthira).",
        "Tuesday: avoid lending. Money given on Mangalvar is said not to come back.",
        "Wednesday: avoid lending. Folk custom says money lent on Budhvar does not return.",
        "Thursday is good for lending when the nakshatra is fixed (sthira).",
        "Friday is good for lending when the nakshatra is fixed (sthira).",
        "Saturday is not among the days used for lending.",
    ],
    "repay": [
        "Sunday is fine for repaying; Tuesday is the best day.",
        "Monday is fine for repaying; Tuesday is the best day.",
        "Tuesday is the best day to repay. Mangal is called Rinaharta, the remover of debt, in the Rin Mochana "
        "Mangala Stotra. Pay outside Rahu Kaal.",
        "Wednesday is fine for repaying; Tuesday is the best day.",
        "Thursday is fine for repaying; Tuesday is the best day.",
        "Friday is fine for repaying; Tuesday is the best day.",
        "Saturday is fine for repaying; Tuesday is the best day.",
    ],
}


# ---------------------------------------------------------------------------
# Natal Moon (for Tarabalam / Chandrabalam)
# ---------------------------------------------------------------------------

def natal_moon(birth_date, birth_time, tz_name):
    """(nakshatra index, rashi index) of the natal Moon, or None."""
    if not birth_date or not birth_time:
        return None
    tz = pytz.timezone(tz_name or "Asia/Kolkata")
    dt = tz.localize(datetime.combine(birth_date, birth_time))
    jd = pe.dt_to_jd(dt)
    ang, _ = pe.angle_and_speed(jd, "nakshatra")
    return int(ang // (360 / 27)), int(ang // 30)


def natal_from_user(user):
    p = getattr(user, "profile", None) if user and user.is_authenticated else None
    if not p or not p.birth_date or not p.birth_time:
        return None
    return natal_moon(p.birth_date, p.birth_time, p.birth_timezone)


def tara_of(nak, natal_nak):
    t = ((nak - natal_nak) % 27) % 9 + 1
    return t, TARA_NAMES[t - 1], t in GOOD_TARAS


def chandra_house(sign, natal_sign):
    h = (sign - natal_sign) % 12 + 1
    return h, h in GOOD_CHANDRA_HOUSES


# ---------------------------------------------------------------------------
# Day segmentation
# ---------------------------------------------------------------------------

def _local(dt_utc, tz):
    return pytz.utc.localize(dt_utc).astimezone(tz)


def _value_at(rows, t):
    for r in rows:
        if r[0] <= t < r[1]:
            return r
    return None


def day_segments(start, end, lat, lon, tz_name):
    """
    For each local date in [start, end]: sunrise frame plus atomic segments in
    which nakshatra, tithi, karana and Moon sign are constant.
    """
    tz = pytz.timezone(tz_name)
    s_utc = tz.localize(datetime.combine(start - timedelta(days=1), datetime.min.time())).astimezone(pytz.utc)
    e_utc = tz.localize(datetime.combine(end + timedelta(days=2), datetime.min.time())).astimezone(pytz.utc)
    ps.ensure_years(s_utc.year, e_utc.year)
    s_n, e_n = s_utc.replace(tzinfo=None), e_utc.replace(tzinfo=None)

    def load(kind):
        return [(_local(r.start_utc, tz), _local(r.end_utc, tz), r.number, r.name)
                for r in ps.events_overlapping(kind, s_n, e_n)]

    naks, tithis, karanas, signs, sun_naks, yogas, sun_signs = (load(k) for k in (
        "nakshatra", "tithi", "karana", "moon_sign", "sun_nakshatra", "yoga", "sun_sign"))
    days = []
    d = start
    sr, ss = pe.sun_times(d, lat, lon, tz)
    while d <= end:
        nsr, nss = pe.sun_times(d + timedelta(days=1), lat, lon, tz)
        vaar = (d.weekday() + 1) % 7            # 0 = Sunday
        part = (ss - sr) / 8
        rk = (sr + part * (RAHU_KAAL_PART[vaar] - 1), sr + part * RAHU_KAAL_PART[vaar])
        cuts = {sr, nsr}
        for rows in (naks, tithis, karanas, signs, yogas, sun_signs):
            for a, b, *_ in rows:
                if sr < a < nsr:
                    cuts.add(a)
        cuts = sorted(cuts)
        segs = []
        for a, b in zip(cuts, cuts[1:]):
            mid = a + (b - a) / 2
            nk, tt, kr, sg = (_value_at(r, mid) for r in (naks, tithis, karanas, signs))
            sn, yg, ss_ = _value_at(sun_naks, mid), _value_at(yogas, mid), _value_at(sun_signs, mid)
            if not (nk and tt and kr and sg and sn and yg and ss_):
                continue
            segs.append({
                "start": a, "end": b, "nak": nk[2], "nak_name": nk[3], "nak_end": nk[1],
                "tithi": tt[2], "tithi_name": tt[3], "tithi_end": tt[1],
                "karana": kr[3], "moon_sign": sg[2], "sun_nak": sn[2], "yoga": yg[3], "sun_sign": ss_[2],
                "yoga_start": yg[0], "yoga_end": yg[1],
            })
        days.append({"date": d, "sunrise": sr, "sunset": ss, "next_sunrise": nsr, "vaar": vaar,
                     "rahu_kaal": rk, "segments": segs})
        d += timedelta(days=1)
        sr, ss = nsr, nss
    return days


# ---------------------------------------------------------------------------
# Special yogas
# ---------------------------------------------------------------------------

SARVARTH = {
    0: _ns("Ashwini", "Pushya", "Hasta", "Moola", "Uttara Phalguni", "Uttara Ashadha", "Uttara Bhadrapada"),
    1: _ns("Mrigashira", "Rohini", "Pushya", "Anuradha", "Shravana"),
    2: _ns("Ashwini", "Krittika", "Ashlesha", "Uttara Bhadrapada"),
    3: _ns("Rohini", "Anuradha", "Mrigashira", "Hasta", "Krittika"),
    4: _ns("Revati", "Anuradha", "Pushya", "Punarvasu", "Ashwini"),
    5: _ns("Revati", "Anuradha", "Ashwini", "Punarvasu", "Shravana"),
    6: _ns("Rohini", "Swati", "Shravana"),
}
AMRIT = {0: N["Hasta"], 1: N["Mrigashira"], 2: N["Ashwini"], 3: N["Anuradha"],
         4: N["Pushya"], 5: N["Revati"], 6: N["Rohini"]}
PUSHKAR_TITHIS = {1, 6, 11, 16, 21, 26}       # Dwitiya, Saptami, Dwadashi (Bhadra tithis)
PUSHKAR_DAYS = {0, 2, 6}
DWIPUSHKAR_NAK = _ns("Mrigashira", "Chitra", "Dhanishta")
TRIPUSHKAR_NAK = _ns("Krittika", "Punarvasu", "Uttara Phalguni", "Vishakha", "Uttara Ashadha", "Purva Bhadrapada")
RAVI_YOGA_COUNTS = {4, 6, 9, 10, 13, 20}

YOGA_INFO = {
    "sarvartha-siddhi": ("Sarvartha Siddhi Yoga", "Weekday + nakshatra combination that increases the probability of success in most works."),
    "amrit-siddhi": ("Amrit Siddhi Yoga", "Nectar combination of weekday and nakshatra - a favourable time to begin good work."),
    "guru-pushya": ("Guru Pushya Yoga", "Pushya nakshatra on Thursday - one of the most favourable times of the year for gold and investments."),
    "ravi-pushya": ("Ravi Pushya Yoga", "Pushya nakshatra on Sunday - favourable for purchases, medicine and mantra practice."),
    "dwipushkar": ("Dwipushkar Yoga", "Results tend to repeat twice - favourable for buying; avoid losses or selling assets."),
    "tripushkar": ("Tripushkar Yoga", "Results tend to repeat three times - favourable for purchases and investment; avoid debts and losses."),
    "ravi-yoga": ("Ravi Yoga", "Sun-Moon nakshatra count of 4, 6, 9, 10, 13 or 20 - said to reduce many doshas of the day."),
}


def segment_yogas(seg, vaar):
    out = []
    if seg["nak"] in SARVARTH[vaar]:
        out.append("sarvartha-siddhi")
    if AMRIT[vaar] == seg["nak"]:
        out.append("amrit-siddhi")
    if seg["nak"] == N["Pushya"] and vaar == 4:
        out.append("guru-pushya")
    if seg["nak"] == N["Pushya"] and vaar == 0:
        out.append("ravi-pushya")
    if vaar in PUSHKAR_DAYS and seg["tithi"] in PUSHKAR_TITHIS:
        if seg["nak"] in DWIPUSHKAR_NAK:
            out.append("dwipushkar")
        if seg["nak"] in TRIPUSHKAR_NAK:
            out.append("tripushkar")
    if (seg["nak"] - seg["sun_nak"]) % 27 + 1 in RAVI_YOGA_COUNTS:
        out.append("ravi-yoga")
    return out


def _merge(windows, min_minutes=5):
    """Join touching/overlapping windows that share a key; drop slivers."""
    out, last = [], {}
    for w in sorted(windows, key=lambda w: w["start"]):
        prev = last.get(w["key"])
        if prev is not None and w["start"] <= prev["end"]:
            prev["end"] = max(prev["end"], w["end"])
            prev["notes"] = sorted(set(prev["notes"]) | set(w["notes"]))
        else:
            item = dict(w)
            out.append(item)
            last[w["key"]] = item
    return [w for w in out if (w["end"] - w["start"]) >= timedelta(minutes=min_minutes)]


def _cached(name, fn, *key):
    """Share location-level results between all visitors (Django cache; ~1 km grid)."""
    from django.core.cache import cache
    parts = [str(round(k, 2)) if isinstance(k, float) else str(k) for k in key]
    ck = "muhurat:" + name + ":" + ":".join(parts).replace(" ", "_")
    hit = cache.get(ck)
    if hit is None:
        hit = fn()
        cache.set(ck, hit, 60 * 60 * 24 * 7)
    return hit


def special_yogas(start, end, lat, lon, tz_name, kinds=None):
    """List of special yoga windows, merged per yoga (cached per location and range)."""
    return _cached("yogas2", lambda: _special_yogas(start, end, lat, lon, tz_name, kinds),
                   start, end, float(lat), float(lon), tz_name, ",".join(sorted(kinds or [])))


def local_solar_time(dt, lon):
    """Sthaniya samay: clock time by the Sun at this longitude (4 minutes per degree from UTC)."""
    return dt.astimezone(pytz.utc).replace(tzinfo=None) + timedelta(minutes=4 * float(lon))


def _special_yogas(start, end, lat, lon, tz_name, kinds=None):
    found, sunrises = [], set()
    for day in day_segments(start, end, lat, lon, tz_name):
        sunrises |= {day["sunrise"], day["next_sunrise"]}
        for seg in day["segments"]:
            for key in segment_yogas(seg, day["vaar"]):
                if kinds and key not in kinds:
                    continue
                found.append({"key": key, "date": day["date"], "start": seg["start"], "end": seg["end"],
                              "notes": [seg["nak_name"]]})
    merged = _merge(found)
    for w in merged:
        w["name"], w["meaning"] = YOGA_INFO[w["key"]]
        w["weekday"] = WEEKDAY_EN[(w["date"].weekday() + 1) % 7]
        w["start_sunrise"], w["end_sunrise"] = w["start"] in sunrises, w["end"] in sunrises
        w["start_solar"], w["end_solar"] = local_solar_time(w["start"], lon), local_solar_time(w["end"], lon)
    return merged


# ---------------------------------------------------------------------------
# Blocked periods (from the festival cache)
# ---------------------------------------------------------------------------

# Which periods stop what.  "daily" needs (groceries, ordinary buying and selling) go on except during a grahan.
BLOCKS = {
    "kharmas": ("Kharmas", {"major", "vivah", "sanskar"}, "Marriage and major purchases wait until the Sun leaves Dhanu or Meena."),
    "adhik-maas": ("Adhik Maas", {"major", "vivah", "sanskar"}, "The extra month is kept for worship, so marriage and major purchases wait."),
    "holashtak": ("Holashtak", {"major", "vivah", "sanskar"}, "The eight days before Holi: no marriage or major purchase."),
    "pitru-paksha": ("Pitru Paksha", {"durable", "major", "vivah", "sanskar"}, "The fortnight for ancestors: no marriage or new purchases, except daily needs."),
    "chaturmas": ("Chaturmas", {"vivah", "sanskar"}, "From Devshayani to Devutthana Ekadashi: no marriage. Everyday buying continues."),
    "guru-asta": ("Guru Asta", {"vivah", "sanskar"}, "Jupiter is combust: no marriage."),
    "shukra-asta": ("Shukra Asta", {"vivah", "sanskar"}, "Venus is combust: no marriage."),
    "grahan": ("Grahan", {"daily", "durable", "major", "vivah", "sanskar"}, "A grahan is visible here: nothing new from sutak until moksha."),
}
# What each blackout means for griha pravesh and the sanskars (the notes above speak of marriage and purchases)
SANSKAR_NOTES = {
    "kharmas": "Griha pravesh and sanskars such as mundan and upanayan wait until the Sun leaves Dhanu or Meena.",
    "adhik-maas": "The extra month is kept for worship, so griha pravesh and sanskars wait.",
    "holashtak": "The eight days before Holi: griha pravesh and sanskars wait.",
    "pitru-paksha": "The fortnight for ancestors: griha pravesh and sanskars wait.",
    "chaturmas": "From Devshayani to Devutthana Ekadashi: griha pravesh, mundan and upanayan wait.",
    "guru-asta": "Jupiter is combust: griha pravesh and sanskars wait.",
    "shukra-asta": "Venus is combust: griha pravesh and sanskars wait.",
    "grahan": "A grahan is visible here: no ceremony from sutak until moksha.",
}
ASTA_ORB = {"guru-asta": (swe.JUPITER, 11, 11), "shukra-asta": (swe.VENUS, 10, 8)}   # degrees: direct, retrograde


def rule_level(rule):
    return rule.get("level") or ("major" if rule["major"] else "daily")


def _scan_asta(year):
    """(start, end, slug) for each spell of Jupiter or Venus lost in the Sun's rays, day by day."""
    out = []
    for slug, (body, orb_direct, orb_retro) in ASTA_ORB.items():
        run, d = None, date(year, 1, 1)
        while d.year == year:
            jd = swe.julday(d.year, d.month, d.day, 6.5)
            sun = swe.calc_ut(jd, swe.SUN, swe.FLG_SWIEPH)[0][0]
            pos = swe.calc_ut(jd, body, swe.FLG_SWIEPH | swe.FLG_SPEED)[0]
            gap = abs((pos[0] - sun + 180) % 360 - 180)
            if gap <= (orb_retro if pos[3] < 0 else orb_direct):
                run = (run[0], d) if run else (d, d)
            elif run:
                out.append((run[0], run[1], slug))
                run = None
            d += timedelta(days=1)
        if run:
            out.append((run[0], run[1], slug))
    return out


def _grahan_spells(year, lat, lon, tz_name):
    out = []
    for e in gr.eclipses_in_year(year):
        v = gr.local_view(e, lat, lon, tz_name)
        if v.get("sutak_applies"):
            out.append((v["sutak_start"].date(), v["sutak_end"].date(), "grahan"))
    return out


def _periods_for_year(y, lat, lon, tz_name):
    from .festival_calculations import get_festivals_between
    fests = get_festivals_between(date(y, 1, 1) - timedelta(days=40), date(y, 12, 31))
    out = [(f["date"], f["end_date"], f["slug"]) for f in fests if f["slug"] in BLOCKS]
    by_slug = {f["slug"]: f["date"] for f in fests if f["date"].year == y}
    if "devshayani-ekadashi" in by_slug and "devutthana-ekadashi" in by_slug:
        out.append((by_slug["devshayani-ekadashi"], by_slug["devutthana-ekadashi"], "chaturmas"))
    out += _scan_asta(y)
    if lat is not None:
        out += _grahan_spells(y, lat, lon, tz_name)
    return out


def blocked_periods(start, end, level="major", lat=None, lon=None, tz_name=None):
    """[(from, to, name, what it stops)] touching [start, end] for this level of work; a place adds its grahans."""
    seen, out = set(), []
    for y in range(start.year, end.year + 1):
        rows = _cached("periods", lambda: _periods_for_year(y, lat, lon, tz_name), y, lat or 0.0, lon or 0.0, tz_name or "-")
        for d0, d1, slug in rows:
            name, levels, note = BLOCKS[slug]
            if level == "sanskar":
                note = SANSKAR_NOTES.get(slug, note)
            if level in levels and d0 <= end and d1 >= start and (d0, slug) not in seen:
                seen.add((d0, slug))
                out.append((d0, d1, name, note))
    return sorted(out, key=lambda b: b[0])


# ---------------------------------------------------------------------------
# Purchase / sale muhurat
# ---------------------------------------------------------------------------

def _subtract(a, b, cuts):
    """Remove each (c0, c1) in cuts from [a, b); returns list of intervals."""
    parts = [(a, b)]
    for c0, c1 in cuts:
        nxt = []
        for x, y in parts:
            if c1 <= x or c0 >= y:
                nxt.append((x, y))
                continue
            if x < c0:
                nxt.append((x, c0))
            if c1 < y:
                nxt.append((c1, y))
        parts = nxt
    return [(x, y) for x, y in parts if (y - x) >= timedelta(minutes=20)]


def find_muhurats(purpose, start, end, lat, lon, tz_name, natal=None, include_night=False, days=None):
    """
    Good windows for ``purpose`` between local dates [start, end].
    ``natal`` = (nakshatra index, rashi index) adds Tarabalam/Chandrabalam filtering.
    ``days`` reuses an already built day_segments() list.
    """
    rule = PURPOSES[purpose]
    blocked = blocked_periods(start, end, rule_level(rule), lat, lon, tz_name)
    results = []
    for day in days or day_segments(start, end, lat, lon, tz_name):
        d = day["date"]
        if day["vaar"] not in rule["weekdays"]:
            continue
        if any(b[0] <= d <= b[1] for b in blocked):
            continue
        if rule.get("avoid_sankranti") and len({s["sun_sign"] for s in day["segments"]}) > 1:
            continue
        limit = day["next_sunrise"] if (include_night or rule.get("night")) else day["sunset"]
        for seg in day["segments"]:
            if seg["start"] >= limit or seg["nak"] not in rule["nakshatras"]:
                continue
            if seg["karana"] == "Vishti":
                continue
            if seg["moon_sign"] not in rule.get("nak_moon_signs", {}).get(seg["nak"], range(12)):
                continue
            if not rule.get("allow_rikta") and (seg["tithi"] in RIKTA or seg["tithi"] == AMAVASYA):
                continue
            if rule["avoid_panchak"] and seg["moon_sign"] in (10, 11):
                continue
            if "tithis" in rule and seg["tithi"] not in rule["tithis"]:
                continue
            if "solar_months" in rule and seg["sun_sign"] not in rule["solar_months"]:
                continue
            if seg["yoga"] in rule.get("bad_yogas", ()):
                continue
            notes, score = [], 2 if day["vaar"] in rule.get("best_weekdays", ()) else 1
            if natal:
                t_no, t_name, t_ok = tara_of(seg["nak"], natal[0])
                house, c_ok = chandra_house(seg["moon_sign"], natal[1])
                if not (t_ok and c_ok):
                    continue
                notes.append(f"{t_name} tara, Moon in {house}th from natal")
                score += 1
            yogas = segment_yogas(seg, day["vaar"])
            if purpose == "sell":
                yogas = [y for y in yogas if y not in ("dwipushkar", "tripushkar")]
            score += 2 * len([y for y in yogas if y != "ravi-yoga"]) + (1 if "ravi-yoga" in yogas else 0)
            notes += [YOGA_INFO[y][0] for y in yogas]
            cuts = [day["rahu_kaal"]]
            bad_part = yoga_tyajya(seg)
            if bad_part:
                cuts.append(bad_part)
            for a, b in _subtract(seg["start"], min(seg["end"], limit), cuts):
                results.append({
                    "date": d, "weekday": WEEKDAY_EN[day["vaar"]], "start": a, "end": b,
                    "nakshatra": seg["nak_name"], "tithi": seg["tithi_name"],
                    "paksha": "Shukla" if seg["tithi"] < 15 else "Krishna",
                    "score": score, "notes": notes,
                })
    return results


def muhurat_dates(purpose, start, end, lat, lon, tz_name, natal=None):
    """Windows grouped by date (cached per location; personalised results are per natal Moon)."""
    return _cached("dates4", lambda:  # bump when a rule changes (cached 7 days)
                   _muhurat_dates(purpose, start, end, lat, lon, tz_name, natal),
                   purpose, start, end, float(lat), float(lon), tz_name, natal or "-")


def _muhurat_dates(purpose, start, end, lat, lon, tz_name, natal=None):
    by_day = {}
    for w in find_muhurats(purpose, start, end, lat, lon, tz_name, natal):
        by_day.setdefault(w["date"], []).append(w)
    out = []
    for d in sorted(by_day):
        wins = []
        for w in by_day[d]:                       # join windows split only by a karana change
            if wins and w["start"] <= wins[-1]["end"] and w["nakshatra"] == wins[-1]["nakshatra"]:
                wins[-1]["end"] = w["end"]
                wins[-1]["notes"] = sorted(set(wins[-1]["notes"]) | set(w["notes"]))
                wins[-1]["score"] = max(wins[-1]["score"], w["score"])
            else:
                wins.append(dict(w))
        out.append({
            "date": d, "weekday": wins[0]["weekday"], "windows": wins,
            "score": max(w["score"] for w in wins),
            "nakshatras": sorted({w["nakshatra"] for w in wins}),
            "notes": sorted({n for w in wins for n in w["notes"]}),
        })
    return out


# ---------------------------------------------------------------------------
# Today's guidance (the "personal pandit" card)
# ---------------------------------------------------------------------------

def day_guidance(d, lat, lon, tz_name, natal=None):
    day = day_segments(d, d, lat, lon, tz_name)[0]
    vaar = day["vaar"]
    tz = pytz.timezone(tz_name)
    now = datetime.now(tz)
    seg_now = next((s for s in day["segments"] if s["start"] <= now < s["end"]), day["segments"][0])
    cautions = []
    for s in day["segments"]:
        if s["karana"] == "Vishti":
            key, note = BHADRA_CAUTION[BHADRA_LOKA[s["moon_sign"]]]
            cautions.append((key, s["start"], s["end"], note))
        bad_part = yoga_tyajya(s)
        if bad_part and bad_part[0] < s["end"] and bad_part[1] > s["start"]:
            cautions.append((f"{s['yoga']} yoga", max(bad_part[0], s["start"]), min(bad_part[1], s["end"]),
                             YOGA_TYAJYA_NOTE[YOGA_TYAJYA[s["yoga"]]]))
        if s["moon_sign"] in (10, 11):
            cautions.append(("Panchak", s["start"], s["end"],
                             "Avoid buying wood/furniture, roofing, southward travel and cremation rites without remedy."))
        if s["nak"] in GANDA_MOOL:
            cautions.append(("Ganda Mool nakshatra", s["start"], s["end"], "Births need Mool shanti; avoid new ventures."))
    cautions = _merge([{"key": c[0], "start": c[1], "end": c[2], "notes": [c[3]], "date": d} for c in cautions])
    cautions.insert(0, {"key": "Rahu Kaal", "start": day["rahu_kaal"][0], "end": day["rahu_kaal"][1],
                        "notes": ["Do not begin purchases, journeys or new work."], "date": d})

    good_for = []
    for key, rule in PURPOSES.items():
        wins = find_muhurats(key, d, d, lat, lon, tz_name, natal, days=[day])
        if wins:
            good_for.append({"key": key, "title": rule["title"], "windows": wins})

    personal = None
    if natal:
        t_no, t_name, t_ok = tara_of(seg_now["nak"], natal[0])
        house, c_ok = chandra_house(seg_now["moon_sign"], natal[1])
        personal = {
            "natal_nakshatra": NAKSHATRA_NAMES[natal[0]], "natal_rashi": ZODIAC_SIGNS[natal[1]],
            "tara": t_name, "tara_good": t_ok, "chandra_house": house, "chandra_good": c_ok,
            "until": min(seg_now["nak_end"], next((s["end"] for s in day["segments"]
                                                     if s["moon_sign"] != seg_now["moon_sign"]), seg_now["nak_end"])),
        }
    shool_dir, shool_remedy = DISHA_SHOOL[vaar]
    good = {g["key"]: g for g in good_for}
    money = []
    for k in MONEY_KEYS:
        rule = PURPOSES[k]
        reason, reason_naks = "", []
        if k not in good:
            if vaar in rule["weekdays"]:   # the weekday line already explains an excluded day
                naks = sorted({seg["nak"] for seg in day["segments"]})
                reason_naks = [NAKSHATRA_NAMES[n] for n in naks]
                reason = ("Today's nakshatra (" + ", ".join(reason_naks) + "), yoga or "
                          "Bhadra/Rahu Kaal leave no suitable window.")
        money.append({"key": k, "title": rule["title"], "why": rule["why"], "today": MONEY_DAY[k][vaar],
                      "reason": reason, "reason_naks": reason_naks, "windows": good[k]["windows"] if k in good else []})
    seg0 = day["segments"][0] if day["segments"] else None
    ritu = pe.RITU_BY_SIGN[seg0["sun_sign"]] if seg0 else ""
    month = ps.lunar_month_at(day["sunrise"].astimezone(pytz.utc).replace(tzinfo=None)) or {}
    return {
        "money": money,
        "colours": colour_guide(vaar, ritu, month.get("purnimanta")),
        "krishna": month.get("paksha") == "Krishna",
        "date": d, "weekday": WEEKDAY_EN[vaar], "vaar": WEEKDAY_HI[vaar],
        "sunrise": day["sunrise"], "sunset": day["sunset"],
        "guide": WEEKDAY_GUIDE[vaar],
        "shopping": WEEKDAY_SHOPPING[vaar],
        "disha_shool": {"direction": shool_dir, "remedy": shool_remedy},
        "cautions": cautions,
        "good_for": good_for,
        "special_yogas": [w for w in special_yogas(d, d, lat, lon, tz_name)],
        "personal": personal,
        "now": seg_now,
    }


LEGACY_CODES = {
    "sarvartha-siddhi": "SARVARTH_SIDDHI", "amrit-siddhi": "AMRIT_SIDDHI", "dwipushkar": "DWIPUSHKAR",
    "tripushkar": "TRIPUSHKAR", "ravi-yoga": "RAVI", "guru-pushya": "GURU_PUSHYA", "ravi-pushya": "RAVI_PUSHYA",
}


def upcoming_yoga_rows(start, days, lat, lon, tz_name):
    """Special yogas in the row format the home page table expects."""
    rows = []
    for w in special_yogas(start, start + timedelta(days=days), lat, lon, tz_name):
        rows.append({
            "yoga_type": LEGACY_CODES[w["key"]], "key": w["key"], "name": w["name"],
            "start_time": w["start"], "end_time": w["end"],
            "duration_hours": round((w["end"] - w["start"]).total_seconds() / 3600, 1),
            "weekday": w["weekday"], "nakshatra": ", ".join(w["notes"]), "tithi": "",
            "combination_description": f"{w['weekday']} + {', '.join(w['notes'])}",
        })
    return rows
