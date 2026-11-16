# core/utils/dosha_remedies.py
"""
Extra dosha checks for Kundali Milan and the traditional remedy (upaya) for each.

Matching doshas (between the two charts):
    Nadi, Bhakoot, Gana, Yoni-vair, Rajju, Vedha, Mahendra, Stree-Dirgha, Mangal
Individual chart doshas (each partner):
    Kaal Sarp, Pitra, Grahan, Guru Chandal, Shrapit, Angarak, Vish, Kemadruma

Remedies are the commonly prescribed shastric upayas; the page tells users to
have them performed through a qualified acharya.
"""
NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu", "Pushya", "Ashlesha",
    "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha",
    "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
]
ALIASES = {
    "Moola": "Mula", "Mool": "Mula", "Shatabhishak": "Shatabhisha", "Dhanishtha": "Dhanishta",
    "Jyestha": "Jyeshtha", "Purvashadha": "Purva Ashadha", "Uttarashadha": "Uttara Ashadha",
    "Mrigasira": "Mrigashira", "Aslesha": "Ashlesha", "Shravan": "Shravana", "Poorva Phalguni": "Purva Phalguni",
}
RASHIS = ["Mesh", "Vrishabh", "Mithun", "Kark", "Simha", "Kanya", "Tula", "Vrishchik", "Dhanu", "Makar", "Kumbh", "Meen"]
RASHI_LORD = ["Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter"]
FRIENDS = {
    "Sun": {"Moon", "Mars", "Jupiter"}, "Moon": {"Sun", "Mercury"}, "Mars": {"Sun", "Moon", "Jupiter"},
    "Mercury": {"Sun", "Venus"}, "Jupiter": {"Sun", "Moon", "Mars"}, "Venus": {"Mercury", "Saturn"},
    "Saturn": {"Mercury", "Venus"},
}


def norm_nak(name):
    name = (name or "").strip()
    return ALIASES.get(name, name)


def nak_index(name):
    try:
        return NAKSHATRAS.index(norm_nak(name))
    except ValueError:
        return None


# Rajju: Pada, Kati, Nabhi, Kantha, Shiro - repeating Ashwini..Ashlesha forward and back
_RAJJU_CYCLE = ["Pada", "Kati", "Nabhi", "Kantha", "Shiro", "Kantha", "Nabhi", "Kati", "Pada"]
RAJJU = {n: _RAJJU_CYCLE[i % 9] for i, n in enumerate(NAKSHATRAS)}
RAJJU_EFFECT = {
    "Shiro": "danger to the husband's longevity", "Kantha": "danger to the wife",
    "Nabhi": "trouble concerning children", "Kati": "poverty", "Pada": "constant travel / separation",
}

# Vedha (mutually obstructing) nakshatra pairs
_VEDHA = [("Ashwini", "Jyeshtha"), ("Bharani", "Anuradha"), ("Krittika", "Vishakha"), ("Rohini", "Swati"),
          ("Ardra", "Shravana"), ("Punarvasu", "Uttara Ashadha"), ("Pushya", "Purva Ashadha"),
          ("Ashlesha", "Mula"), ("Magha", "Revati"), ("Purva Phalguni", "Uttara Bhadrapada"),
          ("Uttara Phalguni", "Purva Bhadrapada"), ("Hasta", "Shatabhisha"),
          ("Mrigashira", "Dhanishta"), ("Mrigashira", "Chitra"), ("Chitra", "Dhanishta")]
VEDHA = {}
for a, b in _VEDHA:
    VEDHA.setdefault(a, set()).add(b)
    VEDHA.setdefault(b, set()).add(a)

GANA = {}
for n in ("Ashwini", "Mrigashira", "Punarvasu", "Pushya", "Hasta", "Swati", "Anuradha", "Shravana", "Revati"):
    GANA[n] = "Deva"
for n in ("Bharani", "Rohini", "Ardra", "Purva Phalguni", "Uttara Phalguni", "Purva Ashadha", "Uttara Ashadha",
          "Purva Bhadrapada", "Uttara Bhadrapada"):
    GANA[n] = "Manushya"
for n in ("Krittika", "Ashlesha", "Magha", "Chitra", "Vishakha", "Jyeshtha", "Mula", "Dhanishta", "Shatabhisha"):
    GANA[n] = "Rakshasa"

YONI = ["Horse", "Elephant", "Sheep", "Serpent", "Serpent", "Dog", "Cat", "Sheep", "Cat", "Rat", "Rat", "Cow",
        "Buffalo", "Tiger", "Buffalo", "Tiger", "Deer", "Deer", "Dog", "Monkey", "Mongoose", "Monkey", "Lion",
        "Horse", "Lion", "Cow", "Elephant"]
YONI_ENEMY = {frozenset(p) for p in [("Horse", "Buffalo"), ("Elephant", "Lion"), ("Sheep", "Monkey"),
                                     ("Serpent", "Mongoose"), ("Dog", "Deer"), ("Cat", "Rat"), ("Cow", "Tiger")]}

REMEDIES = {
    "mangal": [
        "Kumbh Vivah (symbolic marriage with a clay pot) or Ark/Peepal vivah before the wedding",
        "Mangal Dosha Nivaran puja at Mangalnath (Ujjain) or a Navagraha temple",
        "Recite Hanuman Chalisa / Sundarkand on Tuesdays; Mangal Beej mantra 'Om Kraam Kreem Kraum Sah Bhaumaya Namah' (10,000 jaap)",
        "Tuesday vrat; donate red lentils (masoor), jaggery and red cloth",
        "Marriage is commonly advised with another Manglik, or after age 28 when the dosha weakens",
    ],
    "nadi": [
        "Nadi Dosha Nivaran puja with Maha Mrityunjaya jaap (1.25 lakh) by the couple's families",
        "Daan of gold Nadi (a gold serpent / gold coin), grains and clothes to a Brahmin",
        "Godaan (donation of a cow) or its equivalent seva at a gaushala",
        "Not applicable if the dosha is cancelled (same rashi with different nakshatra, same nakshatra with different rashi or pada)",
    ],
    "bhakoot": [
        "Shiva-Parvati puja and Rudrabhishek on Mondays",
        "Recite mantras of both Moon-sign lords; donate items of the lords on their weekdays",
        "Usually considered cancelled when the Moon-sign lords are the same or friends (strong Graha Maitri)",
    ],
    "gana": [
        "Gana Dosha shanti puja; worship of Lord Ganesha with Ganapati Atharvashirsha",
        "Recite Durga Saptashati or Navarna mantra for the Rakshasa-gana partner",
        "Dosha is reduced when Moon-sign lords are friends or Bhakoot / Nadi are favourable",
    ],
    "yoni": [
        "Yoni Dosha is mild - worship of the couple's Ishta Devata and Navagraha shanti",
        "Donate food to the animal of the enemy yoni (e.g. feed cows, dogs) on auspicious days",
    ],
    "rajju": [
        "Rajju Dosha shanti puja with Mrityunjaya homa",
        "Wearing a mangal sutra blessed with Mrityunjaya mantra; Shiva abhishek on Mondays",
        "Considered serious in South Indian tradition; cancelled if Rashi lords are friends or Rajju is 'Arohana' type per local custom",
    ],
    "vedha": [
        "Vedha Dosha has no lesser remedy - traditionally the match is avoided",
        "If proceeding, perform Navagraha shanti and Vishnu Sahasranama path together",
    ],
    "mahendra": [
        "Mahendra is a positive koota; absence only reduces support for progeny and prosperity - Santana Gopala mantra may be recited",
    ],
    "stree_dirgha": [
        "Absence of Stree Dirgha reduces the bride's wellbeing in the marriage - Lakshmi-Narayana puja is advised",
    ],
    "kaal_sarp": [
        "Kaal Sarp Dosha nivaran puja at Trimbakeshwar (Nashik), Ujjain or Kalahasti",
        "Rudrabhishek on Nag Panchami / Mahashivratri; offer a silver Naag-Nagin pair",
        "Recite Sarpa Suktam and Maha Mrityunjaya mantra; feed birds and fish",
    ],
    "pitra": [
        "Narayan Bali, Tripindi Shraddha or Pind daan at Gaya, Varanasi (Pishach Mochan) or Trimbakeshwar",
        "Offer water and black sesame to ancestors on every Amavasya; feed crows, cows and Brahmins during Pitru Paksha",
        "Water a Peepal tree on Saturdays and light a sesame-oil lamp",
    ],
    "grahan": [
        "Grahan Dosha shanti puja on an eclipse day or Amavasya",
        "Surya / Chandra mantra jaap (Aditya Hridayam for Sun, Om Som Somaya Namah for Moon)",
        "Donate wheat and jaggery (Sun) or rice and milk (Moon); Rahu-Ketu mantra jaap",
    ],
    "guru_chandal": [
        "Guru Chandal Dosha nivaran puja; Brihaspati mantra 'Om Brim Brihaspataye Namah' on Thursdays",
        "Thursday vrat, donate yellow items, turmeric and chana dal; respect elders and teachers",
    ],
    "shrapit": [
        "Shrapit Dosha shanti with Shani-Rahu mantra jaap (Om Sham Shanaishcharaya Namah / Om Raam Rahave Namah)",
        "Light a mustard-oil lamp under a Peepal tree on Saturdays; Hanuman Chalisa daily",
    ],
    "angarak": [
        "Angarak Dosha puja at Mangalnath, Ujjain; Hanuman worship on Tuesdays",
        "Donate red lentils and avoid anger-driven decisions; Mangal and Rahu mantra jaap",
    ],
    "vish": [
        "Vish Yoga shanti: Shiva abhishek with milk on Mondays and Shani mantra on Saturdays",
        "Recite Hanuman Chalisa; donate black sesame and rice",
    ],
    "gand_mool": [
        "Gand Mool (Mool) Shanti puja on the day the Moon returns to the birth nakshatra, about 27 days after birth",
        "If that day is missed, perform it on a later day of the same nakshatra, traditionally within the first year",
        "Japa of the nakshatra lord: Ketu ('Om Kem Ketave Namah') for Ashwini, Magha, Mula; Budh ('Om Bum Budhaya "
        "Namah') for Ashlesha, Jyeshtha, Revati",
        "Daan after the shanti: sesame and a blanket for Ketu, green moong and green cloth for Budh",
    ],
    "kemadruma": [
        "Worship Lord Shiva and Mother Parvati on Mondays; Chandra mantra 'Om Shraam Shreem Shraum Sah Chandraya Namah'",
        "Wear silver, keep a silver square in the wallet, offer milk to Shivling on Mondays",
    ],
}
NOTE = "Remedies are traditional upayas; have them performed through a qualified acharya after a full chart reading."


def _planet(k, name):
    return (getattr(k, "planets", None) or {}).get(name) or {}


def _house(k, name):
    return _planet(k, name).get("house")


def _lon(k, name):
    return _planet(k, name).get("longitude")


def _same_sign(k, a, b):
    pa, pb = _planet(k, a), _planet(k, b)
    return pa and pb and pa.get("zodiac_sign") == pb.get("zodiac_sign")


def _dosha(present, title, reasons, key, cancelled=False, severity=None, message=None):
    return {
        "present": bool(present), "cancelled": bool(cancelled), "severity": severity,
        "title": title, "reasons": reasons, "user_message": message or (reasons[0] if reasons else ""),
        "remedies": REMEDIES.get(key, []) if present and not cancelled else [],
    }


# ---------------------------------------------------------------------------
# Matching doshas
# ---------------------------------------------------------------------------

def _lords(k1, k2):
    try:
        return RASHI_LORD[RASHIS.index(k1.rashi)], RASHI_LORD[RASHIS.index(k2.rashi)]
    except (ValueError, AttributeError):
        return None, None


def lords_friendly(k1, k2):
    a, b = _lords(k1, k2)
    return bool(a and b and (a == b or (b in FRIENDS.get(a, set()) and a in FRIENDS.get(b, set()))))


def nadi_cancellation(k1, k2):
    """Classical Nadi-dosha exceptions."""
    n1, n2 = norm_nak(k1.nakshatra), norm_nak(k2.nakshatra)
    reasons = []
    if k1.rashi == k2.rashi and n1 != n2:
        reasons.append("Same Moon sign but different nakshatras - Nadi Dosha cancelled")
    if n1 == n2 and k1.rashi != k2.rashi:
        reasons.append("Same nakshatra but different Moon signs - Nadi Dosha cancelled")
    if n1 == n2 and getattr(k1, "nakshatra_pada", None) != getattr(k2, "nakshatra_pada", None):
        reasons.append("Same nakshatra in different padas - Nadi Dosha cancelled")
    return reasons


def check_gana(k1, k2):
    g1, g2 = GANA.get(norm_nak(k1.nakshatra)), GANA.get(norm_nak(k2.nakshatra))
    bad = {g1, g2} in ({"Deva", "Rakshasa"}, {"Manushya", "Rakshasa"}) and g1 != g2
    cancel = bad and lords_friendly(k1, k2)
    reasons = [f"Boy {g1} gana, girl {g2} gana"]
    if cancel:
        reasons.append("Moon-sign lords are friendly - Gana Dosha cancelled")
    return _dosha(bad, "Gana Dosha", reasons, "gana", cancelled=cancel, severity="medium" if bad else None,
                  message=("Temperament mismatch (Gana Dosha)" if bad else "Gana compatible"))


def check_yoni(k1, k2):
    i1, i2 = nak_index(k1.nakshatra), nak_index(k2.nakshatra)
    if i1 is None or i2 is None:
        return _dosha(False, "Yoni Dosha", ["Nakshatra unavailable"], "yoni")
    y1, y2 = YONI[i1], YONI[i2]
    bad = frozenset((y1, y2)) in YONI_ENEMY
    return _dosha(bad, "Yoni Dosha", [f"Boy {y1} yoni, girl {y2} yoni" + (" - sworn enemies" if bad else "")],
                  "yoni", severity="low" if bad else None)


def check_rajju(k1, k2):
    n1, n2 = norm_nak(k1.nakshatra), norm_nak(k2.nakshatra)
    r1, r2 = RAJJU.get(n1), RAJJU.get(n2)
    bad = bool(r1 and r1 == r2)
    cancel = bad and (n1 == n2 or lords_friendly(k1, k2))
    reasons = [f"Boy {r1} Rajju, girl {r2} Rajju"]
    if bad:
        reasons.append(f"Same Rajju ({r1}): {RAJJU_EFFECT[r1]}")
    if cancel:
        reasons.append("Moon-sign lords friendly / same nakshatra - Rajju Dosha mitigated")
    return _dosha(bad, "Rajju Dosha", reasons, "rajju", cancelled=cancel, severity="high" if bad else None)


def check_vedha(k1, k2):
    n1, n2 = norm_nak(k1.nakshatra), norm_nak(k2.nakshatra)
    bad = n2 in VEDHA.get(n1, set())
    return _dosha(bad, "Vedha Dosha", [f"{n1} and {n2}" + (" obstruct each other (Vedha pair)" if bad else " - no Vedha")],
                  "vedha", severity="high" if bad else None)


def check_mahendra(k1, k2):
    i1, i2 = nak_index(k1.nakshatra), nak_index(k2.nakshatra)
    if i1 is None or i2 is None:
        return _dosha(False, "Mahendra", ["Nakshatra unavailable"], "mahendra")
    count = (i1 - i2) % 27 + 1          # girl's star to boy's star
    ok = count in (4, 7, 10, 13, 16, 19, 22, 25)
    return _dosha(not ok, "Mahendra Koota", [f"Boy's star is {count} from girl's - " + ("favourable" if ok else "not favourable")],
                  "mahendra", severity="low" if not ok else None)


def check_stree_dirgha(k1, k2):
    i1, i2 = nak_index(k1.nakshatra), nak_index(k2.nakshatra)
    if i1 is None or i2 is None:
        return _dosha(False, "Stree Dirgha", ["Nakshatra unavailable"], "stree_dirgha")
    count = (i1 - i2) % 27 + 1
    ok = count > 9                      # North Indian norm (>13 is ideal in South India)
    return _dosha(not ok, "Stree Dirgha", [f"Boy's star is {count} from girl's - " + ("favourable" if ok else "less than 9")],
                  "stree_dirgha", severity="low" if not ok else None)


# ---------------------------------------------------------------------------
# Individual chart doshas
# ---------------------------------------------------------------------------

def _between(lon, a, b):
    """True if lon lies on the arc going forward from a to b."""
    return (lon - a) % 360 < (b - a) % 360


def individual_doshas(k):
    """Doshas present in one chart (needs k.planets with longitude/house/zodiac_sign)."""
    out = {}
    rahu, ketu = _lon(k, "Rahu"), _lon(k, "Ketu")
    seven = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
    if rahu is not None and ketu is not None:
        lons = [_lon(k, p) for p in seven if _lon(k, p) is not None]
        one_side = all(_between(l, rahu, ketu) for l in lons) or all(_between(l, ketu, rahu) for l in lons)
        if lons and one_side:
            out["kaal_sarp"] = _dosha(True, "Kaal Sarp Dosha",
                                      ["All seven planets are hemmed between Rahu and Ketu"], "kaal_sarp", severity="high")
    sun_h, rahu_h, ketu_h, sat_h = _house(k, "Sun"), _house(k, "Rahu"), _house(k, "Ketu"), _house(k, "Saturn")
    pitra = []
    if _same_sign(k, "Sun", "Rahu") or _same_sign(k, "Sun", "Ketu"):
        pitra.append("Sun conjunct Rahu/Ketu")
    if 9 in (rahu_h, ketu_h):
        pitra.append("Rahu/Ketu in the 9th house (house of ancestors)")
    if sun_h == 9 and _same_sign(k, "Sun", "Saturn"):
        pitra.append("Sun and Saturn together in the 9th house")
    if pitra:
        out["pitra"] = _dosha(True, "Pitra Dosha", pitra, "pitra", severity="medium")
    grahan = [f"{p} conjunct {n}" for p in ("Sun", "Moon") for n in ("Rahu", "Ketu") if _same_sign(k, p, n)]
    if grahan:
        out["grahan"] = _dosha(True, "Grahan Dosha", grahan, "grahan", severity="medium")
    if _same_sign(k, "Jupiter", "Rahu") or _same_sign(k, "Jupiter", "Ketu"):
        out["guru_chandal"] = _dosha(True, "Guru Chandal Dosha", ["Jupiter conjunct Rahu/Ketu"], "guru_chandal",
                                     severity="medium")
    if _same_sign(k, "Saturn", "Rahu"):
        out["shrapit"] = _dosha(True, "Shrapit Dosha", ["Saturn conjunct Rahu"], "shrapit", severity="medium")
    if _same_sign(k, "Mars", "Rahu"):
        out["angarak"] = _dosha(True, "Angarak Dosha", ["Mars conjunct Rahu"], "angarak", severity="medium")
    if _same_sign(k, "Saturn", "Moon"):
        out["vish"] = _dosha(True, "Vish Yoga", ["Saturn conjunct Moon"], "vish", severity="medium")
    moon = _planet(k, "Moon")
    if moon.get("zodiac_sign") in RASHIS:
        mi = RASHIS.index(moon["zodiac_sign"])
        neighbours = {RASHIS[(mi + 1) % 12], RASHIS[(mi - 1) % 12]}
        others = [p for p in ("Mars", "Mercury", "Jupiter", "Venus", "Saturn")
                  if _planet(k, p).get("zodiac_sign") in neighbours | {moon["zodiac_sign"]}]
        kendra_ok = any(_house(k, p) in (1, 4, 7, 10) for p in ("Jupiter", "Venus"))
        if not others:
            out["kemadruma"] = _dosha(True, "Kemadruma Yoga",
                                      ["No planet in the 2nd or 12th from the Moon (or with it)"], "kemadruma",
                                      cancelled=kendra_ok, severity="low")
            if kendra_ok:
                out["kemadruma"]["reasons"].append("Benefic in a kendra cancels Kemadruma")
    return out


def mangal_remedies(report):
    if report and (report.get("partner1_manglik") or report.get("partner2_manglik")) and not report.get("cancelled"):
        report["remedies"] = REMEDIES["mangal"]
    else:
        report.setdefault("remedies", [])
    return report


def enrich(report, k1, k2):
    """Add missing doshas + remedies to a DoshaEvaluator report (in place)."""
    for key in ("nadi", "bhakoot", "rajju", "vedha"):
        r = report.get(key) or {}
        if key == "nadi" and r.get("present"):
            cancel = nadi_cancellation(k1, k2)
            if cancel:
                r["cancelled"] = True
                r.setdefault("reasons", []).extend(cancel)
                r["user_message"] = cancel[0]
        r["remedies"] = REMEDIES[key] if r.get("present") and not r.get("cancelled") else []
        report[key] = r
    report["rajju"] = check_rajju(k1, k2)
    report["vedha"] = check_vedha(k1, k2)
    report["gana"] = check_gana(k1, k2)
    report["yoni"] = check_yoni(k1, k2)
    report["mahendra"] = check_mahendra(k1, k2)
    report["stree_dirgha"] = check_stree_dirgha(k1, k2)
    mangal_remedies(report.get("mangal") or {})
    report["individual"] = {"partner1": individual_doshas(k1), "partner2": individual_doshas(k2)}
    report["remedy_note"] = NOTE
    return report


# ---------------------------------------------------------------------------
# Mangal Dosha with its parihara (cancellation) rules, shared by Kundali Milan and the printed kundali
# ---------------------------------------------------------------------------

MANGAL_HOUSES = (1, 4, 7, 8, 12)   # North Indian reckoning; the 2nd house is added in the South
SIGN_EN = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn",
           "Aquarius", "Pisces"]
# Mars in these signs in these houses (from Lagna) does not cause the dosha: the sign-house exceptions quoted
# in Muhurta Chintamani commentaries and the Mangal Dosha parihara lists of the Kerala and Kashi traditions
SIGN_HOUSE_EXCEPTIONS = {1: {0}, 4: {0, 7}, 7: {3, 9}, 8: {8, 11}, 12: {1, 6}}
MARS_COMBUST_ORB = 17   # Surya Siddhanta orb for Mars


def _from(sign, base):
    return (sign - base) % 12 + 1


def mangal_dosha(signs, lons, asc_sign, refs=("Lagna", "Moon", "Venus")):
    """
    ``signs``/``lons``: planet name -> sign index 0-11 / sidereal longitude. Returns
    {"present", "cancelled", "reduced", "positions": [...], "parihara": [...], "reducers": [...], "severity"}.
    "cancelled" means a full parihara applies; "reduced" lists weaker mitigations that do not cancel it.
    """
    mars = signs["Mars"]
    bases = {"Lagna": asc_sign, "Moon": signs.get("Moon"), "Venus": signs.get("Venus")}
    positions = [(ref, _from(mars, bases[ref])) for ref in refs if bases.get(ref) is not None
                 and _from(mars, bases[ref]) in MANGAL_HOUSES]
    out = {"present": bool(positions), "cancelled": False, "positions": positions, "parihara": [], "reducers": [],
           "severity": None}
    if not positions:
        return out
    full, weak = out["parihara"], out["reducers"]
    mars_house = _from(mars, asc_sign)
    if mars in (0, 7):
        full.append(("own", f"Mars is in its own sign {SIGN_EN[mars]}"))
    if mars == 9:
        full.append(("exalted", "Mars is exalted in Capricorn"))
    if mars in (4, 10):
        full.append(("leo_aq", f"Mars in {SIGN_EN[mars]} (Leo or Aquarius) does not give the dosha"))
    if mars_house in SIGN_HOUSE_EXCEPTIONS and mars in SIGN_HOUSE_EXCEPTIONS[mars_house] and mars not in (0, 7, 9):
        full.append(("exception", f"Mars in {SIGN_EN[mars]} in house {mars_house} is a listed exception"))
    if asc_sign in (3, 4):
        full.append(("yogakaraka", f"For {SIGN_EN[asc_sign]} Lagna, Mars is the yogakaraka and does not harm"))
    jup = signs.get("Jupiter")
    if jup is not None and _from(mars, jup) in (1, 5, 7, 9):
        full.append(("jup_with", "Jupiter is with Mars") if jup == mars else
                    ("jup_aspect", f"Jupiter aspects Mars (Mars is {_from(mars, jup)}th from Jupiter)"))
    for benefic in ("Jupiter", "Venus"):
        if signs.get(benefic) == asc_sign:
            full.append((f"{benefic.lower()}_lagna", f"{benefic} in the Lagna protects the chart"))
    if mars == 3:
        weak.append(("debilitated", "Mars is debilitated in Cancer and weak"))
    if lons.get("Sun") is not None and lons.get("Mars") is not None:
        gap = abs((lons["Mars"] - lons["Sun"] + 180) % 360 - 180)
        if gap < MARS_COMBUST_ORB:
            weak.append(("combust", f"Mars is combust, {gap:.0f}° from the Sun"))
            out["combust_gap"] = gap
    if signs.get("Moon") == mars:
        weak.append(("moon_with", "Moon is with Mars (Chandra-Mangal yoga)"))
    out["mars_sign"], out["mars_house"], out["asc_sign"] = mars, mars_house, asc_sign
    out["cancelled"] = bool(full)
    out["severity"] = None if full else ("low" if weak else ("high" if any(r == "Lagna" for r, _ in positions)
                                                             else "medium"))
    return out


def mangal_reasons(result):
    """Plain sentences: where the dosha arises, then every parihara and mitigation found."""
    lines = [f"Mars in house {h} from {ref}" for ref, h in result["positions"]]
    lines += [f"Cancelled: {text}" for _, text in result["parihara"]]
    lines += [f"Reduced: {text}" for _, text in result["reducers"]]
    return lines


# ---------------------------------------------------------------------------
# Gand Mool (Ganda Moola) birth
# ---------------------------------------------------------------------------

GAND_MOOL = {
    # the six nakshatras at the water-to-fire sign junctions (gandanta): Ketu's three begin a fire sign,
    # Mercury's three end a water sign
    "Ashwini": "Ketu", "Magha": "Ketu", "Mula": "Ketu",
    "Ashlesha": "Mercury", "Jyeshtha": "Mercury", "Revati": "Mercury",
}
GAND_MOOL_SEVERE_PADA = {"Ashwini": 1, "Magha": 1, "Mula": 1, "Ashlesha": 4, "Jyeshtha": 4, "Revati": 4}


def gand_mool(moon_lon):
    """Gand Mool dosha from the Moon's nakshatra at birth."""
    nak_i = int((moon_lon % 360) // (360 / 27))
    name = NAKSHATRAS[nak_i]
    pada = int(((moon_lon % 360) % (360 / 27)) // (360 / 108)) + 1
    if name not in GAND_MOOL:
        return {"present": False, "nakshatra": name, "pada": pada}
    severe = GAND_MOOL_SEVERE_PADA[name] == pada
    reasons = [f"Moon in {name} nakshatra, pada {pada}: one of the six Gand Mool nakshatras (ruled by {GAND_MOOL[name]})",
               "This pada touches the sign junction itself (gandanta), the strongest form" if severe else
               "This pada is away from the sign junction, a milder form; texts differ on whom each pada affects"]
    return {"present": True, "nakshatra": name, "nak_index": nak_i, "pada": pada, "lord": GAND_MOOL[name],
            "reasons": reasons, "severity": "high" if severe else "low"}
