# core/utils/cities.py
"""
Cities that have their own daily pages: /aaj-ka-panchang/<city>/, /aaj-ka-choghadiya/<city>/, /aaj-ki-hora/<city>/.

Varanasi and Delhi are shown together on /aaj-ka-panchang/ itself, so their panchang slugs redirect there.
To add a city: append it here (key = URL slug); the sitemaps and the daily 05:30 IST build pick it up.
"""
from . import festival_calculations as fc

CITIES = [
    {"key": "varanasi", "name": ("Varanasi", "वाराणसी"), "query": "Varanasi",
     "lat": fc.VARANASI["lat"], "lon": fc.VARANASI["lon"], "tz": fc.VARANASI["tz"]},
    {"key": "delhi", "name": ("Delhi", "दिल्ली"), "query": "New Delhi", "lat": 28.6139, "lon": 77.2090, "tz": "Asia/Kolkata"},
    {"key": "mumbai", "name": ("Mumbai", "मुंबई"), "query": "Mumbai", "lat": 19.0760, "lon": 72.8777, "tz": "Asia/Kolkata"},
    {"key": "kolkata", "name": ("Kolkata", "कोलकाता"), "query": "Kolkata", "lat": 22.5726, "lon": 88.3639, "tz": "Asia/Kolkata"},
    {"key": "lucknow", "name": ("Lucknow", "लखनऊ"), "query": "Lucknow", "lat": 26.8467, "lon": 80.9462, "tz": "Asia/Kolkata"},
    {"key": "patna", "name": ("Patna", "पटना"), "query": "Patna", "lat": 25.5941, "lon": 85.1376, "tz": "Asia/Kolkata"},
    {"key": "jaipur", "name": ("Jaipur", "जयपुर"), "query": "Jaipur", "lat": 26.9124, "lon": 75.7873, "tz": "Asia/Kolkata"},
    {"key": "bhopal", "name": ("Bhopal", "भोपाल"), "query": "Bhopal", "lat": 23.2599, "lon": 77.4126, "tz": "Asia/Kolkata"},
    {"key": "ahmedabad", "name": ("Ahmedabad", "अहमदाबाद"), "query": "Ahmedabad", "lat": 23.0225, "lon": 72.5714, "tz": "Asia/Kolkata"},
    {"key": "bengaluru", "name": ("Bengaluru", "बेंगलुरु"), "query": "Bengaluru", "lat": 12.9716, "lon": 77.5946, "tz": "Asia/Kolkata"},
    {"key": "pune", "name": ("Pune", "पुणे"), "query": "Pune", "lat": 18.5204, "lon": 73.8567, "tz": "Asia/Kolkata"},
]
BY_KEY = {c["key"]: c for c in CITIES}
DEFAULT = "varanasi"
# Shown together on /aaj-ka-panchang/; every other city has its own panchang page
ON_PANCHANG_INDEX = ("varanasi", "delhi")
PANCHANG_PAGES = [c for c in CITIES if c["key"] not in ON_PANCHANG_INDEX]


def get(key):
    return BY_KEY.get(key)
