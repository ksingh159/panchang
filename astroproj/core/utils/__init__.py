# core/utils/__init__.py
from .constants import *
from .helpers import *
from .astro_calculations import *


def planet_for_yogas(target_date, user=None, lat=None, lon=None, timezone_str=None, city_name=None):
    if user and hasattr(user, 'profile'):
        user_profile = user.profile  # This is your UserProfile instance
        
        print(f"DEBUG: User profile found: {user_profile}")
        print(f"DEBUG: Profile has birth details: {user_profile.has_birth_details}")
        
        # Use current location from profile
        lat = user_profile.latitude
        lon = user_profile.longitude
        timezone_str = user_profile.timezone
        city_name = user_profile.city
    else:
        # Use provided parameters or defaults for anonymous users
        lat = lat or 28.6139  # Delhi default
        lon = lon or 77.2090
        timezone_str = timezone_str or 'Asia/Kolkata'
        city_name = city_name or 'New Delhi'
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
    target_time_utc = target_date.astimezone(pytz.utc)
    year = target_time_utc.year
    month = target_time_utc.month
    day = target_time_utc.day
    hour = target_time_utc.hour + target_time_utc.minute/60 + target_time_utc.second/3600
    jd_current = get_julian(year, month, day, hour)
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

    nakshatra_end = find_transition(jd_current, key="nakshatra")
    if nakshatra_end:
        nakshatra_end = jd_to_datetime_correct(nakshatra_end, tz_offset)  # uses tz_offset
    s = sun(city_name.observer, date=target_date.date(), tzinfo=tz)
    s_1 = sun(city_name.observer, date=(target_date + timedelta(days=1)).date(), tzinfo=tz)
    sunrise = s["sunrise"]
    sunset = s["sunset"]
    nextsunrise = s_1["sunrise"]
    vaar, vaar_end = get_vaar(s['sunrise'], s_1['sunrise'], target_date, tz)
    weekday = vaar