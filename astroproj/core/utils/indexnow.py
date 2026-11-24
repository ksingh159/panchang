# core/utils/indexnow.py
"""
Tell Bing (and the other IndexNow engines: Yandex, Seznam, Naver) that a page changed, so they re-read it soon.
Google does not take IndexNow; it re-reads on its own, helped by the sitemap's <lastmod>.

Off until INDEXNOW_KEY is set (any 8-128 letters, digits or dashes). The key is served at /<key>.txt to prove
the site is ours (core/urls.py -> seo_views.indexnow_key).
"""
import json
import logging
import urllib.request

from django.conf import settings
from django.urls import reverse
from django.utils import translation

logger = logging.getLogger(__name__)
ENDPOINT = "https://api.indexnow.org/indexnow"


def key():
    return getattr(settings, "INDEXNOW_KEY", "") or ""


def ping(paths):
    """POST the site's own URLs to IndexNow. Returns a short status line; never raises."""
    k, base = key(), (getattr(settings, "SITE_URL", "") or "").rstrip("/")
    if not k or not base:
        return "off (INDEXNOW_KEY or SITE_URL not set)"
    host = base.split("://", 1)[-1].split("/", 1)[0]
    body = json.dumps({"host": host, "key": k, "keyLocation": f"{base}/{k}.txt",
                       "urlList": [base + p for p in paths]}).encode()
    req = urllib.request.Request(ENDPOINT, data=body, headers={"Content-Type": "application/json; charset=utf-8"})
    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            return f"sent {len(paths)} URLs, HTTP {res.status}"
    except Exception as e:          # a failed ping must never stop the daily job
        logger.warning("IndexNow ping failed: %s", e)
        return f"failed: {e}"


def ping_today():
    with translation.override("en"):
        en = reverse("aaj_ka_panchang")
    return ping([en, "/hi" + en])
