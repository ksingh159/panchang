# core/views/user_views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.crypto import get_random_string
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.conf import settings
import requests
import json
from ..models import UserProfile, Kundali
from ..utils.geo import city_to_dict, resolve_place, search_cities, timezone_for
import logging

logger = logging.getLogger(__name__)


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
            
            if User.objects.filter(email__iexact=email).exists():
                messages.error(request, 'An account with this email already exists. Please sign in instead.')
                return render(request, 'registration/register.html')

            try:
                validate_password(password1, user=User(email=email, first_name=full_name))
            except ValidationError as err:
                for msg in err.messages:
                    messages.error(request, msg)
                return render(request, 'registration/register.html')
            
            # Create user. People sign in with their email; the username is internal only, so it just has to be
            # unique (a count-based suffix collided once an account was deleted).
            username = _unique_username(email)
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
                messages.success(request, f'Welcome to {settings.SITE_NAME}, {full_name}!')
                return redirect('home')
            else:
                messages.error(request, 'Login failed after registration')
                return redirect('login')
            
        except Exception:
            logger.exception("Registration failed")
            messages.error(request, 'Registration failed. Please check your details and try again.')
            return render(request, 'registration/register.html')

    # GET request - show registration form
    return render(request, 'registration/register.html')


def _unique_username(email):
    base = (email.split('@')[0] or 'user')[:30]
    username = base
    while User.objects.filter(username=username).exists():
        username = f"{base}-{get_random_string(6).lower()}"
    return username


def bump(key, timeout):
    """Add 1 to a counter that expires ``timeout`` seconds after its last bump; returns the new count.
    The timeout is always set here: Django's database cache gives an incr()-ed key the 6-hour default instead."""
    from django.core.cache import cache
    if cache.add(key, 1, timeout):
        return 1
    try:
        count = cache.incr(key)
    except ValueError:
        cache.set(key, 1, timeout)
        return 1
    cache.touch(key, timeout)
    return count


def _throttled(request, scope, limit, window=60):
    """True once this IP has made more than ``limit`` calls to ``scope`` in the current ``window``-second slot."""
    import time
    slot = int(time.time() // window)
    return bump(f"throttle:{scope}:{client_ip(request)}:{slot}", window) > limit


def rate_limit(scope, limit, window=60, methods=('POST',)):
    """Decorator: answer 429 once one IP has made ``limit`` calls to ``scope`` within ``window`` seconds.
    For the endpoints that do heavy astronomy for anonymous visitors, so a script cannot tie up the server."""
    from functools import wraps

    def deco(view):
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            if request.method in methods and _throttled(request, scope, limit, window):
                return JsonResponse({'error': 'Too many requests. Please wait a minute and try again.'}, status=429)
            return view(request, *args, **kwargs)
        return wrapped
    return deco


def client_ip(request):
    """The visitor's IP for rate limits. Each proxy (Railway, Cloudflare) appends the address it saw to
    X-Forwarded-For, so with NUM_PROXIES in front the real client is NUM_PROXIES from the right. Entries further left
    were written by the client and can be forged, so they are never used."""
    hops = settings.NUM_PROXIES
    fwd = [x.strip() for x in request.META.get('HTTP_X_FORWARDED_FOR', '').split(',') if x.strip()]
    if hops and len(fwd) >= hops:
        return fwd[-hops]
    return request.META.get('REMOTE_ADDR', '')


def check_email(request):
    """Live check on the sign-up form: is this email free? Throttled so it cannot be used to list accounts."""
    email = request.GET.get('email', '').strip()
    if _throttled(request, 'check_email', limit=30):
        return JsonResponse({'error': 'Too many checks, please wait a minute.'}, status=429)
    try:
        validate_email(email)
    except ValidationError:
        return JsonResponse({'valid': False, 'available': False})
    return JsonResponse({'valid': True, 'available': not User.objects.filter(email__iexact=email).exists()})


@login_required
@require_POST
def delete_account(request):
    """The user deletes their own account: profile, birth details and kundalis go with it (CASCADE).
    Purchases are kept for the sales record with the user link cleared (SET_NULL); their saved PDFs are deleted."""
    user = request.user
    if request.POST.get('confirm', '').strip() != 'DELETE':
        messages.error(request, 'Type DELETE in the box to confirm.')
        return redirect('profile')
    if user.has_usable_password() and not user.check_password(request.POST.get('password', '')):
        messages.error(request, 'That password is not correct.')
        return redirect('profile')
    from ..models import Purchase
    from ..utils import pdf_store
    for purchase in Purchase.objects.filter(user=user):
        pdf_store.forget(purchase)
    Purchase.objects.filter(user=user).update(session_key='')
    logout(request)
    user.delete()
    messages.success(request, 'Your account and all your saved data have been deleted.')
    return redirect('home')


# ---------------------
# Profile & Settings Views
# ---------------------

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
    
    from ..utils import prefs
    from ..utils.aahaar_foods import REGIONS
    return render(request, 'registration/profile.html', {
        'popular_cities': popular_cities,
        'regions': [(r["key"], r["name"][0]) for r in REGIONS], 'month_systems': prefs.MONTH_SYSTEMS,
        'states': prefs.STATES,
        'auto_region': prefs.food_region(request, profile.city, profile.latitude, profile.longitude),
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
            name, lat, lon, tz = _place_from_post(
                request.POST, 'birth_city', 'birth_latitude', 'birth_longitude', 'birth_place_id')

            profile.birth_date = birth_date
            profile.birth_time = birth_time
            profile.birth_place = name[:100]
            profile.birth_latitude = lat
            profile.birth_longitude = lon
            if tz:
                profile.birth_timezone = tz

            profile.save()
            
            messages.success(request, 'Birth details updated successfully!')
            
        except Exception as e:
            messages.error(request, f'Error updating birth details: {str(e)}')
    
    return redirect('profile')

# views.py
def city_autocomplete(request):
    """Place suggestions from the offline GeoNames gazetteer: short names + IANA timezone."""
    query = request.GET.get('q', '').strip()
    prefer = request.GET.get('country', 'IN').upper()[:2]
    try:
        limit = max(1, min(int(request.GET.get('limit', 8)), 20))
    except ValueError:
        limit = 8
    cities = search_cities(query[:80], limit=limit, prefer_country=prefer)
    return JsonResponse({'suggestions': [city_to_dict(c) for c in cities], 'user_country': prefer})


def _place_from_post(post, name_key, lat_key, lon_key, id_key):
    """(name, lat, lon, timezone) from a submitted place, trusting coordinates if given."""
    name = (post.get(name_key) or '').strip()
    hit = resolve_place(name, geoname_id=post.get(id_key) or None) if (name or post.get(id_key)) else None
    lat, lon = post.get(lat_key), post.get(lon_key)
    if lat and lon:
        lat, lon = float(lat), float(lon)
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):   # also rejects nan / inf
            raise ValueError('Latitude must be between -90 and 90 and longitude between -180 and 180.')
        if hit and (abs(hit['lat'] - lat) > 0.2 or abs(hit['lon'] - lon) > 0.2):
            hit = None  # user typed custom coordinates; keep their name, derive tz from coords
    elif hit:
        lat, lon = hit['lat'], hit['lon']
    else:
        return name, None, None, None
    tz = hit['timezone'] if hit else timezone_for(lat, lon)
    return (hit['name'] if hit else name), lat, lon, tz


@login_required
def update_location(request):
    """Update user's current location"""
    if request.method == 'POST':
        try:
            profile = request.user.profile
            
            name, lat, lon, tz = _place_from_post(request.POST, 'city', 'latitude', 'longitude', 'place_id')
            if lat is None:
                raise ValueError('Please pick a city from the suggestions or enter coordinates.')
            profile.city = name[:100]
            profile.latitude = lat
            profile.longitude = lon
            profile.timezone = tz

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
            city, lat, lon, tz = _place_from_post(request.POST, 'city', 'latitude', 'longitude', 'place_id')

            if city and lat is not None:
                request.session['city'] = city
                request.session['lat'] = lat
                request.session['lon'] = lon
                request.session['timezone'] = tz
                request.session.set_expiry(30 * 24 * 60 * 60)
                messages.success(request, 'Location preferences saved for this session!')
            else:
                messages.error(request, 'Please fill all location fields.')
                
        except Exception as e:
            messages.error(request, f'Error saving location: {str(e)}')
    
    return redirect('panchang')


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
    return render(request, 'kundali/list.html', context)

@login_required
def create_kundali(request):
    return render(request, 'create_kundali.html')

def save_preferences(request):
    """POST: native state, aahaar region and month system. Works signed in (profile) or as a visitor (session)."""
    from django.utils.http import url_has_allowed_host_and_scheme
    from ..utils import prefs
    nxt = request.POST.get("next") or request.GET.get("next") or "/"
    if not url_has_allowed_host_and_scheme(nxt, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        nxt = "/"
    if request.method == "POST":
        prefs.save(request, **{k: request.POST[k] for k in prefs.FIELDS if k in request.POST})
        messages.success(request, "Preferences saved.")
    return redirect(nxt)


from django.contrib.auth.views import LoginView


class ThrottledLoginView(LoginView):
    """Django's login with a brake on password guessing: after 10 failed tries from one IP, or for one email,
    sign-in is refused for 15 minutes. Successful sign-ins do not count."""
    WINDOW, LIMIT = 15 * 60, 10

    def _keys(self):
        who = (self.request.POST.get('username') or '').strip().lower()[:254]
        return [f"throttle:login-ip:{client_ip(self.request)}"] + ([f"throttle:login-user:{who}"] if who else [])

    def post(self, request, *args, **kwargs):
        from django.core.cache import cache
        if any((cache.get(k) or 0) >= self.LIMIT for k in self._keys()):
            form = self.get_form()
            form.add_error(None, 'Too many sign-in attempts. Please wait 15 minutes and try again.')
            return self.render_to_response(self.get_context_data(form=form), status=429)
        return super().post(request, *args, **kwargs)

    def form_invalid(self, form):
        for k in self._keys():
            bump(k, self.WINDOW)        # locked until 15 minutes after the last failed try
        return super().form_invalid(form)
