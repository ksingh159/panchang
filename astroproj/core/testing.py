# from timezonefinder import TimezoneFinder
# from geopy.geocoders import Nominatim

# def test_geocoding(city_name="Jaunpur, Uttar Pradesh"):
#     """Test geocoding for a city name"""
#     print(f"Testing geocoding for: '{city_name}'")
#     print("-" * 50)
    
#     try:
#         # Initialize geocoder
#         geolocator = Nominatim(user_agent="test_geocoding_app")
        
#         # Geocode the location
#         print("Geocoding...")
#         location = geolocator.geocode(city_name)
        
#         if location:
#             print("✅ Success! Found location:")
#             print(f"  Address: {location.address}")
#             print(f"  Latitude: {location.latitude}")
#             print(f"  Longitude: {location.longitude}")
            
#             # Get timezone
#             tf = TimezoneFinder()
#             timezone_name = tf.timezone_at(lat=location.latitude, lng=location.longitude)
#             print(f"  Timezone: {timezone_name}")
            
#             # Additional location details
#             print(f"  Raw data: {location.raw}")
            
#         else:
#             print("❌ No location found!")
            
#     except Exception as e:
#         print(f"❌ Error: {e}")

# # Test the function
# if __name__ == "__main__":
#     test_geocoding("Jaunpur, Uttar Pradesh")
    
#     print("\n" + "="*50)
#     print("Testing with other variations:")
#     print("="*50)
    
#     # Test with variations
#     test_cities = [
#         "Jaunpur",
#         "Jaunpur, UP", 
#         "Jaunpur, India",
#         "Delhi, India",
#         "Mumbai, Maharashtra",
#         "Belarus",
#         "Paris",
#         "New York",
#         "Shanghai",
#         "Sydney", 
#     ]
    
#     for city in test_cities:
#         test_geocoding(city)
#         print()

import swisseph as swe
import math
import pytz
from datetime import datetime
from astral.sun import sun
from astral import LocationInfo


def get_julian(year, month, day, hour, minute):
    return swe.julday(year, month, day, hour + minute/60.0)

def get_julian_datetime(dt):
    return swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute/60.0 + dt.second/3600.0)
# swe.set_sid_mode(swe.SIDM_TRUE_CITRA)


# tz = pytz.timezone('Asia/Kolkata')
# target_datetime = tz.localize(datetime(1993, 4, 23, 7, 35))
# target_time_utc = target_datetime.astimezone(pytz.utc)
# jd_current = get_julian_datetime(target_time_utc)
# print(jd_current)
# lat = 19.0760
# lon = 78.8777


# city_name = 'Mumbai'
# city = LocationInfo(city_name, "India", "Asia/Kolkata", lat, lon)

# sunrise = sun(city.observer, date=target_datetime, tzinfo=tz)
# print(sunrise)

# houses = swe.houses(jd_current, lat, lon, b'P')
# house_cusps = houses[0]  # 12 house cusps
# print(houses)
# ayanamsa = swe.get_ayanamsa(jd_current)
# print(ayanamsa)
# ascendant = (house_cusps[0] - ayanamsa ) % 360
# print(f"ascendant: {ascendant}")


import swisseph as swe
from datetime import datetime
import pytz

lon, lat, alt = 75.8777, 19.0760, 50000  # Mumbai
dt = datetime(1993, 12, 22, 12, 35)
jd = swe.julday(dt.year, dt.month, dt.day, 0.0, swe.GREG_CAL)

geopos = [lon, lat, alt]

# Compute sunrise and sunset
ret_rise, rise_tuple = swe.rise_trans(jd, swe.SUN, swe.CALC_RISE, geopos, 1013.25, 15)
ret_set, set_tuple   = swe.rise_trans(jd, swe.SUN, swe.CALC_SET,  geopos, 1013.25, 15)

# Extract only the Julian Day
jd_rise = rise_tuple[0]
jd_set  = set_tuple[0]

# Convert to Y, M, D, Hour in UTC
sunrise_utc = swe.revjul(jd_rise, swe.GREG_CAL)
sunset_utc  = swe.revjul(jd_set,  swe.GREG_CAL)

def jd_to_datetime(revjul_result):
    y, m, d, h = revjul_result
    hr = int(h)
    mn = int((h - hr) * 60)
    sc = int((((h - hr) * 60) - mn) * 60)
    return datetime(y, m, d, hr, mn, sc)

sunrise_dt = jd_to_datetime(sunrise_utc)
sunset_dt  = jd_to_datetime(sunset_utc)

# Convert to local timezone
tz = pytz.timezone("Asia/Kolkata")
sunrise_local = pytz.utc.localize(sunrise_dt).astimezone(tz)
sunset_local  = pytz.utc.localize(sunset_dt).astimezone(tz)

print("🌅 Sunrise (Local):", sunrise_local)
print("🌇 Sunset  (Local):", sunset_local)








# hrm =  4 + (15/60)

# jd = get_julian(2000,6,7,4,15)  
# print(f"jd in local {jd}")
# tz = pytz.timezone('Asia/Kolkata')
# target_datetime = tz.localize(datetime(2000, 6, 7, 4, 15))
# target_time_utc = target_datetime.astimezone(pytz.utc)
# jd_utc = get_julian_datetime(target_time_utc)
# print(f"jd in UTC {jd_utc}")

# def calculate_ascendant_swiss(jd_ut, lat, lon):
#     """
#     Most accurate method using Swiss Ephemeris houses
#     """
#     try:
#         # Use Placidus house system (most common in Vedic astrology)
#         houses = swe.houses(jd_ut, lat, lon, b'P')  # b'P' = Placidus
        
#         # houses[0] contains house cusps, index 0 is Ascendant (1st house)
#         ascendant = houses[0][0]
#         ascendant_sidereal = (ascendant - ayanamsa) % 360

        
#         return ascendant_sidereal
        
#     except Exception as e:
#         print(f"Swiss Ephemeris house calculation failed: {e}")
# print(calculate_ascendant_swiss(jd, lat=19.0760,lon=72.8777))



# # Calculate positions at midpoint with Lahiri ayanamsa
# swe.set_topo(19.0760, 72.8777, 0)
# swe.set_sid_mode(swe.SIDM_TRUE_CITRA)

# ayanamsa = swe.get_ayanamsa(jd)
# ayanamsa_utc = swe.get_ayanamsa_ut(jd_utc)
# print(ayanamsa, ayanamsa_utc)
# sun_pos, _ = swe.calc(jd, swe.SUN)
# sun_pos_, _ = swe.calc_ut(jd_utc, swe.SUN)
# moon_pos, _ = swe.calc(jd, swe.MOON)
# moon_pos_, _ = swe.calc_ut(jd_utc, swe.MOON)
# saturn_pos,_ = swe.calc(jd, swe.SATURN)
# saturn_pos_, _ = swe.calc_ut(jd_utc, swe.SATURN)
# jupiter_pos,_ = swe.calc(jd, swe.JUPITER)
# jupiter_pos_,_ = swe.calc_ut(jd_utc, swe.JUPITER)
# mercury_pos,_ = swe.calc(jd, swe.MERCURY)
# mercury_pos_,_ = swe.calc_ut(jd_utc, swe.MERCURY)
# mars_pos,_ = swe.calc(jd,swe.MARS)
# mars_pos_,_ = swe.calc_ut(jd_utc,swe.MARS)
# venus_pos,_ = swe.calc(jd, swe.VENUS)
# venus_pos_,_ = swe.calc_ut(jd_utc, swe.VENUS)
# rahu_pos,_ = swe.calc(jd, swe.TRUE_NODE)
# rahu_pos_,_ = swe.calc_ut(jd_utc, swe.TRUE_NODE)
# ketu_pos = rahu_pos[0]
# ketu_pos_ = rahu_pos_[0]
# print(f"Sun:{(sun_pos[0]-ayanamsa) % 360}")
# print(f"Sun with UTC calculation : {(sun_pos_[0]-ayanamsa_utc) % 360}")
# print(f"Moon:{(moon_pos[0]-ayanamsa) % 360}")
# print(f"Moon with UTC: {(moon_pos_[0]-ayanamsa_utc) % 360}")
# print(f"Saturn: {(saturn_pos[0]-ayanamsa) % 360}")
# print(f"Saturn with UTC: {(saturn_pos_[0]-ayanamsa_utc) % 360}")
# print(f"jupiter : {(jupiter_pos[0]-ayanamsa) % 360}")
# print(f"jupiter with UTC : {(jupiter_pos_[0]-ayanamsa_utc) % 360}")
# print(f"mercury : {(mercury_pos[0]-ayanamsa) % 360}")
# print(f"mercury utc : {(mercury_pos_[0]-ayanamsa_utc) % 360}")
# print(f"venus : {(venus_pos[0]-ayanamsa) % 360}")
# print(f"venus utc  : {(venus_pos_[0]-ayanamsa_utc) % 360}")
# print(f"rahu : {(rahu_pos[0]-ayanamsa) % 360}")
# print(f"rahu utc : {(rahu_pos_[0]-ayanamsa_utc) % 360}")
# print(f"ketu : {(ketu_pos)}")
# print(f"ketu utc : {(ketu_pos_)}")
# ayanamsa = swe.get_ayanamsa_ut(jd)
# print(ayanamsa)


