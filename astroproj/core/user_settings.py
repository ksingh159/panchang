# core/user_settings.py
import pytz
from timezonefinderL import TimezoneFinder
from geopy.geocoders import Nominatim
import logging

logger = logging.getLogger(__name__)

class UserSettingsManager:
    """Manager for user astrological settings"""
    
    @staticmethod
    def get_user_settings(user):
        """Get or create user settings"""
        from .models import UserProfile
        
        profile, created = UserProfile.objects.get_or_create(user=user)
        return profile
    
    @staticmethod
    def update_location(user, city_name=None, lat=None, lon=None, address=None):
        """Update user's current location"""
        profile = UserSettingsManager.get_user_settings(user)
        
        if city_name:
            # Geocode city to get coordinates
            coords = UserSettingsManager.geocode_location(city_name)
            if coords:
                lat, lon, timezone = coords
                profile.current_city = city_name
                profile.current_latitude = lat
                profile.current_longitude = lon
                profile.current_timezone = timezone
        elif lat is not None and lon is not None:
            # Use provided coordinates
            timezone = UserSettingsManager.get_timezone(lat, lon)
            profile.current_latitude = lat
            profile.current_longitude = lon
            profile.current_timezone = timezone
            profile.current_city = address or f"{lat:.4f}, {lon:.4f}"
        
        profile.save()
        return profile
    
    @staticmethod
    def geocode_location(location_name):
        """Geocode location name to coordinates and timezone"""
        try:
            geolocator = Nominatim(user_agent="vedic_astro_app")
            location = geolocator.geocode(location_name)
            if location:
                tf = TimezoneFinder()
                timezone_name = tf.timezone_at(lat=location.latitude, lng=location.longitude)
                return (location.latitude, location.longitude, timezone_name or 'UTC')
        except Exception as e:
            logger.error(f"Geocoding error: {e}")
        return None
    
    @staticmethod
    def get_timezone(lat, lon):
        """Get timezone from coordinates"""
        try:
            tf = TimezoneFinder()
            return tf.timezone_at(lat=lat, lng=lon) or 'UTC'
        except:
            return 'UTC'
    
    @staticmethod
    def update_preferences(user, preferences_dict):
        """Update user preferences"""
        profile = UserSettingsManager.get_user_settings(user)
        
        # Update notification preferences
        notifications = preferences_dict.get('notifications', {})
        profile.notify_eclipses = notifications.get('eclipses', profile.notify_eclipses)
        profile.notify_muhurats = notifications.get('muhurats', profile.notify_muhurats)
        profile.notify_tithis = notifications.get('tithis', profile.notify_tithis)
        profile.notify_personal = notifications.get('personal', profile.notify_personal)
        
        # Update display preferences
        display = preferences_dict.get('display', {})
        profile.language = display.get('language', profile.language)
        profile.date_format = display.get('date_format', profile.date_format)
        profile.time_format = display.get('time_format', profile.time_format)
        
        # Update kundali preferences
        kundali = preferences_dict.get('kundali', {})
        profile.kundali_style = kundali.get('style', profile.kundali_style)
        profile.show_planets = kundali.get('show_planets', profile.show_planets)
        profile.dasha_system = kundali.get('dasha_system', profile.dasha_system)
        
        profile.save()
        return profile
    