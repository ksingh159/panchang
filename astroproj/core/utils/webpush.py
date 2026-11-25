# core/utils/webpush.py
"""
The morning panchang notification (Web Push, no app needed).

    enabled()                 True when the VAPID keys are set (Railway: VAPID_PUBLIC_KEY, VAPID_PRIVATE_KEY)
    allowed_endpoint(url)     only real browser push services may be stored (we POST to these addresses daily)
    morning_message(lang, city_key, d)   {"title", "body", "url", "tag"} built from today's Aaj Ka Panchang
    send_morning()            one message to every subscribed browser; gone browsers are deleted

Keys: run ``python manage.py vapid_keys`` once and put the two lines it prints into Railway's variables. Never
change them afterwards: every browser subscribed with the old public key would stop receiving messages.
What we store per browser: the push address and its two keys, the language and the city. No name, no email.
"""
import json
import logging
from datetime import timedelta
from urllib.parse import urlparse

from django.conf import settings
from django.utils import timezone, translation

logger = logging.getLogger(__name__)

# Push services of Chrome/Edge/Android, Firefox, Safari (macOS and iOS 16.4+) and Windows
PUSH_HOSTS = ("fcm.googleapis.com", "android.googleapis.com", "updates.push.services.mozilla.com",
              "push.services.mozilla.com", "web.push.apple.com", "notify.windows.com")
MAX_FAILURES = 3          # a browser that fails three mornings in a row (not 404/410) is dropped too
TTL = 6 * 3600            # a phone that is off until noon still gets the morning message; later it is stale

WEEKDAYS_HI = ["सोमवार", "मंगलवार", "बुधवार", "गुरुवार", "शुक्रवार", "शनिवार", "रविवार"]
MONTHS_HI = ["जनवरी", "फ़रवरी", "मार्च", "अप्रैल", "मई", "जून", "जुलाई", "अगस्त", "सितंबर", "अक्टूबर", "नवंबर", "दिसंबर"]


def public_key():
    return getattr(settings, "VAPID_PUBLIC_KEY", "") or ""


def enabled():
    return bool(public_key() and getattr(settings, "VAPID_PRIVATE_KEY", ""))


def allowed_endpoint(url):
    try:
        u = urlparse(url)
    except ValueError:
        return False
    host = (u.hostname or "").lower()
    return u.scheme == "https" and any(host == h or host.endswith("." + h) for h in PUSH_HOSTS)


def _city(key):
    from . import aaj_panchang as ap
    if key in ("varanasi", "delhi"):
        snap = ap.today_snapshot()
        return next(c for c in snap["cities"] if c["key"] == key), snap["festivals_today"]
    return ap.city_snapshot(key)["city"], ap.today_snapshot()["festivals_today"]


def _url(lang, city_key):
    from django.urls import reverse
    from . import cities
    with translation.override(lang):
        if city_key in cities.ON_PANCHANG_INDEX:
            return reverse("aaj_ka_panchang")
        return reverse("aaj_ka_panchang_city", args=[city_key])


def morning_message(lang, city_key, d=None):
    from ..templatetags.vp import fest, t
    from . import aaj_panchang as ap
    from . import cities
    d = d or ap.today_ist()
    place = cities.get(city_key) or cities.get(cities.DEFAULT)
    c, festivals = _city(place["key"])
    hm = lambda x: x.strftime("%H:%M") if x else ""
    r0, r1 = c["rahu_kaal"]
    with translation.override(lang):
        if lang == "hi":
            tithi = " ".join("पक्ष" if w == "Paksha" else t(w) for w in (c["paksha_tithi"] or "").split())
            title = f"आज का पंचांग · {WEEKDAYS_HI[d.weekday()]}, {d.day} {MONTHS_HI[d.month - 1]}"
            body = f"{tithi}, {t(c['nakshatra'])} नक्षत्र। राहु काल {hm(r0)}–{hm(r1)} ({place['name'][1]})।"
            if festivals:
                body += " आज: " + ", ".join(fest(f["name"]) for f in festivals[:2]) + "।"
        else:
            title = f"Aaj Ka Panchang · {d:%a} {d.day} {d:%b}"
            body = f"{c['paksha_tithi']}, {c['nakshatra']} nakshatra. Rahu Kaal {hm(r0)}–{hm(r1)} ({place['name'][0]})."
            if festivals:
                body += " Today: " + ", ".join(f["name"] for f in festivals[:2]) + "."
    return {"title": title, "body": body, "url": _url(lang, place["key"]), "tag": f"panchang-{d.isoformat()}"}


def send(sub, message):
    """Send one message. Returns "ok", "gone" (browser unsubscribed: delete it) or "error"."""
    from pywebpush import WebPushException, webpush
    try:
        webpush(subscription_info={"endpoint": sub.endpoint, "keys": {"p256dh": sub.p256dh, "auth": sub.auth}},
                data=json.dumps(message, ensure_ascii=False),
                vapid_private_key=settings.VAPID_PRIVATE_KEY,
                vapid_claims={"sub": settings.VAPID_SUBJECT},
                ttl=TTL, timeout=10)
        return "ok"
    except WebPushException as e:
        status = getattr(e.response, "status_code", None)
        if status in (404, 410):
            return "gone"
        logger.warning("Web push failed (%s) for %s", status, urlparse(sub.endpoint).hostname)
        return "error"
    except Exception:
        logger.exception("Web push failed for %s", urlparse(sub.endpoint).hostname)
        return "error"


def send_morning(d=None):
    """The 05:30 IST job: one message per subscribed browser (messages built once per language and city)."""
    from ..models import PushSubscription
    if not enabled():
        return {"skipped": "VAPID keys not set"}
    now = timezone.now()
    built, counts = {}, {"ok": 0, "gone": 0, "error": 0}
    for sub in PushSubscription.objects.all().iterator():
        if sub.last_sent_at and now - sub.last_sent_at < timedelta(hours=12):
            continue                                            # already sent this morning (job re-run)
        key = (sub.lang, sub.city)
        if key not in built:
            try:
                built[key] = morning_message(*key, d=d)
            except Exception:
                logger.exception("Morning message for %s failed", key)
                built[key] = None
        if built[key] is None:
            continue
        result = send(sub, built[key])
        counts[result] += 1
        if result == "gone":
            sub.delete()
        elif result == "ok":
            PushSubscription.objects.filter(pk=sub.pk).update(last_sent_at=now, failures=0)
        else:
            if sub.failures + 1 >= MAX_FAILURES:
                sub.delete()
            else:
                PushSubscription.objects.filter(pk=sub.pk).update(failures=sub.failures + 1)
    return counts
