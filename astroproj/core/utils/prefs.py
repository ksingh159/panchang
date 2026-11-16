# core/utils/prefs.py
"""
Small per-person preferences: kept on the UserProfile for signed-in users and in the session for visitors.

  native_state  the Indian state or UT the family comes from (a key of STATE_REGION), e.g. "Uttar Pradesh"
  food_region   the aahaar region to open first (a key of aahaar_foods.REGIONS); blank = from native state, then city
  month_system  "purnimanta" (month ends on Purnima: Kashi, North India) or "amanta" (ends on Amavasya: Maharashtra,
                Gujarat, the South)
"""
from .aahaar_regions import region_for_place

MONTH_SYSTEMS = (("purnimanta", "Purnimanta (Purnima to Purnima)"), ("amanta", "Amanta (Amavasya to Amavasya)"))
FIELDS = ("native_state", "food_region", "month_system")

# Every state and union territory -> the aahaar food region whose kitchen is closest to it
STATE_REGION = {
    "Andhra Pradesh": "andhra", "Arunachal Pradesh": "bengal", "Assam": "bengal", "Bihar": "bihar",
    "Chhattisgarh": "chhattisgarh", "Goa": "maharashtra", "Gujarat": "gujarat", "Haryana": "punjab",
    "Himachal Pradesh": "pahadi", "Jharkhand": "bihar", "Karnataka": "karnataka", "Kerala": "kerala",
    "Madhya Pradesh": "mp", "Maharashtra": "maharashtra", "Manipur": "bengal", "Meghalaya": "bengal",
    "Mizoram": "bengal", "Nagaland": "bengal", "Odisha": "odisha", "Punjab": "punjab", "Rajasthan": "rajasthan",
    "Sikkim": "bengal", "Tamil Nadu": "tamilnadu", "Telangana": "andhra", "Tripura": "bengal",
    "Uttar Pradesh": "up", "Uttarakhand": "pahadi", "West Bengal": "bengal",
    "Andaman and Nicobar Islands": "bengal", "Chandigarh": "punjab",
    "Dadra and Nagar Haveli and Daman and Diu": "gujarat", "Delhi": "punjab", "Jammu and Kashmir": "pahadi",
    "Ladakh": "pahadi", "Lakshadweep": "kerala", "Puducherry": "tamilnadu",
}
STATES = tuple(STATE_REGION)


def _region_keys():
    from .aahaar_foods import REGIONS
    return {r["key"] for r in REGIONS}


def get(request, key, default=""):
    user = getattr(request, "user", None)
    if user is not None and user.is_authenticated and hasattr(user, "profile"):
        value = getattr(user.profile, key, "") or ""
        if value:
            return value
    try:
        return request.session.get(f"pref_{key}") or default
    except AttributeError:
        return default


def clean(key, value):
    value = (value or "").strip()
    if key == "food_region":
        return value if value in _region_keys() else ""
    if key == "month_system":
        return value if value in dict(MONTH_SYSTEMS) else ""
    if key == "native_state":
        return value if value in STATE_REGION else ""
    return ""


def save(request, **values):
    """Store each given preference (blank clears it) in the session and, when signed in, on the profile.

    Choosing a native state clears an older food-region pick, so the Aahaar page follows the state again.
    """
    values = {k: clean(k, v) for k, v in values.items() if k in FIELDS}
    if "native_state" in values and "food_region" not in values:
        values["food_region"] = ""
    for k, v in values.items():
        request.session[f"pref_{k}"] = v
    user = request.user
    if user.is_authenticated and hasattr(user, "profile"):
        for k, v in values.items():
            setattr(user.profile, k, v)
        user.profile.save(update_fields=list(values) + ["updated_at"])
    return values


def food_region(request, city="", lat=None, lon=None):
    """The region to open first: chosen region, else native state, else where the person is now."""
    chosen = clean("food_region", get(request, "food_region"))
    if chosen:
        return chosen
    native = clean("native_state", get(request, "native_state"))
    if native:
        return STATE_REGION[native]
    from .aahaar_foods import REGIONS
    return region_for_place(city, lat, lon) or REGIONS[0]["key"]


def month_system(request):
    return clean("month_system", get(request, "month_system")) or "purnimanta"


def month_label(system):
    return "Amanta" if system == "amanta" else "Purnimanta"


def month_in_system(purnimanta_name, krishna, system):
    """A Purnimanta month name told in ``system``: in Amanta, Krishna paksha belongs to the previous month.

    Shukla paksha (and Purnima) carries the same name in both systems.
    """
    name = (purnimanta_name or "").strip()
    if system != "amanta" or not krishna or not name:
        return name
    from .panchang_engine import LUNAR_MONTHS
    adhik = name.startswith("Adhik ")
    base = name.replace("Adhik ", "", 1)
    if base not in LUNAR_MONTHS:
        return name
    return ("Adhik " if adhik else "") + LUNAR_MONTHS[(LUNAR_MONTHS.index(base) - 1) % 12]


def panchang_month(request, panchang):
    """The month of a get_panchang() result in this person's chosen system."""
    key = "amanta_month" if month_system(request) == "amanta" else "purnimanta_month"
    return panchang.get(key) or panchang.get("purnimanta_month") or ""
