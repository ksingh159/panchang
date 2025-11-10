# core/views/page_views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from datetime import datetime
import pytz

from ..utils.astro_calculations import get_panchang
from ..models import UserProfile



def panchang_datetime_html(request, year, month, day, hour, minute,lat,lon,city):
    """Render panchang data in HTML format"""
    try:
        # Get location preferences
        if request.user.is_authenticated:
            profile = getattr(request.user, 'profile', None)
            lat = float(request.GET.get('lat', profile.latitude if profile else 19.0760))
            lon = float(request.GET.get('lon', profile.longitude if profile else 72.8777))
            timezone_str = request.GET.get('tz', profile.timezone if profile else 'Asia/Kolkata')
            city_name = request.GET.get('city', profile.city if profile else 'Mumbai')
        else:
            lat = float(request.GET.get('lat', request.session.get('lat', 19.0760)))
            lon = float(request.GET.get('lon', request.session.get('lon', 72.8777)))
            timezone_str = request.GET.get('tz', request.session.get('timezone', 'Asia/Kolkata'))
            city_name = request.GET.get('city', request.session.get('city', 'Mumbai'))
        
        try:
            tz = pytz.timezone(timezone_str)
        except:
            tz = pytz.timezone('Asia/Kolkata')
        
        target_datetime = datetime(year, month, day, hour, minute)
        target_datetime = tz.localize(target_datetime)
        
        panchang_data = get_panchang(
            target_date=target_datetime,
            user=request.user if request.user.is_authenticated else None,
            lat=lat,
            lon=lon,
            timezone_str=timezone_str,
            city_name=city_name
        )
        
        context = {
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
            'amanta_month': panchang_data.get('amanta_month', 'N/A'),
            'purnimanta_month': panchang_data.get('purnimanta_month', 'N/A'),
            'ritu': panchang_data.get('ritu', 'N/A'),
            'city': city_name,
            'coordinates': f"{lat:.4f}, {lon:.4f}",
            'timezone': timezone_str,
            'planetary_positions': panchang_data.get('planetary_positions', {}),
            'target_datetime': target_datetime.strftime("%B %d, %Y %I:%M %p"),
        }
        
        return render(request, 'home.html', context)
        
    except Exception as e:
        context = {
            'error': f"Error: {str(e)}",
            'target_datetime': f"{year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}",
            'city': city_name,
            'coordinates': f"{lat:.4f}, {lon:.4f}",
            'timezone': timezone_str,
        }
        return render(request, 'home.html', context)

def panchang_view(request):
    return redirect('home')

def about(request):
    return render(request, 'static_pages/about.html')

def how_it_works(request):
    return render(request, 'static_pages/how_it_works.html')

def faq(request):
    return render(request, 'static_pages/faq.html')

def blog(request):
    return render(request, 'static_pages/blog.html')

def privacy(request):
    return render(request, 'static_pages/privacy.html')

def terms(request):
    return render(request, 'static_pages/terms.html')

def about_view(request):
    return render(request, 'about.html')

def contact_view(request):
    return render(request, 'contact.html')

def panchang(request):
    # Panchang data logic
    return render(request, 'panchang2.html')