# core/utils/transits.py
"""Readable natal / transit details shared by the kundali page and the transit chart."""
SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius",
         "Capricorn", "Aquarius", "Pisces"]
NAKSHATRAS = ["Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu", "Pushya", "Ashlesha",
              "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha",
              "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
              "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"]
HINDI = {"Sun": "सूर्य", "Moon": "चन्द्र", "Mars": "मङ्गल", "Mercury": "बुध", "Jupiter": "गुरु", "Venus": "शुक्र",
         "Saturn": "शनि", "Rahu": "राहु", "Ketu": "केतु", "Ascendant": "लग्न"}
SIGN_LORDS = ["Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter"]

EXALTED = {"Sun": 0, "Moon": 1, "Mars": 9, "Mercury": 5, "Jupiter": 3, "Venus": 11, "Saturn": 6}
OWN = {"Sun": {4}, "Moon": {3}, "Mars": {0, 7}, "Mercury": {2, 5}, "Jupiter": {8, 11}, "Venus": {1, 6}, "Saturn": {9, 10}}
KENDRA = {1, 4, 7, 10}
TRIKONA = {1, 5, 9}
DUSTHANA = {6, 8, 12}


def dignity(planet, sign):
    if planet not in EXALTED:
        return ""
    if EXALTED[planet] == sign:
        return "Exalted"
    if (EXALTED[planet] + 6) % 12 == sign:
        return "Debilitated"
    return "Own sign" if sign in OWN[planet] else ""


def house_from(sign, base):
    return (sign - base) % 12 + 1


def house_kind(house):
    if house in KENDRA:
        return "Kendra"
    if house in TRIKONA:
        return "Trikona"
    return "Dusthana" if house in DUSTHANA else ""


def position(planet, longitude, retrograde=False):
    longitude %= 360
    sign = int(longitude // 30)
    nak = int(longitude // (360 / 27))
    return {
        "sign": SIGNS[sign], "sign_index": sign, "degree": round(longitude % 30, 2), "lord": SIGN_LORDS[sign],
        "nakshatra": NAKSHATRAS[nak], "pada": int((longitude % (360 / 27)) // (360 / 108)) + 1,
        "retrograde": bool(retrograde), "dignity": dignity(planet, sign),
    }


def sade_sati(moon_sign, saturn_sign):
    """Shani's transit from the natal Moon: Sade Sati, Dhaiya or none."""
    house = house_from(saturn_sign, moon_sign)
    phase = {12: "rising (first) phase", 1: "peak (second) phase", 2: "setting (third) phase"}.get(house)
    if phase:
        return f"Sade Sati is running: {phase}"
    if house == 4:
        return "Kantak Shani (Dhaiya): Saturn transits the 4th from your Moon"
    if house == 8:
        return "Ashtama Shani (Dhaiya): Saturn transits the 8th from your Moon"
    return "No Sade Sati or Dhaiya at present"


def transit_rows(transits, lagna_sign, moon_sign):
    """Rows for a table: each current planet with its house from Lagna and from the natal Moon."""
    rows = []
    for t in transits:
        pos = position(t["name"], t["longitude"], t.get("retrograde"))
        house = house_from(pos["sign_index"], lagna_sign)
        rows.append({**pos, "name": t["name"], "hindi": HINDI.get(t["name"], ""), "house": house,
                     "house_kind": house_kind(house), "from_moon": house_from(pos["sign_index"], moon_sign)})
    return rows


def close_contacts(natal, transits, orb=3.0):
    """Transits within ``orb`` degrees of a natal point, slowest planets first."""
    pace = {"Saturn": 0, "Rahu": 1, "Ketu": 1, "Jupiter": 2, "Mars": 3, "Sun": 4, "Venus": 5, "Mercury": 6, "Moon": 7}
    hits = []
    for t in transits:
        for n in natal:
            gap = abs((t["longitude"] - n["longitude"] + 180) % 360 - 180)
            if gap <= orb:
                hits.append((pace.get(t["name"], 9), f"Transit {t['name']} is {gap:.1f}° from natal {n['name']}"))
    return [text for _, text in sorted(hits)]


def contact_pairs(natal, transits, orb=3.0):
    """Like close_contacts, as data: [{"transit", "gap", "natal"}], slowest planets first."""
    pace = {"Saturn": 0, "Rahu": 1, "Ketu": 1, "Jupiter": 2, "Mars": 3, "Sun": 4, "Venus": 5, "Mercury": 6, "Moon": 7}
    hits = []
    for t in transits:
        for n in natal:
            gap = abs((t["longitude"] - n["longitude"] + 180) % 360 - 180)
            if gap <= orb:
                hits.append((pace.get(t["name"], 9), {"transit": t["name"], "gap": round(gap, 1), "natal": n["name"]}))
    return [x for _, x in sorted(hits, key=lambda h: h[0])]


def chart_details(natal, transits, lagna_sign):
    """Everything the Planetary Details tab needs."""
    by_name = {t["name"]: t for t in transits}
    moon = next((n for n in natal if n["name"] == "Moon"), None)
    moon_sign = moon["sign"] if moon else lagna_sign
    planets = []
    for n in natal:
        if n["name"] == "Ascendant":
            continue
        t = by_name.get(n["name"])
        np = position(n["name"], n["longitude"], n.get("retrograde"))
        item = {"name": n["name"], "hindi": HINDI.get(n["name"], ""),
                "natal": {**np, "house": house_from(np["sign_index"], lagna_sign)}}
        if t:
            tp = position(t["name"], t["longitude"], t.get("retrograde"))
            house = house_from(tp["sign_index"], lagna_sign)
            item["transit"] = {**tp, "house": house, "house_kind": house_kind(house),
                               "from_moon": house_from(tp["sign_index"], moon_sign)}
        planets.append(item)
    saturn = by_name.get("Saturn")
    moon_pos = position("Moon", moon["longitude"]) if moon else None
    return {
        "lagna": SIGNS[lagna_sign], "lagna_lord": SIGN_LORDS[lagna_sign],
        "moon_sign": SIGNS[moon_sign], "moon_nakshatra": moon_pos["nakshatra"] if moon_pos else "",
        "sade_sati": sade_sati(moon_sign, saturn["sign"]) if saturn else "",
        "contacts": close_contacts(natal, transits), "contact_pairs": contact_pairs(natal, transits), "planets": planets,
    }
