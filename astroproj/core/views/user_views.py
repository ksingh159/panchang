# core/views/user_views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.crypto import get_random_string
from django.contrib.auth import login, authenticate
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.conf import settings
import requests
import json
from geopy.geocoders import Nominatim
from ..models import UserProfile, Kundali


# ---------------------
# Authentication Views
# ---------------------

def register(request):
    """
    Handle user registration with location preferences
    """
    if request.method == 'POST':
        try:
            # Get form data
            full_name = request.POST.get('full_name', '').strip()
            email = request.POST.get('email', '').strip()
            password1 = request.POST.get('password1')
            password2 = request.POST.get('password2')
            city = request.POST.get('city', 'Mumbai')
            latitude = request.POST.get('latitude', 19.0760)
            longitude = request.POST.get('longitude', 72.8777)
            
            # Validation
            if not all([full_name, email, password1, password2]):
                messages.error(request, 'All fields are required')
                return render(request, 'registration/register.html')
            
            if password1 != password2:
                messages.error(request, 'Passwords do not match')
                return render(request, 'registration/register.html')
            
            if User.objects.filter(email=email).exists():
                messages.error(request, 'Email already exists')
                return render(request, 'registration/register.html')
            
            # Create user
            username = email.split('@')[0] + str(User.objects.count() + 1)
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1,
                first_name=full_name
            )
            
            # FIX: Handle profile creation safely
            try:
                # Check if profile already exists (shouldn't, but just in case)
                profile = UserProfile.objects.get(user=user)
                # Update existing profile
                profile.city = city
                profile.latitude = float(latitude)
                profile.longitude = float(longitude)
                profile.save()
            except UserProfile.DoesNotExist:
                # Create new profile
                profile = UserProfile.objects.create(
                    user=user,
                    city=city,
                    latitude=float(latitude),
                    longitude=float(longitude)
                )
            except UserProfile.MultipleObjectsReturned:
                # Handle multiple profiles - use first and delete others
                profiles = UserProfile.objects.filter(user=user)
                profile = profiles.first()
                profile.city = city
                profile.latitude = float(latitude)
                profile.longitude = float(longitude)
                profile.save()
                # Delete duplicates
                profiles.exclude(id=profile.id).delete()
            
            # Log the user in
            user = authenticate(request, username=username, password=password1)
            if user is not None:
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                messages.success(request, f'Welcome to Vedic Astro, {full_name}!')
                return redirect('home')
            else:
                messages.error(request, 'Login failed after registration')
                return redirect('login')
            
        except Exception as e:
            messages.error(request, f'Registration failed: {str(e)}')
            return render(request, 'registration/register.html')
    
    # GET request - show registration form
    return render(request, 'registration/register.html')


# ---------------------
# Profile & Settings Views
# ---------------------

def get_user_country_from_ip(request):
    """Get user's country based on IP address"""
    try:
        # Get client IP
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        
        # For local development, use a default (India)
        if ip in ['127.0.0.1', 'localhost']:
            return 'IN'  # Default to India for local development
        
        # Use ipapi.co (free tier available) or ipinfo.io
        response = requests.get(f'http://ip-api.com/json/{ip}?fields=countryCode')
        data = response.json()
        
        return data.get('countryCode', 'IN')  # Default to India if fails
        
    except Exception as e:
        print(f"IP geolocation error: {e}")
        return 'IN'  # Default to India

@login_required
def profile(request):
    """User profile with location editing"""
    popular_cities = [
        {'name': 'Mumbai', 'state': 'Maharashtra', 'lat': 19.0760, 'lon': 72.8777},
        {'name': 'Delhi', 'state': 'Delhi', 'lat': 28.6139, 'lon': 77.2090},
        {'name': 'Bangalore', 'state': 'Karnataka', 'lat': 12.9716, 'lon': 77.5946},
        {'name': 'Hyderabad', 'state': 'Telangana', 'lat': 17.3850, 'lon': 78.4867},
        {'name': 'Chennai', 'state': 'Tamil Nadu', 'lat': 13.0827, 'lon': 80.2707},
        {'name': 'Kolkata', 'state': 'West Bengal', 'lat': 22.5726, 'lon': 88.3639},
        {'name': 'Pune', 'state': 'Maharashtra', 'lat': 18.5204, 'lon': 73.8567},
        {'name': 'Ahmedabad', 'state': 'Gujarat', 'lat': 23.0225, 'lon': 72.5714},
        {'name': 'Jaipur', 'state': 'Rajasthan', 'lat': 26.9124, 'lon': 75.7873},
        {'name': 'Lucknow', 'state': 'Uttar Pradesh', 'lat': 26.8467, 'lon': 80.9462},
    ]
    
    # Ensure profile exists
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # Handle POST request (location update)
    if request.method == 'POST':
        try:
            city = request.POST.get('city')
            latitude = request.POST.get('latitude')
            longitude = request.POST.get('longitude')
            
            # Validate data
            if not all([city, latitude, longitude]):
                messages.error(request, 'All fields are required.')
                return redirect('profile')
            
            # Update profile
            profile.city = city
            profile.latitude = float(latitude)
            profile.longitude = float(longitude)
            profile.save()
            
            messages.success(request, 'Location preferences updated successfully!')
            return redirect('profile')
            
        except Exception as e:
            messages.error(request, f'Error updating location: {str(e)}')
    
    return render(request, 'registration/profile.html', {
        'popular_cities': popular_cities
    })

@login_required
def update_birth_details(request):
    """Update user's birth details - safe handling"""
    if request.method == 'POST':
        try:
            profile = request.user.profile
            
            # Get form data with safe defaults
            birth_date = request.POST.get('birth_date') or None
            birth_time = request.POST.get('birth_time') or None
            birth_city = request.POST.get('birth_city', '').strip()
            birth_latitude = request.POST.get('birth_latitude')
            birth_longitude = request.POST.get('birth_longitude')
            
            # Update profile safely
            profile.birth_date = birth_date
            profile.birth_time = birth_time
            profile.birth_place = birth_city
            
            # Handle latitude/longitude conversion safely
            try:
                profile.birth_latitude = float(birth_latitude) if birth_latitude else None
            except (TypeError, ValueError):
                profile.birth_latitude = None
                
            try:
                profile.birth_longitude = float(birth_longitude) if birth_longitude else None
            except (TypeError, ValueError):
                profile.birth_longitude = None
            
            profile.save()
            
            messages.success(request, 'Birth details updated successfully!')
            
        except Exception as e:
            messages.error(request, f'Error updating birth details: {str(e)}')
    
    return redirect('profile')

# views.py
@login_required
def city_autocomplete(request):
    """API endpoint for city autocomplete with country-based priority"""
    query = request.GET.get('q', '').strip().lower()
    
    if len(query) < 2:
        return JsonResponse({'suggestions': []})
    
    try:
        user_country = get_user_country_from_ip(request)
        geolocator = Nominatim(user_agent="vedic_astro_app")
        
        # Search with country bias
        country_biased_query = f"{query}, {user_country}"
        locations = geolocator.geocode(country_biased_query, exactly_one=False, limit=10)
        
        suggestions = []
        
        if locations:
            for location in locations:
                if location.address:
                    location_country = get_country_from_address(location.address)
                    is_user_country = location_country == user_country
                    
                    suggestions.append({
                        'name': format_city_display_name(location.address),
                        'full_address': location.address,
                        'lat': location.latitude,
                        'lon': location.longitude,
                        'country': location_country,
                        'priority': 1 if is_user_country else 0  # Only change: set priority based on country
                    })
        
        # Only sort by priority (user's country first) - NO duplicate removal
        suggestions.sort(key=lambda x: x['priority'], reverse=True)
        
        # Limit to 5 results (keeping all including duplicates)
        suggestions = suggestions[:5]
        
        return JsonResponse({'suggestions': suggestions, 'user_country': user_country})
    
    except Exception as e:
        return JsonResponse({'suggestions': [], 'error': str(e)})

def extract_city_name(address):
    """Extract the main city name from address"""
    parts = address.split(',')
    if parts:
        return parts[0].strip().lower()
    return address.lower()

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

# Removed: create_unique_city_key function
# Removed: remove_duplicate_suggestions function  
# Removed: are_similar_cities function
#   
def get_country_from_address(address):
    """Extract country code from address string"""
    address_parts = address.split(',')
    if len(address_parts) > 0:
        last_part = address_parts[-1].strip().upper()
        
        # Simple country mapping (you can expand this)
        country_map = {
            'INDIA': 'IN',
            'UNITED STATES': 'US',
            'UNITED KINGDOM': 'GB',
            'BANGLADESH': 'BD',
            'PAKISTAN': 'PK',
            'NEPAL': 'NP',
            'SRILANKA': 'LK',
            'SRI LANKA': 'LK'
        }
        
        for country_name, code in country_map.items():
            if country_name in last_part:
                return code
        
        # If no match, return the last part (might be country name)
        return last_part[:2] if len(last_part) == 2 else 'Unknown'
    
    return 'Unknown'

@login_required
def update_location(request):
    """Update user's current location"""
    if request.method == 'POST':
        try:
            profile = request.user.profile
            
            # Get form data
            city = request.POST.get('city')
            latitude = request.POST.get('latitude')
            longitude = request.POST.get('longitude')
            
            # Update profile
            if city:
                profile.city = city
            if latitude:
                profile.latitude = float(latitude)
            if longitude:
                profile.longitude = float(longitude)
            
            profile.save()
            
            messages.success(request, 'Location preferences updated successfully!')
            
        except Exception as e:
            messages.error(request, f'Error updating location: {str(e)}')
    
    return redirect('profile')

@login_required
def debug_profile(request):
    """Debug view to check profile data"""
    profile = request.user.profile
    return JsonResponse({
        'username': request.user.username,
        'profile_exists': hasattr(request.user, 'profile'),
        'city': profile.city,
        'latitude': profile.latitude,
        'longitude': profile.longitude,
        'timezone': profile.timezone,
    })

def save_location_preferences(request):
    """Save location preferences for anonymous users"""
    if request.method == 'POST':
        try:
            if request.user.is_authenticated:
                messages.info(request, 'Please update your location in your profile page.')
                return redirect('profile')
            
            # For anonymous users, save to session
            city = request.POST.get('city')
            lat = request.POST.get('latitude')
            lon = request.POST.get('longitude')
            
            if city and lat and lon:
                request.session['city'] = city
                request.session['lat'] = float(lat)
                request.session['lon'] = float(lon)
                request.session['timezone'] = 'Asia/Kolkata'
                request.session.set_expiry(30 * 24 * 60 * 60)
                messages.success(request, 'Location preferences saved for this session!')
            else:
                messages.error(request, 'Please fill all location fields.')
                
        except Exception as e:
            messages.error(request, f'Error saving location: {str(e)}')
    
    return redirect('home')


# ---------------------
# Kundali Management Views
# ---------------------

@login_required
def kundali_list(request):
    """Display list of user's saved kundalis"""
    user_kundalis = Kundali.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'user_kundalis': user_kundalis,
    }
    return render(request, 'kundali/detail.html', context)

@login_required
def create_kundali(request):
    return render(request, 'create_kundali.html')