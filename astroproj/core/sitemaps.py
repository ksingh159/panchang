from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from django.conf import settings

from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.utils import timezone

from core.utils import festival_calculations as fc
from core.utils import grahan as gr
from core.utils import muhurat as mu


def _years():
    y = timezone.now().year
    return range(y - 1, y + 4)


class BilingualSitemap(Sitemap):
    """Lists each page in English and under /hi/, each entry naming the other as its hreflang alternate."""
    i18n = True
    alternates = True
    x_default = True


class StaticSitemap(BilingualSitemap):
    changefreq = "weekly"
    priority = 0.6

    def items(self):
        return ["home", "festival_calendar", "panchang_finder", "shubh_muhurat", "auspicious_yogas", "grahan_calendar", "aahaar",
                "compatibility", "create_kundali", "panchang", "kumbh_mela", "about", "how_it_works", "faq", "contact", "privacy", "terms",
                "refund_policy", "shipping_policy", "blog"]

    def location(self, item):
        return reverse(item)


class AajPanchangSitemap(BilingualSitemap):
    """/aaj-ka-panchang/ changes every morning; lastmod is when today's page was computed (05:30 IST)."""
    changefreq = "daily"
    priority = 1.0

    def items(self):
        return ["aaj_ka_panchang"]

    def location(self, item):
        return reverse(item)

    def lastmod(self, item):
        from core.utils import aaj_panchang as ap
        d = ap.today_ist()
        return ap.stamp_for(d) or ap.IST.localize(datetime.combine(d, time(0, 0)))


class CityPanchangSitemap(BilingualSitemap):
    """/aaj-ka-panchang/<city>/ for every city in utils/cities.py except the two on /aaj-ka-panchang/ itself."""
    changefreq = "daily"
    priority = 0.9

    def items(self):
        from core.utils import cities
        return [c["key"] for c in cities.PANCHANG_PAGES]

    def location(self, key):
        return reverse("aaj_ka_panchang_city", args=[key])

    def lastmod(self, key):
        from core.utils import aaj_panchang as ap
        d = ap.today_ist()
        return ap.city_stamp_for(key, d) or ap.IST.localize(datetime.combine(d, time(0, 0)))


class DayPeriodsSitemap(BilingualSitemap):
    """/aaj-ka-choghadiya/ and /aaj-ki-hora/, bare (Varanasi) and for each other city."""
    changefreq = "daily"
    priority = 0.8

    def items(self):
        from core.utils import cities
        return [(page, c["key"]) for page in ("choghadiya", "hora") for c in cities.CITIES]

    def location(self, item):
        from core.utils import cities
        page, key = item
        return reverse(page) if key == cities.DEFAULT else reverse(f"{page}_city", args=[key])


class RashifalSitemap(BilingualSitemap):
    """/rashifal/ and one page per rashi; all rebuilt every morning."""
    changefreq = "daily"
    priority = 0.9

    def items(self):
        from core.utils import rashifal
        return [None] + rashifal.SLUGS

    def location(self, slug):
        return reverse("rashifal") if slug is None else reverse("rashifal_sign", args=[slug])

    def lastmod(self, slug):
        from core.utils import aaj_panchang as ap
        from core.utils import rashifal
        d = ap.today_ist()
        return rashifal.stamp_for(d) or ap.IST.localize(datetime.combine(d, time(0, 0)))


class VratSitemap(BilingualSitemap):
    changefreq = "monthly"
    priority = 0.8

    def items(self):
        from core.utils import vrat
        return [("hub", None)] + [(k, y) for y in _years() for k in vrat.KINDS]

    def location(self, item):
        if item[0] == "hub":
            return reverse("vrat_hub")
        return reverse("vrat_list", args=[item[0], item[1]])


class HinduCalendarSitemap(BilingualSitemap):
    """/hindu-calendar/ and each month from last year to three years ahead (as the festival years)."""
    changefreq = "monthly"
    priority = 0.8

    def items(self):
        from core.utils import hindu_calendar as hc
        return [None] + [(y, s) for y in _years() for s in hc.MONTH_SLUGS]

    def location(self, item):
        if item is None:
            return reverse("hindu_calendar")
        return reverse("hindu_calendar_month", args=list(item))


class DailyPanchangSitemap(BilingualSitemap):
    changefreq = "daily"
    priority = 0.7

    def items(self):
        today = timezone.now().date()
        return [today + timedelta(days=i) for i in range(-30, 366)]

    def location(self, d):
        return reverse("panchang_on_date", args=[d.isoformat()])


class FestivalYearSitemap(BilingualSitemap):
    changefreq = "monthly"
    priority = 0.8

    def items(self):
        return list(_years())

    def location(self, y):
        return reverse("festival_year", args=[y])


class FestivalSitemap(BilingualSitemap):
    changefreq = "monthly"
    priority = 0.9

    def items(self):
        seen = []
        for y in _years():
            slugs = {f["slug"] for f in fc.get_festivals_for_year(y)
                     if f["importance"] == "high" or f["category"] == "Ekadashi"}
            seen += [(y, s) for s in sorted(slugs)]
        return seen

    def location(self, item):
        return reverse("festival_detail", args=[item[0], item[1]])


class MuhuratSitemap(BilingualSitemap):
    changefreq = "monthly"
    priority = 0.8

    def items(self):
        return [(p, y) for y in _years() for p in mu.PURPOSES]

    def location(self, item):
        return reverse("muhurat_purpose", args=[item[0], item[1]])


class YogaSitemap(BilingualSitemap):
    changefreq = "monthly"
    priority = 0.7

    def items(self):
        return [(k, y) for y in _years() for k in mu.YOGA_INFO]

    def location(self, item):
        return reverse("yoga_calendar", args=[item[0], item[1]])


class GrahanSitemap(BilingualSitemap):
    changefreq = "monthly"
    priority = 0.8

    def items(self):
        return [("year", y) for y in _years()] + [("one", e["slug"]) for y in _years() for e in gr.eclipses_in_year(y)]

    def location(self, item):
        return reverse("grahan_year" if item[0] == "year" else "grahan_detail", args=[item[1]])


class ArticleSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.6

    def items(self):
        from .models import Article
        return Article.objects.filter(status="published")

    def lastmod(self, a):
        # USE_TZ is off, so updated_at is naive; Google rejects a <lastmod> time with no offset.
        return a.updated_at.replace(tzinfo=ZoneInfo(settings.TIME_ZONE))


SITEMAPS = {
    "today": AajPanchangSitemap,
    "cities": CityPanchangSitemap,
    "choghadiya-hora": DayPeriodsSitemap,
    "vrat": VratSitemap,
    "hindu-calendar": HinduCalendarSitemap,
    "rashifal": RashifalSitemap,
    "static": StaticSitemap,
    "panchang": DailyPanchangSitemap,
    "festival-years": FestivalYearSitemap,
    "festivals": FestivalSitemap,
    "muhurat": MuhuratSitemap,
    "yogas": YogaSitemap,
    "grahan": GrahanSitemap,
    "articles": ArticleSitemap,
}
