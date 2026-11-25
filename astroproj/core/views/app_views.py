# core/views/app_views.py
"""
Install-as-app (PWA) and the morning notification.

    /manifest.webmanifest, /manifest-hi.webmanifest   the app's name, icons and start page (English / Hindi)
    /sw.js                                            the service worker, at the root so it covers /hi/ as well
    /offline/                                         shown when there is no network and the page is not saved
    /push/subscribe/, /push/unsubscribe/              store / forget a browser's push address (core/utils/webpush.py)

These live outside i18n_patterns (astroproj/urls.py): one app and one service worker for both languages.
"""
import json

from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import render
from django.templatetags.static import static
from django.views.decorators.cache import cache_control
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from ..utils import cities, webpush

SW_VERSION = 1       # bump when sw.js changes in a way that must drop the old caches


def _manifest(hindi):
    name = settings.SITE_NAME_HI if hindi else settings.SITE_NAME
    start = "/hi/aaj-ka-panchang/" if hindi else "/aaj-ka-panchang/"
    return {
        "id": start,
        "name": name,
        "short_name": "पंचांग" if hindi else "Panchang",
        "description": ("आज का पंचांग, राशिफल, चौघड़िया, व्रत और त्योहार, काशी के नियमों से।" if hindi else
                        "Today's panchang, rashifal, choghadiya, vrat and festival dates by Kashi rules."),
        "lang": "hi" if hindi else "en",
        "start_url": start + "?source=app",
        "scope": "/",
        "display": "standalone",
        "background_color": "#fffaf0",
        "theme_color": "#8b4513",
        "icons": [
            {"src": static("icons/icon-192.png"), "sizes": "192x192", "type": "image/png", "purpose": "any"},
            {"src": static("icons/icon-512.png"), "sizes": "512x512", "type": "image/png", "purpose": "any"},
            {"src": static("icons/maskable-512.png"), "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
        ],
        "shortcuts": [
            {"name": "आज का पंचांग" if hindi else "Aaj Ka Panchang", "url": start},
            {"name": "आज का राशिफल" if hindi else "Rashifal", "url": ("/hi" if hindi else "") + "/rashifal/"},
            {"name": "चौघड़िया" if hindi else "Choghadiya", "url": ("/hi" if hindi else "") + "/aaj-ka-choghadiya/"},
            {"name": "हिन्दू कैलेंडर" if hindi else "Hindu Calendar", "url": ("/hi" if hindi else "") + "/hindu-calendar/"},
        ],
    }


@cache_control(public=True, max_age=86400)
def manifest(request, hindi=False):
    return HttpResponse(json.dumps(_manifest(hindi), ensure_ascii=False), content_type="application/manifest+json")


@cache_control(no_cache=True, max_age=0)     # browsers check for a new worker on every visit
def service_worker(request):
    response = render(request, "app/sw.js", {
        "version": SW_VERSION,
        "precache": [static("css/pages.css"), static("icons/icon-192.png"), static("icons/badge-96.png")],
        "badge": static("icons/badge-96.png"), "icon": static("icons/icon-192.png"),
    }, content_type="application/javascript")
    response["Service-Worker-Allowed"] = "/"
    return response


def offline(request):
    return render(request, "app/offline.html")


def _json(request):
    if len(request.body) > 4096:
        return None
    try:
        data = json.loads(request.body)
    except (ValueError, UnicodeDecodeError):
        return None
    return data if isinstance(data, dict) else None


# No CSRF token: the pages that carry the button are cached and shared, and this stores nothing about a person.
# The endpoint must be a real browser push service (webpush.allowed_endpoint), so it cannot be pointed elsewhere.
@csrf_exempt
@require_POST
def push_subscribe(request):
    data = _json(request)
    sub = (data or {}).get("subscription") or {}
    keys = sub.get("keys") or {}
    endpoint, p256dh, auth = sub.get("endpoint", ""), keys.get("p256dh", ""), keys.get("auth", "")
    if not (webpush.enabled() and isinstance(endpoint, str) and webpush.allowed_endpoint(endpoint)
            and isinstance(p256dh, str) and isinstance(auth, str)
            and 0 < len(endpoint) <= 1000 and 0 < len(p256dh) <= 200 and 0 < len(auth) <= 100):
        return HttpResponseBadRequest("bad subscription")
    lang = "hi" if data.get("lang") == "hi" else "en"
    city = data.get("city") if data.get("city") in cities.BY_KEY else cities.DEFAULT
    from ..models import PushSubscription
    PushSubscription.objects.update_or_create(endpoint=endpoint, defaults={
        "p256dh": p256dh, "auth": auth, "lang": lang, "city": city, "failures": 0})
    return JsonResponse({"ok": True, "city": city, "lang": lang})


@csrf_exempt
@require_POST
def push_unsubscribe(request):
    data = _json(request) or {}
    endpoint = data.get("endpoint")
    if isinstance(endpoint, str) and endpoint:
        from ..models import PushSubscription
        PushSubscription.objects.filter(endpoint=endpoint).delete()
    return JsonResponse({"ok": True})
