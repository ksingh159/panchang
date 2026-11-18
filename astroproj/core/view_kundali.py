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
from .utils.geo import timezone_for
from .utils import transits as transit_info
from dateutil.parser import parse

from .utils.astro_calculations import (
    get_panchang
)
import logging

logger = logging.getLogger(__name__)

# # -------------------- Kundali Form --------------------

def kundali_form(request):
    """The create-kundali form. Its POST goes to generate_kundali; an old client posting here gets the same handler
    (an earlier copy of it saved timezone-aware datetimes, which the database rejects with USE_TZ=False).

    Anyone can make a kundali; no account is needed (see GUEST_KEY)."""
    if request.method == 'POST':
        from .views.user_views import rate_limit
        return rate_limit('kundali-generate', 20)(generate_kundali)(request)
    from .utils.kundali_seo_content import kundali_context
    return render(request, 'kundali/create_kundali.html', {"seo": kundali_context()})


@login_required
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
    except Exception:
        logger.exception("Could not delete kundali %s", kundali_id)
        return JsonResponse({
            'success': False,
            'error': 'Could not delete this kundali. Please try again.'
        }, status=500)

# -------------------- Guest kundalis --------------------
# A visitor who is not signed in can still make a kundali. It is saved with user=None and its id is kept in their
# session, so only that browser can open it. Signing in moves those kundalis to the account (claim_guest_kundalis,
# connected to user_logged_in in apps.py); unclaimed ones are deleted after GUEST_DAYS by the daily job.
GUEST_KEY = "guest_kundalis"
GUEST_DAYS = 30


def _guest_ids(request):
    return [int(i) for i in request.session.get(GUEST_KEY, []) if str(i).isdigit()]


def _remember_guest(request, kundali_id):
    request.session[GUEST_KEY] = (_guest_ids(request) + [kundali_id])[-50:]


def claim_guest_kundalis(sender, request, user, **kwargs):
    """On sign-in, kundalis made in this browser as a guest become the account's."""
    ids = _guest_ids(request)
    if ids:
        Kundali.objects.filter(id__in=ids, user__isnull=True).update(user=user)
        request.session.pop(GUEST_KEY, None)


def purge_guest_kundalis(days=GUEST_DAYS):
    from datetime import timedelta
    from django.utils import timezone as dj_tz
    cutoff = dj_tz.now() - timedelta(days=days)   # naive local time, as stored (USE_TZ=False)
    return Kundali.objects.filter(user__isnull=True, created_at__lt=cutoff).delete()[0]


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
            detected_tz = timezone_for(lat, lon, default=None)
            timezone_str = detected_tz or timezone_str or 'Asia/Kolkata'
            
            # Make timezone aware for calculations
            tz = pytz.timezone(timezone_str)
            birth_datetime_local = tz.localize(birth_dt_naive)
            
            # Calculate timezone offset in hours for the calculator
            tz_offset = birth_datetime_local.utcoffset().total_seconds() / 3600.0
            
            
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
            if not request.user.is_authenticated:
                _remember_guest(request, kundali.id)

            return redirect('kundali_detail', kundali_id=kundali.id)
        
        except Exception:
            logger.exception("Kundali generation failed")
            return render(request, 'kundali/create_kundali.html', {
                'error': 'Could not create the kundali. Please check the date, time and place and try again.',
                'form_data': request.POST
            })

def save_dashas_to_database(kundali, structured_dashas):
    """Save dasha periods to DashaPeriod model: two bulk inserts in one transaction (one commit, not ~90)."""
    from django.db import transaction
    try:
        with transaction.atomic():
            blocks = [b.get('mahadasha', {}) for b in structured_dashas]
            mahadashas = DashaPeriod.objects.bulk_create([
                DashaPeriod(
                    kundali=kundali, dasha_type='mahadasha', planet=md.get('planet', ''),
                    start_date=_naive(parse_date_string(md.get('start_date'))),
                    end_date=_naive(parse_date_string(md.get('end_date'))),
                    duration_years=md.get('duration_years', 0), description=f"{md.get('planet', '')} Mahadasha")
                for md in blocks])
            DashaPeriod.objects.bulk_create([
                DashaPeriod(
                    kundali=kundali, dasha_type='antardasha', planet=ad.get('planet', ''),
                    start_date=_naive(parse_date_string(ad.get('start_date'))),
                    end_date=_naive(parse_date_string(ad.get('end_date'))),
                    duration_years=ad.get('duration_years', 0), mahadasha=md_obj,
                    description=f"{ad.get('planet', '')} Antardasha in {md.get('planet', '')} Mahadasha")
                for block, md, md_obj in zip(structured_dashas, blocks, mahadashas)
                for ad in block.get('antardashas', [])])
    except Exception as e:
        logger.error(f"Error saving dashas to database: {e}")

def parse_date_string(date_str):
    """Parse date string to datetime object"""
    if not date_str:
        return datetime.now()
    if isinstance(date_str, datetime):
        return date_str

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
def _visible_kundali(request, kundali_id):
    """The kundali if it belongs to this visitor. Birth details are never served to anyone else."""
    if request.user.is_authenticated:
        mine = Kundali.objects.filter(id=kundali_id, user=request.user).first()
        if mine:
            return mine
    if kundali_id in _guest_ids(request):
        return Kundali.objects.filter(id=kundali_id, user__isnull=True).first()
    return None


def _naive(value):
    return value.replace(tzinfo=None) if getattr(value, 'tzinfo', None) else value


def _running_periods(structured_dashas):
    """Parse dasha dates and flag the mahadasha and antardasha running now."""
    now = datetime.now()
    for block in structured_dashas:
        periods = [block.get('mahadasha') or {}] + list(block.get('antardashas') or [])
        for period in periods:
            for key in ('start_date', 'end_date'):
                if isinstance(period.get(key), str):
                    period[key] = parse_date_string(period[key])
                period[key] = _naive(period.get(key))
            if period.get('start_date') and period.get('end_date'):
                period['is_current'] = period['start_date'] <= now < period['end_date']
    return structured_dashas


def _current_transits(kundali):
    from .views.astro_views import calculate_current_transits
    d1 = kundali.planetary_positions or {}
    signs = transit_info.SIGNS
    lagna = kundali.ascendant.get('sign_sidereal') if kundali.ascendant else None
    moon = (d1.get('Moon') or {}).get('sign')
    if lagna not in signs or moon not in signs:
        return {'rows': [], 'sade_sati': ''}
    planets = calculate_current_transits(kundali)['planets']
    saturn = next((p for p in planets if p['name'] == 'Saturn'), None)
    return {
        'rows': transit_info.transit_rows(planets, signs.index(lagna), signs.index(moon)),
        'sade_sati': transit_info.sade_sati(signs.index(moon), saturn['sign']) if saturn else '',
    }


def chart_labels():
    """Words the chart script writes into the page, in the current language."""
    from django.utils.translation import get_language, gettext as _
    from .pdf import i18n
    hi = (get_language() or "").startswith("hi")
    lang = "hi" if hi else "en"
    signs = [en for en, _h in i18n.SIGNS]
    return {
        "signs": {en: i18n.pick((en, h), lang) for en, h in i18n.SIGNS},
        "abbr": {en: (h[:2] if hi else en[:3]) for en, h in i18n.SIGNS},
        "planets": {en: i18n.pick(pair, lang) for en, pair in i18n.PLANETS.items()},
        "planet_abbr": {en: i18n.pick(pair, lang) for en, pair in i18n.PLANET_ABBR.items()},
        "nakshatras": {en: i18n.pick((en, h), lang) for en, h in i18n.NAKSHATRAS},
        "asc": _("Asc"), "chart": _("Chart"), "zodiac_sign": _("Zodiac Sign"), "house": _("House"), "degree": _("Degree"),
        "nakshatra": _("Nakshatra"), "chart_asc": _("Chart Ascendant"), "in": _("in"), "no_data": _("No data for this chart"),
        "note": _("Planet placement based on zodiac sign derived from ascendant"), "signs_order": signs,
    }


def transit_labels():
    """chart_labels plus the words of the transit page."""
    from django.utils.translation import gettext as _
    labels = chart_labels()
    labels.update({
        "dsc": _("Dsc"), "select": _("Select Kundali"), "none_saved": _("No kundalis saved"),
        "select_first": _("Select a kundali above to see planetary details."), "house_word": _("House"),
        "pada": _("pada"), "lord": _("lord"), "lagna": _("Lagna"), "moon_sign": _("Moon sign"), "shani": _("Shani"),
        "contacts": _("Exact contacts right now"), "graha": _("Graha"), "natal": _("Natal"), "transit_today": _("Transit today"),
        "from_lagna": _("From Lagna"), "from_moon": _("From Moon"),
        "houses_note": _("Houses · natal in red, transit in blue, kendras in gold"), "transit": _("Transit"),
        "longitude": _("Longitude"), "retro": _("Currently Retrograde"), "speed": _("Speed"), "per_day": _("°/day"),
        "lock": _("Click to lock tooltip • ESC to close"), "R": _("R"),
        "confirm_title": _("Confirm Deletion"), "confirm_text": _("Are you sure you want to delete this kundali?"),
        "confirm_named": _('Are you sure you want to delete "%(name)s"? This action cannot be undone.'),
        "cancel": _("Cancel"), "delete": _("Delete"), "deleted": _("Kundali deleted successfully!"),
        "delete_error": _("Error deleting kundali:"), "delete_retry": _("Error deleting kundali. Please try again."),
        "contact_text": _("Transit %(transit)s is %(gap)s° from natal %(natal)s"),
        "words": {w: _(w) for w in ("Exalted", "Debilitated", "Own sign", "Kendra", "Trikona", "Dusthana")},
        "sade": {s: _(s) for s in (
            "Sade Sati is running: rising (first) phase", "Sade Sati is running: peak (second) phase",
            "Sade Sati is running: setting (third) phase",
            "Kantak Shani (Dhaiya): Saturn transits the 4th from your Moon",
            "Ashtama Shani (Dhaiya): Saturn transits the 8th from your Moon", "No Sade Sati or Dhaiya at present")},
    })
    from django.utils.translation import get_language
    if (get_language() or "").startswith("hi"):
        labels["abbr_planets"] = {"Sun": "सू", "Moon": "च", "Mercury": "बु", "Venus": "शु", "Mars": "मं", "Jupiter": "गु",
                                  "Saturn": "श", "Rahu": "रा", "Ketu": "के", "Ascendant": "ल"}
    return labels


def _dasha_windows(planets, structured_dashas):
    """'Jupiter Mahadasha 2031-2047' lines (English, Hindi) for the planets that carry a yoga or dosha."""
    from .pdf import i18n
    now = datetime.now()                # only current and coming periods: what one can still prepare for
    out = []
    for p in planets:
        for block in structured_dashas:
            md = block.get('mahadasha') or {}
            if md.get('planet') == p and md.get('start_date') and md.get('end_date') and md['end_date'] >= now:
                a, b = md['start_date'].year, md['end_date'].year
                out.append((f"{i18n.planet(p, 'en')} Mahadasha {a}-{b}", f"{i18n.planet(p, 'hi')} महादशा {a}-{b}"))
    return out


def chart_yogas_doshas(kundali, structured_dashas=()):
    """Yogas and doshas for the kundali page: which planets form each one, where they sit, what it can mean,
    how strong the planets are and in which dashas it acts. Remedies stay in the PDF."""
    from .utils import kundali_yogas as ky, dosha_page
    from .utils.dosha_remedies import gand_mool, individual_doshas, mangal_dosha
    from .pdf.kundali_report import DOSHA_INFO, _DoshaChart
    chart = ky.chart_from_kundali(kundali)
    if not chart:
        return {"yogas": [], "doshas": [], "overview": []}
    signs, lons, asc = chart
    found = individual_doshas(_DoshaChart(signs, lons, asc))
    extra = {}
    mangal = mangal_dosha(signs, lons, asc)
    if mangal["present"]:
        found["mangal"] = {"present": True, "cancelled": mangal["cancelled"], "severity": mangal["severity"]}
        extra["mangal"] = mangal
    gm = gand_mool(lons["Moon"])
    if gm["present"]:
        found["gand_mool"] = {"present": True, "cancelled": False, "severity": gm["severity"]}
        extra["gand_mool"] = gm
    doshas = []
    for key, (title, _about) in DOSHA_INFO.items():
        d = found.get(key)
        if d and d.get("present"):
            status = ("cancelled" if d.get("cancelled") else "reduced" if d.get("severity") == "low" else "present")
            doshas.append({"key": key, "name": title, "meaning": dosha_page.MEANING[key], "status": status,
                           "facts": dosha_page.facts(key, signs, lons, asc, extra.get(key)),
                           "dashas": _dasha_windows(dosha_page.planets_of(key, signs), structured_dashas)})
    yogas = ky.find_yogas(signs, lons, asc)
    for y in yogas:
        y["dashas"] = _dasha_windows([p for p in y["planets"]], structured_dashas)
    return {"yogas": yogas, "doshas": doshas, "overview": ky.overview(signs, lons, asc, yogas)}


def shani_periods(kundali):
    from .utils import shani
    try:
        return shani.for_kundali(kundali)
    except Exception:
        logger.exception("Sade Sati periods failed for kundali %s", kundali.id)
        return []


def kundali_detail(request, kundali_id):
    kundali = _visible_kundali(request, kundali_id)
    if not kundali:
        return render(request, 'kundali/error.html', {"error": "Kundali not found"}, status=404)

    user_kundalis = []
    if request.user.is_authenticated:
        user_kundalis = Kundali.objects.filter(user=request.user).exclude(id=kundali_id).order_by('-created_at')[:10]

    ascendant = kundali.ascendant or {}
    from .utils import varga
    divisional_charts, divisional_asc = varga.charts_for_kundali(kundali)
    structured_dashas = _running_periods(get_structured_dashas(kundali))
    context = {
        "kundali": kundali,
        "user_kundalis": user_kundalis,
        "structured_dashas": structured_dashas,
        "divisional_charts": divisional_charts,
        "ascendant": ascendant,
        "current_transits": _current_transits(kundali),
        "chart_yogas": chart_yogas_doshas(kundali, structured_dashas),
        "shani_periods": shani_periods(kundali),
        "chart_labels": chart_labels(),
        "chart_json": {
            "ascendantSign": ascendant.get('sign_sidereal') or 'Aries',
            "ascendantDegree": ascendant.get('degree_in_sign') or 0,
            "divisional_charts": divisional_charts,
            "divisional_asc": divisional_asc,
        },
    }
    context.update(_birth_month(request, kundali))
    from .models import Purchase
    from .utils import payments
    currency = payments.detect_currency(request)
    other = "USD" if currency == "INR" else "INR"
    context.update({
        "pdf_price": payments.format_price("kundali_pdf", currency),
        "pdf_other_currency": other, "pdf_other_price": payments.format_price("kundali_pdf", other),
        "pdf_can_change_currency": not payments.currency_from_country(request),
        "pdf_order": Purchase.objects.filter(kundali=kundali, user=request.user, product="kundali_pdf",
                                             status="paid").first() if request.user.is_authenticated else None,
        "guest": not request.user.is_authenticated,
    })
    return render(request, 'kundali/detail.html', context)

def _birth_month(request, kundali):
    """Lunar month and paksha at birth, told in the viewer's month system (Purnimanta or Amanta)."""
    from .utils import panchang_store as ps, prefs
    try:
        b = kundali.birth_date
        utc = (b.astimezone(pytz.utc) if b.tzinfo else pytz.timezone(kundali.birth_timezone or 'UTC').localize(b)
               .astimezone(pytz.utc)).replace(tzinfo=None)
        m = ps.lunar_month_at(utc) or {}
    except Exception:
        return {}
    system = prefs.month_system(request)
    name = m.get("amanta" if system == "amanta" else "purnimanta")
    if not name:
        return {}
    adhik = m.get("purnimanta_adhik") if system != "amanta" else m.get("adhik")
    return {"birth_masa": ("Adhik " if adhik else "") + name, "birth_paksha": m.get("paksha", ""),
            "month_label": prefs.month_label(system)}


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
        logger.error(f"Error getting dashas from database: {e}")
    
    # Fallback to JSON data from Kundali model
    try:
        json_dashas = kundali.dashas or []
        if isinstance(json_dashas, list):
            return json_dashas
    except Exception as e:
        logger.error(f"Error getting dashas from JSON: {e}")
    
    # Final fallback - empty list
    return []

# -------------------- API --------------------
def kundali_api(request, kundali_id):
    try:
        kundali = _visible_kundali(request, kundali_id)
        if not kundali:
            raise Kundali.DoesNotExist
        structured_dashas = get_structured_dashas(kundali)
        from .utils import varga

        return JsonResponse({
            "name": kundali.name,
            "birth_date": kundali.birth_date.isoformat(),
            "kundali_type": kundali.kundali_type,
            "planetary_positions": kundali.planetary_positions,
            "divisional_charts": varga.charts_for_kundali(kundali)[0],
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