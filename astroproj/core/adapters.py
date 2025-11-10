from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth.models import User
from .models import UserProfile

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        # Handle profile creation for social logins
        user = sociallogin.user
        if user.id:
            # User already exists, ensure profile exists
            UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    'city': 'Mumbai',
                    'latitude': 19.0760,
                    'longitude': 72.8777
                }
            )
    
    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)
        # Create profile for new social user
        UserProfile.objects.get_or_create(
            user=user,
            defaults={
                'city': 'Mumbai', 
                'latitude': 19.0760,
                'longitude': 72.8777
            }
        )
        return user