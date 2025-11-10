from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import datetime
import pytz

# Add UserProfile model at the TOP
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Birth details for personalization (optional fields)
    birth_date = models.DateField(null=True, blank=True, help_text="User's birth date")
    birth_time = models.TimeField(null=True, blank=True, help_text="User's birth time")
    birth_place = models.CharField(max_length=100, blank=True, help_text="City of birth")
    birth_latitude = models.FloatField(null=True, blank=True, help_text="Birth location latitude")
    birth_longitude = models.FloatField(null=True, blank=True, help_text="Birth location longitude")
    birth_timezone = models.CharField(max_length=50, default='Asia/Kolkata', help_text="Timezone at birth place")
    
    # Current location preferences
    city = models.CharField(max_length=100, default='Mumbai')
    state = models.CharField(max_length=100, default='Maharashtra', blank=True)
    country = models.CharField(max_length=100, default='India', blank=True)
    latitude = models.FloatField(default=19.0760)
    longitude = models.FloatField(default=72.8777)
    timezone = models.CharField(max_length=50, default='Asia/Kolkata')
    
    # Astro preferences
    calculation_method = models.CharField(max_length=50, default='Lahiri')
    language = models.CharField(max_length=10, default='en')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

    @property
    def has_birth_details(self):
        """Check if user has complete birth details for personalization"""
        return all([
            self.birth_date is not None, 
            self.birth_time is not None, 
            self.birth_latitude is not None, 
            self.birth_longitude is not None
        ])

    def save(self, *args, **kwargs):
        # Ensure we have default values
        if not self.city:
            self.city = 'Mumbai'
        if not self.latitude:
            self.latitude = 19.0760
        if not self.longitude:
            self.longitude = 72.8777
        if not self.timezone:
            self.timezone = 'Asia/Kolkata'
        if not self.birth_timezone:
            self.birth_timezone = 'Asia/Kolkata'
            
        super().save(*args, **kwargs)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()

class Eclipse(models.Model):
    ECLIPSE_TYPES = [
        ('solar', 'Solar'),
        ('lunar', 'Lunar'),
    ]
    
    eclipse_type = models.CharField(max_length=10, choices=ECLIPSE_TYPES, default='solar')
    jd_max = models.FloatField(default=0.0)  # Julian Day of maximum eclipse
    date_max = models.DateTimeField(null=True, blank=True)
    date_start = models.DateTimeField(null=True, blank=True)
    date_end = models.DateTimeField(null=True, blank=True)
    magnitude = models.FloatField(default=0.0)
    subtype = models.CharField(max_length=20, default='', blank=True)  # Now can store 'partial', 'total', etc.
    umbral_magnitude = models.FloatField(null=True, blank=True)
    penumbral_magnitude = models.FloatField(null=True, blank=True)
    gamma = models.FloatField(null=True, blank=True)
    central_lat = models.FloatField(null=True, blank=True)
    central_lon = models.FloatField(null=True, blank=True)
    path_geojson = models.JSONField(null=True, blank=True)
    sutak_start = models.DateTimeField(null=True, blank=True)
    sutak_end = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['date_max']
    
    def __str__(self):
        date_str = self.date_max.strftime('%Y-%m-%d') if self.date_max else 'Unknown Date'
        return f"{self.get_eclipse_type_display()} Eclipse - {date_str}"
    
    def save(self, *args, **kwargs):
        # Ensure all datetime fields are timezone-aware
        for field in ['date_max', 'date_start', 'date_end', 'sutak_start', 'sutak_end']:
            value = getattr(self, field)
            if value and timezone.is_naive(value):
                setattr(self, field, timezone.make_aware(value))
        
        super().save(*args, **kwargs)
    
    def has_path(self):
        """Determine if eclipse has a visible path"""
        if self.eclipse_type == 'lunar':
            return False  # Lunar eclipses typically don't have geographic paths
        return bool(self.path_geojson) and self.central_lat is not None and self.central_lon is not None
    
    def get_central_coords(self):
        """Get formatted central coordinates"""
        if self.central_lat is not None and self.central_lon is not None:
            return f"{self.central_lat:.6f}, {self.central_lon:.6f}"
        return "N/A"
    
    def is_solar_eclipse(self):
        """Check if this is a solar eclipse"""
        return self.eclipse_type == 'solar'
    
    def is_lunar_eclipse(self):
        """Check if this is a lunar eclipse"""
        return self.eclipse_type == 'lunar'
    
    def get_eclipse_details(self):
        """Get comprehensive eclipse details as dictionary"""
        return {
            'id': self.id,
            'type': self.eclipse_type,
            'date_max': self.date_max.isoformat() if self.date_max else None,
            'date_start': self.date_start.isoformat() if self.date_start else None,
            'date_end': self.date_end.isoformat() if self.date_end else None,
            'magnitude': self.magnitude,
            'subtype': self.subtype,
            'central_coords': self.get_central_coords(),
            'has_path': self.has_path(),
            'sutak_start': self.sutak_start.isoformat() if self.sutak_start else None,
            'sutak_end': self.sutak_end.isoformat() if self.sutak_end else None,
        }
    

class Kundali(models.Model):
    BRIDE_OR_GROOM = [
        ('bride', 'Bride'),
        ('groom', 'Groom')
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100)
    birth_date = models.DateTimeField()
    birth_place = models.CharField(max_length=100)
    birth_lat = models.FloatField()
    birth_lon = models.FloatField()
    birth_timezone = models.CharField(max_length=50, default='Asia/Kolkata')
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Indicate if this Kundali is for bride or groom
    kundali_type = models.CharField(max_length=10, choices=BRIDE_OR_GROOM, default='groom')

    # -------------------- Calculated fields --------------------
    planetary_positions = models.JSONField(default=dict)   # D1 planetary positions
    divisional_charts = models.JSONField(default=dict)     # D2, D3, D4, D5, D7, D9, D12
    houses = models.JSONField(default=dict)                # Sidereal/ Tropical houses
    ascendant = models.JSONField(default=dict)             # Ascendant details
    dashas = models.JSONField(default=dict)                # Vimshottari Dashas

    # -------------------- Gun Milan / Matchmaking --------------------
    gunmilan = models.JSONField(default=dict)
    # Example structure:
    # gunmilan = {
    #     "ashtkoot": {
    #         "varna": "Brahmin",
    #         "gan": "Deva",
    #         "nadi": "Madhya",
    #         "yoni": "Horse",
    #         ...
    #     },
    #     "birth_tithi": {
    #         "tithi": "Chaturthi",
    #         "paksha": "Shukla",
    #         "rashi": "Cancer",
    #         "nakshatra": "Rohini",
    #         "nakshatra_lord": "Moon",
    #         ...
    #     },
    #     "doshas": {
    #         "mangal_dosha": True,
    #         "grahan_dosha": False,
    #         "shani_dosha": True,
    #         "rahu_ketu_dosha": False,
    #         "other_doshas": {}
    #     }
    # }

    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.birth_date.date()}) - {self.kundali_type}"

class DashaPeriod(models.Model):
    kundali = models.ForeignKey(Kundali, on_delete=models.CASCADE)
    dasha_type = models.CharField(max_length=20)
    planet = models.CharField(max_length=20)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    duration_years = models.FloatField(null=True, blank=True)  # 👈 add this
    description = models.TextField(blank=True)

    # NEW FIELD to link antardasha → mahadasha
    mahadasha = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.CASCADE,
        related_name="antardashas"
    )
    
    class Meta:
        ordering = ['start_date']


class AuspiciousYoga(models.Model):
    YOGA_TYPES = [
        ('SARVARTH_SIDDHI', 'Sarvarth Siddhi Yoga'),
        ('AMRIT_SIDDHI', 'Amrit Siddhi Yoga'),
        ('DWIPUSHKAR', 'Dwipushkar Yoga'),
        ('TRIPUSHKAR', 'Tripushkar Yoga'),
        ('RAVI', 'Ravi Yoga'),
    ]
    
    # Basic yoga information
    yoga_type = models.CharField(max_length=20, choices=YOGA_TYPES)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    duration_hours = models.FloatField()
    
    # Combination elements - store ALL relevant data
    weekday = models.CharField(max_length=20, blank=True, null=True)
    nakshatra = models.CharField(max_length=50, blank=True, null=True)
    tithi = models.CharField(max_length=50, blank=True, null=True)  # Now used for Sarvarth Siddhi too
    sun_nakshatra = models.CharField(max_length=50, blank=True, null=True)
    moon_nakshatra = models.CharField(max_length=50, blank=True, null=True)
    nakshatra_difference = models.IntegerField(blank=True, null=True)
    yoga_subtype = models.CharField(max_length=50, blank=True, null=True)
    
    # Store the exact combination that created this yoga
    combination_description = models.TextField(blank=True, null=True)
    combination_rules = models.JSONField(default=dict, blank=True)  # Store the specific rules
    
    class Meta:
        db_table = 'auspicious_yogas'
        indexes = [
            models.Index(fields=['yoga_type', 'start_time']),
            models.Index(fields=['start_time', 'end_time']),
            models.Index(fields=['weekday', 'nakshatra']),  # For combination queries
            models.Index(fields=['yoga_type', 'weekday']),  # For yoga type + weekday queries
            models.Index(fields=['nakshatra', 'tithi']),    # For nakshatra + tithi queries
        ]
        ordering = ['start_time']
    
    def __str__(self):
        return f"{self.get_yoga_type_display()} - {self.start_time.strftime('%Y-%m-%d %H:%M')}"
    
    def get_standardized_combination(self):
        """Return standardized combination format for each yoga type"""
        if self.yoga_type == 'SARVARTH_SIDDHI':
            return f"{self.weekday} · {self.nakshatra} · {self.tithi}"
        
        elif self.yoga_type == 'AMRIT_SIDDHI':
            return f"{self.weekday} · {self.nakshatra}"
        
        elif self.yoga_type == 'RAVI':
            return f"Sun-Moon Nakshatra Diff: {self.nakshatra_difference}"
        
        elif self.yoga_type == 'DWIPUSHKAR':
            return f"{self.weekday} · {self.nakshatra} · {self.tithi}"
        
        elif self.yoga_type == 'TRIPUSHKAR':
            return f"{self.weekday} · {self.nakshatra} · {self.tithi}"
        
        else:
            return self.combination_description or "Combination details"

    def get_combination_icon(self):
        """Return icon for each yoga type"""
        icons = {
            'SARVARTH_SIDDHI': '✓',
            'AMRIT_SIDDHI': '★',
            'RAVI': '☀',
            'DWIPUSHKAR': '②',
            'TRIPUSHKAR': '③',
        }
        return icons.get(self.yoga_type, '●')
    
    def get_clean_combination(self):
        """Ultra-clean standardized format"""
        formats = {
            'SARVARTH_SIDDHI': f"Weekday: {self.weekday} | Nakshatra: {self.nakshatra} | Tithi: {self.tithi}",
            'AMRIT_SIDDHI': f"Weekday: {self.weekday} | Nakshatra: {self.nakshatra}",
            'RAVI': f"Sun : {self.sun_nakshatra} | Moon : {self.moon_nakshatra}",
            'DWIPUSHKAR': f"Weekday: {self.weekday} | Nakshatra: {self.nakshatra} | Tithi: {self.tithi}",
            'TRIPUSHKAR': f"Weekday: {self.weekday} | Nakshatra: {self.nakshatra} | Tithi: {self.tithi}",
        }
        return formats.get(self.yoga_type, "Combination details")
    
    def save(self, *args, **kwargs):
        # Auto-generate combination description if not provided
        if not self.combination_description:
            self.combination_description = self.get_combination_display()
        super().save(*args, **kwargs)


# Run migrations after creating this
# python manage.py makemigrations
# python manage.py migrate