import swisseph as swe
import math, json
from datetime import datetime, timedelta, timezone
import geojson
from shapely.geometry import Point, Polygon
import os
from .models import Eclipse


EPHE_PATH = r"D:\Fyers API\vedicastro\astroproj\core\data\sweph"
os.environ["SE_EPHE_PATH"] = EPHE_PATH
swe.set_ephe_path(EPHE_PATH)

def compute_solar_eclipse(start_jd=None):
    """Compute solar eclipse using available Swiss Ephemeris functions"""
    if start_jd is None:
        now = datetime.now(timezone.utc)
        start_jd = swe.julday(now.year, now.month, now.day, now.hour + 1, swe.GREG_CAL)
    
    # Try different function names that might be available
    try:
        # First try the most common function name
        retflag, tret = swe.sol_eclipse_when_glob(start_jd, swe.FLG_SWIEPH)
    except AttributeError:
        try:
            # Try alternative function names
            retflag, tret = swe.sol_eclipse_when(start_jd, swe.FLG_SWIEPH)
        except AttributeError:
            try:
                # Try without flags
                retflag, tret = swe.sol_eclipse_when(start_jd)
            except AttributeError as e:
                print(f"No solar eclipse function found: {e}")
                return None
    
    if retflag <= 0:
        return None
    
    # Handle different return formats
    if isinstance(tret, (list, tuple)) and len(tret) > 0:
        jd_max = tret[0]
    else:
        jd_max = tret
    
    # Get eclipse details
    try:
        ret, geopos, attr = swe.sol_eclipse_where(jd_max, swe.FLG_SWIEPH)
    except AttributeError:
        try:
            ret, geopos, attr = swe.sol_eclipse_where(jd_max)
        except AttributeError as e:
            print(f"No solar eclipse where function: {e}")
            return None
    
    if ret < 0:
        return None
    
    # Calculate start and end times
    if isinstance(tret, (list, tuple)) and len(tret) > 4:
        jd_start = tret[1]
        jd_end = tret[4]
    else:
        jd_start = jd_max - 0.1  # Default 2.4 hours before
        jd_end = jd_max + 0.1    # Default 2.4 hours after
    
    return {
        "type": "solar",
        "jd": jd_max,
        "geopos": geopos,
        "subtype": attr[0] if len(attr) > 0 else 0,
        "magnitude": attr[0] if len(attr) > 0 else 0,
        "gamma": attr[1] if len(attr) > 1 else 0,
        "start": jd_to_datetime(jd_start),
        "max": jd_to_datetime(jd_max),
        "end": jd_to_datetime(jd_end),
        "path": generate_solar_eclipse_path(jd_max),
        "sutak": get_sutak_times("solar", jd_max),
    }

def compute_lunar_eclipse(start_jd=None):
    """Compute lunar eclipse with correct return format handling"""
    if start_jd is None:
        now = datetime.now(timezone.utc)
        start_jd = swe.julday(now.year, now.month, now.day, 0.0, swe.GREG_CAL)

    print(f"DEBUG: Searching for lunar eclipse starting from JD: {start_jd}")

    try:
        # Call the lunar eclipse function
        retflag, tret = swe.lun_eclipse_when(start_jd, swe.FLG_SWIEPH)
        print(f"DEBUG: lun_eclipse_when returned - retflag: {retflag}, tret length: {len(tret) if isinstance(tret, tuple) else 'not tuple'}")
        print(f"DEBUG: tret values: {tret}")
        
    except Exception as e:
        print(f"ERROR: Lunar eclipse search failed: {e}")
        return None

    if retflag <= 0:
        print(f"DEBUG: No lunar eclipse found (retflag: {retflag})")
        return None

    # Handle the return format correctly
    # Based on your test, tret is a tuple with 10 elements
    if isinstance(tret, (tuple, list)) and len(tret) >= 1:
        jd_max = tret[0]  # Maximum eclipse time
        
        # Extract start and end times from the tuple
        if len(tret) >= 5:
            # tret[1] = beginning of penumbral eclipse
            # tret[2] = beginning of partial eclipse  
            # tret[3] = beginning of total eclipse
            # tret[4] = end of total eclipse
            # tret[5] = end of partial eclipse
            # tret[6] = end of penumbral eclipse
            
            jd_start = tret[1]  # Start of penumbral phase
            jd_end = tret[6]    # End of penumbral phase
            
            # If it's a partial eclipse, use different indices
            if tret[3] == 0:  # No total phase
                jd_start = tret[2]  # Start of partial phase
                jd_end = tret[5]    # End of partial phase
        else:
            jd_start = jd_max - 0.05
            jd_end = jd_max + 0.05
    else:
        print(f"DEBUG: Unexpected tret format: {tret}")
        return None

    print(f"DEBUG: Lunar eclipse found at JD: {jd_max}")
    print(f"DEBUG: Eclipse phases - Start: {jd_start}, Max: {jd_max}, End: {jd_end}")

    # Get lunar eclipse details
    try:
        ret, attr = swe.lun_eclipse_how(jd_max, swe.FLG_SWIEPH)
        print(f"DEBUG: lun_eclipse_how returned - ret: {ret}, attr: {attr}")
        
        # attr contains: [penumbral magnitude, umbral magnitude, phase]
        if not attr or len(attr) < 2:
            print("DEBUG: Invalid attributes returned, using defaults")
            attr = [0.5, 0.3, 0]  # Default values
            
    except Exception as e:
        print(f"ERROR: Getting lunar eclipse details failed: {e}")
        # Use reasonable defaults
        attr = [0.5, 0.3, 0]
        ret = 1

    # Determine eclipse type based on magnitudes
    umbral_mag = attr[1] if len(attr) > 1 else 0
    penumbral_mag = attr[0] if len(attr) > 0 else 0
    
    eclipse_type = "penumbral"
    if umbral_mag > 0:
        eclipse_type = "partial" if umbral_mag < 1.0 else "total"

    print(f"DEBUG: Eclipse type: {eclipse_type}, Umbral mag: {umbral_mag:.3f}, Penumbral mag: {penumbral_mag:.3f}")

    return {
        "type": "lunar",
        "jd": jd_max,
        "subtype": eclipse_type,
        "start": jd_to_datetime(jd_start),
        "max": jd_to_datetime(jd_max),
        "end": jd_to_datetime(jd_end),
        "magnitude": umbral_mag,  # Main magnitude is umbral magnitude
        "umbral_magnitude": umbral_mag,
        "penumbral_magnitude": penumbral_mag,
        "path": generate_lunar_eclipse_path(jd_max),
        "sutak": get_sutak_times("lunar", jd_max),
    }

def discover_available_functions():
    """Discover what eclipse functions are available in Swiss Ephemeris"""
    available_funcs = []
    eclipse_funcs = [
        'sol_eclipse_when_glob', 'sol_eclipse_when', 'solar_eclipse_when',
        'sol_eclipse_where', 'solar_eclipse_where',
        'lun_eclipse_when', 'lunar_eclipse_when',
        'lun_eclipse_how', 'lunar_eclipse_how'
    ]
    
    for func_name in eclipse_funcs:
        if hasattr(swe, func_name):
            available_funcs.append(func_name)
    
    print("Available eclipse functions:", available_funcs)
    return available_funcs

# Run this to see what functions are available
discover_available_functions()

def is_significant_eclipse(eclipse_data, min_magnitude=0.01):
    """Check if eclipse is significant enough to include"""
    if eclipse_data['type'] == 'solar':
        return eclipse_data.get('magnitude', 0) > min_magnitude
    else:  # lunar
        # For lunar eclipses, be more inclusive
        umbral = eclipse_data.get('umbral_magnitude', 0)
        penumbral = eclipse_data.get('penumbral_magnitude', 0)
        
        # Include all lunar eclipses with any noticeable magnitude
        # Even penumbral eclipses can be significant
        return umbral > 0.1 or penumbral > 0.3  # More lenient thresholds

def generate_solar_eclipse_path(jd_max):
    """Generate simplified solar eclipse path"""
    features = []
    central_points = []
    
    # Calculate path points
    for hours_offset in range(-180, 181, 60):  # Every hour for speed
        jd_point = jd_max + (hours_offset / 60.0) / 24.0
        
        try:
            ret, geopos, attr = swe.sol_eclipse_where(jd_point, swe.FLG_SWIEPH)
            if ret:
                central_points.append([geopos[0], geopos[1]])
        except:
            continue
    
    if central_points:
        features.append({
            "type": "Feature",
            "properties": {"name": "Central Eclipse Line"},
            "geometry": {
                "type": "LineString",
                "coordinates": central_points
            }
        })
    
    return {
        "type": "FeatureCollection",
        "features": features
    }

def generate_lunar_eclipse_path(jd_max):
    """Generate simplified lunar eclipse path"""
    try:
        moon_pos, _ = swe.calc_ut(jd_max, swe.MOON)
        ra, dec = moon_pos[0], moon_pos[1]
        
        gst = swe.sidtime(jd_max)
        lon = (ra - gst*15) % 360
        if lon > 180: lon -= 360
        lat = dec
        
        # Simple visibility circle
        circle_points = []
        for angle in range(0, 360, 90):  # Only 4 points for simplicity
            rad = math.radians(angle)
            circle_lat = lat + 1.0  # Small circle around moon position
            circle_lon = lon + 1.0
            circle_points.append([circle_lon, circle_lat])
        
        circle_points.append(circle_points[0])
        
        return {
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature",
                "properties": {"name": "Lunar Eclipse Visibility"},
                "geometry": {"type": "Polygon", "coordinates": [circle_points]}
            }]
        }
    except Exception as e:
        print(f"Error generating lunar path: {e}")
        return {"type": "FeatureCollection", "features": []}

def get_sutak_times(eclipse_type, jd_max):
    """Calculate Sutak times"""
    sutak_duration = timedelta(hours=12) if eclipse_type == "solar" else timedelta(hours=9)
    sutak_start = jd_max - sutak_duration.total_seconds() / 86400.0
    
    return {
        "sutak_start": jd_to_datetime(sutak_start),
        "sutak_end": jd_to_datetime(jd_max),
    }

def find_all_upcoming_eclipses(num_eclipses=20, save_to_db=False):
    """Find upcoming eclipses with better balancing"""
    today = datetime.now()
    eclipses_found = []
    jd_start = swe.julday(today.year, today.month, today.day, today.hour)
    jd = jd_start
    max_attempts = 300  # Increased for better coverage
    
    attempts = 0
    eclipse_dates_found = set()
    
    print("Starting eclipse search...")
    print(f"Starting JD: {jd_start}, Date: {jd_to_datetime(jd_start)}")
    
    # Track what we're finding
    solar_count = 0
    lunar_count = 0
    
    while len(eclipses_found) < num_eclipses and attempts < max_attempts:
        attempts += 1
        
        if attempts % 50 == 0:
            print(f"Attempt {attempts}, JD: {jd}, Found: {len(eclipses_found)} eclipses")
        
        try:
            # Check for solar eclipse every time
            solar_data = compute_solar_eclipse(jd)
            if (solar_data and solar_data.get('jd') and 
                solar_data['jd'] not in eclipse_dates_found and
                solar_data['jd'] > jd_start):
                
                if is_significant_eclipse(solar_data):
                    eclipses_found.append(solar_data)
                    eclipse_dates_found.add(solar_data['jd'])
                    solar_count += 1
                    date_str = solar_data['max'].strftime('%Y-%m-%d') if solar_data.get('max') else 'Unknown'
                    print(f"✅ SOLAR eclipse #{solar_count}: {date_str}, JD: {solar_data['jd']:.2f}")
        
            # Check for lunar eclipse every time  
            lunar_data = compute_lunar_eclipse(jd)
            if (lunar_data and lunar_data.get('jd') and 
                lunar_data['jd'] not in eclipse_dates_found and
                lunar_data['jd'] > jd_start):
                
                if is_significant_eclipse(lunar_data):
                    eclipses_found.append(lunar_data)
                    eclipse_dates_found.add(lunar_data['jd'])
                    lunar_count += 1
                    date_str = lunar_data['max'].strftime('%Y-%m-%d') if lunar_data.get('max') else 'Unknown'
                    print(f"🌙 LUNAR eclipse #{lunar_count}: {date_str}, JD: {lunar_data['jd']:.2f}")
                    
        except Exception as e:
            print(f"❌ Error searching for eclipses at JD {jd}: {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
        
        # Smaller increment to not miss anything
        jd += 3  # Scan every 3 days instead of 5 or 10
        
        # Remove duplicates periodically
        if attempts % 30 == 0:
            unique_eclipses = []
            seen_jds = set()
            for eclipse in eclipses_found:
                if eclipse['jd'] not in seen_jds:
                    unique_eclipses.append(eclipse)
                    seen_jds.add(eclipse['jd'])
            eclipses_found = unique_eclipses
    
    # Final processing
    eclipses_found.sort(key=lambda x: x['jd'])
    eclipses_found = eclipses_found[:num_eclipses]
    
    print(f"\n=== SEARCH COMPLETE ===")
    print(f"Total attempts: {attempts}")
    print(f"Solar eclipses found: {solar_count}")
    print(f"Lunar eclipses found: {lunar_count}")
    print(f"Total eclipses: {len(eclipses_found)}")
    
    # Print the found eclipses
    for i, eclipse in enumerate(eclipses_found):
        date_str = eclipse['max'].strftime('%Y-%m-%d %H:%M') if eclipse.get('max') else 'Unknown'
        print(f"{i+1}. {eclipse['type'].upper()} - {date_str} - Magnitude: {eclipse.get('magnitude', 0):.3f}")
    
    if save_to_db:
        successful_saves = 0
        for eclipse_info in eclipses_found:
            result = save_eclipse_to_db(eclipse_info)
            if result:
                successful_saves += 1
        
        print(f"✅ Successfully saved {successful_saves}/{len(eclipses_found)} eclipses to database")
    
    return eclipses_found

def save_eclipse_to_db(eclipse_data):
    """Save eclipse data to database with proper timezone handling"""
    try:
        print(f"DEBUG: Eclipse data keys: {list(eclipse_data.keys())}")
        
        # Extract the maximum eclipse date
        if 'max' in eclipse_data:
            date_max = eclipse_data['max']
        else:
            print("ERROR: No 'max' key found in eclipse data")
            return None
        
        # Ensure date_max is timezone-aware
        if date_max and date_max.tzinfo is None:
            from datetime import timezone
            date_max = date_max.replace(tzinfo=timezone.utc)
            print(f"DEBUG: Made date_max timezone-aware: {date_max}")
        
        # Handle start and end dates
        date_start = eclipse_data.get('start', date_max)
        date_end = eclipse_data.get('end', date_max)
        
        if date_start and date_start.tzinfo is None:
            date_start = date_start.replace(tzinfo=timezone.utc)
        if date_end and date_end.tzinfo is None:
            date_end = date_end.replace(tzinfo=timezone.utc)
        
        # Extract central coordinates
        central_lat = None
        central_lon = None
        if 'geopos' in eclipse_data and eclipse_data['geopos']:
            central_lon = eclipse_data['geopos'][0]
            central_lat = eclipse_data['geopos'][1]
        
        # Extract sutak times
        sutak_data = eclipse_data.get('sutak', {})
        sutak_start = sutak_data.get('sutak_start')
        sutak_end = sutak_data.get('sutak_end')
        
        if sutak_start and sutak_start.tzinfo is None:
            sutak_start = sutak_start.replace(tzinfo=timezone.utc)
        if sutak_end and sutak_end.tzinfo is None:
            sutak_end = sutak_end.replace(tzinfo=timezone.utc)
        
        print(f"DEBUG: date_max = {date_max} (type: {type(date_max)})")
        
        # Create the eclipse object
        eclipse = Eclipse(
            eclipse_type=eclipse_data['type'],
            jd_max=eclipse_data['jd'],
            date_max=date_max,
            date_start=date_start,
            date_end=date_end,
            magnitude=eclipse_data.get('magnitude', 0),
            subtype=eclipse_data.get('subtype', 0),
            umbral_magnitude=eclipse_data.get('umbral_magnitude'),
            penumbral_magnitude=eclipse_data.get('penumbral_magnitude'),
            gamma=eclipse_data.get('gamma'),
            central_lat=central_lat,
            central_lon=central_lon,
            path_geojson=eclipse_data.get('path', {}),
            sutak_start=sutak_start,
            sutak_end=sutak_end,
        )
        
        eclipse.save()
        print(f"SUCCESS: Saved {eclipse_data['type']} eclipse with date_max: {date_max}")
        return eclipse
        
    except Exception as e:
        print(f"Error saving eclipse to DB: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return None



def jd_to_datetime(jd):
    """Convert Julian Day to datetime (more robust version)"""
    if jd is None or jd <= 0:
        return None
    
    try:
        # Use the standard Julian Day conversion formula
        unix_timestamp = (jd - 2440587.5) * 86400.0
        
        # Handle timezone - make it UTC
        from datetime import timezone
        return datetime.fromtimestamp(unix_timestamp, tz=timezone.utc)
        
    except (ValueError, OverflowError, OSError) as e:
        print(f"Error converting JD {jd} to datetime: {e}")
        return None

