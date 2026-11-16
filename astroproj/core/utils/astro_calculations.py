# core/utils/astro_calculations.py
import swisseph as swe
import math
from datetime import datetime, timedelta
import pytz
from astral import LocationInfo
from astral.sun import sun
import pandas as pd
from django.utils import timezone
from datetime import timedelta
from core.models import AuspiciousYoga

from . import panchang_store
from .helpers import (
    get_julian, jd_to_datetime_correct, get_ritu, find_tithi_end_time, hms_format, format_offset, get_nakshatra_with_pada, degrees_to_dm,
    get_karana, find_transition, calculate_moon_times, get_moon_phase_info, get_horas, get_chandratarabalam,
    calculate_ascendant, get_zodiac_sign, calculate_house, get_panchak_info, get_disha_shool, get_choghadiya
)
from .constants import (
    TITHI_NAMES, NAKSHATRA_NAMES, YOGA_NAMES, KARANA_NAMES, SARVARATH_SIDDHIYOG, AMRIT_SIDDHI_YOGA, DWIPUSHKAR_YOGA,TRIPUSHKAR_YOGA,
    WEEKDAYS, AMANTA_MONTHS, PURNIMANTA_MONTHS, RITUS, ZODIAC_SIGNS, PANCHAK,RAHU_KAAL, YAM_KAAL, GULIKA_KAAL, RAVI_YOGA,RAVI_PUSHYA_YOGA, GURU_PUSHYA_YOGA
)
import logging

logger = logging.getLogger(__name__)

def get_vaar(sunrise_time, next_day_sunrise, target_date, tz):
    """
    Calculate correct Vedic weekday (changes at sunrise)
    """
    # Convert both times to the same timezone
    if sunrise_time.tzinfo and next_day_sunrise.tzinfo is None:
        sunrise_time = tz.localize(sunrise_time)
        next_day_sunrise = tz.localize(next_day_sunrise)
    
    if target_date.tzinfo is None:
        target_date = tz.localize(target_date)
    
    # If target time is before sunrise, it's previous day's weekday
    if target_date < sunrise_time:
        # It's still previous day's weekday
        previous_day = target_date - timedelta(days=1)
        weekday_index = (previous_day.weekday() + 1) % 7
        vaar_end = sunrise_time
    else:
        # Normal weekday calculation
        weekday_index = (target_date.weekday() + 1) % 7
        vaar_end = next_day_sunrise+timedelta(minutes=1)
    
    return WEEKDAYS[weekday_index], vaar_end

def get_daily_ascendants(sunrise_dt, sunset_dt, next_sunrise_dt, lat, lon, tz_offset):
    """
    Get daily ascendant transitions using actual transition times
    """
    # Convert local time to UTC before converting to Julian days
    def local_to_utc_jd(local_dt, tz_offset):
        """Convert local datetime to UTC Julian day"""
        # Convert local to UTC
        utc_dt = local_dt.astimezone(pytz.UTC)
        # Calculate JD from UTC
        jd_utc = swe.julday(utc_dt.year, utc_dt.month, utc_dt.day,
                           utc_dt.hour + utc_dt.minute/60.0 + utc_dt.second/3600.0)
        return jd_utc

    # Convert to Julian days in UTC
    jd_sunrise = local_to_utc_jd(sunrise_dt, tz_offset)
    jd_sunset = local_to_utc_jd(sunset_dt, tz_offset)
    jd_next_sunrise = local_to_utc_jd(next_sunrise_dt, tz_offset)

    # Rest of your function remains the same...
    def get_ascendant_periods(start_jd, end_jd, period_name):
        periods = []
        current_jd = start_jd
        
        
        while current_jd < end_jd:
            try:
                # Get current ascendant sign
                houses = swe.houses(current_jd, lat, lon, b'P')
                ascendant_longitude = houses[0][0] % 360
                ayanamsa = swe.get_ayanamsa_ut(current_jd)
                ascendant_sidereal = (ascendant_longitude - ayanamsa) % 360
                
                asc_zodiac_index = int(ascendant_sidereal // 30)
                asc_zodiac_sign = ZODIAC_SIGNS[asc_zodiac_index]
                
                # Find transition
                sign_end_jd = find_transition(current_jd, key="ascendant", lat=lat, lon=lon, planet_id=None)
                
                if not sign_end_jd or sign_end_jd > end_jd:
                    period_end_jd = end_jd
                else:
                    period_end_jd = sign_end_jd
                
                # Convert JD to local time for display
                start_time_local = jd_to_datetime_correct(current_jd, tz_offset)
                end_time_local = jd_to_datetime_correct(period_end_jd, tz_offset)
                
                duration = end_time_local - start_time_local
                total_minutes = duration.total_seconds() / 60
                hours = int(total_minutes // 60)
                minutes = int(total_minutes % 60)
                
                if duration.total_seconds() > 60:
                    period_data = {
                        'start_time': start_time_local.strftime('%H:%M'),
                        'end_time': end_time_local.strftime('%H:%M'),
                        'sign': asc_zodiac_sign,
                        'sign_index': asc_zodiac_index,
                        'duration_hours': hours,
                        'duration_minutes': minutes,
                        'duration_display': f"{hours}h {minutes}m"
                    }
                    periods.append(period_data)
                
                # Move to next period
                if sign_end_jd and sign_end_jd < end_jd:
                    current_jd = sign_end_jd
                else:
                    break
                    
            except Exception as e:
                logger.error(f"Error: {e}")
                break
        
        return periods

    # Get day and night ascendants
    day_ascendants = get_ascendant_periods(jd_sunrise, jd_sunset, "Day")
    night_ascendants = get_ascendant_periods(jd_sunset, jd_next_sunrise, "Night")
    
    return {
        'day': day_ascendants,
        'night': night_ascendants
    }

def get_planetary_positions(jd_current, lat, lon, tz_offset):
    """Get positions of all planets including Rahu/Ketu and Ascendant with house positions"""
    
    planets = {
        swe.SUN: "Sun",
        swe.MOON: "Moon", 
        swe.MARS: "Mars",
        swe.MERCURY: "Mercury", 
        swe.JUPITER: "Jupiter",
        swe.VENUS: "Venus",
        swe.SATURN: "Saturn",
        swe.TRUE_NODE: "Rahu",  # North Node
    }
    
    planetary_data = []
    ayanamsa = swe.get_ayanamsa_ut(jd_current)
    
    # Store Rahu data to calculate Ketu later
    rahu_data = None
    
    # Calculate houses FIRST to get house cusps
    try:
        # Calculate houses using Placidus system
        houses = swe.houses(jd_current, lat, lon, b'P')
        house_cusps = houses[0]  # 12 house cusps + 13th (ascendant again)
        ascendant_longitude = house_cusps[0] % 360
        ascendant_longitude_nirayana = (ascendant_longitude - ayanamsa) % 360
        
        
    except Exception as e:
        logger.error(f"❌ Error calculating houses: {e}")
        house_cusps = None
        ascendant_longitude_nirayana = 0

    def calculate_house_position(planet_longitude, ascendant_longitude):
        asc_sign = int(ascendant_longitude // 30)
        planet_sign = int(planet_longitude // 30)
        return (planet_sign - asc_sign) % 12 + 1

    # Calculate all planets
    for planet_id, planet_name in planets.items():
        try:
            # Calculate planet position with proper error handling
            flags = swe.FLG_SWIEPH | swe.FLG_SPEED
            result = swe.calc_ut(jd_current, planet_id, flags)
            zodiac_sign_end_time = None

            if isinstance(result, tuple) and len(result) > 0:
                ephemeris_data = result[0]
                
                # Handle both scalar and array speeds
                longitude_sayana = ephemeris_data[0]
                speed_value = ephemeris_data[3]  # ← THIS IS THE KEY!
                
                longitude_nirayana = (longitude_sayana - ayanamsa) % 360

                # Determine if retrograde (negative speed)
                is_retrograde = speed_value < -0.0001
                
                # Calculate house position
                house_position = calculate_house_position(longitude_nirayana, ascendant_longitude_nirayana)
                
                # Get zodiac sign (30° each)
                zodiac_index = int(longitude_nirayana // 30)
                zodiac_sign = ZODIAC_SIGNS[zodiac_index]
                zodiac_sign_end = find_transition(jd_current, key="planet", lat=lat, lon=lon, planet_id=planet_id)
                if zodiac_sign_end:
                    zodiac_sign_end_time = jd_to_datetime_correct(zodiac_sign_end, tz_offset)

                # Calculate position within sign
                sign_degree = round(longitude_nirayana % 30, 6)
                sign_dm = degrees_to_dm(sign_degree)

                nakshatra = get_nakshatra_with_pada(longitude_nirayana)['nakshatra']
                nakshatra_pada = get_nakshatra_with_pada(longitude_nirayana)['pada']
                
                planet_data = {
                    "planet": planet_name,
                    "longitude": round(longitude_nirayana, 6),
                    "longitude_sayana": round(longitude_sayana, 6),  # For debugging
                    "sign_degree": sign_dm,
                    "zodiac_sign": zodiac_sign,
                    "zodiac_sign_end_time": zodiac_sign_end_time,
                    "nakshatra": nakshatra,
                    "nakshatra_pada": nakshatra_pada,
                    "is_retrograde": is_retrograde,
                    "speed": round(speed_value, 6),
                    "retrograde_status": "Retrograde" if is_retrograde else "Direct",
                    "house": house_position  # NEW: House position added
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
            logger.error(f"Error calculating {planet_name}: {e}")
            planetary_data.append({
                "planet": planet_name,
                "error": str(e)
            })
    
    # Calculate Ketu as 180 degrees from Rahu
    if rahu_data and "longitude" in rahu_data:
        rahu_longitude_nirayana = rahu_data["longitude"]
        ketu_longitude_nirayana = (rahu_longitude_nirayana + 180) % 360
        
        # Calculate house position for Ketu
        ketu_house_position = calculate_house_position(ketu_longitude_nirayana, ascendant_longitude_nirayana)
        
        # Get zodiac sign
        ketu_zodiac_index = int(ketu_longitude_nirayana // 30)
        ketu_zodiac_sign = ZODIAC_SIGNS[ketu_zodiac_index]
        ketu_zodiac_sign_end_time = rahu_data.get("zodiac_sign_end_time", None)
        
        # Calculate position within sign
        ketu_sign_degree = ketu_longitude_nirayana % 30
        ketu_sign_dm = degrees_to_dm(ketu_sign_degree)

        ketu_nakshatra = get_nakshatra_with_pada(ketu_longitude_nirayana)['nakshatra']
        ketu_nakshatra_pada = get_nakshatra_with_pada(ketu_longitude_nirayana)['pada']

        # Ketu is always retrograde (opposite to Rahu)
        ketu_data = {
            "planet": "Ketu",
            "longitude": round(ketu_longitude_nirayana, 6),
            "sign_degree": ketu_sign_dm,
            "zodiac_sign": ketu_zodiac_sign,
            "zodiac_sign_end_time": ketu_zodiac_sign_end_time,
            "nakshatra": ketu_nakshatra,
            "nakshatra_pada": ketu_nakshatra_pada,
            "is_retrograde": True,
            "speed": rahu_data.get("speed", 0),
            "retrograde_status": "Retrograde",
            "house": ketu_house_position  # NEW: House position for Ketu
        }
        
        planetary_data.append(ketu_data)
    
    # Calculate Ascendant
    try:
        if house_cusps is not None:
            # Get zodiac sign
            asc_zodiac_index = int(ascendant_longitude_nirayana // 30)
            asc_zodiac_sign = ZODIAC_SIGNS[asc_zodiac_index]
            asc_zodiac_sign_end = find_transition(jd_current, key="ascendant", lat=lat, lon=lon, planet_id=None)
            if asc_zodiac_sign_end:
                asc_zodiac_sign_end_time = jd_to_datetime_correct(asc_zodiac_sign_end, tz_offset)
            
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
                "asc_zodiac_end_time": asc_zodiac_sign_end_time,
                "nakshatra": asc_nakshatra,
                "nakshatra_pada": asc_nakshatra_pada,
                "is_retrograde": False,
                "speed": 0,
                "retrograde_status": "Direct",
                "house": 1,  # Ascendant is always 1st house
                "raw_sayana": round(ascendant_longitude, 6),
                "ayanamsa": round(ayanamsa, 6)
            }

            planetary_data.append(ascendant_data)
        
    except Exception as e:
        logger.error(f"❌ Error calculating ascendant: {e}")
        import traceback
        traceback.print_exc()
    
    return planetary_data

def lunar_month_names(instant_utc):
    """(amanta, purnimanta) month names at a naive-UTC instant, from the shared panchang store."""
    row = panchang_store.event_at("paksha", instant_utc)
    if not row:
        return "N/A", "N/A"
    prefix = "Adhik " if row.extra.get("adhik") else ""
    purnimanta_prefix = "Adhik " if row.extra.get("purnimanta_adhik", row.extra.get("adhik")) else ""
    return prefix + row.extra["masa_amanta"], purnimanta_prefix + row.extra["masa_purnimanta"]


def get_panchang(target_date, user=None, lat=None, lon=None, timezone_str=None, city_name=None):
    """Get Panchang for a specific date - handles both authenticated and anonymous users"""
    
    birthdate, birthtime, birthlat, birthlon, birthtimezone, birthcity = (None,)*6
    
    # If user is provided and is a Django User object, use their settings
    if user and hasattr(user, 'profile'):
        user_profile = user.profile  # This is your UserProfile instance
        
        
        # Use current location from profile
        lat = user_profile.latitude
        lon = user_profile.longitude
        timezone_str = user_profile.timezone
        city_name = user_profile.city
        
        # Get birth details for Chandrabalam calculation
        birthdate = user_profile.birth_date
        birthtime = user_profile.birth_time
        birthlat = user_profile.birth_latitude
        birthlon = user_profile.birth_longitude
        birthtimezone = user_profile.birth_timezone
        birthcity = user_profile.birth_place
        
        
    else:
        # Use provided parameters or defaults for anonymous users
        lat = lat or 28.6139  # Delhi default
        lon = lon or 77.2090
        timezone_str = timezone_str or 'Asia/Kolkata'
        city_name = city_name or 'New Delhi'
    
    # FIX: Define tz here so it's available for all cases
    tz = pytz.timezone(timezone_str) if timezone_str else pytz.timezone('Asia/Kolkata')
    
    if target_date.tzinfo is None:
        # Make naive datetime timezone-aware using the pre-defined tz
        target_date = tz.localize(target_date)
    else:
        # If already timezone-aware, convert to our desired timezone for consistency
        target_date = target_date.astimezone(tz)

    tz_offset = target_date.utcoffset().total_seconds() / 3600
        
    swe.set_topo(lat, lon, 0)
    swe.set_sid_mode(swe.SIDM_TRUE_CITRA)
    city = LocationInfo(city_name, "India", timezone_str, lat, lon)

    # Convert to UTC for calculations
    target_time_utc = target_date.astimezone(pytz.utc)

    # print(f"Target time in UTC: {target_time_utc}")
    year = target_time_utc.year
    month = target_time_utc.month
    day = target_time_utc.day
    hour = target_time_utc.hour + target_time_utc.minute/60 + target_time_utc.second/3600

    jd_current = get_julian(year, month, day, hour)

    # 🌙 Moon Times Calculation - uses tz
    moon_rise, moon_set = calculate_moon_times(city.observer, target_date, tz)
    moon_phase_info = get_moon_phase_info(target_date, tz)
    
    # ♄ Planetary Positions
    planetary_positions = get_planetary_positions(jd_current, lat, lon, tz_offset)

    # Core calculations
    ayanamsa = swe.get_ayanamsa_ut(jd_current)
    sun_pos, _ = swe.calc_ut(jd_current, swe.SUN)
    moon_pos, _ = swe.calc_ut(jd_current, swe.MOON)
    sun_lon = (sun_pos[0] - ayanamsa) % 360
    moon_lon = (moon_pos[0] - ayanamsa) % 360
    sun_nakshatra = NAKSHATRA_NAMES[math.floor(sun_lon / (360/27))]
    moon_nakshatra = NAKSHATRA_NAMES[math.floor(moon_lon / (360/27))]


    # 🌙 Tithi - CORRECTED
    tithi_angle = (moon_lon - sun_lon) % 360
    tithi_num_raw = int(tithi_angle // 12) + 1  # 1-30

    # Determine Paksha and correct tithi number (1-15)
    if tithi_num_raw <= 15:
        paksha = "Shukla Paksha"
        tithi_num = tithi_num_raw  # 1-15
    else:
        paksha = "Krishna Paksha"
        tithi_num = tithi_num_raw - 15  # Convert to 1-15

    # Get tithi name
    tithi_name = TITHI_NAMES[tithi_num - 1]
    # Special cases for Purnima and Amavasya
    if tithi_num == 15:
        if paksha == "Shukla Paksha":
            tithi_name = "Purnima"
        else:
            tithi_name = "Amavasya"

    tithi_end_jd = find_tithi_end_time(jd_current, tithi_angle / 12)
    tithi_end_time = jd_to_datetime_correct(tithi_end_jd, tz_offset)

    # For panchang muhurat - use the corrected 1-15 tithi number
    tithi_index = tithi_num  # Now correctly 1-15

    # 🌌 Nakshatra
    nak_index = math.floor(moon_lon / (360/27))
    nakshatra = NAKSHATRA_NAMES[nak_index]
    nakshatra_end = find_transition(jd_current, key="nakshatra")
    if nakshatra_end:
        nakshatra_end = jd_to_datetime_correct(nakshatra_end, tz_offset)  # uses tz_offset

    # 🌀 Yoga
    yoga_angle = (sun_lon + moon_lon) % 360
    yoga_index = math.floor(yoga_angle / (360/27))
    yoga = YOGA_NAMES[yoga_index]
    yoga_end = find_transition(jd_current, key="yoga")
    if yoga_end:
        yoga_end = jd_to_datetime_correct(yoga_end, tz_offset)  # uses tz_offset

    # 🐘 Karana
    karana = get_karana(tithi_angle)
    karana_end = find_transition(jd_current, key="karana")
    if karana_end:
        karana_end = jd_to_datetime_correct(karana_end, tz_offset)  # uses tz_offset

    # 🌅 Sunrise / Sunset - uses tz
    s = sun(city.observer, date=target_date.date(), tzinfo=tz)
    s_1 = sun(city.observer, date=(target_date + timedelta(days=1)).date(), tzinfo=tz)
    sunrise = s["sunrise"]
    sunset = s["sunset"]
    nextsunrise = s_1["sunrise"]
    day_length = (sunset - sunrise)
    night_length = nextsunrise - sunset
    
    # Months & Ritu
    zodiac = int(sun_lon // 30)
    # Both use the same indexing (0-11)
    instant = target_date if target_date.tzinfo else tz.localize(target_date)
    instant = instant.astimezone(pytz.utc).replace(tzinfo=None)
    amanta_month, purnimanta_month = lunar_month_names(instant)
    ritu = get_ritu(sun_lon)
    ritu_sayana = get_ritu(sun_pos[0] % 360)   # tropical Sun: the ritu most printed panchangs announce

    # Weekday - uses tz
    vaar, vaar_end = get_vaar(s['sunrise'], s_1['sunrise'], target_date, tz)
    weekday = vaar

    # Get Ascendant from planetary positions
    ascendant_sign = None
    ascendant_index = None

    
    # Find Ascendant in planetary positions
    for planet_data in planetary_positions:
        if planet_data.get("planet") == "Ascendant":
            ascendant_sign = planet_data.get("zodiac_sign")
            if ascendant_sign:
                ascendant_index = ZODIAC_SIGNS.index(ascendant_sign) + 1
                ascendant_end_jd = find_transition(jd_current,key="ascendant", lat=lat, lon=lon)
                if ascendant_end_jd:
                    ascendant_zodiac_end = jd_to_datetime_correct(ascendant_end_jd, tz_offset)
                break
    
    # If Ascendant not found, use a default (Aries)
    if not ascendant_sign:
        ascendant_sign = "Aries"
        ascendant_index = 1

    # Calculate Panchang Muhurat
    # Get index numbers starting from 1
    tithi_index = tithi_num  # Already 1-based (1 to 30)
    nakshatra_index = nak_index + 1  # Convert from 0-based to 1-based (1 to 27)
    weekday_index = WEEKDAYS.index(weekday) + 1  # Convert from 0-based to 1-based (1 to 7)
    
    # Calculate sum and remainder when divided by 9
    total_sum = tithi_index + nakshatra_index + weekday_index + ascendant_index
    panchang_muhurat = total_sum % 9
    
    weekday_index = WEEKDAYS.index(weekday)  # 0=Sunday
    chog = get_choghadiya(sunrise, sunset, nextsunrise, weekday_index)


    # Split into auspicious and inauspicious for day and night
    def split_chog(periods):
        ausp = ["Amrit", "Shubh", "Labh"]
        inausp = ["Kaal", "Rog", "Udveg", "Char"]
        ausp_list = [p for p in periods if p["name"] in ausp]
        inausp_list = [p for p in periods if p["name"] in inausp]
        return ausp_list, inausp_list

    day_ausp, day_inausp = split_chog(chog["day"])
    night_ausp, night_inausp = split_chog(chog["night"])

    chandrabalam_data = {}
    if user and birthdate:  # Only call if user has birth data
        chandrabalam_data = get_chandratarabalam(
            currentmoonsign=get_zodiac_sign(moon_lon), 
            currentnakshatra=nakshatra, 
            user=user,
            target_date=target_date  # Add this parameter
        )

    ascendants = get_daily_ascendants(sunrise, sunset, nextsunrise, lat, lon, tz_offset)
    panchak_info = get_panchak_info(jd_current, nak_index)
    rahu_kaal_start = sunrise + (sunset - sunrise)/8*(RAHU_KAAL[WEEKDAYS.index(weekday)])
    rahu_kaal_end = rahu_kaal_start + (day_length/8)
    gulika_kaal_start = sunrise + (sunset - sunrise)/8*(GULIKA_KAAL[WEEKDAYS.index(weekday)])
    gulika_kaal_end = gulika_kaal_start + (day_length/8)
    yam_kaal_start = sunrise + (sunset - sunrise)/8*(YAM_KAAL[WEEKDAYS.index(weekday)])
    yam_kaal_end = yam_kaal_start + (day_length/8)
    pradosh_start = sunset
    pradosh_end = sunset + timedelta(minutes=144)
    abhijeetstart = sunrise + (day_length)/2 - timedelta(minutes=24)
    abhijeetend = sunrise + (day_length)/2 + timedelta(minutes=24)
    vijaymuhuratstart = day_length/15*10 + sunrise
    vijaymuhuratend = day_length/15*11 + sunrise
    varjyam = sunrise + (day_length/60*25)
    horas = get_horas(sunrise, sunset, nextsunrise, weekday)

    #print("ascendant_zodiac_end:", ascendant_zodiac_end, ascendant_zodiac_end.tzinfo)

    return {
        "location_info": {
            "city": city_name,
            "coordinates": f"{lat:.4f}, {lon:.4f}",
            "timezone": timezone_str,
            "timezone_offset": f"UTC{tz_offset:+g}"  # uses tz_offset
        },
        "date_time": target_date.strftime("%d-%m-%Y %H:%M"),
        
        # Sun and Moon Times
        "sunrise": s["sunrise"].strftime("%H:%M"),
        "sun_longitude": sun_lon,
        "moon_longitude": moon_lon,
        "moon_nakshatra": moon_nakshatra,
        "sun_nakshatra" : sun_nakshatra,
        "vaar_end": vaar_end.strftime("%d-%m-%Y, %H:%M"),
        "sunset": s["sunset"].strftime("%H:%M"),
        "day length" : hms_format(day_length),
        "moonrise": moon_rise,
        "moonset": moon_set,
        "night length": hms_format(night_length),
        "moon_phase": moon_phase_info,
        "brahma_muhurat_start": (s["sunrise"] - timedelta(minutes =96)).strftime("%H:%M"),
        "brahma_muhurat_end": (s["sunrise"] - timedelta(minutes =48)).strftime("%H:%M"),        
        # Panchang Elements
        "tithi": tithi_name,
        "paksha_tithi": f"{paksha} {tithi_name}",
        "tithi_end": tithi_end_time.strftime("%d-%m-%Y, %H:%M") if tithi_end_time else "—",
        "weekday": weekday,
        "nakshatra": nakshatra,
        "nakshatra_end": nakshatra_end.strftime("%d-%m-%Y, %H:%M") if nakshatra_end else "—",
        "yoga": yoga,
        "yoga_end": yoga_end.strftime("%d-%m-%Y, %H:%M") if yoga_end else "—",
        "karana": karana,
        "karana_end": karana_end.strftime("%d-%m-%Y, %H:%M") if karana_end else "—",
        "amanta_month": amanta_month,
        "purnimanta_month": purnimanta_month,
        "ritu": ritu,
        "ritu_sayana": ritu_sayana,
        "lagna_sign": ascendant_sign,
        "lagna_longitude": next((p["longitude"] for p in planetary_positions if p["planet"] == "Ascendant"), None),
        "lagna_end" : ascendant_zodiac_end.strftime("%d-%m-%Y, %H:%M") if ascendant_zodiac_end else "—",
        "panchak": panchak_info,
        "disha_shool": get_disha_shool(weekday),
        "abhijeetstart" : abhijeetstart.strftime("%H:%M"),
        "abhijeetend" : abhijeetend.strftime("%H:%M"),
        "vijaymuhuratstart":vijaymuhuratstart.strftime("%H:%M"),
        "vijaymuhuratend":vijaymuhuratend.strftime("%H:%M"),
        "rahukaalstart": rahu_kaal_start.strftime("%H:%M") if rahu_kaal_start else "—",
        "rahukaalend" : rahu_kaal_end.strftime('%H:%M') if rahu_kaal_end else "—",
        "gulikakaalstart": gulika_kaal_start.strftime("%H:%M"),
        "gulikakaalend" : gulika_kaal_end.strftime('%H:%M'),
        "yamakaalstart": yam_kaal_start.strftime("%H:%M"),
        "yamakaalend" : yam_kaal_end.strftime('%H:%M'),
        "pradoshstart": pradosh_start.strftime("%H:%M"),
        "pradoshend" : pradosh_end.strftime('%H:%M'),
        "varjyam" : varjyam.strftime('%H:%M'),
        "chandrabalam": chandrabalam_data,
        # Planetary Positions
        "planetary_positions": {item["planet"]: item for item in planetary_positions},
        "day_horas": horas["day"],
        "night_horas": horas["night"],
        "day_ascendants": ascendants["day"],    # Same pattern!
        "night_ascendants": ascendants["night"], # Same pattern!
        "choghadiya": {
            "day_ausp": [{"name": p["name"], 
                        "start": p["start"].strftime("%H:%M"), 
                        "end": p["end"].strftime("%H:%M")} 
                        for p in day_ausp],
            "day_inausp": [{"name": p["name"], 
                            "start": p["start"].strftime("%H:%M"), 
                            "end": p["end"].strftime("%H:%M")} 
                        for p in day_inausp],
            "night_ausp": [{"name": p["name"], 
                            "start": p["start"].strftime("%H:%M"), 
                            "end": p["end"].strftime("%H:%M")} 
                        for p in night_ausp],
            "night_inausp": [{"name": p["name"], 
                            "start": p["start"].strftime("%H:%M"), 
                            "end": p["end"].strftime("%H:%M")} 
                            for p in night_inausp],
            },
        
        # Panchang Muhurat Calculation
        "panchang_muhurat": panchang_muhurat,
        "panchang_muhurat_end": min(tithi_end_time, nakshatra_end, vaar_end, ascendant_zodiac_end).strftime("%d-%m-%Y, %H:%M"),
        "panchang_muhurat_details": {
            "tithi_index": tithi_index,
            "nakshatra_index": nakshatra_index,
            "weekday_index": weekday_index,
            "ascendant_index": ascendant_index,
            "total_sum": total_sum,
            "ascendant_sign": ascendant_sign
        }
    }

def parse_end_datetime(end_str, reference_date, tz):
    """
    Parses a string like '27-10-2025, 13:25' into a timezone-aware datetime.
    If parsing fails, returns None.
    """
    if end_str is None or end_str == "—":
        return None
    try:
        dt = datetime.strptime(end_str, "%d-%m-%Y, %H:%M")
    except ValueError:
        # fallback: only time given, use reference date
        try:
            t = datetime.strptime(end_str, "%H:%M").time()
            dt = datetime.combine(reference_date.date(), t)
        except ValueError:
            return None
    return tz.localize(dt)

def calculate_sarvarth_sidhi(year, month, user=None):
    lat=28.6139
    lon=77.2090
    timezone_str="Asia/Kolkata"
    city_name="New Delhi"
    tz = pytz.timezone(timezone_str)
    start_date = tz.localize(datetime(year, month, 1))
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1
    end_date = tz.localize(datetime(next_year, next_month, 1))
    results = []


    current_time = start_date

    while current_time < end_date:
        try:
            # Get panchang for current time
            panchang = get_panchang(
                target_date=current_time,
                lat=lat, lon=lon, timezone_str=timezone_str, city_name=city_name
            )

            current_vaar = panchang.get("weekday")
            current_nakshatra = panchang.get("nakshatra")
            nakshatra_end_str = panchang.get("nakshatra_end")
            vaar_end_str = panchang.get("vaar_end")  # added


            # Parse datetimes
            nakshatra_end_dt = tz.localize(datetime.strptime(nakshatra_end_str, "%d-%m-%Y, %H:%M"))
            vaar_end_dt = tz.localize(datetime.strptime(vaar_end_str, "%d-%m-%Y, %H:%M"))

            next_time = min(nakshatra_end_dt, vaar_end_dt)


            # Check if current combination qualifies
            if (current_vaar in SARVARATH_SIDDHIYOG and
                current_nakshatra in SARVARATH_SIDDHIYOG[current_vaar]):

                duration_hours = (next_time - current_time).total_seconds() / 3600

                results.append({
                    "date": current_time.strftime("%Y-%m-%d"),
                    "weekday": current_vaar,
                    "nakshatra": current_nakshatra,
                    "start_time": current_time.strftime("%d %b %Y, %I:%M %p"),
                    "end_time": next_time.strftime("%d %b %Y, %I:%M %p"),
                    "duration_hours": round(duration_hours, 2)
                })


            # Move to next check time + 1 minute to avoid missing transitions
            current_time = next_time + timedelta(minutes=1)

        except Exception as e:
            logger.error(f"Error at {current_time}: {e}")
            current_time += timedelta(days=1)

    # Merge consecutive segments with same vaar+nakshatra
    merged_results = []
    if results:
        merged_results.append(results[0])
        for i in range(1, len(results)):
            last = merged_results[-1]
            current = results[i]

            last_end = datetime.strptime(last['end_time'], "%d %b %Y, %I:%M %p")
            current_start = datetime.strptime(current['start_time'], "%d %b %Y, %I:%M %p")

            time_gap = (current_start - last_end).total_seconds()

            if (last['weekday'] == current['weekday'] and
                last['nakshatra'] == current['nakshatra'] and
                time_gap <= 300):  # 5 minutes gap

                merged_results[-1]['end_time'] = current['end_time']
                merged_results[-1]['duration_hours'] = round(
                    (datetime.strptime(current['end_time'], "%d %b %Y, %I:%M %p") -
                     datetime.strptime(last['start_time'], "%d %b %Y, %I:%M %p")).total_seconds() / 3600, 2
                )
            else:
                merged_results.append(current)

    return pd.DataFrame(merged_results) if merged_results else None

def calculate_amrit_sidhi(year, month, user=None):
    lat = 28.6139
    lon = 77.2090
    timezone_str = "Asia/Kolkata"
    city_name = "New Delhi"
    tz = pytz.timezone(timezone_str)
    start_date = tz.localize(datetime(year, month, 1))
    # next_month = month + 1 if month < 12 else 1
    next_year = year + 1
    end_date = tz.localize(datetime(next_year, month, 1))
    results = []


    current_time = start_date

    while current_time < end_date:
        try:
            # Get panchang for current time
            panchang = get_panchang(
                target_date=current_time,
                lat=lat, lon=lon, timezone_str=timezone_str, city_name=city_name
            )

            current_vaar = panchang.get("weekday")
            current_nakshatra = panchang.get("nakshatra")
            nakshatra_end_str = panchang.get("nakshatra_end")
            vaar_end_str = panchang.get("vaar_end")


            # Parse datetimes
            nakshatra_end_dt = tz.localize(datetime.strptime(nakshatra_end_str, "%d-%m-%Y, %H:%M"))
            vaar_end_dt = tz.localize(datetime.strptime(vaar_end_str, "%d-%m-%Y, %H:%M"))

            next_time = min(nakshatra_end_dt, vaar_end_dt)


            # Check if current combination qualifies for Amrit Siddhi Yoga
            qualifies = False
            if current_vaar in AMRIT_SIDDHI_YOGA:
                # Check if current nakshatra matches any of the allowed nakshatras for this day
                allowed_nakshatras = AMRIT_SIDDHI_YOGA[current_vaar]
                for nakshatra_pattern in allowed_nakshatras:
                    if nakshatra_pattern.lower() in current_nakshatra.lower():
                        qualifies = True
                        break

            if qualifies:
                duration_hours = (next_time - current_time).total_seconds() / 3600

                results.append({
                    "date": current_time.strftime("%Y-%m-%d"),
                    "weekday": current_vaar,
                    "nakshatra": current_nakshatra,
                    "start_time": current_time.strftime("%d %b %Y, %I:%M %p"),
                    "end_time": next_time.strftime("%d %b %Y, %I:%M %p"),
                    "duration_hours": round(duration_hours, 2),
                    "yoga_type": "Amrit Siddhi Yoga"
                })


            # Move to next check time + 1 minute to avoid missing transitions
            current_time = next_time + timedelta(minutes=1)

        except Exception as e:
            logger.error(f"Error at {current_time}: {e}")
            current_time += timedelta(days=1)

    # Merge consecutive segments with same vaar+nakshatra
    merged_results = []
    if results:
        merged_results.append(results[0])
        for i in range(1, len(results)):
            last = merged_results[-1]
            current = results[i]

            last_end = datetime.strptime(last['end_time'], "%d %b %Y, %I:%M %p")
            current_start = datetime.strptime(current['start_time'], "%d %b %Y, %I:%M %p")

            time_gap = (current_start - last_end).total_seconds()

            if (last['weekday'] == current['weekday'] and
                last['nakshatra'] == current['nakshatra'] and
                time_gap <= 300):  # 5 minutes gap

                merged_results[-1]['end_time'] = current['end_time']
                merged_results[-1]['duration_hours'] = round(
                    (datetime.strptime(current['end_time'], "%d %b %Y, %I:%M %p") -
                     datetime.strptime(last['start_time'], "%d %b %Y, %I:%M %p")).total_seconds() / 3600, 2
                )
            else:
                merged_results.append(current)

    return pd.DataFrame(merged_results) if merged_results else None

def calculate_pushkar_yoga(year, month, user=None):
    lat = 28.6139
    lon = 77.2090
    timezone_str = "Asia/Kolkata"
    city_name = "New Delhi"
    tz = pytz.timezone(timezone_str)
    start_date = tz.localize(datetime(year, month, 1))
    next_month = month + 1 if month < 12 else 1
    next_year = year + 1
    end_date = tz.localize(datetime(next_year, month, 1))
    results = []


    current_time = start_date

    while current_time < end_date:
        try:
            # Get panchang for current time
            panchang = get_panchang(
                target_date=current_time,
                lat=lat, lon=lon, timezone_str=timezone_str, city_name=city_name
            )

            current_vaar = panchang.get("weekday")
            current_nakshatra = panchang.get("nakshatra")
            current_tithi = panchang.get("tithi", "")
            nakshatra_end_str = panchang.get("nakshatra_end")
            vaar_end_str = panchang.get("vaar_end")
            tithi_end_str = panchang.get("tithi_end", "")


            # Parse datetimes
            nakshatra_end_dt = tz.localize(datetime.strptime(nakshatra_end_str, "%d-%m-%Y, %H:%M"))
            vaar_end_dt = tz.localize(datetime.strptime(vaar_end_str, "%d-%m-%Y, %H:%M"))
            
            # Parse tithi end if available
            if tithi_end_str:
                tithi_end_dt = tz.localize(datetime.strptime(tithi_end_str, "%d-%m-%Y, %H:%M"))
                next_time = min(nakshatra_end_dt, vaar_end_dt, tithi_end_dt)
            else:
                next_time = min(nakshatra_end_dt, vaar_end_dt)


            # Check for Pushkar Yoga combinations
            yoga_type = None
            
            # Check for Tripushkar Yoga
            tripushkar_match = False
            # Check nakshatra
            nakshatra_match_tri = current_nakshatra in TRIPUSHKAR_YOGA["nakshatra"]
            # Check tithi
            tithi_match_tri = current_tithi in TRIPUSHKAR_YOGA["tithi"]
            # Check day
            day_match_tri = current_vaar in TRIPUSHKAR_YOGA["vaar"]
            
            if nakshatra_match_tri and tithi_match_tri and day_match_tri:
                yoga_type = "Tripushkar Yoga"
            
            # Check for Dwipushkar Yoga (only if Tripushkar not found)
            if not yoga_type:
                # Check nakshatra
                nakshatra_match_dwi = current_nakshatra in DWIPUSHKAR_YOGA["nakshatra"]
                # Check tithi
                tithi_match_dwi = current_tithi in DWIPUSHKAR_YOGA["tithi"]
                # Check day
                day_match_dwi = current_vaar in DWIPUSHKAR_YOGA["vaar"]
                
                if nakshatra_match_dwi and tithi_match_dwi and day_match_dwi:
                    yoga_type = "Dwipushkar Yoga"

            if yoga_type:
                duration_hours = (next_time - current_time).total_seconds() / 3600

                results.append({
                    "date": current_time.strftime("%Y-%m-%d"),
                    "weekday": current_vaar,
                    "nakshatra": current_nakshatra,
                    "tithi": current_tithi,
                    "start_time": current_time.strftime("%d %b %Y, %I:%M %p"),
                    "end_time": next_time.strftime("%d %b %Y, %I:%M %p"),
                    "duration_hours": round(duration_hours, 2),
                    "yoga_type": yoga_type
                })


            # Move to next check time + 1 minute to avoid missing transitions
            current_time = next_time + timedelta(minutes=1)

        except Exception as e:
            logger.error(f"Error at {current_time}: {e}")
            current_time += timedelta(days=1)

    # Merge consecutive segments with same vaar+nakshatra+tithi+yoga_type
    merged_results = []
    if results:
        merged_results.append(results[0])
        for i in range(1, len(results)):
            last = merged_results[-1]
            current = results[i]

            last_end = datetime.strptime(last['end_time'], "%d %b %Y, %I:%M %p")
            current_start = datetime.strptime(current['start_time'], "%d %b %Y, %I:%M %p")

            time_gap = (current_start - last_end).total_seconds()

            if (last['weekday'] == current['weekday'] and
                last['nakshatra'] == current['nakshatra'] and
                last['tithi'] == current['tithi'] and
                last['yoga_type'] == current['yoga_type'] and
                time_gap <= 300):  # 5 minutes gap

                merged_results[-1]['end_time'] = current['end_time']
                merged_results[-1]['duration_hours'] = round(
                    (datetime.strptime(current['end_time'], "%d %b %Y, %I:%M %p") -
                     datetime.strptime(last['start_time'], "%d %b %Y, %I:%M %p")).total_seconds() / 3600, 2
                )
            else:
                merged_results.append(current)

    return pd.DataFrame(merged_results) if merged_results else None

def calculate_all_pushkar_yog(year, month, user=None):
    """Calculate both Dwipushkar and Tripushkar yogas"""
    df = calculate_pushkar_yoga(year, month, user)
    
    if df is not None and not df.empty:
        # Separate Dwipushkar and Tripushkar
        dwipushkar_df = df[df['yoga_type'] == 'Dwipushkar Yoga']
        tripushkar_df = df[df['yoga_type'] == 'Tripushkar Yoga']
        
        
        # Print details
        if not dwipushkar_df.empty:
            for idx, row in dwipushkar_df.iterrows():
                pass
                
        if not tripushkar_df.empty:
            for idx, row in tripushkar_df.iterrows():
                pass
        
        return {
            'all_pushkar': df,
            'dwipushkar': dwipushkar_df,
            'tripushkar': tripushkar_df
        }
    else:
        return None

def calculate_ravi_yoga(year, month, user=None):
    lat = 28.6139
    lon = 77.2090
    timezone_str = "Asia/Kolkata"
    city_name = "New Delhi"
    tz = pytz.timezone(timezone_str)
    start_date = tz.localize(datetime(year, month, 1))
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1
    end_date = tz.localize(datetime(next_year, next_month, 1))
    results = []


    current_time = start_date
    iteration_count = 0
    max_iterations = 1000  # Safety limit to prevent infinite loops

    while current_time < end_date and iteration_count < max_iterations:
        iteration_count += 1
        try:
            # Get panchang for current time
            panchang = get_panchang(
                target_date=current_time,
                lat=lat, lon=lon, timezone_str=timezone_str, city_name=city_name
            )

            # Get nakshatra positions for Sun and Moon
            moon_nakshatra = panchang.get("moon_nakshatra")
            sun_nakshatra = panchang.get("sun_nakshatra")
            
            # If sun_nakshatra is not directly available, calculate from sun longitude
            if not sun_nakshatra and "sun_longitude" in panchang:
                sun_long = panchang.get("sun_longitude")
                sun_nakshatra = panchang.get("sun_nakshatra") 
            
            if not moon_nakshatra or not sun_nakshatra:
                current_time += timedelta(hours=6)  # Move forward more aggressively
                continue


            # Calculate nakshatra difference
            nakshatra_diff = get_nakshatra_difference(sun_nakshatra, moon_nakshatra)
            
            if nakshatra_diff is None:
                current_time += timedelta(hours=6)
                continue


            # Check if difference matches Ravi Yoga criteria
            if nakshatra_diff in RAVI_YOGA:
                # Get end time of current nakshatra (Moon's nakshatra determines duration)
                nakshatra_end_str = panchang.get("nakshatra_end")
                if not nakshatra_end_str:
                    current_time += timedelta(hours=6)
                    continue
                    
                nakshatra_end_dt = tz.localize(datetime.strptime(nakshatra_end_str, "%d-%m-%Y, %H:%M"))
                
                # Safety check: ensure we're moving forward in time
                if nakshatra_end_dt <= current_time:
                    current_time += timedelta(hours=6)
                    continue
                
                duration_hours = (nakshatra_end_dt - current_time).total_seconds() / 3600

                results.append({
                    "date": current_time.strftime("%Y-%m-%d"),
                    "start_time": current_time.strftime("%d %b %Y, %I:%M %p"),
                    "end_time": nakshatra_end_dt.strftime("%d %b %Y, %I:%M %p"),
                    "duration_hours": round(duration_hours, 2),
                    "sun_nakshatra": sun_nakshatra,
                    "moon_nakshatra": moon_nakshatra,
                    "nakshatra_difference": nakshatra_diff,
                    "yoga_type": "Ravi Yoga"
                })


            # Move to next nakshatra change (with safety check)
            nakshatra_end_str = panchang.get("nakshatra_end")
            if nakshatra_end_str:
                nakshatra_end_dt = tz.localize(datetime.strptime(nakshatra_end_str, "%d-%m-%Y, %H:%M"))
                if nakshatra_end_dt > current_time:
                    current_time = nakshatra_end_dt + timedelta(minutes=1)
                else:
                    current_time += timedelta(hours=6)

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            logger.error(f"Error at {current_time}: {e}")
            # Move forward more aggressively on error
            current_time += timedelta(hours=6)

    # Safety check
    if iteration_count >= max_iterations:
        pass
    
    return pd.DataFrame(results) if results else None

def calculate_guru_pushya(year, month, user=None):
    lat = 28.6139
    lon = 77.2090
    timezone_str = "Asia/Kolkata"
    city_name = "New Delhi"
    tz = pytz.timezone(timezone_str)
    start_date = tz.localize(datetime(year, month, 1))
    # next_month = month + 1 if month < 12 else 1
    next_year = year + 1
    end_date = tz.localize(datetime(next_year, month, 1))
    results = []


    current_time = start_date

    while current_time < end_date:
        try:
            # Get panchang for current time
            panchang = get_panchang(
                target_date=current_time,
                lat=lat, lon=lon, timezone_str=timezone_str, city_name=city_name
            )

            current_vaar = panchang.get("weekday")
            current_nakshatra = panchang.get("nakshatra")
            nakshatra_end_str = panchang.get("nakshatra_end")
            vaar_end_str = panchang.get("vaar_end")


            # Parse datetimes
            nakshatra_end_dt = tz.localize(datetime.strptime(nakshatra_end_str, "%d-%m-%Y, %H:%M"))
            vaar_end_dt = tz.localize(datetime.strptime(vaar_end_str, "%d-%m-%Y, %H:%M"))

            next_time = min(nakshatra_end_dt, vaar_end_dt)


            # Check if current combination qualifies for Amrit Siddhi Yoga
            qualifies = False
            if current_vaar in GURU_PUSHYA_YOGA:
                # Check if current nakshatra matches any of the allowed nakshatras for this day
                allowed_nakshatras = GURU_PUSHYA_YOGA[current_vaar]
                for nakshatra_pattern in allowed_nakshatras:
                    if nakshatra_pattern.lower() in current_nakshatra.lower():
                        qualifies = True
                        break

            if qualifies:
                duration_hours = (next_time - current_time).total_seconds() / 3600

                results.append({
                    "date": current_time.strftime("%Y-%m-%d"),
                    "weekday": current_vaar,
                    "nakshatra": current_nakshatra,
                    "start_time": current_time.strftime("%d %b %Y, %I:%M %p"),
                    "end_time": next_time.strftime("%d %b %Y, %I:%M %p"),
                    "duration_hours": round(duration_hours, 2),
                    "yoga_type": "Guru Pushya Yoga"
                })


            # Move to next check time + 1 minute to avoid missing transitions
            current_time = next_time + timedelta(minutes=1)

        except Exception as e:
            logger.error(f"Error at {current_time}: {e}")
            current_time += timedelta(days=1)

    # Merge consecutive segments with same vaar+nakshatra
    merged_results = []
    if results:
        merged_results.append(results[0])
        for i in range(1, len(results)):
            last = merged_results[-1]
            current = results[i]

            last_end = datetime.strptime(last['end_time'], "%d %b %Y, %I:%M %p")
            current_start = datetime.strptime(current['start_time'], "%d %b %Y, %I:%M %p")

            time_gap = (current_start - last_end).total_seconds()

            if (last['weekday'] == current['weekday'] and
                last['nakshatra'] == current['nakshatra'] and
                time_gap <= 300):  # 5 minutes gap

                merged_results[-1]['end_time'] = current['end_time']
                merged_results[-1]['duration_hours'] = round(
                    (datetime.strptime(current['end_time'], "%d %b %Y, %I:%M %p") -
                     datetime.strptime(last['start_time'], "%d %b %Y, %I:%M %p")).total_seconds() / 3600, 2
                )
            else:
                merged_results.append(current)

    return pd.DataFrame(merged_results) if merged_results else None

def calculate_ravi_pushya(year, month, user=None):
    lat = 28.6139
    lon = 77.2090
    timezone_str = "Asia/Kolkata"
    city_name = "New Delhi"
    tz = pytz.timezone(timezone_str)
    start_date = tz.localize(datetime(year, month, 1))
    # next_month = month + 1 if month < 12 else 1
    next_year = year + 1
    end_date = tz.localize(datetime(next_year, month, 1))
    results = []


    current_time = start_date

    while current_time < end_date:
        try:
            # Get panchang for current time
            panchang = get_panchang(
                target_date=current_time,
                lat=lat, lon=lon, timezone_str=timezone_str, city_name=city_name
            )

            current_vaar = panchang.get("weekday")
            current_nakshatra = panchang.get("nakshatra")
            nakshatra_end_str = panchang.get("nakshatra_end")
            vaar_end_str = panchang.get("vaar_end")


            # Parse datetimes
            nakshatra_end_dt = tz.localize(datetime.strptime(nakshatra_end_str, "%d-%m-%Y, %H:%M"))
            vaar_end_dt = tz.localize(datetime.strptime(vaar_end_str, "%d-%m-%Y, %H:%M"))

            next_time = min(nakshatra_end_dt, vaar_end_dt)


            # Check if current combination qualifies for Amrit Siddhi Yoga
            qualifies = False
            if current_vaar in RAVI_PUSHYA_YOGA:
                # Check if current nakshatra matches any of the allowed nakshatras for this day
                allowed_nakshatras = RAVI_PUSHYA_YOGA[current_vaar]
                for nakshatra_pattern in allowed_nakshatras:
                    if nakshatra_pattern.lower() in current_nakshatra.lower():
                        qualifies = True
                        break

            if qualifies:
                duration_hours = (next_time - current_time).total_seconds() / 3600

                results.append({
                    "date": current_time.strftime("%Y-%m-%d"),
                    "weekday": current_vaar,
                    "nakshatra": current_nakshatra,
                    "start_time": current_time.strftime("%d %b %Y, %I:%M %p"),
                    "end_time": next_time.strftime("%d %b %Y, %I:%M %p"),
                    "duration_hours": round(duration_hours, 2),
                    "yoga_type": "Guru Pushya Yoga"
                })


            # Move to next check time + 1 minute to avoid missing transitions
            current_time = next_time + timedelta(minutes=1)

        except Exception as e:
            logger.error(f"Error at {current_time}: {e}")
            current_time += timedelta(days=1)

    # Merge consecutive segments with same vaar+nakshatra
    merged_results = []
    if results:
        merged_results.append(results[0])
        for i in range(1, len(results)):
            last = merged_results[-1]
            current = results[i]

            last_end = datetime.strptime(last['end_time'], "%d %b %Y, %I:%M %p")
            current_start = datetime.strptime(current['start_time'], "%d %b %Y, %I:%M %p")

            time_gap = (current_start - last_end).total_seconds()

            if (last['weekday'] == current['weekday'] and
                last['nakshatra'] == current['nakshatra'] and
                time_gap <= 300):  # 5 minutes gap

                merged_results[-1]['end_time'] = current['end_time']
                merged_results[-1]['duration_hours'] = round(
                    (datetime.strptime(current['end_time'], "%d %b %Y, %I:%M %p") -
                     datetime.strptime(last['start_time'], "%d %b %Y, %I:%M %p")).total_seconds() / 3600, 2
                )
            else:
                merged_results.append(current)

    return pd.DataFrame(merged_results) if merged_results else None

def get_nakshatra_difference(sun_nakshatra, moon_nakshatra):
    """
    Calculate the difference in nakshatra positions between Sun and Moon.
    Returns the difference as an integer (1-27) or None if not found.
    """
    try:
        sun_index = NAKSHATRA_NAMES.index(sun_nakshatra)
        moon_index = NAKSHATRA_NAMES.index(moon_nakshatra)
        diff = (moon_index - sun_index) % 27 + 1
        return diff if diff != 0 else 27  # Return 27 instead of 0
    except ValueError:
        return None
    
def get_upcoming_auspicious_yogas(year, month, user=None):
    """Calculate and return all auspicious yogas for the given month."""
    sarvarth_df = calculate_sarvarth_sidhi(year, month, user)
    amrit_df = calculate_amrit_sidhi(year, month, user)
    pushkar_dict = calculate_all_pushkar_yog(year, month, user)
    ravi_df = calculate_ravi_yoga(year, month, user)

    return {
        "sarvarth_sidhi": sarvarth_df,
        "amrit_sidhi": amrit_df,
        "pushkar_yogas": pushkar_dict,
        "ravi_yoga": ravi_df
    }

# yoga_calculator.py
def calculate_yogas_for_month(year, month):
    """
    Calculate ALL yoga types in a single pass through the timeline
    """
    from datetime import datetime, timedelta
    import pytz
    
    all_yogas = []
    tz = pytz.timezone("Asia/Kolkata")
    
    # Start from beginning of month
    current_time = tz.localize(datetime(year, month, 1))
    end_time = tz.localize(datetime(year, month + 1, 1)) if month < 12 else tz.localize(datetime(year + 1, 1, 1))
    
    
    iteration_count = 0
    max_iterations = 10000  # Safety limit
    
    while current_time < end_time and iteration_count < max_iterations:
        iteration_count += 1
        
        try:
            # Get panchang data ONCE for current time
            panchang = get_panchang(
                target_date=current_time,
                lat=28.6139,
                lon=77.2090, 
                timezone_str="Asia/Kolkata",
                city_name="New Delhi"
            )
            
            if not panchang:
                current_time += timedelta(hours=1)  # Move forward if failed
                continue
            
            # Extract all relevant data ONCE
            current_vaar = panchang.get("weekday")
            current_nakshatra = panchang.get("nakshatra")
            current_tithi = panchang.get("tithi")
            sun_nakshatra = panchang.get("sun_nakshatra")
            moon_nakshatra = panchang.get("moon_nakshatra")
            
            # Get end times
            nakshatra_end_str = panchang.get("nakshatra_end")
            vaar_end_str = panchang.get("vaar_end")
            tithi_end_str = panchang.get("tithi_end")
            
            # Parse end times
            nakshatra_end_dt = parse_end_datetime(nakshatra_end_str, current_time, tz) if nakshatra_end_str else end_time
            vaar_end_dt = parse_end_datetime(vaar_end_str, current_time, tz) if vaar_end_str else end_time
            tithi_end_dt = parse_end_datetime(tithi_end_str, current_time, tz) if tithi_end_str else end_time
            
            # Find next transition point (when any element changes)
            next_time = min(nakshatra_end_dt, vaar_end_dt, tithi_end_dt, end_time)
            
            # Check ALL yoga types for current combination
            yoga_periods = check_all_yogas(
                current_vaar, current_nakshatra, current_tithi, 
                sun_nakshatra, moon_nakshatra, current_time, next_time
            )
            
            all_yogas.extend(yoga_periods)
            
            # Move to next period
            current_time = next_time + timedelta(minutes=1)
            
        except Exception as e:
            logger.error(f"Error at {current_time}: {e}")
            current_time += timedelta(hours=6)  # Move forward on error
    
    return all_yogas

def check_all_yogas(vaar, nakshatra, tithi, sun_nakshatra, moon_nakshatra, start_time, end_time):
    """
    Check ALL yoga types for a given time period
    Returns list of yoga periods found
    """
    yoga_periods = []
    duration_hours = (end_time - start_time).total_seconds() / 3600
    
    # 1. Check Sarvarth Siddhi Yoga
    if (vaar in SARVARATH_SIDDHIYOG and 
        nakshatra in SARVARATH_SIDDHIYOG[vaar]):
        
        yoga_periods.append({
            'yoga_type': 'SARVARTH_SIDDHI',
            'start_time': start_time,
            'end_time': end_time,
            'duration_hours': duration_hours,
            'weekday': vaar,
            'nakshatra': nakshatra,
            'tithi': tithi,
            'combination_rules': {
                'required_weekday': vaar,
                'required_nakshatra': nakshatra,
                'required_tithi': tithi,
                'rule_source': 'SARVARTH_SIDDHIYOG'
            },
            'combination_description': f"Sarvarth Siddhi: {vaar} + {nakshatra} + {tithi}",
        })
    
    # 2. Check Amrit Siddhi Yoga
    if vaar in AMRIT_SIDDHI_YOGA:
        for nakshatra_pattern in AMRIT_SIDDHI_YOGA[vaar]:
            if nakshatra_pattern.lower() in nakshatra.lower():
                yoga_periods.append({
                    'yoga_type': 'AMRIT_SIDDHI',
                    'start_time': start_time,
                    'end_time': end_time,
                    'duration_hours': duration_hours,
                    'weekday': vaar,
                    'nakshatra': nakshatra,
                    'combination_rules': {
                        'required_weekday': vaar,
                        'required_nakshatra': nakshatra,
                        'rule_source': 'AMRIT_SIDDHI_YOGA'
                    },
                    'combination_description': f"Amrit Siddhi: {vaar} + {nakshatra}",
                })
                break
    
    # 3. Check Pushkar Yogas
    # Tripushkar
    if (nakshatra in TRIPUSHKAR_YOGA["nakshatra"] and
        tithi in TRIPUSHKAR_YOGA["tithi"] and
        vaar in TRIPUSHKAR_YOGA["vaar"]):
        
        yoga_periods.append({
            'yoga_type': 'TRIPUSHKAR',
            'start_time': start_time,
            'end_time': end_time,
            'duration_hours': duration_hours,
            'weekday': vaar,
            'nakshatra': nakshatra,
            'tithi': tithi,
            'combination_rules': {
                'required_weekday': vaar,
                'required_nakshatra': nakshatra,
                'required_tithi': tithi,
                'rule_source': 'TRIPUSHKAR_YOGA'
            },
            'combination_description': f"Tripushkar: {vaar} + {nakshatra} + {tithi}",
        })
    
    # Dwipushkar (only if not Tripushkar)
    elif (nakshatra in DWIPUSHKAR_YOGA["nakshatra"] and
          tithi in DWIPUSHKAR_YOGA["tithi"] and
          vaar in DWIPUSHKAR_YOGA["vaar"]):
        
        yoga_periods.append({
            'yoga_type': 'DWIPUSHKAR',
            'start_time': start_time,
            'end_time': end_time,
            'duration_hours': duration_hours,
            'weekday': vaar,
            'nakshatra': nakshatra,
            'tithi': tithi,
            'combination_rules': {
                'required_weekday': vaar,
                'required_nakshatra': nakshatra,
                'required_tithi': tithi,
                'rule_source': 'DWIPUSHKAR_YOGA'
            },
            'combination_description': f"Dwipushkar: {vaar} + {nakshatra} + {tithi}",
        })
    
    # 4. Check Ravi Yoga
    nakshatra_diff = get_nakshatra_difference(sun_nakshatra, moon_nakshatra)
    if nakshatra_diff and nakshatra_diff in RAVI_YOGA:
        yoga_periods.append({
            'yoga_type': 'RAVI',
            'start_time': start_time,
            'end_time': end_time,
            'duration_hours': duration_hours,
            'sun_nakshatra': sun_nakshatra,
            'moon_nakshatra': moon_nakshatra,
            'nakshatra_difference': nakshatra_diff,
            'combination_rules': {
                'required_difference': nakshatra_diff,
                'sun_nakshatra': sun_nakshatra,
                'moon_nakshatra': moon_nakshatra,
                'rule_source': 'RAVI_YOGA'
            },
            'combination_description': f"Ravi Yoga: Sun({sun_nakshatra}) + Moon({moon_nakshatra}) = Difference {nakshatra_diff}",
        })
    
    return yoga_periods

def parse_end_datetime(end_str, reference_date, tz):
    """
    Parse end datetime string
    """
    if end_str is None or end_str == "—":
        return reference_date + timedelta(days=30)  # Far future
    
    try:
        # Try full datetime format
        dt = datetime.strptime(end_str, "%d-%m-%Y, %H:%M")
        return tz.localize(dt)
    except ValueError:
        try:
            # Try time-only format
            t = datetime.strptime(end_str, "%H:%M").time()
            dt = datetime.combine(reference_date.date(), t)
            return tz.localize(dt)
        except ValueError:
            return reference_date + timedelta(days=30)  # Fallback

def get_panchang_data_for_time(datetime_str):
    """
    Helper function to get panchang data for a specific datetime
    """
    try:
        dt = datetime.strptime(datetime_str, "%d %b %Y, %I:%M %p")
        panchang = get_panchang(
            target_date=dt,
            lat=28.6139,  # Default coordinates
            lon=77.2090,
            timezone_str="Asia/Kolkata",
            city_name="New Delhi"
        )
        return panchang
    except Exception as e:
        logger.error(f"Error getting panchang data for {datetime_str}: {e}")
        return None
    
# Add these query functions to astro_calculations.py

def save_yogas_to_db(yogas_list):
    """
    Save list of yoga data to database
    """
    from core.models import AuspiciousYoga
    
    saved_count = 0
    for yoga_data in yogas_list:
        try:
            # Check if this yoga already exists (avoid duplicates)
            exists = AuspiciousYoga.objects.filter(
                yoga_type=yoga_data['yoga_type'],
                start_time=yoga_data['start_time'],
                end_time=yoga_data['end_time']
            ).exists()
            
            if not exists:
                AuspiciousYoga.objects.create(**yoga_data)
                saved_count += 1
        except Exception as e:
            logger.error(f"Error saving yoga: {e}")
            import traceback
            traceback.print_exc()
    
    return saved_count

def calculate_all_yogas_for_period(start_year, end_year):
    """
    Calculate all auspicious yogas for a given period and store in database
    Loops through years and months, calling calculate_yogas_for_month for each
    """
    from core.models import AuspiciousYoga
    
    
    total_yogas = 0
    
    for year in range(start_year, end_year + 1):
        for month in range(1, 13):
            
            try:
                # Calculate all yoga types for this month
                yogas = calculate_yogas_for_month(year, month)
                
                # Save to database
                saved_count = save_yogas_to_db(yogas)
                total_yogas += saved_count
                
                
            except Exception as e:
                logger.error(f"Error processing {year}-{month:02d}: {e}")
                import traceback
                traceback.print_exc()
                continue
    
    return total_yogas

def get_upcoming_yogas(days=30, yoga_types=None):
    """
    Get upcoming yogas in the next N days
    """
    start_date = timezone.now()
    end_date = start_date + timedelta(days=days)
    
    queryset = AuspiciousYoga.objects.filter(
        start_time__gte=start_date,
        end_time__lte=end_date
    )
    
    if yoga_types:
        queryset = queryset.filter(yoga_type__in=yoga_types)
    return queryset.order_by('start_time')

def search_yogas(date=None, yoga_type=None, nakshatra=None, weekday=None):
    """
    Advanced search for yogas
    """
    from core.models import AuspiciousYoga
    from django.db.models import Q
    
    queryset = AuspiciousYoga.objects.all()
    
    if date:
        queryset = queryset.filter(start_time__date=date)
    if yoga_type:
        queryset = queryset.filter(yoga_type=yoga_type)
    if nakshatra:
        queryset = queryset.filter(
            Q(nakshatra__icontains=nakshatra) | 
            Q(moon_nakshatra__icontains=nakshatra) |
            Q(sun_nakshatra__icontains=nakshatra)
        )
    if weekday:
        queryset = queryset.filter(weekday__icontains=weekday)
    
    return queryset.order_by('start_time')

def get_yogas_by_combination(weekday=None, nakshatra=None, tithi=None, yoga_type=None):
    """
    Find yogas by specific combinations
    """
    from core.models import AuspiciousYoga
    
    queryset = AuspiciousYoga.objects.all()
    
    filters = {}
    if weekday:
        filters['weekday'] = weekday
    if nakshatra:
        filters['nakshatra'] = nakshatra
    if tithi:
        filters['tithi__icontains'] = tithi
    if yoga_type:
        filters['yoga_type'] = yoga_type
    
    return queryset.filter(**filters).order_by('start_time')

def get_sarvarth_siddhi_with_tithi(tithi=None):
    """
    Get Sarvarth Siddhi yogas with optional tithi filter
    """
    from core.models import AuspiciousYoga
    
    queryset = AuspiciousYoga.objects.filter(yoga_type='SARVARTH_SIDDHI')
    if tithi:
        queryset = queryset.filter(tithi__icontains=tithi)
    return queryset.order_by('start_time')

def get_yoga_combinations_stats():
    """
    Get statistics about yoga combinations
    """
    from core.models import AuspiciousYoga
    from django.db.models import Count
    
    stats = {}
    
    # Sarvarth Siddhi combinations
    stats['SARVARTH_SIDDHI'] = list(
        AuspiciousYoga.objects
        .filter(yoga_type='SARVARTH_SIDDHI')
        .values('weekday', 'nakshatra', 'tithi')
        .annotate(count=Count('id'))
        .order_by('-count')[:10]
    )
    
    # Amrit Siddhi combinations
    stats['AMRIT_SIDDHI'] = list(
        AuspiciousYoga.objects
        .filter(yoga_type='AMRIT_SIDDHI')
        .values('weekday', 'nakshatra')
        .annotate(count=Count('id'))
        .order_by('-count')[:10]
    )
    
    # Pushkar yoga combinations
    for pushkar_type in ['DWIPUSHKAR', 'TRIPUSHKAR']:
        stats[pushkar_type] = list(
            AuspiciousYoga.objects
            .filter(yoga_type=pushkar_type)
            .values('weekday', 'nakshatra', 'tithi')
            .annotate(count=Count('id'))
            .order_by('-count')[:10]
        )
    
    # Ravi Yoga combinations
    stats['RAVI'] = list(
        AuspiciousYoga.objects
        .filter(yoga_type='RAVI')
        .values('nakshatra_difference')
        .annotate(count=Count('id'))
        .order_by('-count')[:10]
    )
    
    return stats

def get_yoga_essential_data(target_date, user=None, lat=None, lon=None, timezone_str=None, city_name=None):
    """
    Lightweight function to get only essential data for yoga calculations
    Returns: weekday, nakshatra, tithi, sun/moon positions with end times
    """
    if user and hasattr(user, 'profile'):
        user_profile = user.profile
        lat = user_profile.latitude
        lon = user_profile.longitude
        timezone_str = user_profile.timezone
        city_name = user_profile.city
    else:
        lat = lat or 28.6139
        lon = lon or 77.2090
        timezone_str = timezone_str or 'Asia/Kolkata'
        city_name = city_name or 'New Delhi'
    
    tz = pytz.timezone(timezone_str)
    
    # Ensure timezone awareness
    if target_date.tzinfo is None:
        target_date = tz.localize(target_date)
    else:
        target_date = target_date.astimezone(tz)
    
    tz_offset = target_date.utcoffset().total_seconds() / 3600
    
    # Set up Swiss Ephemeris
    swe.set_topo(lat, lon, 0)
    swe.set_sid_mode(swe.SIDM_TRUE_CITRA)
    
    # Convert to UTC for calculations
    target_time_utc = target_date.astimezone(pytz.utc)
    year = target_time_utc.year
    month = target_time_utc.month
    day = target_time_utc.day
    hour = target_time_utc.hour + target_time_utc.minute/60 + target_time_utc.second/3600
    
    jd_current = get_julian(year, month, day, hour)
    ayanamsa = swe.get_ayanamsa_ut(jd_current)
    
    # Get Sun and Moon positions (essential for yogas)
    sun_pos, _ = swe.calc_ut(jd_current, swe.SUN)
    moon_pos, _ = swe.calc_ut(jd_current, swe.MOON)
    
    sun_lon = (sun_pos[0] - ayanamsa) % 360
    moon_lon = (moon_pos[0] - ayanamsa) % 360
    
    # Calculate nakshatras
    sun_nakshatra_num = math.floor(sun_lon / (360/27))
    moon_nakshatra_num = math.floor(moon_lon / (360/27))
    sun_nakshatra = NAKSHATRA_NAMES[sun_nakshatra_num]
    moon_nakshatra = NAKSHATRA_NAMES[moon_nakshatra_num]
    
    # Calculate tithi
    tithi_angle = (moon_lon - sun_lon) % 360
    tithi_num_raw = int(tithi_angle // 12) + 1
    
    if tithi_num_raw <= 15:
        paksha = "Shukla Paksha"
        tithi_num = tithi_num_raw
    else:
        paksha = "Krishna Paksha"
        tithi_num = tithi_num_raw - 15
    
    tithi_name = TITHI_NAMES[tithi_num - 1]
    if tithi_num == 15:
        if paksha == "Shukla Paksha":
            tithi_name = "Purnima"
        else:
            tithi_name = "Amavasya"
    
    # Calculate end times
    tithi_end_jd = find_tithi_end_time(jd_current, tithi_angle / 12)
    tithi_end_time = jd_to_datetime_correct(tithi_end_jd, tz_offset)
    
    nakshatra_end_jd = find_transition(jd_current, key="nakshatra")
    nakshatra_end_time = jd_to_datetime_correct(nakshatra_end_jd, tz_offset) if nakshatra_end_jd else None
    
    # Get weekday and vaar end
    s = sun(city_name.observer, date=target_date.date(), tzinfo=tz)
    s_1 = sun(city_name.observer, date=(target_date + timedelta(days=1)).date(), tzinfo=tz)
    vaar, vaar_end = get_vaar(s['sunrise'], s_1['sunrise'], target_date, tz)
    
    return {
        'weekday': vaar,
        'vaar_end': vaar_end,
        'nakshatra': moon_nakshatra,  # Moon's nakshatra is used for most yogas
        'nakshatra_end': nakshatra_end_time,
        'tithi': tithi_name,
        'tithi_end': tithi_end_time,
        'sun_nakshatra': sun_nakshatra,
        'moon_nakshatra': moon_nakshatra,
        'sun_longitude': sun_lon,
        'moon_longitude': moon_lon,
        'paksha': paksha,
        'sunrise': s['sunrise'],
        'sunset': s['sunset']
    }


def calculate_all_yogas_efficient(year, month, user=None, lat=None, lon=None, timezone_str=None, city_name=None):
    """
    Efficient unified yoga calculation using lightweight essential data
    """
    # Setup timezone and dates
    tz = pytz.timezone(timezone_str or 'Asia/Kolkata')
    start_date = tz.localize(datetime(year, month, 1))
    next_year = year if month < 12 else year + 1
    next_month = month + 1 if month < 12 else 1
    end_date = tz.localize(datetime(next_year, next_month, 1))
    
    all_results = {
        'sarvarth_siddhi': [],
        'amrit_siddhi': [],
        'pushkar': [],
        'ravi': [],
        'guru_pushya': [],
        'ravi_pushya': []
    }
    
    
    current_time = start_date
    iteration_count = 0

    while current_time < end_date and iteration_count < 5000:
        iteration_count += 1
        
        try:
            # Get lightweight essential data
            yoga_data = get_yoga_essential_data(
                current_time, user, lat, lon, timezone_str, city_name
            )
            
            if not yoga_data:
                current_time += timedelta(hours=1)
                continue

            # Determine next check time (minimum of all end times)
            end_times = []
            if yoga_data.get('nakshatra_end'):
                end_times.append(yoga_data['nakshatra_end'])
            if yoga_data.get('tithi_end'):
                end_times.append(yoga_data['tithi_end'])
            if yoga_data.get('vaar_end'):
                end_times.append(yoga_data['vaar_end'])
            
            if not end_times:
                current_time += timedelta(hours=1)
                continue
                
            next_time = min(end_times)
            
            if next_time <= current_time:
                current_time += timedelta(hours=1)
                continue

            duration_hours = (next_time - current_time).total_seconds() / 3600
            
            # Check all yoga combinations
            check_all_yogas_efficient(
                all_results=all_results,
                current_time=current_time,
                next_time=next_time,
                duration_hours=duration_hours,
                yoga_data=yoga_data
            )

            current_time = next_time + timedelta(minutes=1)

        except Exception as e:
            logger.error(f"Error at {current_time}: {e}")
            current_time += timedelta(hours=1)

    # Process results
    final_results = process_yoga_results_efficient(all_results)
    print_efficient_summary(final_results, iteration_count)
    
    return final_results


def check_all_yogas_efficient(all_results, current_time, next_time, duration_hours, yoga_data):
    """
    Check all yoga combinations using efficient data
    """
    base_data = {
        "date": current_time.strftime("%Y-%m-%d"),
        "start_time": current_time.strftime("%d %b %Y, %I:%M %p"),
        "end_time": next_time.strftime("%d %b %Y, %I:%M %p"),
        "duration_hours": round(duration_hours, 2),
        "weekday": yoga_data.get('weekday', ''),
        "nakshatra": yoga_data.get('nakshatra', ''),
        "tithi": yoga_data.get('tithi', '')
    }
    
    vaar = yoga_data.get('weekday', '')
    nakshatra = yoga_data.get('nakshatra', '')
    tithi = yoga_data.get('tithi', '')
    sun_nakshatra = yoga_data.get('sun_nakshatra', '')
    moon_nakshatra = yoga_data.get('moon_nakshatra', '')
    
    # 1. Sarvarth Siddhi Yoga
    if (vaar in SARVARATH_SIDDHIYOG and 
        nakshatra in SARVARATH_SIDDHIYOG[vaar]):
        all_results['sarvarth_siddhi'].append({
            **base_data,
            "yoga_type": "Sarvarth Siddhi Yoga"
        })
    
    # 2. Amrit Siddhi Yoga
    if vaar in AMRIT_SIDDHI_YOGA:
        for nakshatra_pattern in AMRIT_SIDDHI_YOGA[vaar]:
            if nakshatra_pattern.lower() in nakshatra.lower():
                all_results['amrit_siddhi'].append({
                    **base_data,
                    "yoga_type": "Amrit Siddhi Yoga"
                })
                break
    
    # 3. Tripushkar Yogas
    yoga_type = None
    # Check for Tripushkar Yoga
    tripushkar_match = False
    # Check nakshatra
    nakshatra_match_tri = nakshatra in TRIPUSHKAR_YOGA["nakshatra"]
    # Check tithi
    tithi_match_tri = tithi in TRIPUSHKAR_YOGA["tithi"]
    # Check day
    day_match_tri = vaar in TRIPUSHKAR_YOGA["vaar"]
    
    if nakshatra_match_tri and tithi_match_tri and day_match_tri:
        yoga_type = "Tripushkar Yoga"
    
    # Check for Dwipushkar Yoga (only if Tripushkar not found)
    if not yoga_type:
        # Check nakshatra
        nakshatra_match_dwi = nakshatra in DWIPUSHKAR_YOGA["nakshatra"]
        # Check tithi
        tithi_match_dwi = tithi in DWIPUSHKAR_YOGA["tithi"]
        # Check day
        day_match_dwi = vaar in DWIPUSHKAR_YOGA["vaar"]
        
        if nakshatra_match_dwi and tithi_match_dwi and day_match_dwi:
            yoga_type = "Dwipushkar Yoga"


    if yoga_type:
        all_results['pushkar'].append({
            **base_data,
            "yoga_type": yoga_type
        })
    
    # 4. Ravi Yoga
    if sun_nakshatra and moon_nakshatra:
        nakshatra_diff = get_nakshatra_difference(sun_nakshatra, moon_nakshatra)
        if nakshatra_diff is not None and nakshatra_diff in RAVI_YOGA:
            all_results['ravi'].append({
                **base_data,
                "sun_nakshatra": sun_nakshatra,
                "moon_nakshatra": moon_nakshatra,
                "nakshatra_difference": nakshatra_diff,
                "yoga_type": "Ravi Yoga"
            })
    
    # 5. Guru Pushya Yoga
    if vaar in GURU_PUSHYA_YOGA:
        for nakshatra_pattern in GURU_PUSHYA_YOGA[vaar]:
            if nakshatra_pattern.lower() in nakshatra.lower():
                all_results['guru_pushya'].append({
                    **base_data,
                    "yoga_type": "Guru Pushya Yoga"
                })
                break
    
    # 6. Ravi Pushya Yoga
    if vaar in RAVI_PUSHYA_YOGA:
        for nakshatra_pattern in RAVI_PUSHYA_YOGA[vaar]:
            if nakshatra_pattern.lower() in nakshatra.lower():
                all_results['ravi_pushya'].append({
                    **base_data,
                    "yoga_type": "Ravi Pushya Yoga"
                })
                break


def process_yoga_results_efficient(all_results):
    """
    Process and merge results for each yoga type
    """
    final_results = {}
    
    for yoga_type, results in all_results.items():
        if results:
            # Simple deduplication and conversion to DataFrame
            df = pd.DataFrame(results)
            df = df.drop_duplicates()
            final_results[yoga_type] = df
        else:
            final_results[yoga_type] = None
    
    return final_results


def print_efficient_summary(final_results, iteration_count):
    """
    Print summary for efficient calculation
    """
    
    total_yogas = 0
    for yoga_type, df in final_results.items():
        count = len(df) if df is not None else 0
        total_yogas += count
        yoga_name = yoga_type.replace('_', ' ').title()
    
