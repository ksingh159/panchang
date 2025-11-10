# from django.shortcuts import render, redirect
# from django.contrib.auth.decorators import login_required
# from django.contrib import messages
# from django.views.decorators.csrf import csrf_exempt
# from django.utils.crypto import get_random_string
# from django.contrib.auth import login
# from django.contrib.auth.models import User
# from django.contrib.auth import authenticate

# from rest_framework.response import Response
# from rest_framework.decorators import api_view, permission_classes
# from rest_framework.permissions import IsAuthenticated
# from rest_framework.permissions import AllowAny

# import swisseph as swe
# from .user_settings import UserSettingsManager
# from django.http import JsonResponse
# from .models import Kundali, DashaPeriod, UserProfile
# from .kundali_calculator import KundaliCalculator
# import json
# from datetime import datetime, date, timedelta
# import pytz





# @api_view(["GET"])
# @permission_classes([IsAuthenticated])
# def panchang_today(request):
#     """Get today's Panchang for authenticated user"""
#     try:
#         # Get user's timezone and convert today accordingly
#         user_profile = UserSettingsManager.get_user_settings(request.user)
#         timezone_str = user_profile.current_timezone
        
#         try:
#             tz = pytz.timezone(timezone_str)
#         except:
#             tz = pytz.timezone('Asia/Kolkata')
        
#         today = datetime.now(tz)
        
#         # Pass the actual user object
#         data = get_panchang(today, user=request.user)
#         return Response(data)
        
#     except Exception as e:
#         return Response({"error": str(e)}, status=400)

# @api_view(["GET"])
# @permission_classes([IsAuthenticated])
# def panchang_date(request, year, month, day):
#     """Get Panchang for specific date for authenticated user"""
#     try:
#         user_profile = UserSettingsManager.get_user_settings(request.user)
#         timezone_str = user_profile.current_timezone
        
#         try:
#             tz = pytz.timezone(timezone_str)
#         except:
#             tz = pytz.timezone('Asia/Kolkata')
        
#         target_date = tz.localize(datetime(year, month, day))
        
#         # Pass the actual user object
#         data = get_panchang(target_date, user=request.user)
#         return Response(data)
        
#     except Exception as e:
#         return Response({"error": str(e)}, status=400)

# @api_view(["GET"])
# def panchang_anonymous(request):
#     """Get Panchang for anonymous users (with location parameters)"""
#     try:
#         print("Starting panchang_anonymous...")
        
#         # Get location from query parameters or use defaults
#         lat = float(request.GET.get('lat', 28.6139))
#         lon = float(request.GET.get('lon', 77.2090))
#         timezone_str = request.GET.get('tz', 'Asia/Kolkata')
#         city_name = request.GET.get('city', 'New Delhi')
        
#         print(f"Params: lat={lat}, lon={lon}, tz={timezone_str}, city={city_name}")
        
#         # Get timezone object
#         try:
#             tz = pytz.timezone(timezone_str)
#             print(f"Timezone created: {tz}")
#         except Exception as e:
#             print(f"Timezone error: {e}")
#             tz = pytz.timezone('Asia/Kolkata')
        
#         # Create timezone-aware datetime
#         today = datetime.now(tz)
#         print(f"Today with timezone: {today}")
        
#         data = get_panchang(
#             target_date=today, 
#             user=None,
#             lat=lat, 
#             lon=lon, 
#             timezone_str=timezone_str, 
#             city_name=city_name
#         )
#         return Response(data)
        
#     except Exception as e:
#         import traceback
#         error_details = traceback.format_exc()
#         print(f"Full error: {error_details}")
#         return Response({"anonymous_error": str(e), "traceback": error_details}, status=400)

# # @api_view(["GET"])
# # @permission_classes([])
# # def panchang_datetime(request, year, month, day, hour, minute):
# #     """Get Panchang for anonymous users (with location parameters)"""
# #     try:
# #         print("Starting panchang_anonymous...")
        
# #         # Get location from query parameters or use defaults
# #         lat = float(request.GET.get('lat', 19.0760))
# #         lon = float(request.GET.get('lon', 72.8777))
# #         timezone_str = request.GET.get('tz', 'Asia/Kolkata')
# #         city_name = request.GET.get('city', 'Mumbai')
        
# #         print(f"Params: lat={lat}, lon={lon}, tz={timezone_str}, city={city_name}")
        
# #         # Get timezone object
# #         try:
# #             tz = pytz.timezone(timezone_str)
# #             print(f"Timezone created: {tz}")
# #         except Exception as e:
# #             print(f"Timezone error: {e}")
# #             tz = pytz.timezone('Asia/Kolkata')
        
# #         # Create timezone-aware datetime
# #         dob = datetime(year, month, day, hour, minute, tzinfo=tz)
# #         print(f"Today with timezone: {dob}")
        
# #         data = get_panchang(
# #             target_date=dob, 
# #             user=None,
# #             lat=lat, 
# #             lon=lon, 
# #             timezone_str=timezone_str, 
# #             city_name=city_name
# #         )
# #         return Response(data)
        
# #     except Exception as e:
# #         import traceback
# #         error_details = traceback.format_exc()
# #         print(f"Full error: {error_details}")
# #         return Response({"anonymous_error": str(e), "traceback": error_details}, status=400)


# # @api_view(["GET"])
# # @permission_classes([])
# # def panchang_datetime(request, year, month, day, hour, minute):
# #     """Get Panchang for anonymous users (with location parameters)"""
# #     try:
# #         print("Starting panchang_anonymous...")
        
# #         # Get location from query parameters or use defaults
# #         lat = float(request.GET.get('lat', 28.6139))
# #         lon = float(request.GET.get('lon', 77.2090))
# #         timezone_str = request.GET.get('tz', 'Asia/Kolkata')
# #         city_name = request.GET.get('city', 'New Delhi')
        
# #         print(f"Params: lat={lat}, lon={lon}, tz={timezone_str}, city={city_name}")
        
# #         # Get timezone object
# #         try:
# #             tz = pytz.timezone(timezone_str)
# #             print(f"Timezone created: {tz}")
# #         except Exception as e:
# #             print(f"Timezone error: {e}")
# #             tz = pytz.timezone('Asia/Kolkata')
        
# #         # Create timezone-aware datetime
# #         dob = datetime(year, month, day, hour, minute, tzinfo=tz)
# #         print(f"Today with timezone: {dob}")
        
# #         data = get_panchang(
# #             target_date=dob, 
# #             user=None,
# #             lat=lat, 
# #             lon=lon, 
# #             timezone_str=timezone_str, 
# #             city_name=city_name
# #         )
# #         return Response(data)
        
# #     except Exception as e:
# #         import traceback
# #         error_details = traceback.format_exc()
# #         print(f"Full error: {error_details}")
# #         return Response({"anonymous_error": str(e), "traceback": error_details}, status=400)


# @api_view(["GET"])
# def testing_call(request):
#     return JsonResponse({"status": "success", "message": "Testing call successful!"})


# @api_view(["GET"])
# def panchang_sidhi(request, year, month,):
#     from .utils.astro_calculations import sarvarth_sidhi
#     try:
#         year = int(request.GET.get("year"))
#         month = int(request.GET.get("month"))
#     except (TypeError, ValueError):
#         return JsonResponse({"error": "Please provide valid 'year' and 'month' parameters."}, status=400)

#     lat = float(request.GET.get("lat", 28.6139))
#     lon = float(request.GET.get("lon", 77.2090))
#     tz_str = request.GET.get("tz", "Asia/Kolkata")
#     city = request.GET.get("city", "New Delhi")

#     try:
#         results = sarvarth_sidhi(
#             year=year,
#             month=month,
#             lat=lat,
#             lon=lon,
#             timezone_str=tz_str,
#             city_name=city,
#         )
#     except Exception as e:
#         return JsonResponse({"error": str(e)}, status=500)

#     return JsonResponse({
#         "year": year,
#         "month": month,
#         "location": {
#             "city": city,
#             "latitude": lat,
#             "longitude": lon,
#             "timezone": tz_str
#         },
#         "sarvarth_siddhi_yog": results
#     }, safe=False)


# @api_view(["GET"])
# @permission_classes([IsAuthenticated])
# def panchang_range(request, start_date, end_date):
#     """Get Panchang for a date range (useful for monthly view)"""
#     try:
#         user_profile = UserSettingsManager.get_user_settings(request.user)
#         timezone_str = user_profile.current_timezone
        
#         try:
#             tz = pytz.timezone(timezone_str)
#         except:
#             tz = pytz.timezone('Asia/Kolkata')
        
#         start = datetime.strptime(start_date, "%Y-%m-%d")
#         end = datetime.strptime(end_date, "%Y-%m-%d")
        
#         panchang_data = []
#         current_date = start
#         while current_date <= end:
#             date_with_tz = tz.localize(current_date)
#             daily_panchang = get_panchang(date_with_tz, user=request.user)
#             panchang_data.append(daily_panchang)
#             current_date += timedelta(days=1)
        
#         return Response({
#             "location": daily_panchang["location_info"],
#             "date_range": f"{start_date} to {end_date}",
#             "panchang_data": panchang_data
#         })
        
#     except Exception as e:
#         return Response({"error": str(e)}, status=400)
    


# # def kundali_form(request):
# #     """Render Kundali creation form"""
# #     return render(request, 'kundali/form.html')


# def generate_kundali(request):
#     """Generate Kundali - handles both form display and processing"""
#     print("=== GENERATE KUNDALI CALLED ===")
#     print(f"Request method: {request.method}")
    
#     if request.method == 'GET':
#         return render(request, 'kundali/form.html')
    
#     elif request.method == 'POST':
#         try:
#             # Extract form data
#             name = request.POST.get('name', '').strip()
#             birth_date_str = request.POST.get('birth_date', '').strip()
#             birth_time_str = request.POST.get('birth_time', '12:00').strip()
#             birth_place = request.POST.get('birth_place', '').strip()
#             lat_str = request.POST.get('lat', '').strip()
#             lon_str = request.POST.get('lon', '').strip()
#             timezone_str = request.POST.get('timezone', 'Asia/Kolkata')
            
#             # Validate required fields
#             if not name or not birth_date_str:
#                 return render(request, 'kundali/form.html', {
#                     'error': 'Name and birth date are required',
#                     'form_data': request.POST
#                 })
            
#             # Parse coordinates
#             try:
#                 birth_lat = float(lat_str) if lat_str else 28.6139
#                 birth_lon = float(lon_str) if lon_str else 77.2090
#             except ValueError:
#                 return render(request, 'kundali/form.html', {
#                     'error': 'Invalid latitude or longitude',
#                     'form_data': request.POST
#                 })
            
#             # Parse date and time with timezone
#             try:
#                 # Combine date and time
#                 birth_datetime_naive = datetime.strptime(
#                     f"{birth_date_str} {birth_time_str}", 
#                     '%Y-%m-%d %H:%M'
#                 )
                
#                 # Make timezone aware
#                 tz = pytz.timezone(timezone_str)
#                 birth_datetime = tz.localize(birth_datetime_naive)
                
#                 print(f"Birth datetime (local): {birth_datetime}")
                
#             except ValueError as e:
#                 return render(request, 'kundali/form.html', {
#                     'error': f'Invalid date or time format: {str(e)}',
#                     'form_data': request.POST
#                 })
            
#             # Calculate Kundali
#             calculator = KundaliCalculator(birth_datetime, birth_lat, birth_lon, 5.5)
#             planetary_positions = calculator.calculate_planetary_positions()
#             ascendant = calculator.calculate_ascendant()
            
#             # Create Kundali record
#             kundali = Kundali.objects.create(
#                 user=request.user if request.user.is_authenticated else None,
#                 name=name,
#                 birth_date=birth_datetime,
#                 birth_place=birth_place,
#                 birth_lat=birth_lat,
#                 birth_lon=birth_lon,
#                 birth_timezone=timezone_str,
#                 planetary_positions=planetary_positions,
#                 ascendant=ascendant
#             )
            
#             # Save Dasha periods
#             dashas = calculator.calculate_dasha_periods()
#             for dasha in dashas:
#                 DashaPeriod.objects.create(
#                     kundali=kundali,
#                     dasha_type=dasha['type'],
#                     planet=dasha['planet'],
#                     start_date=dasha['start_date'],
#                     end_date=dasha['end_date'],
#                     duration_years=dasha.get('duration_years', 0)
#                 )
            
#             return redirect('kundali_detail', kundali_id=kundali.id)
            
#         except Exception as e:
#             print(f"ERROR in generate_kundali: {str(e)}")
#             import traceback
#             traceback.print_exc()
            
#             return render(request, 'kundali/form.html', {
#                 'error': f'Error generating kundali: {str(e)}',
#                 'form_data': request.POST
#             })
    
#     return redirect('kundali_form')

# def calculate_aspect(planet, current_data, birth_data):
#     """Calculate planetary aspects"""
#     try:
#         current_house = current_data.get('house', 1)
#         birth_house = birth_data.get('house', 1)
        
#         aspect_diff = abs(current_house - birth_house)
#         if aspect_diff == 0:
#             return "Conjunction"
#         elif aspect_diff in [3, 6, 9]:
#             return "Strong Aspect"
#         elif aspect_diff in [1, 2, 4, 5, 7, 8, 10, 11]:
#             return "Weak Aspect"
#         else:
#             return "Neutral"
#     except:
#         return "Unknown"

# def get_influence_level(planet, current_data, birth_data):
#     """Determine influence level of transit"""
#     try:
#         current_house = current_data.get('house', 1)
#         birth_house = birth_data.get('house', 1)
        
#         if current_house == birth_house:
#             return "Strong Influence"
#         elif abs(current_house - birth_house) in [1, 5, 9]:
#             return "Moderate Influence"
#         else:
#             return "Mild Influence"
#     except:
#         return "Unknown"

# # Also add a simplified calculate_current_transits function for testing
# def calculate_current_transits(kundali):
#     """Calculate current planetary transits affecting the Kundali - simplified version"""
#     try:
#         # For now, return some sample data to test the page
#         sample_transits = [
#             {
#                 'planet': 'Sun',
#                 'current_house': 5,
#                 'birth_house': 3,
#                 'aspect': 'Conjunction',
#                 'influence': 'Strong Influence'
#             },
#             {
#                 'planet': 'Moon', 
#                 'current_house': 7,
#                 'birth_house': 7,
#                 'aspect': 'Strong Aspect',
#                 'influence': 'Moderate Influence'
#             },
#             {
#                 'planet': 'Mars',
#                 'current_house': 2, 
#                 'birth_house': 9,
#                 'aspect': 'Weak Aspect',
#                 'influence': 'Mild Influence'
#             }
#         ]
#         return sample_transits
#     except Exception as e:
#         print(f"Error in calculate_current_transits: {e}")
#         return []

# def kundali_detail(request, kundali_id):
#     """Display Kundali details with beautiful charts"""
#     try:
#         kundali = Kundali.objects.get(id=kundali_id)
#         dashas = DashaPeriod.objects.filter(kundali=kundali).order_by('start_date')

#         # Ensure timezone-aware birth_date
#         birth_dt = kundali.birth_date
#         if kundali.birth_timezone:
#             local_tz = pytz.timezone(kundali.birth_timezone)
#             birth_dt = birth_dt.astimezone(local_tz)

#         # tz_offset in hours for KundaliCalculator
#         tz_offset = birth_dt.utcoffset().total_seconds() / 3600.0

#         # Structure Mahadashas with their Antardashas
#         structured_dashas = []
#         for dasha in dashas.filter(dasha_type='mahadasha'):
#             antardashas = dashas.filter(
#                 dasha_type='antardasha',
#                 mahadasha=dasha
#             ).order_by('start_date')

#             structured_dashas.append({
#                 "mahadasha": dasha,
#                 "antardashas": antardashas
#             })

#         # Initialize calculator
#         calculator = KundaliCalculator(
#             birth_dt,
#             kundali.birth_lat,
#             kundali.birth_lon,
#             tz_offset
#         )

#         # Calculate D2-D12 divisional charts
#         divisional_charts = calculator.calculate_divisional_charts()

#         # Add duration years dynamically
#         for dasha in dashas:
#             dasha.duration_years = (dasha.end_date - dasha.start_date).days / 365.25

#         context = {
#             "kundali": kundali,
#             "structured_dashas": structured_dashas,
#             "dashas": dashas,  # raw list if template needs it
#             "divisional_charts": divisional_charts,
#             "planetary_positions": kundali.planetary_positions,
#         }

#         return render(request, "kundali/detail.html", context)

#     except Exception as e:
#         return render(request, "kundali/error.html", {"error": str(e)})



# def calculate_current_transits(kundali):
#     """Calculate current planetary transits affecting the Kundali"""
#     calculator = KundaliCalculator(datetime.now(), kundali.birth_lat, kundali.birth_lon, 5.5)
#     current_positions = calculator.calculate_planetary_positions()
    
#     transits = []
#     for planet, current_data in current_positions.items():
#         birth_data = kundali.planetary_positions.get(planet, {})
        
#         transits.append({
#             'planet': planet,
#             'current_house': current_data.get('house'),
#             'birth_house': birth_data.get('house'),
#             'aspect': calculate_aspect(planet, current_data, birth_data),
#             'influence': get_influence_level(planet, current_data, birth_data)
#         })
    
#     return transits

# def kundali_api(request, kundali_id):
#     """API endpoint for Kundali data"""
#     kundali = Kundali.objects.get(id=kundali_id)
#     return JsonResponse({
#         'kundali': {
#             'name': kundali.name,
#             'birth_date': kundali.birth_date,
#             'planetary_positions': kundali.planetary_positions,
#             'dashas': list(DashaPeriod.objects.filter(kundali=kundali).values())
#         }
#     })

    




# def register(request):
#     """
#     Create and log in a temporary 'guest' user automatically.
#     """
#     # Generate unique guest username
#     guest_username = f"guest_{get_random_string(8)}"
#     guest_email = f"{guest_username}@guest.vedicastro.local"
#     guest_password = get_random_string(12)

#     # Create the user
#     guest_user = User.objects.create_user(
#         username=guest_username,
#         email=guest_email,
#         password=guest_password,
#         first_name="Guest"
#     )

#     # Optionally mark them as guest
#     guest_user.is_active = True
#     guest_user.save()

#     # Log in the guest automatically
#     login(request, guest_user)

#     # Redirect to homepage or dashboard
#     return redirect('home')  # Change 'home' to your landing page route name

# def save_location_preferences(request):
#     """Save location preferences for anonymous users"""
#     if request.method == 'POST':
#         try:
#             if request.user.is_authenticated:
#                 # For logged-in users, redirect to profile page
#                 messages.info(request, 'Please update your location in your profile page.')
#                 return redirect('profile')
            
#             # For anonymous users, save to session
#             city = request.POST.get('city')
#             lat = request.POST.get('latitude')
#             lon = request.POST.get('longitude')
            
#             if city and lat and lon:
#                 request.session['city'] = city
#                 request.session['lat'] = float(lat)
#                 request.session['lon'] = float(lon)
#                 request.session['timezone'] = 'Asia/Kolkata'
#                 request.session.set_expiry(30 * 24 * 60 * 60)  # 30 days
#                 messages.success(request, 'Location preferences saved for this session!')
#             else:
#                 messages.error(request, 'Please fill all location fields.')
                
#         except Exception as e:
#             messages.error(request, f'Error saving location: {str(e)}')
    
#     return redirect('home')


# # @api_view(["GET"])
# # @permission_classes([AllowAny])
# # def panchang_datetime(request, year, month, day, hour, minute):
# #     """Get Panchang for specific date and time - API endpoint"""
# #     try:
# #         # Get location from query parameters or session
# #         if request.user.is_authenticated:
# #             profile = getattr(request.user, 'profile', None)
# #             lat = float(request.GET.get('lat', profile.latitude if profile else 19.0760))
# #             lon = float(request.GET.get('lon', profile.longitude if profile else 72.8777))
# #             timezone_str = request.GET.get('tz', profile.timezone if profile else 'Asia/Kolkata')
# #             city_name = request.GET.get('city', profile.city if profile else 'Mumbai')
# #         else:
# #             lat = float(request.GET.get('lat', request.session.get('lat', 19.0760)))
# #             lon = float(request.GET.get('lon', request.session.get('lon', 72.8777)))
# #             timezone_str = request.GET.get('tz', request.session.get('timezone', 'Asia/Kolkata'))
# #             city_name = request.GET.get('city', request.session.get('city', 'Mumbai'))
        
# #         # Get timezone object
# #         try:
# #             tz = pytz.timezone(timezone_str)
# #         except:
# #             tz = pytz.timezone('Asia/Kolkata')
        
# #         # Create timezone-aware datetime
# #         target_datetime = datetime(year, month, day, hour, minute)
# #         target_datetime = tz.localize(target_datetime)
        
# #         # Get panchang data
# #         data = get_panchang(
# #             target_date=target_datetime,
# #             user=request.user if request.user.is_authenticated else None,
# #             lat=lat,
# #             lon=lon,
# #             timezone_str=timezone_str,
# #             city_name=city_name
# #         )
        
# #         return Response(data)
        
# #     except Exception as e:
# #         import traceback
# #         return Response({
# #             "error": str(e),
# #             "traceback": traceback.format_exc()
# #         }, status=400)





# def register(request):
#     """
#     Handle user registration with location preferences
#     """
#     if request.method == 'POST':
#         try:
#             # Get form data
#             full_name = request.POST.get('full_name', '').strip()
#             email = request.POST.get('email', '').strip()
#             password1 = request.POST.get('password1')
#             password2 = request.POST.get('password2')
#             city = request.POST.get('city', 'Mumbai')
#             latitude = request.POST.get('latitude', 19.0760)
#             longitude = request.POST.get('longitude', 72.8777)
            
#             print(f"Registration data: {full_name}, {email}, {city}, {latitude}, {longitude}")
            
#             # Validation
#             if not all([full_name, email, password1, password2]):
#                 messages.error(request, 'All fields are required')
#                 return render(request, 'registration/register.html')
            
#             if password1 != password2:
#                 messages.error(request, 'Passwords do not match')
#                 return render(request, 'registration/register.html')
            
#             if User.objects.filter(email=email).exists():
#                 messages.error(request, 'Email already exists')
#                 return render(request, 'registration/register.html')
            
#             # Create user
#             username = email.split('@')[0] + str(User.objects.count() + 1)
#             user = User.objects.create_user(
#                 username=username,
#                 email=email,
#                 password=password1,
#                 first_name=full_name
#             )
            
#             # Update user profile with location
#             profile = user.profile  # This should exist due to the signal
#             profile.city = city
#             profile.latitude = float(latitude)
#             profile.longitude = float(longitude)
#             profile.save()
            
#             print(f"User created: {user.username}, Profile: {profile.city}")
            
#             # Log the user in - specify the backend
#             user = authenticate(request, username=username, password=password1)
#             if user is not None:
#                 login(request, user, backend='django.contrib.auth.backends.ModelBackend')
#                 messages.success(request, f'Welcome to Vedic Astro, {full_name}!')
#                 return redirect('home')
#             else:
#                 messages.error(request, 'Login failed after registration')
#                 return redirect('login')
            
#         except Exception as e:
#             print(f"Registration error: {e}")
#             messages.error(request, f'Registration failed: {str(e)}')
#             return render(request, 'registration/register.html')
    
#     # GET request - show registration form
#     return render(request, 'registration/register.html')

# @login_required
# def debug_profile(request):
#     """Debug view to check profile data"""
#     profile = request.user.profile
#     return JsonResponse({
#         'username': request.user.username,
#         'profile_exists': hasattr(request.user, 'profile'),
#         'city': profile.city,
#         'latitude': profile.latitude,
#         'longitude': profile.longitude,
#         'timezone': profile.timezone,
#     })

# # Placeholder views for other pages
# def panchang_view(request):
#     return redirect('home')

# def kundali_list(request):
#     return render(request, 'kundali_list.html')

# #login_required
# def create_kundali(request):
#     return render(request, 'create_kundali.html')

# def compatibility_view(request):
#     return render(request, 'compatibility.html')



# def about_view(request):
#     return render(request, 'about.html')

# def contact_view(request):
#     return render(request, 'contact.html')


# def about(request):
#     return render(request, 'static_pages/about.html')

# def how_it_works(request):
#     return render(request, 'static_pages/how_it_works.html')

# def faq(request):
#     return render(request, 'static_pages/faq.html')

# def blog(request):
#     return render(request, 'static_pages/blog.html')

# def privacy(request):
#     return render(request, 'static_pages/privacy.html')

# def terms(request):
#     return render(request, 'static_pages/terms.html')


# # def home(request):
# #     # Your home page data
# #     context = {
# #         'target_datetime': '2025-01-20 10:30:00',
# #         'city': 'Varanasi',
# #         'coordinates': '25.3176° N, 82.9739° E',
# #         'paksha_tithi': 'Shukla Paksha, Ekadashi',
# #         # ... other context data
# #     }
# #     return render(request, 'home2.html', context)


# @login_required
# def profile(request):
#     """User profile with location editing"""
#     popular_cities = [
#         {'name': 'Mumbai', 'state': 'Maharashtra', 'lat': 19.0760, 'lon': 72.8777},
#         {'name': 'Delhi', 'state': 'Delhi', 'lat': 28.6139, 'lon': 77.2090},
#         {'name': 'Bangalore', 'state': 'Karnataka', 'lat': 12.9716, 'lon': 77.5946},
#         {'name': 'Hyderabad', 'state': 'Telangana', 'lat': 17.3850, 'lon': 78.4867},
#         {'name': 'Chennai', 'state': 'Tamil Nadu', 'lat': 13.0827, 'lon': 80.2707},
#         {'name': 'Kolkata', 'state': 'West Bengal', 'lat': 22.5726, 'lon': 88.3639},
#         {'name': 'Pune', 'state': 'Maharashtra', 'lat': 18.5204, 'lon': 73.8567},
#         {'name': 'Ahmedabad', 'state': 'Gujarat', 'lat': 23.0225, 'lon': 72.5714},
#         {'name': 'Jaipur', 'state': 'Rajasthan', 'lat': 26.9124, 'lon': 75.7873},
#         {'name': 'Lucknow', 'state': 'Uttar Pradesh', 'lat': 26.8467, 'lon': 80.9462},
#     ]
    
#     # Ensure profile exists
#     profile, created = UserProfile.objects.get_or_create(user=request.user)
    
#     # Handle POST request (location update)
#     if request.method == 'POST':
#         print("=== PROFILE POST REQUEST ===")
#         print(f"POST data: {request.POST}")
#         try:
#             city = request.POST.get('city')
#             latitude = request.POST.get('latitude')
#             longitude = request.POST.get('longitude')
            
#             print(f"City: {city}, Lat: {latitude}, Lon: {longitude}")
            
#             # Validate data
#             if not all([city, latitude, longitude]):
#                 messages.error(request, 'All fields are required.')
#                 return redirect('profile')
            
#             # Update profile
#             profile.city = city
#             profile.latitude = float(latitude)
#             profile.longitude = float(longitude)
#             profile.save()
            
#             print(f"Profile saved: {profile.city}, {profile.latitude}, {profile.longitude}")
            
#             messages.success(request, 'Location preferences updated successfully!')
#             # Redirect back to profile page to show updated data
#             return redirect('profile')
            
#         except Exception as e:
#             print(f"Error saving profile: {e}")
#             messages.error(request, f'Error updating location: {str(e)}')
    
#     print(f"Current profile data: {profile.city}, {profile.latitude}, {profile.longitude}")
#     return render(request, 'registration/profile.html', {
#         'popular_cities': popular_cities
#     })

# @login_required
# def transit_chart(request):
#     user_kundalis = Kundali.objects.filter(user=request.user)
#     context = {
#         'user_kundalis': user_kundalis,
#         'chart_data': get_chart_data(request.user)
#     }
#     return render(request, 'transit_chart2.html', context)

# def panchang(request):
#     # Panchang data logic
#     return render(request, 'panchang2.html', context)

# @login_required
# def kundali_list(request):
#     user_kundalis = Kundali.objects.filter(user=request.user)
#     return render(request, 'kundali_list.html', {'kundalis': user_kundalis})