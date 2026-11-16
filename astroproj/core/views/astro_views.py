# core/views/astro_views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from datetime import date, datetime, timedelta, time as dt_time  # Alias datetime's time
from time import sleep 
import calendar
import traceback
import pytz
import json
from ..utils import prefs
from ..utils.kundali_milan import calculate_ashtakoot, DoshaEvaluator
import swisseph as swe
import math

from ..utils.astro_calculations import (
    get_panchang, calculate_ascendant, get_planetary_positions,get_upcoming_auspicious_yogas, get_upcoming_yogas, search_yogas, 
    get_yogas_by_combination, get_sarvarth_siddhi_with_tithi, get_yoga_combinations_stats,
    get_zodiac_sign, calculate_house,calculate_sarvarth_sidhi,calculate_amrit_sidhi, calculate_all_pushkar_yog, calculate_ravi_yoga,
)
from ..utils.festival_calculations import (
    VARANASI,
    get_carryover_periods,
    get_festivals_between,
    get_festivals_for_day,
    get_festivals_for_year,
    get_pilgrimage_windows_for_year,
)

from ..models import Kundali, DashaPeriod, AuspiciousYoga
from ..utils.geo import resolve_place
from ..utils import muhurat
from ..utils import panchang_engine as pe
from ..utils import namakshar
from ..utils.constants import NAKSHATRA_NAMES
from ..utils import transits as transit_info
from ..kundali_calculator import KundaliCalculator
import logging

from .user_views import rate_limit

logger = logging.getLogger(__name__)


# ---------------------
# Panchang Views
# ---------------------


def _sky(moment, lat, lon, live):
    """Rise/set instants (ms since epoch) and Moon phase for the home page sky arc."""
    def ms(jd):
        return int(pe.jd_to_local(jd, pytz.utc).timestamp() * 1000) if jd else 0

    try:
        jd = pe.dt_to_jd(moment)
        sunrise, sunset = pe.sun_times(moment.date(), lat, lon, moment.tzinfo)
        rise = pe._rise_set_jd(jd - 1.1, swe.MOON, "rise", lat, lon)
        following = pe._rise_set_jd(rise + .1, swe.MOON, "rise", lat, lon)
        if following and following < jd:
            rise = following
        moon_set = pe._rise_set_jd(rise, swe.MOON, "set", lat, lon)
        elongation = pe.angle_and_speed(jd, "tithi")[0]
    except (TypeError, ValueError, swe.Error):      # no rise or set near the poles
        return None
    return {
        "now": int(moment.timestamp() * 1000), "live": live,
        "sunrise": int(sunrise.timestamp() * 1000), "sunset": int(sunset.timestamp() * 1000),
        "moonrise": ms(rise), "moonset": ms(moon_set),
        "illumination": round((1 - math.cos(math.radians(elongation))) / 2, 3), "waxing": elongation < 180,
    }


def home(request):
    """Homepage with panchang data"""
    try:
        # Get user's saved location or use defaults
        if request.user.is_authenticated:
            profile = getattr(request.user, 'profile', None)
            lat = profile.latitude if profile else 19.0760
            lon = profile.longitude if profile else 72.8777
            timezone_str = profile.timezone if profile else 'Asia/Kolkata'
            city_name = profile.city if profile else 'Mumbai'
        else:
            lat = request.session.get('lat', 19.0760)
            lon = request.session.get('lon', 72.8777)
            timezone_str = request.session.get('timezone', 'Asia/Kolkata')
            city_name = request.session.get('city', 'Mumbai')

        # A place picked in the search box overrides the saved location for this view
        # (and becomes the session default for anonymous visitors).
        place_id = request.GET.get('place_id')
        place_text = request.GET.get('city', '').strip()
        if place_id or (place_text and place_text != city_name):
            hit = resolve_place(place_text, geoname_id=place_id)
            if hit:
                lat, lon, timezone_str, city_name = hit['lat'], hit['lon'], hit['timezone'], hit['name']
                if not request.user.is_authenticated:
                    request.session.update({'lat': lat, 'lon': lon, 'timezone': timezone_str, 'city': city_name})

        # Get timezone object
        user_tz = pytz.timezone(timezone_str)
        current_datetime = timezone.now().astimezone(user_tz)
        current_time = current_datetime.time()  # Get just the time part

        def _parse_day(value):
            for fmt in ('%Y-%m-%dT%H:%M', '%Y-%m-%d'):
                try:
                    parsed = datetime.strptime(value.strip(), fmt)
                    return parsed.date(), (parsed.time() if 'T' in value else None)
                except (ValueError, AttributeError):
                    continue
            return None, None

        
        # Check if we're viewing today (no date parameter)
        is_today_view = 'date' not in request.GET and 'prev_day' not in request.GET and 'next_day' not in request.GET
        
        # Handle navigation buttons
        navigation_date = None
        
        if 'prev_day' in request.GET:
            # Get current date from request or use today
            selected_date_str = request.GET.get('date')
            if selected_date_str and selected_date_str.strip():
                try:
                    current_date = _parse_day(selected_date_str)[0] or datetime.strptime(selected_date_str, '%Y-%m-%d').date()
                    navigation_date = current_date - timedelta(days=1)
                except ValueError:
                    navigation_date = timezone.now().astimezone(user_tz).date() - timedelta(days=1)
            else:
                navigation_date = timezone.now().astimezone(user_tz).date() - timedelta(days=1)
                
        elif 'next_day' in request.GET:
            # Get current date from request or use today
            selected_date_str = request.GET.get('date')
            if selected_date_str and selected_date_str.strip():
                try:
                    current_date = _parse_day(selected_date_str)[0] or datetime.strptime(selected_date_str, '%Y-%m-%d').date()
                    navigation_date = current_date + timedelta(days=1)
                except ValueError:
                    navigation_date = timezone.now().astimezone(user_tz).date() + timedelta(days=1)
            else:
                navigation_date = timezone.now().astimezone(user_tz).date() + timedelta(days=1)
        
        picked_date, picked_time = _parse_day(request.GET.get('date', ''))
        if picked_time and not navigation_date:
            current_time = picked_time

        # Determine which date to use
        if navigation_date:
            # Use date from navigation buttons
            selected_date = navigation_date
        else:
            # Use date from URL parameter or today
            selected_date_str = request.GET.get('date')
            if selected_date_str and selected_date_str.strip():
                selected_date = picked_date or timezone.now().astimezone(user_tz).date()
            else:
                selected_date = timezone.now().astimezone(user_tz).date()
        
        # Create datetime object for calculations (use noon as default time)
        # In your home function, change this line:
        selected_datetime = user_tz.localize(
            datetime.combine(selected_date, current_time)  # Use dt_time instead of time
        )
        
        
        # Calculate previous and next day datetimes (for navigation buttons)
        prev_day_datetime_obj = selected_datetime - timedelta(days=1)
        next_day_datetime_obj = selected_datetime + timedelta(days=1)
        
        # Get panchang data
        panchang_data = get_panchang(
            target_date=selected_datetime,
            user=request.user if request.user.is_authenticated else None,
            lat=lat,
            lon=lon,
            timezone_str=timezone_str,
            city_name=city_name
        )
        festivals_today = get_festivals_for_day(selected_date)
        upcoming_festivals = [
            f for f in get_festivals_between(selected_date + timedelta(days=1), selected_date + timedelta(days=120))
            if f["importance"] == "high"
        ][:12]
        
        upcoming_yoga_rows = muhurat.upcoming_yoga_rows(selected_date, 30, lat, lon, timezone_str)

        # Prepare context
        context = {
            'user': request.user,
            'target_datetime': selected_datetime.strftime('%Y-%m-%d %H:%M:%S'),
            'selected_datetime': selected_datetime.strftime('%Y-%m-%dT%H:%M'),
            'prev_day_datetime': prev_day_datetime_obj,
            'next_day_datetime': next_day_datetime_obj,
            'paksha_tithi': panchang_data.get('paksha_tithi', 'N/A'),
            'tithi_end': panchang_data.get('tithi_end', 'N/A'),
            'nakshatra': panchang_data.get('nakshatra', 'N/A'),
            'nakshatra_end': panchang_data.get('nakshatra_end', 'N/A'),
            'yoga': panchang_data.get('yoga', 'N/A'),
            'yoga_end': panchang_data.get('yoga_end', 'N/A'),
            'karana': panchang_data.get('karana', 'N/A'),
            'karana_end': panchang_data.get('karana_end', 'N/A'),
            'sunrise': panchang_data.get('sunrise', 'N/A'),
            'sunset': panchang_data.get('sunset', 'N/A'),
            'moonrise': panchang_data.get('moonrise', 'N/A'),
            'moonset': panchang_data.get('moonset', 'N/A'),
            'moon_phase': panchang_data.get('moon_phase', {'illumination': 0}),
            'weekday': panchang_data.get('weekday', 'N/A'),
            'vaar_end': panchang_data.get('vaar_end', 'N/A'),
            'amanta_month': panchang_data.get('amanta_month', 'N/A'),
            'purnimanta_month': panchang_data.get('purnimanta_month', 'N/A'),
            'ritu_sayana': panchang_data.get('ritu_sayana', ''),
            'month_system': prefs.month_system(request),
            'ritu': panchang_data.get('ritu', 'N/A'),
            'city': city_name,
            'coordinates': f"{lat:.4f}, {lon:.4f}",
            'timezone': timezone_str,
            'planetary_positions': panchang_data.get('planetary_positions', {}),
            'lagna_sign': panchang_data.get('lagna_sign', 'N/A'),
            'lagna_longitude': panchang_data.get('lagna_longitude', 'N/A'),
            'lagna_end': panchang_data.get('lagna_end', 'N/A'),
            'day_ascendants': panchang_data.get('day_ascendants', []),
            'night_ascendants': panchang_data.get('night_ascendants', []),
            'target_datetime': selected_datetime.strftime("%B %d, %Y %I:%M %p"),  # Fixed this line
            "panchak": panchang_data.get('panchak'),
            "disha_shool": panchang_data.get('disha_shool'),
            'brahmamuhuratstart': panchang_data.get('brahma_muhurat_start', 'N/A'),  # Fixed key
            'brahmamuhuratend': panchang_data.get('brahma_muhurat_end', 'N/A'),     # Fixed key
            "abhijeetstart": panchang_data.get('abhijeetstart', 'N/A'),
            "abhijeetend": panchang_data.get('abhijeetend', 'N/A'),
            "rahukaalstart": panchang_data.get('rahukaalstart', 'N/A'),             # This should work now
            "rahukaalend": panchang_data.get('rahukaalend', 'N/A'),                 # This should work now
            "gulikakaalstart": panchang_data.get('gulikakaalstart', 'N/A'),
            "gulikakaalend": panchang_data.get('gulikakaalend', 'N/A'),
            "yamakaalstart": panchang_data.get('yamakaalstart', 'N/A'),
            "yamakaalend": panchang_data.get('yamakaalend', 'N/A'),
            "pradoshstart": panchang_data.get('pradoshstart', 'N/A'),
            "pradoshend": panchang_data.get('pradoshend', 'N/A'),
            "vijaymuhuratstart": panchang_data.get('vijaymuhuratstart','N/A'),
            "vijaymuhuratend": panchang_data.get('vijaymuhuratend','N/A'),
            "varjyam": panchang_data.get('varjyam', 'N/A'),
            "panchang_muhurat":panchang_data.get('panchang_muhurat','N/A'),
            "panchang_muhurat_end":panchang_data.get('panchang_muhurat_end','N/A'),
            "Disha_Shool":panchang_data.get('disha_shool','N/A'),
            "Chandrabalam": panchang_data.get('chandrabalam', {}).get('chandrabalam', 'N/A'),
            "Tarabalam": panchang_data.get('chandrabalam', {}).get('tarabalam', 'N/A'),
            "festivals_today": festivals_today,
            "upcoming_festivals": upcoming_festivals,
            
            "dshubhstart": panchang_data["choghadiya"]["day_ausp"][1]["start"],  # example
            "dshubhend": panchang_data["choghadiya"]["day_ausp"][1]["end"],
            "damritstart": panchang_data["choghadiya"]["day_ausp"][0]["start"],
            "damritend": panchang_data["choghadiya"]["day_ausp"][0]["end"],
            "dlabhstart": panchang_data["choghadiya"]["day_ausp"][2]["start"],
            "dlabhend": panchang_data["choghadiya"]["day_ausp"][2]["end"],
            "dkalastart": panchang_data["choghadiya"]["day_inausp"][0]["start"],
            "dkalaend": panchang_data["choghadiya"]["day_inausp"][0]["end"],
            "drogstart": panchang_data["choghadiya"]["day_inausp"][1]["start"],
            "drogend": panchang_data["choghadiya"]["day_inausp"][1]["end"],
            "dudvegstart": panchang_data["choghadiya"]["day_inausp"][2]["start"],
            "dudvegend": panchang_data["choghadiya"]["day_inausp"][2]["end"],
            "dcharstart": panchang_data["choghadiya"]["day_inausp"][3]["start"],
            "dcharend": panchang_data["choghadiya"]["day_inausp"][3]["end"],


            # Night
            "nshubhstart": panchang_data["choghadiya"]["night_ausp"][1]["start"],
            "nshubhend": panchang_data["choghadiya"]["night_ausp"][1]["end"],
            "namritstart": panchang_data["choghadiya"]["night_ausp"][0]["start"],
            "namritend": panchang_data["choghadiya"]["night_ausp"][0]["end"],
            "nlabhstart": panchang_data["choghadiya"]["night_ausp"][2]["start"],
            "nlabhend": panchang_data["choghadiya"]["night_ausp"][2]["end"],
            "nkalastart": panchang_data["choghadiya"]["night_inausp"][0]["start"],
            "nkalaend": panchang_data["choghadiya"]["night_inausp"][0]["end"],
            "nrogstart": panchang_data["choghadiya"]["night_inausp"][1]["start"],
            "nrogend": panchang_data["choghadiya"]["night_inausp"][1]["end"],
            "nudvegstart": panchang_data["choghadiya"]["night_inausp"][2]["start"],
            "nudvegend": panchang_data["choghadiya"]["night_inausp"][2]["end"],
            "ncharstart": panchang_data["choghadiya"]["night_inausp"][3]["start"],
            "ncharend": panchang_data["choghadiya"]["night_inausp"][3]["end"],
            "day_horas": panchang_data.get("day_horas", []),
            "night_horas": panchang_data.get("night_horas", []),
            "upcoming_auspicious_yogas": upcoming_yoga_rows,
            "selected_date": selected_date,
            "sky": _sky(selected_datetime, lat, lon, is_today_view),
        }
        
        return render(request, 'home.html', context)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        context = {
            'error': str(e),
            'target_datetime': datetime.now().strftime("%B %d, %Y %I:%M %p"),
            'city': 'Mumbai',
            'coordinates': '19.0760, 72.8777',
            'timezone': 'Asia/Kolkata',
        }
        return render(request, 'home.html', context)


def festival_calendar(request, year=None):
    """Hindu festival calendar for a year, dates per Kashi (Varanasi) panchang rules."""
    today = timezone.now().astimezone(pytz.timezone(VARANASI["tz"])).date()
    if year is None:
        try:
            year = int(request.GET.get("year", today.year))
        except ValueError:
            year = today.year
    if not (1900 <= year <= 2200):
        from django.http import Http404
        raise Http404("Year out of range")

    category = request.GET.get("category", "")
    events = get_carryover_periods(year) + get_festivals_for_year(year)
    events.extend(get_pilgrimage_windows_for_year(year))
    events.sort(key=lambda e: (e["date"], e["name"]))
    categories = sorted({e["category"] for e in events})
    if category:
        events = [e for e in events if e["category"] == category]

    # Strictly this year's months; a period carried over from December is listed under January.
    by_month = {}
    for e in events:
        by_month.setdefault(max(e["date"], date(year, 1, 1)).month, []).append(e)
    # The running year starts at the current month and wraps round to its January.
    first = today.month if year == today.year else 1
    order = sorted(by_month, key=lambda m: (m < first, m))
    months = [{"name": calendar.month_name[m], "items": by_month[m], "past": m < first} for m in order]

    # Puja time for the visitor's own city, right in the list (upcoming festivals only, to keep it quick)
    from ..utils import festival_muhurat as fm
    from .seo_views import user_location
    lat, lon, tz_name, user_city = user_location(request)
    for e in events:
        if e["slug"] in fm.RECIPES and e["date"] >= today - timedelta(days=1) and e["date"].year == year:
            e["puja"] = fm.best_window(e["slug"], e["date"], lat, lon, tz_name)

    context = {
        "year": year,
        "previous_year": year - 1,
        "next_year": year + 1,
        "events": events,
        "months": months,
        "categories": categories,
        "category": category,
        "today": today,
        "city": VARANASI["name"],
        "user_city": user_city, "timezone": tz_name,
    }
    return render(request, "festival_calendar.html", context)

# ---------------------
# Panchang Views
# ---------------------

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def panchang_today(request):
    """Get today's Panchang for authenticated user"""
    try:
        from ..user_settings import UserSettingsManager
        
        user_profile = UserSettingsManager.get_user_settings(request.user)
        timezone_str = user_profile.current_timezone
        
        try:
            tz = pytz.timezone(timezone_str)
        except:
            tz = pytz.timezone('Asia/Kolkata')
        
        today = datetime.now(tz)
        
        data = get_panchang(today, user=request.user)
        return Response(data)
        
    except Exception as e:
        return Response({"error": str(e)}, status=400)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def panchang_date(request, year, month, day):
    """Get Panchang for specific date for authenticated user"""
    try:
        from ..user_settings import UserSettingsManager
        
        user_profile = UserSettingsManager.get_user_settings(request.user)
        timezone_str = user_profile.current_timezone
        
        try:
            tz = pytz.timezone(timezone_str)
        except:
            tz = pytz.timezone('Asia/Kolkata')
        
        target_date = tz.localize(datetime(year, month, day))
        
        data = get_panchang(target_date, user=request.user)
        return Response(data)
        
    except Exception as e:
        return Response({"error": str(e)}, status=400)

@api_view(["GET"])
def panchang_anonymous(request):
    """Get Panchang for anonymous users (with location parameters)"""
    try:
        # Get location from query parameters or use defaults
        lat = float(request.GET.get('lat', 28.6139))
        lon = float(request.GET.get('lon', 77.2090))
        timezone_str = request.GET.get('tz', 'Asia/Kolkata')
        city_name = request.GET.get('city', 'New Delhi')
        
        # Get timezone object
        try:
            tz = pytz.timezone(timezone_str)
        except Exception as e:
            tz = pytz.timezone('Asia/Kolkata')
        
        # Create timezone-aware datetime
        today = datetime.now(tz)
        
        data = get_panchang(
            target_date=today, 
            user=None,
            lat=lat, 
            lon=lon, 
            timezone_str=timezone_str, 
            city_name=city_name
        )
        return Response(data)
        
    except Exception as e:
        
        logger.exception("Panchang API failed")
        
        return Response({"error": "Could not calculate the panchang for these inputs."}, status=400)

@api_view(["GET"])
@permission_classes([])
def panchang_datetime(request, year, month, day, hour, minute,lat,lon,city):
    """Get Panchang for anonymous users (with location parameters)"""
    try:
        # Use URL parameters, but allow query parameters to override them
        lat = float(request.GET.get('lat', lat))  # Use query param if exists, else URL param
        lon = float(request.GET.get('lon', lon))
        city_name = request.GET.get('city', city)
        timezone_str = request.GET.get('tz', 'Asia/Kolkata')

        
        # Get timezone object
        try:
            tz = pytz.timezone(timezone_str)
        except Exception as e:
            tz = pytz.timezone('Asia/Kolkata')
        
        # Create timezone-aware datetime
        naive_dt = datetime(year, month, day, hour, minute)
        dob = tz.localize(naive_dt)
        
        data = get_panchang(
            target_date=dob, 
            user=None,
            lat=lat, 
            lon=lon, 
            timezone_str=timezone_str, 
            city_name=city_name
        )
        return Response(data)
        
    except Exception as e:
        
        logger.exception("Panchang API failed")
        
        return Response({"error": "Could not calculate the panchang for these inputs."}, status=400)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def panchang_range(request, start_date, end_date):
    """Get Panchang for a date range (useful for monthly view)"""
    try:
        from ..user_settings import UserSettingsManager
        
        user_profile = UserSettingsManager.get_user_settings(request.user)
        timezone_str = user_profile.current_timezone
        
        try:
            tz = pytz.timezone(timezone_str)
        except:
            tz = pytz.timezone('Asia/Kolkata')
        
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        
        panchang_data = []
        current_date = start
        while current_date <= end:
            date_with_tz = tz.localize(current_date)
            daily_panchang = get_panchang(date_with_tz, user=request.user)
            panchang_data.append(daily_panchang)
            current_date += timedelta(days=1)
        
        return Response({
            "location": daily_panchang["location_info"],
            "date_range": f"{start_date} to {end_date}",
            "panchang_data": panchang_data
        })
        
    except Exception as e:
        return Response({"error": str(e)}, status=400)

@api_view(["GET"])
@permission_classes([])
def sarvarth_sidhi(request, year, month):
    """Get Panchang for anonymous users (with location parameters)"""
    try:
        # Use URL parameters, but allow query parameters to override them
        # year = int(request.GET.get('year', year))  # Use query param if exists, else URL param
        # month = int(request.GET.get('month', month))       
        user = request.user if request.user.is_authenticated else None



        data = calculate_sarvarth_sidhi(year, month,user)
        return Response(data)
        
    except Exception as e:
        
        logger.exception("Panchang API failed")
        
        return Response({"error": "Could not calculate the panchang for these inputs."}, status=400)


@api_view(["GET"])
@permission_classes([])
def amrit_sidhi(request, year, month):
    """Get Panchang for anonymous users (with location parameters)"""
    try:
        # Use URL parameters, but allow query parameters to override them
        # year = int(request.GET.get('year', year))  # Use query param if exists, else URL param
        # month = int(request.GET.get('month', month))       
        user = request.user if request.user.is_authenticated else None

        data = calculate_amrit_sidhi(year, month,user)
        return Response(data)
        
    except Exception as e:
        
        logger.exception("Panchang API failed")
        
        return Response({"error": "Could not calculate the panchang for these inputs."}, status=400)

@api_view(["GET"])
@permission_classes([])
def all_pushkar_yog(request, year, month):
    """Get Panchang for anonymous users (with location parameters)"""
    try:
        # Use URL parameters, but allow query parameters to override them
        # year = int(request.GET.get('year', year))  # Use query param if exists, else URL param
        # month = int(request.GET.get('month', month))       
        user = request.user if request.user.is_authenticated else None

        data = calculate_all_pushkar_yog(year, month,user)
        return Response(data)
        
    except Exception as e:
        
        logger.exception("Panchang API failed")
        
        return Response({"error": "Could not calculate the panchang for these inputs."}, status=400)
    
@api_view(["GET"])
@permission_classes([])
def ravi_yoga(request, year, month):
    """Get Panchang for anonymous users (with location parameters)"""
    try:
        # Use URL parameters, but allow query parameters to override them
        # year = int(request.GET.get('year', year))  # Use query param if exists, else URL param
        # month = int(request.GET.get('month', month))       
        user = request.user if request.user.is_authenticated else None

        data = calculate_ravi_yoga(year, month,user)
        return Response(data)
        
    except Exception as e:
        
        logger.exception("Panchang API failed")
        
        return Response({"error": "Could not calculate the panchang for these inputs."}, status=400)
    
# ---------------------
# Kundali Views
# ---------------------

 
def generate_kundali(request):
    """Generate Kundali - handles both form display and processing"""
    if request.method == 'GET':
        return render(request, 'kundali/form.html')
    
    elif request.method == 'POST':
        try:
            # Extract form data
            name = request.POST.get('name', '').strip()
            birth_date_str = request.POST.get('birth_date', '').strip()
            birth_time_str = request.POST.get('birth_time', '12:00').strip()
            birth_place = request.POST.get('birth_place', '').strip()
            lat_str = request.POST.get('lat', '').strip()
            lon_str = request.POST.get('lon', '').strip()
            timezone_str = request.POST.get('timezone', 'Asia/Kolkata')
            
            # Validate required fields
            if not name or not birth_date_str:
                return render(request, 'kundali/form.html', {
                    'error': 'Name and birth date are required',
                    'form_data': request.POST
                })
            
            # Parse coordinates
            try:
                birth_lat = float(lat_str) if lat_str else 28.6139
                birth_lon = float(lon_str) if lon_str else 77.2090
            except ValueError:
                return render(request, 'kundali/form.html', {
                    'error': 'Invalid latitude or longitude',
                    'form_data': request.POST
                })
            
            # Parse date and time with timezone
            try:
                # Combine date and time
                birth_datetime_naive = datetime.strptime(
                    f"{birth_date_str} {birth_time_str}", 
                    '%Y-%m-%d %H:%M'
                )
                
                # Make timezone aware
                tz = pytz.timezone(timezone_str)
                birth_datetime = tz.localize(birth_datetime_naive)
                
            except ValueError as e:
                return render(request, 'kundali/form.html', {
                    'error': f'Invalid date or time format: {str(e)}',
                    'form_data': request.POST
                })
            
            # Calculate Kundali
            calculator = KundaliCalculator(birth_datetime, birth_lat, birth_lon, 5.5)
            planetary_positions = calculator.calculate_planetary_positions()
            ascendant = calculator.calculate_ascendant()
            
            # Create Kundali record
            kundali = Kundali.objects.create(
                user=request.user if request.user.is_authenticated else None,
                name=name,
                birth_date=birth_datetime,
                birth_place=birth_place,
                birth_lat=birth_lat,
                birth_lon=birth_lon,
                birth_timezone=timezone_str,
                planetary_positions=planetary_positions,
                ascendant=ascendant
            )
            
            # Save Dasha periods
            dashas = calculator.calculate_dasha_periods()
            for dasha in dashas:
                DashaPeriod.objects.create(
                    kundali=kundali,
                    dasha_type=dasha['type'],
                    planet=dasha['planet'],
                    start_date=dasha['start_date'],
                    end_date=dasha['end_date'],
                    duration_years=dasha.get('duration_years', 0)
                )
            
            return redirect('kundali_detail', kundali_id=kundali.id)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            
            return render(request, 'kundali/form.html', {
                'error': f'Error generating kundali: {str(e)}',
                'form_data': request.POST
            })
    
    return redirect('kundali_form')

# kundali_detail and kundali_api live in core/view_kundali.py, where they only serve the owner's own kundali.

# ---------------------
# Transit Views
# ---------------------




@login_required
def transit_chart_old(request):
    """
    Transit Chart View - Uses get_panchang() for planetary calculations
    Shows natal positions (inner circle) vs current transits (outer circle)
    """
    # Get user's saved kundalis for dropdown
    user_kundalis = Kundali.objects.filter(user=request.user)
    
    # Default chart data structure
    chart_data = {
        'signs': [
            {'id': 1, 'name': 'Aries', 'symbol': '♈'},
            {'id': 2, 'name': 'Taurus', 'symbol': '♉'},
            {'id': 3, 'name': 'Gemini', 'symbol': '♊'},
            {'id': 4, 'name': 'Cancer', 'symbol': '♋'},
            {'id': 5, 'name': 'Leo', 'symbol': '♌'},
            {'id': 6, 'name': 'Virgo', 'symbol': '♍'},
            {'id': 7, 'name': 'Libra', 'symbol': '♎'},
            {'id': 8, 'name': 'Scorpio', 'symbol': '♏'},
            {'id': 9, 'name': 'Sagittarius', 'symbol': '♐'},
            {'id': 10, 'name': 'Capricorn', 'symbol': '♑'},
            {'id': 11, 'name': 'Aquarius', 'symbol': '♒'},
            {'id': 12, 'name': 'Pisces', 'symbol': '♓'},
        ],
        'natal_planets': [],
        'transit_planets': [],
        'selected_kundali': None,
        'ascendant': 1  # Default to Aries
    }
    
    # If kundali is selected via GET parameter
    kundali_id = request.GET.get('kundali_id')
    
    if kundali_id:
        try:
            kundali = Kundali.objects.get(id=kundali_id, user=request.user)
            chart_data['selected_kundali'] = kundali.name
            
            # Calculate NATAL positions
            natal_planets, natal_ascendant = calculate_natal_positions(kundali)
            
            chart_data['natal_planets'] = natal_planets
            chart_data['ascendant'] = natal_ascendant
            
            # Calculate CURRENT TRANSIT positions
            transit_planets, transit_ascendant = calculate_current_transits(kundali)
            
            chart_data['transit_planets'] = transit_planets
            
        except Kundali.DoesNotExist:
            logger.error("Kundali.DoesNotExist error")
            pass
        except Exception as e:
            logger.error(f"Error in kundali processing: {e}")
    
    
    context = {
        'user_kundalis': user_kundalis,
        'chart_data': json.dumps(chart_data),
    }
    
    return render(request, 'transit_chart2.html', context)

def calculate_natal_positions(kundali):
    """
    Calculate planetary positions at birth time using get_panchang()
    """
    try:
        
        # Extract time components for debugging
        birth_time = kundali.birth_date.time()
        
        # Get natal chart using get_panchang - use the full datetime
        natal_panchang = get_panchang(
            target_date=kundali.birth_date,  # Use the full datetime object
            lat=kundali.birth_lat,
            lon=kundali.birth_lon,
            timezone_str=kundali.birth_timezone,
        )
        
        if natal_panchang:
            if 'planetary_positions' in natal_panchang:
                planetary_data = natal_panchang['planetary_positions']
                
                # Debug: print first few planets
                for i, (planet_name, planet_data) in enumerate(list(planetary_data.items())[:3]):
                    pass
            else:
                pass
        else:
            return {'planets': [], 'ascendant': 0}
        
        # Extract planetary positions
        planetary_data = natal_panchang.get('planetary_positions', {})
        
        if not planetary_data:
            return {'planets': [], 'ascendant': 0}
        
        # Convert to chart format
        planets_list = []
        ascendant_sign = 0
        
        for planet_name, planet_data in planetary_data.items():
            if 'longitude' in planet_data:
                longitude = planet_data['longitude']
                sign_number = int(longitude // 30)
                degree_in_sign = longitude % 30
                
                planet_info = {
                    'name': planet_name,
                    'sign': sign_number,
                    'degree': round(degree_in_sign, 1),
                    'retrograde': planet_data.get('is_retrograde', False),
                    'longitude': round(longitude, 6)
                }
                
                planets_list.append(planet_info)
                
                if planet_name == 'Ascendant':
                    ascendant_sign = sign_number
            else:
                pass
        
        
        return {
            'planets': planets_list,
            'ascendant': ascendant_sign
        }
        
    except Exception as e:
        logger.error(f"❌ Error in calculate_natal_positions: {e}")
        import traceback
        traceback.print_exc()
        return {'planets': [], 'ascendant': 0}

def calculate_current_transits(kundali):
    """
    Calculate current planetary positions using get_panchang()
    Returns: dict with 'planets' list
    """
    try:
        # Get current datetime in kundali's timezone
        timezone = pytz.timezone(kundali.birth_timezone)
        current_datetime = datetime.now(timezone)
        
        # Get transit chart using get_panchang
        transit_panchang = get_panchang(
            target_date=current_datetime,
            lat=kundali.birth_lat,  # Using birth location for transits
            lon=kundali.birth_lon,
            timezone_str='Asia/Kolkata'
        )
        
        # Extract planetary positions
        planetary_data = transit_panchang.get('planetary_positions', {})
        
        # Convert to chart format
        planets_list = []
        
        for planet_name, planet_data in planetary_data.items():
            if planet_name == 'Ascendant':
                # Skip ascendant for transits
                continue
                
            if 'longitude' in planet_data:
                longitude = planet_data['longitude']
                sign_number = int(longitude // 30)  # Already 0-based
                degree_in_sign = longitude % 30
                
                planets_list.append({
                    'name': planet_name,
                    'sign': sign_number,  # 0-based
                    'degree': round(degree_in_sign, 1),
                    'retrograde': planet_data.get('is_retrograde', False),
                    'longitude': round(longitude, 6)
                })
        
        # RETURN DICT, NOT TUPLE
        return {
            'planets': planets_list
        }
        
    except Exception as e:
        logger.error(f"Error calculating transit positions: {e}")
        import traceback
        traceback.print_exc()
        # Return dict, not tuple
        return {'planets': []}

#New Natal Chart with calculation in python
@login_required
def transit_chart_new(request):
    """
    Transit Chart View - Pre-calculates all coordinates for easy JavaScript rendering
    """
    user_kundalis = Kundali.objects.filter(user=request.user)
    
    # Chart configuration
    chart_config = {
        'center_x': 450,
        'center_y': 350,
        'outer_radius': 330,
        'natal_radius': 242,    # natal band: zodiac_radius..natal_radius
        'zodiac_radius': 156,   # zodiac band: inner_radius..zodiac_radius
        'inner_radius': 70,
        'sign_gap': 20  # Gap for planet spacing
    }
    
    chart_data = {
        'signs': [
            {'id': 0, 'name': 'Aries', 'symbol': '♈', 'color': '#ff6b6b'},
            {'id': 1, 'name': 'Taurus', 'symbol': '♉', 'color': '#feca57'},
            {'id': 2, 'name': 'Gemini', 'symbol': '♊', 'color': '#48dbfb'},
            {'id': 3, 'name': 'Cancer', 'symbol': '♋', 'color': '#1dd1a1'},
            {'id': 4, 'name': 'Leo', 'symbol': '♌', 'color': '#ff9ff3'},
            {'id': 5, 'name': 'Virgo', 'symbol': '♍', 'color': '#54a0ff'},
            {'id': 6, 'name': 'Libra', 'symbol': '♎', 'color': '#5f27cd'},
            {'id': 7, 'name': 'Scorpio', 'symbol': '♏', 'color': '#00d2d3'},
            {'id': 8, 'name': 'Sagittarius', 'symbol': '♐', 'color': '#ee5a6f'},
            {'id': 9, 'name': 'Capricorn', 'symbol': '♑', 'color': '#c8d6e5'},
            {'id': 10, 'name': 'Aquarius', 'symbol': '♒', 'color': '#576574'},
            {'id': 11, 'name': 'Pisces', 'symbol': '♓', 'color': '#222f3e'},
        ],
        'natal_planets': [],
        'transit_planets': [],
        'houses': [],
        'zodiac_positions': [],
        'radial_lines': [],
        'ascendant': 0,
        'config': chart_config,
        'selected_kundali_id': None,  # Change this to store ID
        'selected_kundali_name': None
    }
    
    kundali_id = request.GET.get('kundali_id')
    selected_kundali = None
    
    if kundali_id:
        try:
            kundali = Kundali.objects.get(id=kundali_id, user=request.user)
            selected_kundali = kundali
            chart_data['selected_kundali_id'] = kundali.id
            chart_data['selected_kundali_name'] = kundali.name

            
            # Calculate positions
            try:
                natal_data = calculate_natal_positions(kundali)
                chart_data['natal_planets'] = natal_data['planets']
                chart_data['ascendant'] = natal_data['ascendant']
            except Exception as e:
                logger.error(f"Error in natal positions: {e}")
                import traceback
                traceback.print_exc()
                # Use empty data but continue
                chart_data['natal_planets'] = []
                chart_data['ascendant'] = 0
            
            try:
                transit_data = calculate_current_transits(kundali)
                chart_data['transit_planets'] = transit_data['planets']
            except Exception as e:
                logger.error(f"Error in transit positions: {e}")
                import traceback
                traceback.print_exc()
                # Use empty data but continue
                chart_data['transit_planets'] = []
            
            # Pre-calculate all coordinates only if we have planets
            if chart_data['natal_planets'] or chart_data['transit_planets']:
                try:
                    chart_data = pre_calculate_chart_coordinates(chart_data)
                except Exception as e:
                    logger.error(f"Error in pre-calculation: {e}")
                    import traceback
                    traceback.print_exc()
                    # Keep the basic structure but skip coordinates
            else:
                pass
                
        except Exception as e:
            logger.error(f"Error in kundali processing: {e}")
            import traceback
            traceback.print_exc()
            # Keep the basic structure with empty 

    if 'zodiac_segments' in chart_data:
        if chart_data['zodiac_segments']:
            first_seg = chart_data['zodiac_segments'][0]
    
    # Convert to JSON
    chart_data_json = json.dumps(chart_data, default=str)
    
    # Debug: Check what's in the JSON
    parsed_back = json.loads(chart_data_json)
    if 'zodiac_segments' in parsed_back:
        pass
    
    # Debug: Print final data structure
    
    context = {
        'user_kundalis': user_kundalis,
        'selected_kundali': selected_kundali,  # Pass the actual object
        'chart_data': json.loads(json.dumps(chart_data, default=str)),
    }
    from ..view_kundali import transit_labels
    context['transit_labels'] = transit_labels()
    
    return render(request, 'transit_chart2.html', context)

def pre_calculate_chart_coordinates(chart_data):
    """
    Pre-calculate all coordinates, angles, and positions for the chart
    """
    config = chart_data['config']
    center_x = config['center_x']
    center_y = config['center_y']
    
    # FIX: Use the stored ascendant value instead of searching in planets
    ascendant_sign = chart_data.get('ascendant', 0)
    
    # If you need the ascendant degree, calculate it or use a default
    # Since we don't have the exact degree, we'll use the middle of the sign (15°)
    asc_degree = 15.0  # Default to middle of the sign
    
    # Try to find Ascendant in natal_planets if it exists
    for planet in chart_data.get('natal_planets', []):
        if planet.get('name') == 'Ascendant':
            asc_degree = planet.get('degree', 15.0)
            break
    
    # Calculate rotation angle to bring ascendant to left (270 degrees)
    ascendant_degree = ascendant_sign * 30 + asc_degree  # Each sign is 30 degrees
    rotation_angle = 270 - ascendant_degree  # Rotation needed
    chart_data["rotation_angle"] = rotation_angle

    
    # Rest of your function remains the same...
    # 1. Pre-calculate zodiac segment coordinates
    chart_data['zodiac_segments'] = []
    for i, sign in enumerate(chart_data['signs']):
        # Calculate segment angles with rotation
        start_angle_original = (i * 30 - 90) % 360
        end_angle_original = ((i + 1) * 30 - 90) % 360
        
        start_angle_rotated = (start_angle_original + rotation_angle) % 360
        end_angle_rotated = (end_angle_original + rotation_angle) % 360
        
        # Convert to radians for coordinate calculation
        start_rad = math.radians(start_angle_rotated)
        end_rad = math.radians(end_angle_rotated)
        
        # Calculate points for the segment wedge
        inner_points = []
        outer_points = []
        
        # Add multiple points for smooth arc
        steps = 10
        for step in range(steps + 1):
            angle = start_angle_rotated + (end_angle_rotated - start_angle_rotated) * step / steps
            rad_angle = math.radians(angle)
            
            # Inner circle point
            inner_x = center_x + config['inner_radius'] * math.cos(rad_angle)
            inner_y = center_y + config['inner_radius'] * math.sin(rad_angle)
            inner_points.append([inner_x, inner_y])  # Use lists for JSON
            
            # Outer circle point (zodiac radius)
            outer_x = center_x + config['zodiac_radius'] * math.cos(rad_angle)
            outer_y = center_y + config['zodiac_radius'] * math.sin(rad_angle)
            outer_points.append([outer_x, outer_y])  # Use lists for JSON
        
        chart_data['zodiac_segments'].append({
            'sign_id': sign['id'],
            'color': sign['color'],
            'inner_points': inner_points,
            'outer_points': outer_points,
            'start_angle': start_angle_rotated,
            'end_angle': end_angle_rotated
        })
    
    # Debug: Print what we calculated
    if chart_data['zodiac_segments']:
        first_seg = chart_data['zodiac_segments'][0]
    

    # 2. Pre-calculate zodiac sign label positions (your existing code)
    chart_data['zodiac_positions'] = []
    for i, sign in enumerate(chart_data['signs']):
        # Original position (0° at top, 90° at right)
        original_angle = (i * 30 - 90) % 360
        # Apply ascendant rotation
        rotated_angle = (original_angle + rotation_angle) % 360
        rad_angle = math.radians(rotated_angle+15)
        
        # Symbol position (inner circle)
        symbol_radius = (config['zodiac_radius'] + config['inner_radius']) / 2
        symbol_x = center_x + symbol_radius * math.cos(rad_angle)
        symbol_y = center_y + symbol_radius * math.sin(rad_angle)
        
        # Name position (outer circle)
        name_radius = config['zodiac_radius'] + 20
        name_x = center_x + name_radius * math.cos(rad_angle)
        name_y = center_y + name_radius * math.sin(rad_angle)
        
        chart_data['zodiac_positions'].append({
            'sign_id': sign['id'],
            'symbol': {
                'x': symbol_x,
                'y': symbol_y,
                'angle': rotated_angle
            },
            'name': {
                'x': name_x,
                'y': name_y,
                'angle': rotated_angle
            }
        })
    
    # 3. Pre-calculate house positions
    chart_data['houses'] = []
    for i in range(12):
        # Calculate house number based on ascendant
        house_number = ((i - ascendant_sign + 12) % 12) + 1
        
        # Position calculation with rotation
        house_cusp_angle = (i * 30 - 90) % 360
        rotated_cusp_angle = (house_cusp_angle + rotation_angle) % 360
        rad_angle = math.radians(rotated_cusp_angle + 15)  # Center of house
        
        house_radius = config['inner_radius'] - 20
        house_x = center_x + house_radius * math.cos(rad_angle)
        house_y = center_y + house_radius * math.sin(rad_angle)
        
        chart_data['houses'].append({
            'number': house_number,
            'x': house_x,
            'y': house_y,
            'angle': rotated_cusp_angle,
            'is_important': house_number in [1, 4, 7, 10]
        })
    
    # 4. Pre-calculate radial lines
    chart_data['radial_lines'] = []
    for i in range(12):
        original_angle = (i * 30 - 90) % 360
        rotated_angle = (original_angle + rotation_angle) % 360
        rad_angle = math.radians(rotated_angle)
        
        start_x = center_x + config['inner_radius'] * math.cos(rad_angle)
        start_y = center_y + config['inner_radius'] * math.sin(rad_angle)
        end_x = center_x + config['outer_radius'] * math.cos(rad_angle)
        end_y = center_y + config['outer_radius'] * math.sin(rad_angle)
        
        house_number = ((i - ascendant_sign + 12) % 12) + 1
        is_important_house = house_number in [1, 4, 7, 10]
        
        chart_data['radial_lines'].append({
            'start_x': start_x,
            'start_y': start_y,
            'end_x': end_x,
            'end_y': end_y,
            'angle': rotated_angle,
            'is_ascendant': i == 0,
            'is_important': is_important_house,
            'house_number': house_number
        })
    
    # 5. Pre-calculate planet positions
    chart_data['details'] = transit_info.chart_details(chart_data['natal_planets'], chart_data['transit_planets'],
                                                       ascendant_sign)
    chart_data['natal_planets'] = calculate_planet_positions(
        chart_data['natal_planets'],
        config['zodiac_radius'],
        config['natal_radius'],
        rotation_angle,
        center_x,
        center_y,
        'natal'
    )
    
    chart_data['transit_planets'] = calculate_planet_positions(
        chart_data['transit_planets'],
        config['natal_radius'],
        config['outer_radius'],
        rotation_angle,
        center_x,
        center_y,
        'transit'
    )
    
    # Final debug
    
    return chart_data


def spread_angles(angles, gap):
    """Nudge sorted angles apart until neighbours are at least ``gap`` degrees from each other."""
    out = list(angles)
    for _ in range(60):
        moved = False
        for i in range(len(out)):
            j = (i + 1) % len(out)
            if i == j:
                break
            distance = (out[j] - out[i]) % 360
            if distance < gap:
                push = (gap - distance) / 2
                out[i] -= push
                out[j] += push
                moved = True
        if not moved:
            break
    return out


def calculate_planet_positions(planets, inner_radius, outer_radius, rotation_angle, center_x, center_y, planet_type):
    """Canvas coordinates for planets, spaced so their discs and labels do not collide."""
    if not planets:
        return []
    radius = (inner_radius + outer_radius) / 2
    gap = math.degrees(42 / radius)              # disc plus a little air
    ordered = sorted(planets, key=lambda p: p['sign'] * 30 + p['degree'])
    angles = spread_angles([p['sign'] * 30 + p['degree'] + rotation_angle for p in ordered], gap)
    positioned = []
    for planet, angle in zip(ordered, angles):
        rad = math.radians(angle - 90)
        positioned.append({**planet, 'canvas_x': center_x + radius * math.cos(rad),
                           'canvas_y': center_y + radius * math.sin(rad),
                           'display_angle': angle % 360, 'type': planet_type})
    return positioned


def get_sample_chart_with_coordinates():
    """Fallback sample data with pre-calculated coordinates"""
    # This would return a complete chart_data structure with all coordinates pre-calculated
    pass


def get_sample_natal_data():
    """Sample natal data for testing"""
    return [
        {'name': 'Sun', 'sign': 0, 'degree': 15.5, 'retrograde': False},
        {'name': 'Moon', 'sign': 1, 'degree': 20.0, 'retrograde': False},
        {'name': 'Mars', 'sign': 2, 'degree': 10.0, 'retrograde': False},
        {'name': 'Mercury', 'sign': 0, 'degree': 25.0, 'retrograde': False},
        {'name': 'Jupiter', 'sign': 3, 'degree': 5.0, 'retrograde': False},
        {'name': 'Venus', 'sign': 11, 'degree': 18.0, 'retrograde': False},
        {'name': 'Saturn', 'sign': 7, 'degree': 22.0, 'retrograde': False},
        {'name': 'Rahu', 'sign': 5, 'degree': 15.0, 'retrograde': False},
        {'name': 'Ketu', 'sign': 11, 'degree': 15.0, 'retrograde': False},
    ]

def get_sample_transit_data():
    """Sample transit data for testing"""
    return [
        {'name': 'Sun', 'sign': 2, 'degree': 7.2, 'retrograde': False},
        {'name': 'Moon', 'sign': 3, 'degree': 12.8, 'retrograde': False},
        {'name': 'Mars', 'sign': 4, 'degree': 18.5, 'retrograde': False},
        {'name': 'Mercury', 'sign': 2, 'degree': 25.0, 'retrograde': True},
        {'name': 'Jupiter', 'sign': 1, 'degree': 14.0, 'retrograde': False},
        {'name': 'Venus', 'sign': 3, 'degree': 8.0, 'retrograde': False},
        {'name': 'Saturn', 'sign': 8, 'degree': 19.0, 'retrograde': False},
        {'name': 'Rahu', 'sign': 6, 'degree': 5.0, 'retrograde': False},
        {'name': 'Ketu', 'sign': 0, 'degree': 5.0, 'retrograde': False},
    ]



#----------Auscpicious Yogas-----------------

def auspicious_yogas_dashboard(request):
    """Special yogas for the next 60 days at the visitor's location (computed from the shared cache)."""
    from .seo_views import user_location
    lat, lon, tz, city = user_location(request)
    today = timezone.now().astimezone(pytz.timezone(tz)).date()
    kind = request.GET.get('type', '')
    kinds = {kind} if kind in muhurat.YOGA_INFO else None
    windows = muhurat.special_yogas(today, today + timedelta(days=60), lat, lon, tz, kinds=kinds)
    return render(request, 'yogas/dashboard.html', {
        'windows': windows, 'yoga_types': muhurat.YOGA_INFO, 'type': kind,
        'city': city, 'timezone': tz, 'year': today.year, 'total_count': len(windows),
    })

def yoga_search(request):
    """
    Search/filter yogas
    """
    yogas = []
    search_performed = False
    
    # Yoga types for the dropdown
    yoga_types = {
        'SARVARTH_SIDDHI': 'Sarvarth Siddhi Yoga',
        'AMRIT_SIDDHI': 'Amrit Siddhi Yoga', 
        'DWIPUSHKAR': 'Dwipushkar Yoga',
        'TRIPUSHKAR': 'Tripushkar Yoga',
        'RAVI': 'Ravi Yoga'
    }
    
    if request.method == 'GET' and any(param in request.GET for param in ['date', 'yoga_type', 'nakshatra', 'weekday']):
        search_performed = True
        date_str = request.GET.get('date')
        yoga_type = request.GET.get('yoga_type')
        nakshatra = request.GET.get('nakshatra')
        weekday = request.GET.get('weekday')
        
        # Convert date string to date object
        date_obj = None
        if date_str:
            try:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        yogas = search_yogas(
            date=date_obj,
            yoga_type=yoga_type,
            nakshatra=nakshatra,
            weekday=weekday
        )
    
    context = {
        'yogas': yogas,
        'yoga_types': yoga_types,
        'search_performed': search_performed
    }
    
    return render(request, 'yogas/search.html', context)

# You can also add more yoga-related views here
def yoga_combinations_stats(request):
    """
    Show statistics about yoga combinations
    """
    stats = get_yoga_combinations_stats()
    
    context = {
        'stats': stats
    }
    
    return render(request, 'yogas/stats.html', context)

#----------------COMPATIBILITY CHECK-----------------

def compatibility(request):
    """Main matchmaking page"""
    return render(request, 'kundali/compatibility.html', {'nakshatras': NAKSHATRA_NAMES})

def get_coordinates_and_timezone(place_name, place_id=None):
    """Resolve a birth place via the offline GeoNames gazetteer (see utils/geo.py)."""
    hit = resolve_place(place_name, geoname_id=place_id)
    if not hit:
        return None
    return {'lat': hit['lat'], 'lon': hit['lon'], 'timezone': hit['timezone'], 'address': hit['name']}

def get_timezone_offset(timezone_name, dt):
    """Get timezone offset in hours for a specific datetime"""
    try:
        if timezone_name:
            tz = pytz.timezone(timezone_name)
            # Get UTC offset for the specific datetime (accounts for DST)
            utc_offset = tz.utcoffset(dt)
            return utc_offset.total_seconds() / 3600  # Convert to hours
        return 5.5  # Default to IST
    except Exception as e:
        logger.error(f"Timezone offset error: {e}")
        return 5.5  # Default to IST

def get_user_country_from_ip(request):
    """Extract user's country from IP address (simplified)"""
    return "India"  # Default to India

def get_country_from_address(address):
    """Extract country from address string"""
    parts = address.split(',')
    if parts:
        return parts[-1].strip()
    return "Unknown"

def format_city_display_name(address):
    """Format address for clean display"""
    parts = [part.strip() for part in address.split(',')]
    
    # Remove duplicate consecutive parts
    unique_parts = []
    for part in parts:
        if part and (not unique_parts or part != unique_parts[-1]):
            unique_parts.append(part)
    
    # Join with comma, limit to 3 parts for cleaner display
    if len(unique_parts) > 3:
        return ', '.join(unique_parts[:3])
    
    return ', '.join(unique_parts)

def calculate_individual_kootas(kundali):
    """Calculate individual koota values for a person's chart"""
    try:
        # Get basic data
        rashi = getattr(kundali, 'rashi', 'Unknown')
        nakshatra = getattr(kundali, 'nakshatra', 'Unknown')
        nakshatra_pada = getattr(kundali, 'nakshatra_pada', 1)
        
        # Calculate individual koota values
        return {
            'varna': calculate_varna(rashi),
            'vashya': calculate_vashya(rashi),
            'tara': nakshatra,  # The nakshatra itself for Tara Koot
            'yoni': calculate_yoni(nakshatra),
            'graha_maitri': rashi,  # Moon sign for mental compatibility
            'gana': calculate_gana(nakshatra),
            'bhakoot': rashi,  # Moon sign for emotional compatibility
            'nadi': calculate_nadi(nakshatra),
        }
    except Exception as e:
        logger.error(f"Error calculating individual kootas: {e}")
        return {}

def calculate_varna(rashi):
    """Calculate Varna based on moon sign"""
    varna_map = {
        'Mesh': 'Kshatriya', 'Simha': 'Kshatriya', 'Dhanu': 'Kshatriya',
        'Vrishabha': 'Vaishya', 'Kanya': 'Vaishya', 'Makar': 'Vaishya',
        'Mithuna': 'Shudra', 'Tula': 'Shudra', 'Kumbha': 'Shudra',
        'Kark': 'Brahmin', 'Vrishchik': 'Brahmin', 'Meena': 'Brahmin'
    }
    return varna_map.get(rashi, 'Unknown')

def calculate_vashya(rashi):
    """Calculate Vasya based on moon sign"""
    vashya_map = {
        'Mesh': 'Chatushpada', 'Vrishabha': 'Manav', 'Mithuna': 'Vanachara',
        'Kark': 'Jalachara', 'Simha': 'Chatushpada', 'Kanya': 'Manav',
        'Tula': 'Vanachara', 'Vrishchik': 'Keeta', 'Dhanu': 'Chatushpada',
        'Makar': 'Manav', 'Kumbha': 'Vanachara', 'Meena': 'Jalachara'
    }
    return vashya_map.get(rashi, 'Unknown')

def calculate_yoni(nakshatra):
    """Calculate Yoni animal from nakshatra"""
    yoni_map = {
        'Ashwini': 'Horse', 'Bharani': 'Elephant', 'Krittika': 'Sheep',
        'Rohini': 'Serpent', 'Mrigashira': 'Serpent', 'Ardra': 'Dog',
        'Punarvasu': 'Cat', 'Pushya': 'Sheep', 'Ashlesha': 'Cat',
        'Magha': 'Rat', 'Purva Phalguni': 'Rat', 'Uttara Phalguni': 'Cow',
        'Hasta': 'Buffalo', 'Chitra': 'Tiger', 'Swati': 'Buffalo',
        'Vishakha': 'Tiger', 'Anuradha': 'Deer', 'Jyeshtha': 'Deer',
        'Mula': 'Dog', 'Purva Ashadha': 'Monkey', 'Uttara Ashadha': 'Mongoose',
        'Shravana': 'Monkey', 'Dhanishta': 'Lion', 'Shatabhisha': 'Horse',
        'Purva Bhadrapada': 'Lion', 'Uttara Bhadrapada': 'Cow', 'Revati': 'Elephant'
    }
    return yoni_map.get(nakshatra, 'Unknown')

def calculate_gana(nakshatra):
    """Calculate Gana type from nakshatra"""
    deva_nakshatras = ['Ashwini', 'Mrigashira', 'Punarvasu', 'Pushya', 'Hasta', 
                    'Swati', 'Anuradha', 'Shravana', 'Revati']
    manushya_nakshatras = ['Bharani', 'Rohini', 'Ardra', 'Purva Phalguni', 
                        'Uttara Phalguni', 'Purva Ashadha', 'Uttara Ashadha', 
                        'Purva Bhadrapada', 'Uttara Bhadrapada']
    rakshasa_nakshatras = ['Krittika', 'Ashlesha', 'Magha', 'Chitra', 'Vishakha', 
                        'Jyeshtha', 'Mula', 'Dhanishta', 'Shatabhisha']
    
    if nakshatra in deva_nakshatras:
        return 'Deva'
    elif nakshatra in manushya_nakshatras:
        return 'Manushya'
    elif nakshatra in rakshasa_nakshatras:
        return 'Rakshasa'
    return 'Unknown'

def calculate_nadi(nakshatra):
    """Calculate Nadi type from nakshatra"""
    nakshatras = ['Ashwini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashira', 
                'Ardra', 'Punarvasu', 'Pushya', 'Ashlesha', 'Magha', 
                'Purva Phalguni', 'Uttara Phalguni', 'Hasta', 'Chitra', 
                'Swati', 'Vishakha', 'Anuradha', 'Jyeshtha', 'Mula', 
                'Purva Ashadha', 'Uttara Ashadha', 'Shravana', 'Dhanishta', 
                'Shatabhisha', 'Purva Bhadrapada', 'Uttara Bhadrapada', 'Revati']
    
    try:
        index = nakshatras.index(nakshatra)
        if index < 9:
            return 'Adi'
        elif index < 18:
            return 'Madhya'
        else:
            return 'Antya'
    except ValueError:
        return 'Unknown'

class _NameChart:
    """The little that a name reveals: the Moon's nakshatra and sign, nothing else."""
    def __init__(self, name, moon):
        self.name = name
        self.rashi, self.nakshatra, self.nakshatra_pada = moon['rashi'], moon['nakshatra'], moon['pada']
        self.moon_degree = moon['moon_longitude']
        self.moon_zodiac_degree = moon['moon_longitude'] % 30
        self.planets, self.planets_data = {}, []


def _milan_by_name(data):
    charts = []
    for who, label in (('person1', 'groom'), ('person2', 'bride')):
        name = (data.get(f'{who}_name') or '').strip()
        nak = data.get(f'{who}_nakshatra')
        moon = namakshar.from_nakshatra(nak, data.get(f'{who}_pada')) if nak in NAKSHATRA_NAMES else namakshar.from_name(name)
        if not moon:
            return {'success': False, 'error': f"Could not read the {label}'s name. Please enter it, or choose the janma nakshatra."}
        charts.append((_NameChart(name, moon), moon))
    (k1, m1), (k2, m2) = charts
    ashtakoot = calculate_ashtakoot(k1, k2)
    # No dosha analysis: a name gives the Moon's nakshatra only, not the planets at birth
    person = lambda k, m: {'name': k.name, 'rashi': k.rashi, 'nakshatra': k.nakshatra, 'pada': m['pada'], 'planets': {}}
    return {'success': True, 'mode': 'name', 'limits': namakshar.LIMITS, 'person1': person(k1, m1), 'person2': person(k2, m2),
            'ashtakoot': ashtakoot, 'doshas': {}}


@csrf_exempt
@rate_limit('compatibility', 20)
def calculate_compatibility(request):
    """Calculate Ashtakoot Gun Milan based on birth details"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            if data.get('mode') == 'name':
                return JsonResponse(_milan_by_name(data))

            # Get birth details for both persons
            person1_details = {
                'name': data.get('person1_name', 'Person 1'),
                'birth_date': data.get('person1_birth_date'),
                'birth_time': data.get('person1_birth_time'),
                'birth_place': data.get('person1_birth_place')
            }
            
            person2_details = {
                'name': data.get('person2_name', 'Person 2'),
                'birth_date': data.get('person2_birth_date'),
                'birth_time': data.get('person2_birth_time'),
                'birth_place': data.get('person2_birth_place')
            }
            
            # Validate inputs
            if not all([person1_details['birth_date'], person1_details['birth_time'], person1_details['birth_place'],
                       person2_details['birth_date'], person2_details['birth_time'], person2_details['birth_place']]):
                return JsonResponse({
                    'success': False,
                    'error': 'Please provide all birth details for both persons'
                })
            
            # Offline gazetteer lookups take ~1 ms, so no threads (Swiss Ephemeris state is global anyway)
            person1_location = get_coordinates_and_timezone(person1_details['birth_place'], data.get('person1_place_id'))
            person2_location = get_coordinates_and_timezone(person2_details['birth_place'], data.get('person2_place_id'))

            if not person1_location or not person2_location:
                return JsonResponse({
                    'success': False,
                    'error': 'Could not find coordinates for one or both birth places. Please use the autocomplete suggestions for accurate location.'
                })
            
            # Parse date and time to create datetime objects
            def create_datetime_obj(date_str, time_str):
                try:
                    datetime_str = f"{date_str} {time_str}"
                    return datetime.strptime(datetime_str, '%Y-%m-%d %H:%M')
                except Exception as e:
                    raise ValueError(f"Invalid date/time format: {e}")
            
            # Create datetime objects
            person1_dt = create_datetime_obj(person1_details['birth_date'], person1_details['birth_time'])
            person2_dt = create_datetime_obj(person2_details['birth_date'], person2_details['birth_time'])
            
            # Convert datetime to Julian Date and get accurate timezone offset
            def get_jd_and_tz_offset(dt, location_data):
                """Convert datetime to Julian Date with accurate timezone"""
                try:
                    # Get accurate timezone offset
                    tz_offset = get_timezone_offset(location_data['timezone'], dt)
                    
                    tz = pytz.timezone(location_data['timezone'])
                    target_datetime = tz.localize(dt)
                    dt_utc = target_datetime.astimezone(pytz.utc)                    
                    jd = swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, dt_utc.hour + dt_utc.minute/60.0)
                    
                    return jd, tz_offset
                    
                except Exception as e:
                    logger.error(f"JD conversion error: {e}")
                    # Fallback calculation
                    jd = 2451545.0 + (dt - datetime(2000, 1, 1)).days
                    return jd, 5.5  # Default to IST
            
            # Get Julian Dates and accurate timezone offsets
            person1_jd, person1_tz = get_jd_and_tz_offset(person1_dt, person1_location)
            person2_jd, person2_tz = get_jd_and_tz_offset(person2_dt, person2_location)
            
            person1_planets = get_planetary_positions(person1_jd, person1_location['lat'], person1_location['lon'], person1_tz)
            person2_planets = get_planetary_positions(person2_jd, person2_location['lat'], person2_location['lon'], person2_tz)

            # Create kundali objects
            class Kundali:
                def __init__(self, name, planets_data):
                    self.name = name
                    # Extract Moon data for Ashtakoot calculation
                    moon_data = next((p for p in planets_data if p.get('planet') == 'Moon'), None)
                    
                    if moon_data:
                        self.rashi = moon_data.get('zodiac_sign', 'Unknown')
                        self.nakshatra = moon_data.get('nakshatra', 'Unknown')
                        self.nakshatra_pada = moon_data.get('nakshatra_pada', 1)
                        self.moon_degree = moon_data.get('longitude', 0)
                        # FIX: Convert sign_degree to float safely
                        sign_degree = moon_data.get('sign_degree', 0)
                        try:
                            self.moon_zodiac_degree = float(sign_degree)
                        except (ValueError, TypeError):
                            self.moon_zodiac_degree = 0.0  # Default value
                    else:
                        self.rashi = 'Unknown'
                        self.nakshatra = 'Unknown'
                        self.nakshatra_pada = 1
                        self.moon_degree = 0
                        self.moon_zodiac_degree = 0.0  # Default value
                    
                    # Store all planetary data for display
                    self.planets_data = planets_data
                    self.planets = {p['planet']: p for p in planets_data}
            
            person1_kundali = Kundali(person1_details['name'], person1_planets)
            person2_kundali = Kundali(person2_details['name'], person2_planets)

            # Doshas need the Ashtakoot scores, so these must run in order
            ashtakoot_result = calculate_ashtakoot(person1_kundali, person2_kundali)
            dosha_result = DoshaEvaluator().evaluate_all(person1_kundali, person2_kundali, ashtakoot_result)

            # Validate that we have the required data
            if person1_kundali.rashi == 'Unknown' or person2_kundali.rashi == 'Unknown':
                return JsonResponse({
                    'success': False,
                    'error': 'Could not calculate Moon positions for one or both persons'
                })
            

            return JsonResponse({
                'success': True,
                'person1': {
                    'name': getattr(person1_kundali, 'name', 'Boy'),
                    'rashi': getattr(person1_kundali, 'rashi', ''),
                    'nakshatra': getattr(person1_kundali, 'nakshatra', ''),
                    'planets': getattr(person1_kundali, 'planets', {}),
                    'birth_place': person1_details['birth_place'],
                    'coordinates': f"{person1_location['lat']:.4f}, {person1_location['lon']:.4f}",
                    'timezone': person1_location['timezone']
                },
                'person2': {
                    'name': getattr(person2_kundali, 'name', 'Girl'), 
                    'rashi': getattr(person2_kundali, 'rashi', ''),
                    'nakshatra': getattr(person2_kundali, 'nakshatra', ''),
                    'planets': getattr(person2_kundali, 'planets', {}),
                    'birth_place': person2_details['birth_place'],
                    'coordinates': f"{person2_location['lat']:.4f}, {person2_location['lon']:.4f}",
                    'timezone': person2_location['timezone']
                },
                'ashtakoot': ashtakoot_result,
                'doshas': dosha_result
            })
            
        except Exception as e:
            import traceback
            logger.error(f"Error in calculate_compatibility: {str(e)}")
            logger.error(traceback.format_exc())
            return JsonResponse({
                'success': False,
                'error': f'Calculation error: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})
