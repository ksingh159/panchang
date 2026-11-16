# core/utils/varga.py
"""
Divisional charts (vargas) by the Parashari definitions of Brihat Parashara Hora Shastra, ch. 6 (Shodashavarga).

These are the "Traditional Parasara" options that Jagannatha Hora uses by default, one rule per chart:

  D2  Hora           JHora's default "D-2 (US)": Uma-Shambhu hora, P.V.R. Narasimha Rao's re-reading of Parashara.
                     The 24 half-signs run through the zodiac twice from Aries; odd signs take their pair in order,
                     even signs reversed (Ar: Ar, Ta; Ta: Cn, Ge; Ge: Le, Vi; Cn: Sc, Li ...).
                     The older Sun/Moon hora (odd: Leo then Cancer, even: Cancer then Leo) is parashari_hora().
  D3  Drekkana       the sign, its 5th, its 9th
  D4  Chaturthamsha  the sign, its 4th, 7th, 10th
  D5  Panchamsha     odd: Ar, Aq, Sg, Ge, Li; even: Ta, Vi, Pi, Cp, Sc   (JHora "Standard Parasara D-5")
  D7  Saptamsha      odd: from the sign; even: from its 7th
  D9  Navamsha       fire from Ar, earth from Cp, air from Li, water from Cn
  D10 Dashamsha      odd: from the sign; even: from its 9th
  D12 Dwadashamsha   from the sign
  D16 Shodashamsha   movable from Ar, fixed from Le, dual from Sg
  D20 Vimshamsha     movable from Ar, fixed from Sg, dual from Le
  D24 Siddhamsha     odd from Le, even from Cn
  D27 Bhamsha        fire from Ar, earth from Cn, air from Li, water from Cp
  D30 Trimshamsha    odd: Mars 5°, Saturn 5°, Jupiter 8°, Mercury 7°, Venus 5° (Ar, Aq, Sg, Ge, Li);
                     even: Venus 5°, Mercury 7°, Jupiter 8°, Saturn 5°, Mars 5° (Ta, Vi, Pi, Cp, Sc)
  D40 Khavedamsha    odd from Ar, even from Li
  D45 Akshavedamsha  movable from Ar, fixed from Le, dual from Sg
  D60 Shashtiamsha   from the sign

The older code placed every chart cyclically (sign x N + part), the "parivritti" option in JHora. That happens to
give the same answer as Parashara for D7, D9, D16, D20 and D27, and a different one for D2, D3, D4, D5, D10, D12,
D24, D30, D40, D45 and D60.
"""

SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn",
         "Aquarius", "Pisces"]
NAKSHATRAS = ["Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu", "Pushya", "Ashlesha",
              "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha",
              "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
              "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"]
FACTORS = [1, 2, 3, 4, 5, 7, 9, 10, 12, 16, 20, 24, 27, 30, 40, 45, 60]

ODD_D30 = [(5, 0), (10, 10), (18, 8), (25, 2), (30, 6)]    # (upper degree, sign)
EVEN_D30 = [(5, 1), (12, 5), (20, 11), (25, 9), (30, 7)]
D5_ODD = [0, 10, 8, 2, 6]
D5_EVEN = [1, 5, 11, 9, 7]


def _movable_fixed_dual(sign, movable, fixed, dual):
    return (movable, fixed, dual)[sign % 3]


def varga_sign(lon, n):
    """Sign index (0 = Aries) of sidereal longitude ``lon`` in the D-``n`` chart."""
    lon %= 360
    sign, deg = int(lon // 30), lon % 30
    odd = sign % 2 == 0        # Aries (index 0) is an odd sign
    if n == 1:
        return sign
    if n == 30:
        for upper, s in (ODD_D30 if odd else EVEN_D30):
            if deg < upper:
                return s
        return (ODD_D30 if odd else EVEN_D30)[-1][1]
    part = min(int(deg // (30.0 / n)), n - 1)
    if n == 2:
        first, second = (2 * sign) % 12, (2 * sign + 1) % 12
        return (first if part == 0 else second) if odd else (second if part == 0 else first)
    if n == 3:
        return (sign + 4 * part) % 12
    if n == 4:
        return (sign + 3 * part) % 12
    if n == 5:
        return (D5_ODD if odd else D5_EVEN)[part]
    if n == 7:
        return (sign + (0 if odd else 6) + part) % 12
    if n == 9:
        return ((0, 9, 6, 3)[sign % 4] + part) % 12
    if n == 10:
        return (sign + (0 if odd else 8) + part) % 12
    if n == 12:
        return (sign + part) % 12
    if n == 16:
        return (_movable_fixed_dual(sign, 0, 4, 8) + part) % 12
    if n == 20:
        return (_movable_fixed_dual(sign, 0, 8, 4) + part) % 12
    if n == 24:
        return ((4 if odd else 3) + part) % 12
    if n == 27:
        return ((0, 3, 6, 9)[sign % 4] + part) % 12
    if n == 40:
        return ((0 if odd else 6) + part) % 12
    if n == 45:
        return (_movable_fixed_dual(sign, 0, 4, 8) + part) % 12
    if n == 60:
        return (sign + part) % 12
    return (sign * n + part) % 12   # any other D-n: cyclical


def parashari_hora(lon):
    """The Sun/Moon hora of BPHS 6.5-6 as usually read: 4 (Leo, Sun's hora) or 3 (Cancer, Moon's hora)."""
    sign, deg = int((lon % 360) // 30), lon % 30
    odd = sign % 2 == 0
    return (4 if deg < 15 else 3) if odd else (3 if deg < 15 else 4)


def varga_degree(lon, n):
    """Degree inside the varga sign: the planet's progress through its part, stretched to 30°."""
    deg = lon % 30
    if n == 30:
        odd = int((lon % 360) // 30) % 2 == 0
        lower = 0
        for upper, _ in (ODD_D30 if odd else EVEN_D30):
            if deg < upper:
                return (deg - lower) / (upper - lower) * 30
            lower = upper
        return 29.999
    size = 30.0 / n
    return (deg % size) * n


def position(lon, n):
    sign = varga_sign(lon, n)
    degree = varga_degree(lon, n)
    vlon = sign * 30 + degree
    return {"sign_index": sign, "sign": SIGNS[sign], "degree": round(degree, 6), "longitude_sidereal": round(vlon, 6),
            "longitude_raw": vlon, "nakshatra": NAKSHATRAS[int(vlon // (360 / 27)) % 27]}


def charts(planet_lons, asc_lon):
    """
    {"d1": {...}, "d2": {...}, ...} in the shape the site already stores: each planet has sign, degree, house,
    longitude and nakshatra in that varga. ``asc`` holds each varga's Lagna.
    """
    out, ascs = {}, {}
    for n in FACTORS:
        key = f"d{n}"
        asc = position(asc_lon, n)
        ascs[key] = {"sign": asc["sign"], "degree": asc["degree"], "sign_index": asc["sign_index"]}
        chart = {}
        for name, lon in planet_lons.items():
            if lon is None:
                continue
            p = position(lon, n)
            p["house"] = (p["sign_index"] - asc["sign_index"]) % 12 + 1
            chart[name] = p
        out[key] = chart
    return out, ascs


def charts_for_kundali(kundali):
    """Fresh Parashari vargas for a saved Kundali, from its D1 longitudes (so old saved charts are corrected too)."""
    d1 = kundali.planetary_positions or {}
    lons = {name: (p or {}).get("longitude_sidereal") for name, p in d1.items()}
    asc_lon = (kundali.ascendant or {}).get("asc_sidereal")
    if asc_lon is None:
        sign = (kundali.ascendant or {}).get("sign_sidereal", "Aries")
        asc_lon = SIGNS.index(sign) * 30 + float((kundali.ascendant or {}).get("degree_in_sign") or 0) \
            if sign in SIGNS else 0
    return charts(lons, asc_lon)
