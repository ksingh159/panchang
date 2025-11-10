# core/view_kundali.py
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from .models import Kundali, DashaPeriod
from .kundali_calculator import KundaliCalculator
from datetime import datetime
import pytz
import json
from timezonefinderL import TimezoneFinder
from dateutil.parser import parse

from .utils.astro_calculations import (
    get_panchang
)

# # -------------------- Kundali Form --------------------

@login_required
def kundali_form(request):
    """Display kundali creation form and handle form submission"""
    if request.method == 'POST':
        try:
            # Get form data
            name = request.POST.get('name')
            birth_date_str = request.POST.get('birth_date')
            birth_time_str = request.POST.get('birth_time')
            birth_place = request.POST.get('birth_place')
            birth_lat = float(request.POST.get('lat'))
            birth_lon = float(request.POST.get('lon'))
            birth_timezone = request.POST.get('timezone')
            kundali_type = request.POST.get('kundali_type', 'groom')
            
            # Validate required fields
            if not name or not birth_date_str or not birth_time_str:
                raise ValueError("Name, birth date, and birth time are required.")
            
            # Parse birth datetime and generate kundali data
            birth_dt_naive = datetime.strptime(f"{birth_date_str} {birth_time_str}", '%Y-%m-%d %H:%M')
            
            # Get timezone from coordinates or use provided timezone
            tf = TimezoneFinder()
            detected_tz = tf.timezone_at(lat=birth_lat, lng=birth_lon)
            timezone_str = detected_tz or birth_timezone or 'Asia/Kolkata'
            
            # Make timezone aware but KEEP LOCAL CIVIL TIME
            tz = pytz.timezone(timezone_str)
            birth_datetime_local = tz.localize(birth_dt_naive)
            
            # Calculate timezone offset in hours for the calculator
            tz_offset = birth_datetime_local.utcoffset().total_seconds() / 3600.0
            
            print(f"Birth details:")
            print(f"Local time: {birth_datetime_local}")
            print(f"Timezone: {timezone_str}")
            print(f"Offset: {tz_offset} hours")
            print(f"Lat/Lon: {birth_lat}, {birth_lon}")
            
            # -------------------- Calculate Kundali with LOCAL TIME --------------------
            calculator = KundaliCalculator(birth_datetime_local, birth_lat, birth_lon, tz_offset)
            kundali_data = calculator.calculate_all_data()
            
            # -------------------- Create Kundali with all calculated data --------------------
            kundali = Kundali.objects.create(
                user=request.user,
                name=name,
                birth_date=birth_datetime_local,  # Use timezone-aware datetime
                birth_place=birth_place,
                birth_lat=birth_lat,
                birth_lon=birth_lon,
                birth_timezone=timezone_str,
                kundali_type=kundali_type,
                planetary_positions=kundali_data.get('d1_chart', {}),
                divisional_charts=kundali_data.get('divisional_charts', {}),
                houses=kundali_data.get('houses', {}),
                ascendant=kundali_data.get('ascendant', {}),
                dashas=kundali_data.get('structured_dashas', []),
                gunmilan=kundali_data.get('gunmilan', {})
            )
            
            # Save dashas to DashaPeriod model for better querying
            save_dashas_to_database(kundali, kundali_data.get('structured_dashas', []))
            
            # Redirect to the Kundali detail page with the new kundali_id
            return redirect('kundali_detail', kundali_id=kundali.id)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            # Return form with error and previous data
            return render(request, 'kundali/create_kundali.html', {
                'error': f'Error creating kundali: {str(e)}',
                'form_data': request.POST
            })
    
    # GET request - show empty form with defaults
    return render(request, 'kundali/create_kundali.html')


@require_POST
def delete_kundali(request, kundali_id):
    try:
        kundali = Kundali.objects.get(id=kundali_id, user=request.user)
        kundali_name = kundali.name
        kundali.delete()
        return JsonResponse({
            'success': True,
            'message': f'Kundali "{kundali_name}" deleted successfully'
        })
    except Kundali.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Kundali not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

# -------------------- Generate Kundali --------------------
def generate_kundali(request):
    if request.method == 'GET':
        return render(request, 'kundali/create_kundali.html')
    
    elif request.method == 'POST':
        try:
            # Extract form data
            name = request.POST.get('name', '').strip()
            birth_date_str = request.POST.get('birth_date', '').strip()
            birth_time_str = request.POST.get('birth_time', '12:00').strip()
            birth_place = request.POST.get('birth_place', '').strip()
            lat = float(request.POST.get('lat', 28.6139))
            lon = float(request.POST.get('lon', 77.2090))
            timezone_str = request.POST.get('timezone', 'Asia/Kolkata')
            kundali_type = request.POST.get('kundali_type', 'groom')
            
            if not name or not birth_date_str:
                return render(request, 'kundali/create_kundali.html', {
                    'error': 'Name and birth date are required',
                    'form_data': request.POST
                })
            
            # Parse birth datetime
            birth_dt_naive = datetime.strptime(f"{birth_date_str} {birth_time_str}", '%Y-%m-%d %H:%M')
            
            # Get timezone from coordinates or use provided timezone
            tf = TimezoneFinder()
            detected_tz = tf.timezone_at(lat=lat, lng=lon)
            timezone_str = detected_tz or timezone_str or 'Asia/Kolkata'
            
            # Make timezone aware for calculations
            tz = pytz.timezone(timezone_str)
            birth_datetime_local = tz.localize(birth_dt_naive)
            
            # Calculate timezone offset in hours for the calculator
            tz_offset = birth_datetime_local.utcoffset().total_seconds() / 3600.0
            
            print(f"Birth details:")
            print(f"Local time: {birth_datetime_local}")
            print(f"Timezone: {timezone_str}")
            print(f"Offset: {tz_offset} hours")
            print(f"Lat/Lon: {lat}, {lon}")
            
            # -------------------- Calculate Kundali with LOCAL TIME --------------------
            calculator = KundaliCalculator(birth_datetime_local, lat, lon, tz_offset)
            kundali_data = calculator.calculate_all_data()
            
            # Convert to naive datetime for storage (remove timezone info)
            birth_datetime_naive = birth_datetime_local.replace(tzinfo=None)
            
            # -------------------- Save Dasha Periods to Database --------------------
            kundali = Kundali.objects.create(
                user=request.user if request.user.is_authenticated else None,
                name=name,
                birth_date=birth_datetime_naive,  # Use naive datetime for storage
                birth_place=birth_place,
                birth_lat=lat,
                birth_lon=lon,
                birth_timezone=timezone_str,
                kundali_type=kundali_type,
                planetary_positions=kundali_data.get('d1_chart', {}),
                divisional_charts=kundali_data.get('divisional_charts', {}),
                houses=kundali_data.get('houses', {}),
                ascendant=kundali_data.get('ascendant', {}),
                dashas=kundali_data.get('structured_dashas', []),
                gunmilan=kundali_data.get('gunmilan', {})
            )
            
            # Save dashas to DashaPeriod model for better querying
            save_dashas_to_database(kundali, kundali_data.get('structured_dashas', []))
            
            return redirect('kundali_detail', kundali_id=kundali.id)
        
        except Exception as e:
            import traceback
            traceback.print_exc()
            return render(request, 'kundali/create_kundali.html', {
                'error': f'Error generating kundali: {str(e)}',
                'form_data': request.POST
            })

def save_dashas_to_database(kundali, structured_dashas):
    """Save dasha periods to DashaPeriod model"""
    try:
        for dasha_block in structured_dashas:
            mahadasha_data = dasha_block.get('mahadasha', {})
            
            # Create mahadasha
            mahadasha = DashaPeriod.objects.create(
                kundali=kundali,
                dasha_type='mahadasha',
                planet=mahadasha_data.get('planet', ''),
                start_date=parse_date(mahadasha_data.get('start_date')),
                end_date=parse_date(mahadasha_data.get('end_date')),
                duration_years=mahadasha_data.get('duration_years', 0),
                description=f"{mahadasha_data.get('planet', '')} Mahadasha"
            )
            
            # Create antardashas
            for antardasha_data in dasha_block.get('antardashas', []):
                DashaPeriod.objects.create(
                    kundali=kundali,
                    dasha_type='antardasha',
                    planet=antardasha_data.get('planet', ''),
                    start_date=parse_date(antardasha_data.get('start_date')),
                    end_date=parse_date(antardasha_data.get('end_date')),
                    duration_years=antardasha_data.get('duration_years', 0),
                    mahadasha=mahadasha,
                    description=f"{antardasha_data.get('planet', '')} Antardasha in {mahadasha_data.get('planet', '')} Mahadasha"
                )
    except Exception as e:
        print(f"Error saving dashas to database: {e}")

def parse_date_string(date_str):
    """Parse date string to datetime object"""
    if not date_str:
        return datetime.now()
    
    try:
        # Try ISO format first
        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    except:
        try:
            # Try other common formats
            for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%d/%m/%Y']:
                try:
                    return datetime.strptime(date_str, fmt)
                except:
                    continue
        except:
            pass
    
    return datetime.now()

# -------------------- Kundali Detail --------------------
def kundali_detail(request, kundali_id):
    try:
        kundali = Kundali.objects.get(id=kundali_id)
        
        # Get user's other kundalis
        user_kundalis = Kundali.objects.filter(user=request.user).exclude(id=kundali_id).order_by('-created_at')[:10]
        
        # Get structured dashas from database or JSON fallback
        structured_dashas = get_structured_dashas(kundali)
        
        # Convert date strings to datetime objects for template rendering
        if structured_dashas:
            for block in structured_dashas:
                # Convert mahadasha dates
                if 'mahadasha' in block and block['mahadasha']:
                    mahadasha = block['mahadasha']
                    if isinstance(mahadasha.get('start_date'), str):
                        mahadasha['start_date'] = parse_date_string(mahadasha['start_date'])
                    if isinstance(mahadasha.get('end_date'), str):
                        mahadasha['end_date'] = parse_date_string(mahadasha['end_date'])
                
                # Convert antardasha dates
                if 'antardashas' in block and block['antardashas']:
                    for antardasha in block['antardashas']:
                        if isinstance(antardasha.get('start_date'), str):
                            antardasha['start_date'] = parse_date_string(antardasha['start_date'])
                        if isinstance(antardasha.get('end_date'), str):
                            antardasha['end_date'] = parse_date_string(antardasha['end_date'])

        
        # Ensure all required data is available
        d1_chart = kundali.planetary_positions or {}
        divisional_charts = kundali.divisional_charts or {}
        ascendant = kundali.ascendant or {}
        print(d1_chart)
        
        context = {
            "kundali": kundali,
            "user_kundalis": user_kundalis,  # Add this
            "d1_chart": d1_chart,
            "structured_dashas": structured_dashas,
            "divisional_charts": divisional_charts,
            "ascendant": ascendant,
            "planetsData": d1_chart,
        }
        return render(request, 'kundali/detail.html', context)
    
    except Kundali.DoesNotExist:
        return render(request, 'kundali/error.html', {"error": "Kundali not found"})

def get_structured_dashas(kundali):
    """Get structured dashas from database with fallback to JSON"""
    structured_dashas = []
    
    # Try to get from DashaPeriod model first
    try:
        mahadashas = DashaPeriod.objects.filter(
            kundali=kundali, 
            dasha_type='mahadasha'
        ).order_by('start_date')
        
        for maha in mahadashas:
            antardashas = DashaPeriod.objects.filter(
                kundali=kundali,
                dasha_type='antardasha',
                mahadasha=maha
            ).order_by('start_date')
            
            structured_dashas.append({
                "mahadasha": {
                    "planet": maha.planet,
                    "start_date": maha.start_date,
                    "end_date": maha.end_date,
                    "duration_years": maha.duration_years or 0
                },
                "antardashas": [
                    {
                        "planet": ad.planet,
                        "start_date": ad.start_date,
                        "end_date": ad.end_date,
                        "duration_years": ad.duration_years or 0
                    } for ad in antardashas
                ]
            })
        
        # If we found dashas in database, return them
        if structured_dashas:
            return structured_dashas
    except Exception as e:
        print(f"Error getting dashas from database: {e}")
    
    # Fallback to JSON data from Kundali model
    try:
        json_dashas = kundali.dashas or []
        if isinstance(json_dashas, list):
            return json_dashas
    except Exception as e:
        print(f"Error getting dashas from JSON: {e}")
    
    # Final fallback - empty list
    return []

# -------------------- API --------------------
def kundali_api(request, kundali_id):
    try:
        kundali = Kundali.objects.get(id=kundali_id)
        structured_dashas = get_structured_dashas(kundali)
        
        return JsonResponse({
            "name": kundali.name,
            "birth_date": kundali.birth_date.isoformat(),
            "kundali_type": kundali.kundali_type,
            "planetary_positions": kundali.planetary_positions,
            "divisional_charts": kundali.divisional_charts,
            "houses": kundali.houses,
            "ascendant": kundali.ascendant,
            "structured_dashas": structured_dashas,
            "gunmilan": kundali.gunmilan
        })
    except Kundali.DoesNotExist:
        return JsonResponse({"error": "Kundali not found"}, status=404)

# -------------------- User's Kundalis --------------------
@login_required
def my_kundalis(request):
    kundalis = Kundali.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'kundali/detail.html', {'kundalis': kundalis})