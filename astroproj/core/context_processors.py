import os
import re

from django.conf import settings


def site(request):
    """Site-wide SEO / ads settings for templates."""
    base = getattr(settings, "SITE_URL", "").rstrip("/") or request.build_absolute_uri("/").rstrip("/")
    hindi = request.path == "/hi" or request.path.startswith("/hi/")
    en_path = re.sub(r"^/hi(?=/|$)", "", request.path) or "/"
    return {
        "hindi": hindi,
        "EN_PATH": en_path,
        "HI_PATH": "/hi" + en_path,
        "ASSET_V": int(os.path.getmtime(settings.BASE_DIR / "static/css/pages.css")),
        "SOURCE_URL": getattr(settings, "SOURCE_URL", ""),
        # The brand reads in Devanagari on the Hindi pages
        "SITE_NAME": getattr(settings, "SITE_NAME_HI" if hindi else "SITE_NAME", "Varanasi Panchang"),
        "SITE_TAGLINE": getattr(settings, "SITE_TAGLINE_HI" if hindi else "SITE_TAGLINE", "Know Your Time"),
        "SITE_URL": base,
        "SITE_DESCRIPTION": getattr(settings, "SITE_DESCRIPTION", ""),
        "CANONICAL_URL": base + request.path,
        "ADSENSE_CLIENT_ID": getattr(settings, "ADSENSE_CLIENT_ID", ""),
        "ADSENSE_SLOT_ID": getattr(settings, "ADSENSE_SLOT_ID", ""),
        "GA_MEASUREMENT_ID": getattr(settings, "GA_MEASUREMENT_ID", ""),
        # Morning notification (Web Push); empty = the button stays hidden. The private key never reaches a page.
        "VAPID_PUBLIC_KEY": getattr(settings, "VAPID_PUBLIC_KEY", "") if getattr(settings, "VAPID_PRIVATE_KEY", "") else "",
        "SITE_OWNER": getattr(settings, "SITE_OWNER", ""),
        "CONTACT_EMAIL": getattr(settings, "CONTACT_EMAIL", ""),
        "CONTACT_PHONE": getattr(settings, "CONTACT_PHONE", ""),
        "BUSINESS_ADDRESS": getattr(settings, "BUSINESS_ADDRESS", ""),
        "GRIEVANCE_OFFICER": getattr(settings, "GRIEVANCE_OFFICER", ""),
        "JURISDICTION_CITY": getattr(settings, "JURISDICTION_CITY", ""),
    }
