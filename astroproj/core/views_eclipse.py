from rest_framework.decorators import api_view
from rest_framework.response import Response
from datetime import datetime, timedelta
import swisseph as swe
import json
import pytz
from django.utils import timezone
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from .eclipse_utils import compute_solar_eclipse, compute_lunar_eclipse, jd_to_datetime, find_all_upcoming_eclipses, save_eclipse_to_db
from .models import Eclipse
from .user_settings import UserSettingsManager

@api_view(['GET'])
def update_eclipse_database(request):
    """Update the eclipse database with upcoming eclipses"""
    eclipses = find_all_upcoming_eclipses(num_eclipses=20, save_to_db=True)
    return Response({
        "status": "success",
        "eclipses_found": len(eclipses),
        "message": "Eclipse database updated successfully"
    })

@api_view(['GET'])
def list_eclipses(request):
    """List all eclipses from database with better null handling"""
    eclipses = Eclipse.objects.all().order_by('date_max')
    
    eclipse_list = []
    for eclipse in eclipses:
        # Debug each eclipse
        print(f"DEBUG Eclipse {eclipse.id}: date_max = {eclipse.date_max}, type = {type(eclipse.date_max)}")
        
        eclipse_list.append({
            "id": eclipse.id,
            "type": eclipse.eclipse_type,
            "date": eclipse.date_max.strftime("%Y-%m-%d %H:%M:%S") if eclipse.date_max else None,
            "date_raw": str(eclipse.date_max),  # Add this for debugging
            "magnitude": eclipse.magnitude,
            "subtype": eclipse.subtype,
            "central_coords": f"{eclipse.central_lat:.6f}, {eclipse.central_lon:.6f}" if eclipse.central_lat is not None else "N/A",
            "has_path": bool(eclipse.path_geojson) and eclipse.eclipse_type == 'solar',
            "sutak_start": eclipse.sutak_end,
            "sutak_end" : eclipse.sutak_end
        })
    
    return Response({"eclipses": eclipse_list})

@api_view(['GET'])
def eclipse_detail(request, eclipse_id):
    """Get eclipse details in user's current timezone"""
    try:
        eclipse = Eclipse.objects.get(id=eclipse_id)
        
        # Get user's settings
        if request.user.is_authenticated:
            user_profile = UserSettingsManager.get_user_settings(request.user)
            user_tz = pytz.timezone(user_profile.current_timezone)
            location_info = {
                'city': user_profile.current_city,
                'timezone': user_profile.current_timezone,
                'coordinates': f"{user_profile.current_latitude}, {user_profile.current_longitude}"
            }
        else:
            # Default for anonymous users
            user_tz = pytz.timezone('Asia/Kolkata')
            location_info = {
                'city': 'New Delhi',
                'timezone': 'Asia/Kolkata',
                'coordinates': '28.6139, 77.2090'
            }
        
        # Convert dates to user's timezone
        def convert_to_user_time(utc_dt):
            if not utc_dt:
                return None
            try:
                if utc_dt.tzinfo is None:
                    utc_dt = pytz.utc.localize(utc_dt)
                local_dt = utc_dt.astimezone(user_tz)
                return local_dt.strftime("%Y-%m-%d %H:%M:%S")
            except Exception as e:
                return utc_dt.strftime("%Y-%m-%d %H:%M:%S") if utc_dt else None
        
        response_data = {
            "id": eclipse.id,
            "type": eclipse.eclipse_type,
            "date_max": convert_to_user_time(eclipse.date_max),
            "date_start": convert_to_user_time(eclipse.date_start),
            "date_end": convert_to_user_time(eclipse.date_end),
            "magnitude": eclipse.magnitude,
            "subtype": eclipse.subtype,
            "central_latitude": eclipse.central_lat,
            "central_longitude": eclipse.central_lon,
            "sutak_start": convert_to_user_time(eclipse.sutak_start),
            "sutak_end": convert_to_user_time(eclipse.sutak_end),
            "path_geojson": eclipse.path_geojson,
            "user_location": location_info
        }
        
        return Response(response_data)
    except Eclipse.DoesNotExist:
        return Response({"error": "Eclipse not found"}, status=404)

def eclipse_path_visualization(request, eclipse_id):
    """Enhanced eclipse path visualization"""
    try:
        eclipse = get_object_or_404(Eclipse, id=eclipse_id)
        
        # Debug: Check JD value
        print(f"JD Value: {eclipse.jd_max}")
        
        # Check if JD value is reasonable (should be > 2,400,000 for modern dates)
        if eclipse.jd_max and eclipse.jd_max < 100000:
            return HttpResponse(f"Invalid JD value: {eclipse.jd_max}. Expected value around 2,460,000+", status=500)
        
        # Regenerate path data with enhanced function
        from .eclipse_utils import generate_solar_eclipse_path, jd_to_datetime
        enhanced_path = generate_solar_eclipse_path(eclipse.jd_max)
        
        # Update the eclipse record with enhanced path
        eclipse.path_geojson = enhanced_path
        eclipse.save()
        
        # Safe date formatting with None check
        eclipse_date = "Date not available"
        if eclipse.date_max:
            eclipse_date = eclipse.date_max.strftime("%Y-%m-%d %H:%M:%S UTC")
        
        context = {
            'eclipse': eclipse,
            'path_json': json.dumps(enhanced_path),
            'central_lat': eclipse.central_lat or 0,
            'central_lon': eclipse.central_lon or 0,
            'eclipse_date': eclipse_date,  # Use the safely formatted date
            'magnitude': eclipse.magnitude or 0,
        }
        
        return render(request, 'eclipse_path_enhanced.html', context)
        
    except Exception as e:
        return HttpResponse(f"Error loading eclipse visualization: {e}", status=500)
    
# Keep your existing functions for backward compatibility if needed
@api_view(['GET'])
def upcoming_eclipses(request):
    """Get upcoming eclipses for the next year"""
    today = datetime.now()
    next_year = today + timedelta(days=365)
    
    jd_start = swe.julday(today.year, today.month, today.day, today.hour)
    jd_end = swe.julday(next_year.year, next_year.month, next_year.day, next_year.hour)
    
    eclipses = []
    jd = jd_start
    
    while jd < jd_end:
        # Check for solar eclipses
        solar = compute_solar_eclipse(jd)
        if solar:
            eclipses.append({
                'type': 'solar',
                'date': jd_to_datetime(solar['jd']).strftime('%Y-%m-%d'),
                'subtype': solar['subtype'],
                'magnitude': solar['magnitude']
            })
            jd = solar['jd'] + 30  # Skip ahead
        
        # Check for lunar eclipses
        lunar = compute_lunar_eclipse(jd)
        if lunar:
            eclipses.append({
                'type': 'lunar',
                'date': jd_to_datetime(lunar['jd']).strftime('%Y-%m-%d'),
                'subtype': lunar['subtype'],
                'magnitude': lunar['magnitude']
            })
            jd = lunar['jd'] + 30  # Skip ahead
        
        jd += 15  # Check every 15 days
    
    return Response({'eclipses': eclipses})

@api_view(['GET'])
def eclipse_detail_by_date(request, year, month, day):
    """Get detailed information about a specific eclipse by date"""
    jd = swe.julday(year, month, day, 12)  # Noon on the specified day
    
    # Check for solar eclipse first
    eclipse_data = compute_solar_eclipse(jd)
    eclipse_type = 'solar'
    
    if not eclipse_data:
        eclipse_data = compute_lunar_eclipse(jd)
        eclipse_type = 'lunar'
    
    if not eclipse_data:
        return Response({'error': 'No eclipse found on this date'}, status=404)
    
    # Generate path and sutak times
    from .eclipse_utils import generate_eclipse_path, get_sutak_times
    path_data = generate_eclipse_path(eclipse_data['jd'], eclipse_type)
    sutak_times = get_sutak_times(eclipse_type, eclipse_data['jd'])
    
    result = {
        'type': eclipse_type,
        'subtype': eclipse_data['subtype'],
        'magnitude': eclipse_data['magnitude'],
        'max_eclipse_time': jd_to_datetime(eclipse_data['jd']).isoformat(),
        'sutak_times': sutak_times,
        'path_data': path_data
    }
    
    return Response(result)
# Remove the old upcoming_eclipses and eclipse_detail functions since they're redundant

def jd_to_datetime(jd):
    """Convert Julian Day to datetime"""
    return datetime(2000, 1, 1) + timedelta(days=jd - 2451545.0)

@api_view(['POST'])
def cleanup_eclipse_data(request):
    """Clean up invalid eclipse entries"""
    # Delete eclipses with null dates
    invalid_eclipses = Eclipse.objects.filter(date_max__isnull=True)
    count_deleted = invalid_eclipses.count()
    invalid_eclipses.delete()
    
    # Fix lunar eclipse paths
    lunar_eclipses = Eclipse.objects.filter(eclipse_type='lunar')
    for eclipse in lunar_eclipses:
        eclipse.path_geojson = None
        eclipse.central_lat = None
        eclipse.central_lon = None
        eclipse.save()
    
    return Response({
        "status": "success",
        "deleted_invalid": count_deleted,
        "fixed_lunar_eclipses": lunar_eclipses.count()
    })

# In views_eclipse.py
@api_view(['GET'])
def debug_database_eclipses(request):
    """Debug endpoint to see what's actually in the database"""
    eclipses = Eclipse.objects.all().order_by('id')
    
    debug_list = []
    for eclipse in eclipses:
        debug_list.append({
            "id": eclipse.id,
            "type": eclipse.eclipse_type,
            "date_max": str(eclipse.date_max),  # Raw date_max value
            "date_max_is_null": eclipse.date_max is None,
            "jd_max": eclipse.jd_max,
            "magnitude": eclipse.magnitude,
            "subtype": eclipse.subtype,
        })
    
    return Response({"eclipses": debug_list})