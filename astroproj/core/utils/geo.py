# core/utils/geo.py
"""
Offline place search (GeoNames, see ``manage.py load_cities``).

Replaces Nominatim, which returned long names such as
"Varanasi, Varanasi Tahsil, Varanasi, Uttar Pradesh, 221001, India",
was rate limited (its usage policy forbids autocomplete), and gave no timezone.
"""
from functools import lru_cache

from django.db.models import Case, IntegerField, Value, When

from core.models import City


@lru_cache(maxsize=1)
def _tf():
    from timezonefinder import TimezoneFinder
    return TimezoneFinder()


def timezone_for(lat, lon, default="Asia/Kolkata"):
    """IANA timezone at a coordinate (historical offsets/DST are then handled by pytz)."""
    try:
        return _tf().timezone_at(lat=float(lat), lng=float(lon)) or default
    except Exception:
        return default


def city_to_dict(c):
    return {
        "id": c.geoname_id,
        "name": c.display_name,
        "full_address": c.display_name,
        "city": c.name,
        "state": c.state,
        "country": c.country,
        "country_code": c.country_code,
        "lat": round(c.latitude, 4),
        "lon": round(c.longitude, 4),
        "timezone": c.timezone,
    }


def search_cities(query, limit=8, prefer_country="IN"):
    """
    Prefix search. "var" -> Varanasi; "springfield, il" narrows by state/country.
    Exact-name matches first, then the preferred country, then by population.
    """
    parts = [p.strip() for p in (query or "").split(",") if p.strip()]
    if not parts or len(parts[0]) < 2:
        return []
    name = parts[0].lower()
    qs = City.objects.filter(search_name__startswith=name)
    if len(name) >= 4 and not qs.exists():
        qs = City.objects.filter(aliases__contains=f"|{name}")   # Banaras, Bombay, Gurgaon ...
    for extra in parts[1:]:
        qs = qs.filter(state__istartswith=extra) | qs.filter(country__istartswith=extra) | \
            qs.filter(country_code__iexact=extra)
    qs = qs.annotate(
        exact=Case(When(search_name=name, then=Value(1)), default=Value(0), output_field=IntegerField()),
        # towns of the visitor's country win, unless tiny (so "paris" still finds Paris, France)
        home=Case(When(country_code=prefer_country, population__gte=10000, then=Value(1)),
                  default=Value(0), output_field=IntegerField()),
    ).order_by("-home", "-exact", "-population")
    out, seen = [], set()
    for c in qs[: limit * 3]:
        key = c.display_name
        if key in seen:
            continue
        seen.add(key)
        out.append(c)
        if len(out) >= limit:
            break
    return out


def resolve_place(text=None, geoname_id=None):
    """
    Best City for a submitted place.  Accepts a geoname id (from autocomplete)
    or free text such as "Varanasi, Uttar Pradesh, India" / "Pune".
    Returns a dict like ``city_to_dict`` or None.
    """
    if geoname_id:
        c = City.objects.filter(geoname_id=geoname_id).first()
        if c:
            return city_to_dict(c)
    if not text:
        return None
    parts = [p.strip() for p in text.split(",") if p.strip()]
    if not parts:
        return None
    key = parts[0].lower()
    qs = City.objects.filter(search_name=key) | City.objects.filter(name__iexact=parts[0])
    if not qs.exists():
        qs = City.objects.filter(aliases__contains=f"|{key}|")
    if len(parts) >= 2:
        narrowed = qs.filter(state__iexact=parts[1]) | qs.filter(country__iexact=parts[-1])
        if narrowed.exists():
            qs = narrowed
    c = qs.order_by("-population").first()
    if not c:
        found = search_cities(text, limit=1)
        c = found[0] if found else None
    return city_to_dict(c) if c else None


def short_place_name(text):
    """Trim a long geocoder string to 'City, State, Country' (for legacy saved values)."""
    if not text:
        return text
    hit = resolve_place(text)
    if hit:
        return hit["name"]
    parts = [p.strip() for p in text.split(",") if p.strip() and not p.strip().isdigit()]
    return ", ".join(dict.fromkeys(parts[:1] + parts[-2:]))
