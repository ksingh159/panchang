# core/utils/helpers.py
import swisseph as swe
import math
from datetime import datetime, timedelta, timezone
import time
import pytz
from astral import LocationInfo
from astral.moon import moonrise, moonset, phase
from timezonefinderL import TimezoneFinder

from .constants import (
    TITHI_NAMES, NAKSHATRA_NAMES, YOGA_NAMES, KARANA_NAMES, SARVARATH_SIDDHIYOG,
    WEEKDAYS, AMANTA_MONTHS, PURNIMANTA_MONTHS, RITUS, ZODIAC_SIGNS, PANCHAK, DISHA_SHOOL_DIRECTIONS, DISHA_SHOOL_REMEDY
)

# Nakshatra indices (make sure these match your system)
DHANISHTA_INDEX = 22
SHATABISHA_INDEX = 23
PURVA_BHADRAPADA_INDEX = 24
UTTARA_BHADRAPADA_INDEX = 25
REVATI_INDEX = 26
ASHWINI_INDEX = 0

# Segment size (13°20' = 13.3333... degrees)
SEGMENT = 360 / 27  # ~13.3333 degrees

# ---------------------
# Core Calculation Functions
# ---------------------

def hms_format(td):
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"

def format_offset(dt):
    """Return offset as string like +05:30 or -04:00"""
    offset = dt.utcoffset()
    if offset is None:
        return "Unknown"
    total_minutes = int(offset.total_seconds() / 60)
    sign = "+" if total_minutes >= 0 else "-"
    total_minutes = abs(total_minutes)
    hours, minutes = divmod(total_minutes, 60)
    return f"{sign}{hours:02d}:{minutes:02d}"

def get_julian(year, month, day, hour):
    return swe.julday(year, month, day, hour)

def jd_to_datetime_correct(jd, tz_offset=5.5):
    """Convert Julian Day to timezone-adjusted datetime (returns full date + time)."""
    jd += 0.5
    Z = int(jd)
    F = jd - Z

    if Z < 2299161:
        A = Z
    else:
        alpha = int((Z - 1867216.25) / 36524.25)
        A = Z + 1 + alpha - int(alpha / 4)

    B = A + 1524
    C = int((B - 122.1) / 365.25)
    D = int(365.25 * C)
    E = int((B - D) / 30.6001)

    day = B - D - int(30.6001 * E) + F
    day_int = int(day)
    frac_day = day - day_int

    if E < 14:
        month = E - 1
    else:
        month = E - 13

    if month > 2:
        year = C - 4716
    else:
        year = C - 4715

    # Convert fractional day to time
    total_seconds = frac_day * 86400
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = int(total_seconds % 60)

    tzinfo = timezone(timedelta(hours=tz_offset))
    dt = datetime(year, month, day_int, hours, minutes, seconds,tzinfo = tzinfo)

    # Apply timezone offset
    dt += timedelta(hours=tz_offset)

    return dt

def get_ritu(sun_lon):
    """Get season based on Sun longitude - CORRECTED"""
    if 330 <= sun_lon < 360 or 0 <= sun_lon < 30:
        return "Vasanta (Spring)"
    elif 30 <= sun_lon < 90:
        return "Grishma (Summer)"
    elif 90 <= sun_lon < 150:
        return "Varsha (Monsoon)"
    elif 150 <= sun_lon < 210:
        return "Sharad (Autumn)"
    elif 210 <= sun_lon < 270:
        return "Hemanta (Pre-Winter)"
    else:
        return "Shishira (Winter)"

def find_tithi_end_time(start_jd, current_diff):
    """Find the exact time when the current tithi ends"""
    next_tithi_target = (int(current_diff) + 1) * 12
    
    if next_tithi_target >= 360:
        next_tithi_target = 360
    
    low_jd = start_jd
    high_jd = start_jd + 2.0
    tolerance = 1e-6
    
    for _ in range(50):
        mid_jd = (low_jd + high_jd) / 2.0
        
        ayanamsa = swe.get_ayanamsa_ut(mid_jd)
        sun_pos, _ = swe.calc_ut(mid_jd, swe.SUN)
        moon_pos, _ = swe.calc_ut(mid_jd, swe.MOON)
        
        sun_lon = (sun_pos[0] - ayanamsa) % 360
        moon_lon = (moon_pos[0] - ayanamsa) % 360
        
        if sun_lon < moon_lon:
            current_diff_mid = (moon_lon - sun_lon)
        else:
            current_diff_mid = (360 - sun_lon + moon_lon)
        
        if abs(current_diff_mid - next_tithi_target) < tolerance:
            break
            
        if current_diff_mid < next_tithi_target:
            low_jd = mid_jd
        else:
            high_jd = mid_jd
    
    return (low_jd + high_jd) / 2

def moon_lon_sidereal(jd_utc):
    """Calculate Moon longitude in sidereal zodiac - expects JD in UTC"""
    ay = swe.get_ayanamsa_ut(jd_utc)  # This expects UTC JD
    moon, _ = swe.calc_ut(jd_utc, swe.MOON)  # This expects UTC JD
    moon_lon =  (moon[0] - ay) % 360
    return moon_lon

def nak_index(jd_utc):
    """Get nakshatra index from UTC Julian Day"""
    nak_index_num =    int(moon_lon_sidereal(jd_utc) // SEGMENT) % 27
    return nak_index_num

def binary_search_nak_start(low_jd, high_jd, target_index, tol=1e-7):
    """Find exact transition point to target nakshatra"""
    # Ensure we have the correct transition direction
    if nak_index(low_jd) == target_index:
        # Already in target nakshatra at low_jd, need to go backwards
        return binary_search_nak_start(high_jd, low_jd, (target_index - 1) % 27, tol)
    
    for _ in range(60):
        mid = (low_jd + high_jd) / 2
        if nak_index(mid) == target_index:
            high_jd = mid  # Transition happened before mid
        else:
            low_jd = mid   # Transition happens after mid
        if abs(high_jd - low_jd) < tol:
            break
    
    # Verify we found the correct transition
    if nak_index(low_jd) != target_index and nak_index(high_jd) == target_index:
        return high_jd
    else:
        # Fallback: return midpoint
        return (low_jd + high_jd) / 2

def find_next_nak_start(jd_start, target_index, max_days=30.0, step_days=0.05):
    """Find next occurrence of target nakshatra start"""
    current_idx = nak_index(jd_start)
    
    # Debug info
    print(f"DEBUG: Starting search for nakshatra {target_index} from JD {jd_start}")
    print(f"DEBUG: Current nakshatra: {current_idx}")
    
    # If we're already in the target nakshatra
    if current_idx == target_index:
        print(f"DEBUG: Already in target nakshatra, finding start time")
        # Find when this nakshatra started by going backwards
        jd = jd_start
        steps_back = 0
        while steps_back < 100:  # Search up to ~5 days back
            jd -= step_days
            steps_back += 1
            if nak_index(jd) != target_index:
                result = binary_search_nak_start(jd, jd + step_days, target_index)
                print(f"DEBUG: Found start at JD {result}")
                return result
        return jd_start
    
    # Find next transition to target nakshatra
    jd = jd_start
    steps = 0
    max_steps = int(max_days / step_days)
    
    while steps < max_steps:
        prev_idx = nak_index(jd)
        jd += step_days
        steps += 1
        current_idx = nak_index(jd)
        
        # Found transition to target nakshatra
        if prev_idx != target_index and current_idx == target_index:
            print(f"DEBUG: Found transition at JD {jd}")
            result = binary_search_nak_start(jd - step_days, jd, target_index)
            print(f"DEBUG: Refined to JD {result}")
            return result
        
        # Optional: print transitions for debugging
        if prev_idx != current_idx:
            print(f"DEBUG: Transition at JD {jd}: {prev_idx} -> {current_idx}")
    
    raise ValueError(f"Target nakshatra {target_index} not found within {max_days} days")

def is_in_panchak_nakshatra(nak_index, moon_longitude):
    """Check if current position is in Panchak nakshatra"""
    if nak_index == DHANISHTA_INDEX:
        # For Dhanishta, only 3rd and 4th padas are in Panchak
        pada = get_pada(moon_longitude)
        return pada in [3, 4]
    elif nak_index in [SHATABISHA_INDEX, PURVA_BHADRAPADA_INDEX, UTTARA_BHADRAPADA_INDEX, REVATI_INDEX]:
        return True
    else:
        return False

def binary_search_longitude(low_jd, high_jd, target_lon, tol=1e-7):
    """Binary search for when Moon reaches specific longitude"""
    for _ in range(60):
        mid_jd = (low_jd + high_jd) / 2
        current_lon = moon_lon_sidereal(mid_jd) % 360
        
        if current_lon >= target_lon:
            high_jd = mid_jd
        else:
            low_jd = mid_jd
            
        if abs(high_jd - low_jd) < tol:
            break
    
    return high_jd

def get_panchak_period(jd_current, current_nakshatra):
    """Get Panchak period information - CORRECTED VERSION"""
    print(f"PANCHAK: Current nakshatra: {current_nakshatra}")
    
    # Check if we're currently in Panchak
    # Panchak includes: 3rd & 4th pada of Dhanishta, Shatabisha, Purva Bhadrapada, Uttara Bhadrapada, Revati
    is_in_panchak = is_in_panchak_nakshatra(current_nakshatra, moon_lon_sidereal(jd_current))
    print(f"PANCHAK: Is in Panchak? {is_in_panchak}")
    
    if is_in_panchak:
        # Currently inside Panchak
        panchak_status = "YES"
        panchak_day = get_panchak_day(current_nakshatra, moon_lon_sidereal(jd_current))
        print(f"PANCHAK: Inside Panchak, day {panchak_day}")
        
        # Find when current Panchak ENDS (transition to Ashwini)
        panchak_end = find_next_nak_start(jd_current, ASHWINI_INDEX)
        return panchak_status, panchak_day, None, panchak_end
    else:
        # Outside Panchak - find next Panchak period
        panchak_status = "NO"
        panchak_day = None
        print(f"PANCHAK: Outside Panchak, finding next period")
        
        # Find when next Panchak STARTS (3rd pada of Dhanishta)
        panchak_start = find_panchak_start(jd_current)
        print(f"PANCHAK: Next Panchak starts at JD {panchak_start}")
        
        # Find when that Panchak ENDS (transition to Ashwini)
        panchak_end = find_next_nak_start(panchak_start, ASHWINI_INDEX)
        print(f"PANCHAK: That Panchak ends at JD {panchak_end}")
        
        return panchak_status, panchak_day, panchak_start, panchak_end

def get_panchak_day(nak_index, moon_longitude):
    """Get which day of Panchak we're in (1-5)"""
    panchak_nakshatras = [
        (DHANISHTA_INDEX, [3, 4]),  # Day 1: Dhanishta 3rd & 4th padas
        (SHATABISHA_INDEX, [1, 2, 3, 4]),  # Day 2: Shatabisha all padas
        (PURVA_BHADRAPADA_INDEX, [1, 2, 3, 4]),  # Day 3: Purva Bhadrapada all padas
        (UTTARA_BHADRAPADA_INDEX, [1, 2, 3, 4]),  # Day 4: Uttara Bhadrapada all padas
        (REVATI_INDEX, [1, 2, 3, 4])  # Day 5: Revati all padas
    ]
    
    for day, (nak, padas) in enumerate(panchak_nakshatras, 1):
        if nak_index == nak:
            if nak == DHANISHTA_INDEX:
                current_pada = get_pada(moon_longitude)
                if current_pada in padas:
                    return day
            else:
                return day
    
    return None

def get_pada(longitude):
    """Get pada (quarter) from longitude (1-4)"""
    return int((longitude % SEGMENT) // (SEGMENT / 4)) + 1

def find_panchak_start(jd_start):
    """Find when Panchak actually starts (3rd pada of Dhanishta)"""
    # First find when Dhanishta starts
    dhanishta_start = find_next_nak_start(jd_start, DHANISHTA_INDEX)
    
    # Now find when 3rd pada of Dhanishta starts
    # Each nakshatra = 13°20' = 800'
    # Each pada = 3°20' = 200'
    # 3rd pada starts at 400' into Dhanishta
    
    dhanishta_3rd_pada_start = find_pada_start(dhanishta_start, DHANISHTA_INDEX, 3)
    
    return dhanishta_3rd_pada_start

def find_pada_start(nak_start_jd, nak_index, pada_number):
    """Find when a specific pada of a nakshatra starts"""
    # Each pada = SEGMENT / 4 degrees
    target_longitude = (nak_index * SEGMENT) + ((pada_number - 1) * (SEGMENT / 4))
    
    # Binary search to find when Moon reaches this longitude
    return binary_search_longitude(nak_start_jd, nak_start_jd + 2.0, target_longitude)

def get_panchak_info(jd_current, current_nakshatra):
    """Get Panchak information - FINAL CORRECTED VERSION"""
    panchak_status, panchak_day, panchak_start_jd, panchak_end_jd = get_panchak_period(jd_current, current_nakshatra)
    
    # Debug: show what we found
    print(f"PANCHAK RESULT: status={panchak_status}, day={panchak_day}")
    print(f"PANCHAK JD: start={panchak_start_jd}, end={panchak_end_jd}")
    
    # Verify the results
    if panchak_start_jd:
        start_nak = nak_index(panchak_start_jd)
        start_lon = moon_lon_sidereal(panchak_start_jd) % 360
        start_pada = get_pada(start_lon)
        print(f"VERIFY START: nakshatra={start_nak}, longitude={start_lon:.2f}°, pada={start_pada}")
    
    if panchak_end_jd:
        end_nak = nak_index(panchak_end_jd)
        print(f"VERIFY END: nakshatra={end_nak} (should be Ashwini)")
    
    def jd_to_datetime_adjusted(jd):
        if jd is None:
            return None
        dt = jd_to_datetime_correct(jd)
        return dt
    
    panchak_start_dt = jd_to_datetime_adjusted(panchak_start_jd)
    panchak_end_dt = jd_to_datetime_adjusted(panchak_end_jd)
    
    return {
        "is_in_panchak": panchak_status,
        "panchak_day": panchak_day,
        "panchak_start": panchak_start_dt.strftime("%d-%m-%Y %H:%M") if panchak_start_dt else "—",
        "panchak_end": panchak_end_dt.strftime("%d-%m-%Y %H:%M") if panchak_end_dt else "—",
    }

def get_disha_shool(weekday):
    directions = DISHA_SHOOL_DIRECTIONS.get(weekday, [])
    remedy = DISHA_SHOOL_REMEDY.get(weekday, "No remedy found")
    return {"directions": directions, "remedy": remedy}

def get_karana(tithi_angle):
    """Get correct karana based on the algorithm you provided"""
    # Calculate D (difference between Moon and Sun longitude)
    D = tithi_angle  # This is already (M - S) % 360
    
    # Divide by 6 degrees to find Karana units elapsed
    karana_units = D / 6.0
    
    # Get Karana number K (0-based)
    K = int(karana_units) % 60  # There are 60 karanas in a cycle
    
    # Determine Karana type
    if K == 57:
        return "Shakuni"
    elif K == 58:
        return "Chatushpada"
    elif K == 59:
        return "Naga"
    elif K == 0:
        return "Kimstughna"
    else:
        # For repeating karanas (1-56), subtract multiples of 7
        repeating_k = (K - 1) % 7
        return KARANA_NAMES[repeating_k]

def get_nakshatra_with_pada(longitude):
    """
    Get nakshatra with pada information
    Returns formatted string and separate values
    """
    
    nakshatra_size = 360.0 / 27  # 13.3333 degrees
    nakshatra_index = int(longitude / nakshatra_size)
    nakshatra_name = NAKSHATRA_NAMES[nakshatra_index]
    
    # Calculate pada
    position_in_nakshatra = longitude % nakshatra_size
    pada_size = nakshatra_size / 4  # 3.3333 degrees
    pada_number = int(position_in_nakshatra / pada_size) + 1
    
    return {
        'nakshatra': nakshatra_name,
        'pada': pada_number,
        'nakshatra_pada': f"{nakshatra_name} {pada_number}",
        'position_in_nakshatra': position_in_nakshatra,
        'nakshatra_index': nakshatra_index
    }

def degrees_to_dms(degrees):
    """Convert decimal degrees to degrees, minutes, seconds as formatted string"""
    deg = int(degrees)
    min_decimal = (degrees - deg) * 60
    min = int(min_decimal)
    sec = int((min_decimal - min) * 60)
    return f"{deg}° {min}' {sec}\""

def degrees_to_dm(degrees):
    """Convert decimal degrees to degrees, minutes as formatted string"""
    deg = int(degrees)
    min_decimal = (degrees - deg) * 60
    min = int(min_decimal)
    return f"{deg}° {min}'"

def find_transition(jd_start, key="tithi", lat=None, lon=None, planet_id=None,
                    scan_step_days=0.005, max_scan_days=4.0, tol=1e-6):
    """
    Robust transition finder for tithi/nakshatra/yoga/karana/ascendant/moon_sign.
    """
    def angle_func(jd):
        """Return relevant angular value (0–360) for given key."""
        if key in ("tithi", "nakshatra", "yoga", "karana", "moon_sign", "planet"):
            ay = swe.get_ayanamsa_ut(jd)
            
            if key == "planet":
                if planet_id is None:
                    raise ValueError("planet_id required for planet transition")
                pos = swe.calc_ut(jd, planet_id)[0]
                return (pos[0] - ay) % 360  # Nirayana
            else:
                s_pos = swe.calc_ut(jd, swe.SUN)[0]
                m_pos = swe.calc_ut(jd, swe.MOON)[0]
                sun_lon = (s_pos[0] - ay) % 360  # Nirayana
                moon_lon = (m_pos[0] - ay) % 360  # Nirayana

                if key in ("tithi", "karana"):
                    return (moon_lon - sun_lon) % 360
                elif key in ("nakshatra", "moon_sign"):
                    return moon_lon
                elif key == "yoga":
                    return (sun_lon + moon_lon) % 360

        elif key == "ascendant":
            if lat is None or lon is None:
                raise ValueError("Latitude and longitude required for ascendant transition")
            houses = swe.houses(jd, lat, lon, b'P')
            asc_sayana = houses[0][0] % 360  # Sayana (tropical) longitude
            ayanamsa = swe.get_ayanamsa_ut(jd)
            asc_nirayana = (asc_sayana - ayanamsa) % 360  # Convert to Nirayana
            return asc_nirayana  # Return Nirayana for consistent comparison

        else:
            raise ValueError(f"Invalid key: {key}")

    # Step size in degrees
    if key == "tithi":
        step_size = 12.0
    elif key in ("nakshatra", "yoga"):
        step_size = 360.0 / 27.0
    elif key == "karana":
        step_size = 6.0
    elif key in ("ascendant", "planet", "moon_sign"):
        step_size = 30.0  # each zodiac sign = 30°

    # Current value
    current_val = angle_func(jd_start)

    # Next boundary target
    base_target = (math.floor(current_val / step_size) + 1) * step_size
    target_val = base_target
    if target_val <= current_val:
        target_val += 360.0

    def ang_dist_from_current(val):
        return (val - current_val + 360.0) % 360.0

    target_dist = ang_dist_from_current(target_val)

    # --- Bracket Search ---
    jd_low = jd_start
    jd_high = jd_start
    step = scan_step_days
    scanned = 0.0
    found_bracket = False

    while scanned <= max_scan_days:
        jd_high = jd_start + scanned
        val_high = angle_func(jd_high)
        val_high_dist = ang_dist_from_current(val_high)
        if val_high_dist >= target_dist:
            found_bracket = True
            break
        scanned += step

    if not found_bracket:
        return None

    jd_low = max(jd_start, jd_high - step)

    # --- Binary Search for Precision ---
    iterations = 0
    max_iter = 80
    while iterations < max_iter:
        jd_mid = 0.5 * (jd_low + jd_high)
        val_mid = angle_func(jd_mid)
        mid_dist = ang_dist_from_current(val_mid)

        if mid_dist < target_dist:
            jd_low = jd_mid
        else:
            jd_high = jd_mid

        if abs(jd_high - jd_low) < 1e-7:
            break
        if abs(mid_dist - target_dist) < tol:
            break

        iterations += 1

    exact_jd = 0.5 * (jd_low + jd_high)

    # --- Verification ---
    final_val = angle_func(exact_jd)
    final_dist = ang_dist_from_current(final_val)
    if abs(final_dist - target_dist) > 0.5:
        return None

    return exact_jd



def get_choghadiya(sunrise, sunset, nextsunrise, weekday):
    """
    Returns Choghadiya periods for day and night using classical weekday-based sequences.
    weekday: 0=Sunday, 1=Monday, ..., 6=Saturday
    """

    # 8-period Choghadiya sequences for each weekday (day)
    day_seq = {
        0: ["Udveg", "Char", "Labh", "Amrit", "Kaal", "Shubh", "Rog", "Udveg"],
        1: ["Amrit", "Kaal", "Shubh", "Rog", "Udveg", "Char", "Labh", "Amrit"],
        2: ["Rog", "Udveg", "Char", "Labh", "Amrit", "Kaal", "Shubh", "Rog"],
        3: ["Labh", "Amrit", "Kaal", "Shubh", "Rog", "Udveg", "Char", "Labh"],
        4: ["Shubh", "Rog", "Udveg", "Char", "Labh", "Amrit", "Kaal", "Shubh"],
        5: ["Char", "Labh", "Amrit", "Kaal", "Shubh", "Rog", "Udveg", "Char"],
        6: ["Kaal", "Shubh", "Rog", "Udveg", "Char", "Labh", "Amrit", "Kaal"]
    }

    # 8-period Choghadiya sequences for each weekday (night)
    # Night sequence can be shifted, or use the same logic with sunset → next sunrise
    night_seq = {
        0: ["Shubh", "Amrit", "Char", "Rog", "Kaal", "Labh", "Udveg", "Shubh"],
        1: ["Char", "Rog", "Kaal", "Labh", "Udveg", "Shubh", "Amrit", "Char"],
        2: ["Kaal", "Labh", "Udveg", "Shubh", "Amrit", "Char", "Rog", "Kaal"],
        3: ["Udveg", "Shubh", "Amrit", "Char", "Rog", "Kaal", "Labh", "Udveg"],
        4: ["Amrit", "Char", "Rog", "Kaal", "Labh", "Udveg", "Shubh", "Amrit"],
        5: ["Rog", "Kaal", "Labh", "Udveg", "Shubh", "Amrit", "Char", "Rog"],
        6: ["Labh", "Udveg", "Shubh", "Amrit", "Char", "Rog", "Kaal", "Labh"]
    }

    def build_periods(start_time, end_time, names):
        duration = (end_time - start_time) / 8
        periods = []
        current = start_time
        for name in names:
            periods.append({"name": name, "start": current, "end": current + duration})
            current += duration
        return periods

    day_chog = build_periods(sunrise, sunset, day_seq[weekday])
    night_chog = build_periods(sunset, nextsunrise, night_seq[weekday])

    return {"day": day_chog, "night": night_chog}

def get_horas(sunrise, sunset, nextsunrise, weekday):
    planets = ["Saturn", "Jupiter", "Mars", "Sun", "Venus", "Mercury", "Moon"]

    weekday_start_planet = {
        0: "Sun", 1: "Moon", 2: "Mars", 3: "Mercury", 4: "Jupiter", 5: "Venus", 6: "Saturn",
        "Raviwar": "Sun", "Somawar": "Moon", "Mangalwar": "Mars", "Budhwar": "Mercury",
        "Guruwar": "Jupiter", "Shukrawar": "Venus", "Shaniwar": "Saturn",
        "Sunday": "Sun", "Monday": "Moon", "Tuesday": "Mars", "Wednesday": "Mercury",
        "Thursday": "Jupiter", "Friday": "Venus", "Saturday": "Saturn"
    }

    start_planet = weekday_start_planet.get(weekday)

    def build_horas(start_time, end_time, start_planet):
        """Build 12 Hora periods with planet rulerships"""
        duration = (end_time - start_time) / 12
        periods = []
        start_index = planets.index(start_planet)
        current = start_time

        for i in range(12):
            planet = planets[(start_index + i) % 7]
            periods.append({
                "hora_num": i + 1,
                "planet": planet,
                "start": current.strftime("%H:%M"),
                "end": (current + duration).strftime("%H:%M")
            })
            current += duration

        return periods

    # DAY Horas: sunrise → sunset
    day_horas = build_horas(sunrise, sunset, weekday_start_planet[weekday])

    # NIGHT Horas: sunset → next sunrise
    # Night starts from the 13th Hora → continue sequence
    last_planet_day = day_horas[-1]["planet"]
    next_start_planet = planets[(planets.index(last_planet_day) + 1) % 7]
    night_horas = build_horas(sunset, nextsunrise, next_start_planet)

    return {"day": day_horas, "night": night_horas}

#below function duplicated from astro_calculations for tarabalam
def get_planetary_positions(jd_current, lat, lon, tz_offset):
    """Get positions of all planets including Rahu/Ketu and Ascendant"""
    
    planets = {
        swe.SUN: "Sun",
        swe.MOON: "Moon", 
        swe.MARS: "Mars",
        swe.MERCURY: "Mercury", 
        swe.JUPITER: "Jupiter",
        swe.VENUS: "Venus",
        swe.SATURN: "Saturn",
        swe.TRUE_NODE: "Rahu",  # North Node
        # Note: Ketu will be calculated separately as 180° from Rahu
    }
    
    planetary_data = []
    ayanamsa = swe.get_ayanamsa_ut(jd_current)
    
    # Store Rahu data to calculate Ketu later
    rahu_data = None
    
    # Calculate all planets
    for planet_id, planet_name in planets.items():
        try:
            # Calculate planet position with proper error handling
            flags = swe.FLG_SWIEPH | swe.FLG_SPEED
            result = swe.calc_ut(jd_current, planet_id, flags)
            zodiac_sign_end_time =None
            
            if isinstance(result, tuple) and len(result) >= 2:
                pos, speed = result[0], result[1]
                
                # Handle both scalar and array speeds
                if hasattr(speed, '__len__') and len(speed) > 0:
                    speed_value = speed[0]
                else:
                    speed_value = speed
                
                # Calculate longitude with ayanamsa
                if hasattr(pos, '__len__') and len(pos) > 0:
                    longitude = (pos[0] - ayanamsa) % 360
                else:
                    longitude = (pos - ayanamsa) % 360
                
                # Determine if retrograde (negative speed)
                is_retrograde = speed_value < 0
                
                total_degrees = int(longitude)
                total_dm = degrees_to_dm(longitude)

                # Get zodiac sign (30° each)
                zodiac_index = int(longitude // 30)
                zodiac_sign = ZODIAC_SIGNS[zodiac_index]
                zodiac_sign_end = find_transition(jd_current, key="planet", lat=lat, lon=lon, planet_id=planet_id)
                if zodiac_sign_end:
                    zodiac_sign_end_time = jd_to_datetime_correct(zodiac_sign_end, tz_offset)  # uses tz_offset

                # Calculate position within sign
                sign_degree = round(longitude % 30,6)
                sign_dm = degrees_to_dm(sign_degree)
                

                nakshatra = get_nakshatra_with_pada(longitude)['nakshatra']
                nakshatra_pada = get_nakshatra_with_pada(longitude)['pada']
                
                planet_data = {
                    "planet": planet_name,
                    "longitude": round(longitude, 6),
                    "sign_degree": sign_dm,
                    "zodiac_sign": zodiac_sign,
                    "zodiac_sign_end_time": zodiac_sign_end_time,
                    "nakshatra" : nakshatra,
                    "nakshatra_pada" : nakshatra_pada,
                    "is_retrograde": is_retrograde,
                    "speed": round(speed_value, 6),
                    "retrograde_status": "Retrograde" if is_retrograde else "Direct"
                }
                
                planetary_data.append(planet_data)
                
                # Store Rahu data to calculate Ketu
                if planet_name == "Rahu":
                    rahu_data = planet_data
                
            else:
                planetary_data.append({
                    "planet": planet_name,
                    "error": "Invalid calculation result"
                })
                
        except Exception as e:
            print(f"Error calculating {planet_name}: {e}")
            planetary_data.append({
                "planet": planet_name,
                "error": str(e)
            })
    
    # Calculate Ketu as 180 degrees from Rahu
    if rahu_data and "longitude" in rahu_data:
        rahu_longitude = rahu_data["longitude"]
        ketu_longitude = (rahu_longitude + 180) % 360
        
      
        # Get zodiac sign (30° each)
        ketu_zodiac_index = int(ketu_longitude // 30)
        ketu_zodiac_sign = ZODIAC_SIGNS[zodiac_index]
        ketu_zodiac_sign_end_time = rahu_data.get("zodiac_sign_end_time", None)
        
        # Calculate position within sign
        ketu_sign_degree = ketu_longitude % 30
        ketu_sign_dm = degrees_to_dm(sign_degree)

        ketu_nakshatra = get_nakshatra_with_pada(ketu_longitude)['nakshatra']
        ketu_nakshatra_pada = get_nakshatra_with_pada(ketu_longitude)['pada']

        # Ketu is always retrograde (opposite to Rahu)
        ketu_data = {
            "planet": "Ketu",
            "longitude": round(ketu_longitude, 6),
            "sign_degree": ketu_sign_dm,
            "zodiac_sign": ketu_zodiac_sign,
            "zodiac_sign_end_time": ketu_zodiac_sign_end_time,
            "nakshatra" : ketu_nakshatra,
            "nakshatra_pada" : ketu_nakshatra_pada,
            "is_retrograde": True,  # Ketu is always considered retrograde
            "speed": rahu_data.get("speed", 0),  # Use same speed as Rahu
            "retrograde_status": "Retrograde"
        }
        
        planetary_data.append(ketu_data)
    
    # Calculate Ascendant
    try:
        # Calculate houses using Placidus system
        houses = swe.houses(jd_current, lat, lon, b'P')
        
        # houses[0] contains the cusps (house positions)
        # houses[0][0] is the Ascendant (1st house cusp)
        ascendant_longitude = houses[0][0] % 360
        ayanamsa = swe.get_ayanamsa_ut(jd_current)
        ascendant_longitude_nirayana = (ascendant_longitude - ayanamsa) % 360
        
        # Get zodiac sign (30° each)
        asc_zodiac_index = int(ascendant_longitude_nirayana // 30)
        asc_zodiac_sign = ZODIAC_SIGNS[asc_zodiac_index]
        asc_zodiac_sign_end = find_transition(jd_current, key="ascendant", lat=lat, lon=lon, planet_id=None)
        if asc_zodiac_sign_end:
            asc_zodiac_sign_end_time = jd_to_datetime_correct(asc_zodiac_sign_end, tz_offset)  # uses tz_offset
        
        # Calculate position within sign
        asc_sign_degree = ascendant_longitude_nirayana % 30
        asc_sign_dm = degrees_to_dm(asc_sign_degree)

        asc_nakshatra = get_nakshatra_with_pada(ascendant_longitude_nirayana)['nakshatra']
        asc_nakshatra_pada = get_nakshatra_with_pada(ascendant_longitude_nirayana)['pada']
        
        ascendant_data = {
            "planet": "Ascendant",
            "longitude": round(ascendant_longitude_nirayana, 6),
            "sign_degree": asc_sign_dm,
            "zodiac_sign": asc_zodiac_sign,
            "asc_zodiac_end_time":asc_zodiac_sign_end_time,
            "nakshatra" : asc_nakshatra,
            "nakshatra_pada" : asc_nakshatra_pada,
            "is_retrograde": False,
            "speed": 0,
            "retrograde_status": "Direct",
            "house": 1,
            "raw_sayana": round(ascendant_longitude, 6),  # For debugging
            "ayanamsa": round(ayanamsa, 6)  # For debugging
        }

        
        planetary_data.append(ascendant_data)
        
    except Exception as e:
        print(f"❌ Error calculating ascendant new: {e}")
        import traceback
        traceback.print_exc()
    
    return planetary_data


def get_chandratarabalam(currentmoonsign, currentnakshatra, user, target_date):
    # Default response structure
    default_response = {
        "chandrabalam": "Share Birth Details",
        "chandrabalam_end": "N/A",
        "chandrabalam_next": "N/A",
        "tarabalam": "Share Birth Details", 
        "tarabalam_end": "N/A",
        "tarabalam_next": "N/A",
        "natal_moon_sign": "Unknown",
        "natal_nakshatra": "Unknown",
        "current_moon_sign": currentmoonsign,
        "current_nakshatra": currentnakshatra
    }
    
    if not user or not hasattr(user, 'profile'):
        return default_response
    
    try:
        user_profile = user.profile
        birthdate = user_profile.birth_date
        birthtime = user_profile.birth_time
        birthlat = user_profile.birth_latitude
        birthlon = user_profile.birth_longitude
        birthtimezone = user_profile.birth_timezone
                    
        # Parse birth datetime and generate kundali data
        birth_dt_naive = datetime.combine(birthdate, birthtime)
        
        # Get timezone from coordinates or use provided timezone
        tf = TimezoneFinder()
        detected_tz = tf.timezone_at(lat=birthlat, lng=birthlon)
        timezone_str = detected_tz or birthtimezone or 'Asia/Kolkata'
        
        # Make timezone aware but KEEP LOCAL CIVIL TIME
        tz = pytz.timezone(timezone_str)
        birth_datetime_local = tz.localize(birth_dt_naive)
        
        # Calculate timezone offset in hours for the calculator
        tz_offset = birth_datetime_local.utcoffset().total_seconds() / 3600.0
        jd_birth = get_julian(birth_datetime_local.year, birth_datetime_local.month, birth_datetime_local.day,
                             birth_datetime_local.hour + birth_datetime_local.minute / 60.0 + birth_datetime_local.second / 3600.0 - tz_offset)
        planetpositions = get_planetary_positions(jd_birth, birthlat, birthlon, tz_offset)
        
        natalmoonsign = None
        natalnakshatra = None
        for planet in planetpositions:
            if planet["planet"] == "Moon":
                natalmoonsign = planet["zodiac_sign"]
                natalnakshatra = NAKSHATRA_NAMES[int(planet["longitude"] // (360 / 27))]
                break
        
        if not natalmoonsign:
            return default_response
        
        # Calculate current time's JD for transitions
        current_tz = pytz.timezone('Asia/Kolkata')  # or use your panchang timezone
        if target_date.tzinfo is None:
            current_date_local = current_tz.localize(target_date)
        else:
            current_date_local = target_date.astimezone(current_tz)
        
        current_tz_offset = current_date_local.utcoffset().total_seconds() / 3600.0
        jd_current = get_julian(current_date_local.year, current_date_local.month, current_date_local.day,
                               current_date_local.hour + current_date_local.minute / 60.0 + current_date_local.second / 3600.0 - current_tz_offset)
        
        # Calculate Chandrabalam (Moon strength)
        natalmoonsignindex = ZODIAC_SIGNS.index(natalmoonsign)
        currentmoonsignindex = ZODIAC_SIGNS.index(currentmoonsign)
        diff = (currentmoonsignindex - natalmoonsignindex) % 12
        
        # Find Moon sign transition (when current moon sign ends)
        moon_sign_end_jd = find_transition(jd_current, key="moon_sign")
        moon_sign_end = jd_to_datetime_correct(moon_sign_end_jd, current_tz_offset) if moon_sign_end_jd else None
        
        # Calculate next moon sign and its balam
        next_moon_sign_index = (currentmoonsignindex + 1) % 12
        next_moon_sign = ZODIAC_SIGNS[next_moon_sign_index]
        next_diff = (next_moon_sign_index - natalmoonsignindex) % 12
        
        if next_diff in [1, 3, 6, 7, 10, 11]:
            next_chandrabalam = "Auspicious"
        elif next_diff in [0, 2, 4, 5, 8, 9]:
            next_chandrabalam = "Inauspicious"
        else:
            next_chandrabalam = "neutral"
        
        # Determine Chandrabalam result and messages
        if diff in [1, 3, 6, 7, 10, 11]:
            chandrabalam_result = "Auspicious"
            chandrabalam_end = moon_sign_end
            chandrabalam_next = f"Next: {next_moon_sign} ({next_chandrabalam})"
        elif diff in [6, 8, 12]:
            chandrabalam_result = "Inauspicious"
            chandrabalam_end = moon_sign_end
            chandrabalam_next = f"Next: {next_moon_sign} ({next_chandrabalam})"
        else:
            chandrabalam_result = "neutral"
            chandrabalam_end = moon_sign_end
            chandrabalam_next = f"Next: {next_moon_sign} ({next_chandrabalam})"
        
        # Calculate Tarabalam (Star strength)
        try:
            nak_index = NAKSHATRA_NAMES.index(currentnakshatra)
            janma_nak_index = NAKSHATRA_NAMES.index(natalnakshatra)
            tarabalam_index = (nak_index - janma_nak_index) % 27
            
            # Find Nakshatra transition (when current nakshatra ends)
            nakshatra_end_jd = find_transition(jd_current, key="nakshatra")
            nakshatra_end = jd_to_datetime_correct(nakshatra_end_jd, current_tz_offset) if nakshatra_end_jd else None
            
            # Calculate next nakshatra and its tarabalam
            next_nak_index = (nak_index + 1) % 27
            next_nakshatra = NAKSHATRA_NAMES[next_nak_index]
            next_tarabalam_index = (next_nak_index - janma_nak_index) % 27
            
            if next_tarabalam_index in [1, 3, 5, 7]:
                next_tarabalam = "Auspicious"
            elif next_tarabalam_index in [0, 2, 4, 6, 8]:
                next_tarabalam = "Inauspicious"
            else:
                next_tarabalam = "neutral"
            
            # Determine Tarabalam result and messages
            if tarabalam_index in [1, 3, 5, 7]:
                tarabalam_result = "Auspicious"
                tarabalam_end = nakshatra_end
                tarabalam_next = f"Next: {next_nakshatra} ({next_tarabalam})"
            elif tarabalam_index in [0, 2, 4, 6, 8]:
                tarabalam_result = "Inauspicious"
                tarabalam_end = nakshatra_end
                tarabalam_next = f"Next: {next_nakshatra} ({next_tarabalam})"
            else:
                tarabalam_result = "neutral"
                tarabalam_end = nakshatra_end
                tarabalam_next = f"Next: {next_nakshatra} ({next_tarabalam})"
                
        except ValueError:
            tarabalam_result = "neutral"
            tarabalam_end = None
            tarabalam_next = "N/A"
        
        # Format datetime objects for display
        def format_datetime(dt):
            if dt:
                return dt.strftime("%Y-%m-%d %H:%M:%S")
            return "N/A"
        
        result = {
            "chandrabalam": chandrabalam_result,
            "chandrabalam_end": format_datetime(chandrabalam_end),
            "chandrabalam_next": chandrabalam_next,
            "tarabalam": tarabalam_result,
            "tarabalam_end": format_datetime(tarabalam_end),
            "tarabalam_next": tarabalam_next,
            "natal_moon_sign": natalmoonsign,
            "natal_nakshatra": natalnakshatra,
            "current_moon_sign": currentmoonsign,
            "current_nakshatra": currentnakshatra
        }
        print(f"User: {user.username}")
        print(f"birth datetime: {birth_datetime_local}, jd_birth: {jd_birth}")
        print(f"Chandrabalam: {chandrabalam_result}, Ends: {result['chandrabalam_end']}, Next: {chandrabalam_next}")
        print(f"Tarabalam: {tarabalam_result}, Ends: {result['tarabalam_end']}, Next: {tarabalam_next}")
        return result
        
    except Exception as e:
        print(f"Error in get_chandratarabalam: {e}")
        import traceback
        traceback.print_exc()
        return default_response


# ---------------------
# Moon & Sun Helper Functions
# ---------------------

def calculate_moon_times(observer, date_obj, tz):
    """Calculate moon rise and set times for a given date and location"""
    try:
        # Convert to naive datetime for astral
        date_naive = date_obj.astimezone(pytz.utc).replace(tzinfo=None)
        
        # Calculate with timezone parameter
        mr = moonrise(observer, date_naive, tzinfo=tz)
        moon_rise = mr.strftime("%H:%M") if mr else "No moonrise"
    except Exception as e:
        moon_rise = "No moonrise"
        print(f"Moonrise calculation error: {e}")
    
    try:
        date_naive = date_obj.astimezone(pytz.UTC).replace(tzinfo=None)
        ms = moonset(observer, date_naive, tzinfo=tz)
        moon_set = ms.strftime("%H:%M") if ms else "No moonset"
    except Exception as e:
        moon_set = "No moonset"
        print(f"Moonset calculation error: {e}")
    
    return moon_rise, moon_set

def get_moon_phase_info(date_obj, tz):
    """Get detailed moon phase information"""
    try:
        moon_age_days = phase(date_obj)
        illumination = (1 - math.cos(2 * math.pi * moon_age_days / 29.53)) / 2 * 100

        if moon_age_days < 1.0:
            phase_name = "New Moon (Amavasya)"
        elif moon_age_days < 7.4:
            phase_name = "Waxing Crescent"
        elif moon_age_days < 8.9:
            phase_name = "First Quarter"
        elif moon_age_days < 14.8:
            phase_name = "Waxing Gibbous"
        elif moon_age_days < 15.8:
            phase_name = "Full Moon (Purnima)"
        elif moon_age_days < 22.1:
            phase_name = "Waning Gibbous"
        elif moon_age_days < 23.6:
            phase_name = "Last Quarter"
        else:
            phase_name = "Waning Crescent"

        return {
            "phase_name": phase_name,
            "illumination": round(illumination, 1),
            "age_days": round(moon_age_days, 1)
        }
    except Exception as e:
        print(f"Moon phase calculation error: {e}")
        return {"phase_name": "Unknown", "illumination": 0, "age_days": 0}



# ---------------------
# Ascendant & House Calculation Functions
# ---------------------

def calculate_ascendant(jd_ut, lat, lon):
    """
    Calculate Ascendant (Lagna) position in degrees
    using Swiss Ephemeris house calculation
    """
    try:
        # Calculate houses using Placidus system
        houses = swe.houses(jd_ut, lat, lon, b'P')
        
        # houses[0] contains the cusps (house positions)
        # houses[0][0] is the Ascendant (1st house cusp)
        ascendant_longitude = houses[0][0]
        
        return ascendant_longitude % 360
        
    except Exception as e:
        print(f"Error calculating ascendant: {e}")
        # Fallback: approximate calculation using local sidereal time
        return calculate_ascendant_approximate(jd_ut, lat, lon)

def calculate_ascendant_approximate(jd_ut, lat, lon):
    """
    Approximate Ascendant calculation using local sidereal time
    """
    # Get local sidereal time
    lst = swe.sidtime(jd_ut) + lon/15.0  # Convert longitude to time units
    lst = lst % 24  # Normalize to 0-24 hours
    
    # Convert LST to degrees (15 degrees per hour)
    lst_degrees = lst * 15
    
    # Approximate ascendant (this is simplified)
    ascendant_approx = (lst_degrees + 90) % 360  # Rough approximation
    
    return ascendant_approx

def get_zodiac_sign(longitude):
    """
    Get zodiac sign name from longitude (0-360 degrees)
    """
    sign_index = int(longitude // 30)
    return ZODIAC_SIGNS[sign_index]

def calculate_house(longitude, jd_ut, lat, lon):
    """
    Calculate which house a planet is in (1-12)
    """
    try:
        houses = swe.houses(jd_ut, lat, lon, b'P')
        house_cusps = houses[0]  # Get house cusps
        
        # Find which house contains this longitude
        for i in range(12):
            start_cusp = house_cusps[i]
            end_cusp = house_cusps[(i + 1) % 12]
            
            # Handle the crossing of 360/0 degrees
            if start_cusp > end_cusp:
                if longitude >= start_cusp or longitude < end_cusp:
                    return i + 1
            else:
                if start_cusp <= longitude < end_cusp:
                    return i + 1
        
        return 1  # Default to 1st house if not found
        
    except Exception as e:
        print(f"Error calculating house: {e}")
        # Fallback: approximate house calculation
        return ((int(longitude // 30) + 1 - 1) % 12) + 1
