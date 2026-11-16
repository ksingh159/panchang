# core/views_settings.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from .user_settings import UserSettingsManager
from .models import UserProfile

@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def user_settings(request):
    """Get or update user settings"""
    if request.method == 'GET':
        profile = UserSettingsManager.get_user_settings(request.user)
        return Response(profile.to_settings_dict())
    
    elif request.method == 'PUT':
        data = request.data
        
        # Update location
        if 'location' in data:
            location = data['location']
            UserSettingsManager.update_location(
                request.user,
                city_name=location.get('city'),
                lat=location.get('lat'),
                lon=location.get('lon'),
                address=location.get('address')
            )
        
        # Update preferences
        if 'preferences' in data:
            UserSettingsManager.update_preferences(request.user, data['preferences'])
        
        # Update personal info
        if 'personal' in data:
            personal = data['personal']
            profile = UserSettingsManager.get_user_settings(request.user)
            # Handle birth date/time updates here
        
        profile = UserSettingsManager.get_user_settings(request.user)
        return Response({
            "message": "Settings updated successfully",
            "settings": profile.to_settings_dict()
        })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sync_settings(request):
    """Sync settings with mobile app"""
    mobile_data = request.data
    profile = UserSettingsManager.get_user_settings(request.user)
    
    # Update from mobile data
    if 'location' in mobile_data:
        UserSettingsManager.update_location(
            request.user, 
            **mobile_data['location']
        )
    
    if 'preferences' in mobile_data:
        UserSettingsManager.update_preferences(request.user, mobile_data['preferences'])
    
    # Update sync info
    profile.last_sync = timezone.now()
    profile.sync_token = mobile_data.get('sync_token', profile.sync_token)
    profile.mobile_device_id = mobile_data.get('device_id', profile.mobile_device_id)
    profile.save()
    
    return Response({
        "message": "Settings synced successfully",
        "last_sync": profile.last_sync,
        "settings": profile.to_settings_dict()
    })