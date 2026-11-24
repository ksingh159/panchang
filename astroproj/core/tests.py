from datetime import date

from django.test import TestCase

from core.utils import festival_calculations as fc
from core.utils import panchang_store as ps


# Dates published by Kashi (Varanasi) panchangs / Kashi Vidvat Parishad.
# Each entry was a case where naive rules disagree, so keep them pinned.
VERIFIED = {
    2024: {
        "maha-shivaratri": date(2024, 3, 8),
        "holika-dahan": date(2024, 3, 24),
        "holi": date(2024, 3, 25),            # penumbral eclipse on 25th does not shift Holi
        "raksha-bandhan": date(2024, 8, 19),
        "krishna-janmashtami": date(2024, 8, 26),
        "diwali": date(2024, 10, 31),         # Kashi Vidvat Parishad decision
        "govardhan-puja": date(2024, 11, 2),
        "bhai-dooj": date(2024, 11, 3),
    },
    2025: {
        "makar-sankranti": date(2025, 1, 14),
        "mauni-amavasya": date(2025, 1, 29),
        "vasant-panchami": date(2025, 2, 2),
        "maha-shivaratri": date(2025, 2, 26),
        "holika-dahan": date(2025, 3, 13),
        "holi": date(2025, 3, 14),
        "rama-navami": date(2025, 4, 6),
        "akshaya-tritiya": date(2025, 4, 30),
        "ganga-dussehra": date(2025, 6, 5),
        "nirjala-ekadashi": date(2025, 6, 6),
        "guru-purnima": date(2025, 7, 10),
        "raksha-bandhan": date(2025, 8, 9),   # Bhadra over Aparahna on the 8th
        "ganesh-chaturthi": date(2025, 8, 27),
        "vijaya-dashami": date(2025, 10, 2),
        "dhanteras": date(2025, 10, 18),
        "diwali": date(2025, 10, 20),
        "bhai-dooj": date(2025, 10, 23),
        "chhath-puja-sandhya-arghya": date(2025, 10, 27),
        "devutthana-ekadashi": date(2025, 11, 1),  # kshaya Dwadashi -> Smarta fast a day earlier
        "kalabhairav-jayanti": date(2025, 11, 12),
    },
    2026: {
        "maha-shivaratri": date(2026, 2, 15),
        "holika-dahan": date(2026, 3, 2),     # Bhadra-puchha night of 2nd
        "holi": date(2026, 3, 4),             # Chandra grahan on 3rd
        "diwali": date(2026, 11, 8),
        "govardhan-puja": date(2026, 11, 10),
        "bhai-dooj": date(2026, 11, 11),
    },
}


class FestivalRegressionTests(TestCase):
    def test_verified_dates(self):
        for year, expected in VERIFIED.items():
            got = {}
            for f in fc.compute_festivals(year):
                got.setdefault(f["slug"], f["date"])
            for slug, d in expected.items():
                with self.subTest(year=year, slug=slug):
                    self.assertEqual(got.get(slug), d)


class PanchangStoreTests(TestCase):
    def test_adhik_maas_2026(self):
        rows = ps.find_events("amanta_masa", date(2026, 1, 1), date(2026, 12, 31), adhik=True)
        self.assertEqual([r.name for r in rows], ["Jyeshtha"])

    def test_year_computed_once(self):
        self.assertTrue(ps.ensure_year(2031))
        self.assertFalse(ps.ensure_year(2031))
        n = ps.find_events("tithi", date(2031, 1, 1), date(2031, 12, 31), name="Ekadashi")
        self.assertTrue(24 <= len(n) <= 27)


class MatchmakingTests(TestCase):
    def setUp(self):
        from django.contrib.auth.models import User
        from core.models import City
        City.objects.create(geoname_id=1253405, name="Varanasi", ascii_name="Varanasi", search_name="varanasi",
                            state="Uttar Pradesh", country="India", country_code="IN", latitude=25.3176,
                            longitude=82.9739, timezone="Asia/Kolkata", population=1164404, slug="varanasi",
                            aliases="|banaras|benares|kashi|")
        self.user = User.objects.create_user("m", "m@example.com", "pw-12345!")
        self.client.force_login(self.user)

    def test_moola_partner_and_remedies(self):
        import json
        payload = {
            # 1990-01-24 06:00 IST -> Moon in Moola (the nakshatra that used to crash milan)
            "person1_name": "A", "person1_birth_date": "1990-01-24", "person1_birth_time": "06:00",
            "person1_birth_place": "Banaras",
            "person2_name": "B", "person2_birth_date": "1992-05-10", "person2_birth_time": "14:30",
            "person2_birth_place": "Varanasi, Uttar Pradesh, India",
        }
        r = self.client.post("/compatibility/calculate/", data=json.dumps(payload), content_type="application/json")
        data = r.json()
        self.assertTrue(data["success"], data.get("error"))
        self.assertEqual(data["person1"]["nakshatra"], "Mula")
        for key in ("gana", "yoni", "rajju", "vedha", "mahendra", "stree_dirgha", "individual"):
            self.assertIn(key, data["doshas"])

    def test_bhakoot_navpancham_is_zero(self):
        from core.utils.kundali_milan import calculate_bhakoot
        self.assertEqual(calculate_bhakoot("Dhanu", "Mesh")["score"], 0)   # 5/9
        self.assertEqual(calculate_bhakoot("Mesh", "Mesh")["score"], 7)    # 1/1
        self.assertEqual(calculate_bhakoot("Mesh", "Tula")["score"], 7)    # 7/7
        self.assertEqual(calculate_bhakoot("Mesh", "Kanya")["score"], 0)   # 6/8


class FestivalCalendarTests(TestCase):
    def test_every_event_belongs_to_its_year(self):
        for f in fc.compute_festivals(2026):
            with self.subTest(slug=f["slug"]):
                self.assertEqual(f["date"].year, 2026)

    def test_kharmas_listed_under_january_not_december(self):
        months = {m["name"]: m["items"] for m in self.client.get("/festivals/2026/").context["months"]}
        self.assertTrue(all(e["date"].year == 2026 for e in months["December"]))
        carried = [e for e in months["January"] if e["slug"] == "kharmas"]
        self.assertEqual(carried[0]["date"].year, 2025)

    def test_kharmas_page_gives_times_panchang_and_reading_text(self):
        res = self.client.get("/festivals/2027/kharmas/")
        self.assertContains(res, "Monday, 15 March 2027, 06:44 IST")     # Sun enters Meena
        self.assertContains(res, "still running as 2027 opens")         # the Dec 2026 Kharmas
        self.assertContains(res, "Panchang of the day (Varanasi)")
        self.assertContains(res, "/panchang/date/2027-03-15/")
        self.assertContains(res, "Why is it called Kharmas?")
        self.assertContains(res, "/shubh-muhurat/vivah/2027/")
        hi = self.client.get("/hi/festivals/2027/kharmas/").content.decode()
        self.assertIn("खरमास क्या है?", hi)
        self.assertNotIn("What is Kharmas?", hi)
        self.assertNotIn("until ", hi)

    def test_every_festival_page_shows_the_days_panchang(self):
        res = self.client.get("/festivals/2026/diwali/")
        self.assertContains(res, "Panchang of the day (Varanasi)")
        self.assertContains(res, "Full panchang for this day")

    def test_current_year_opens_at_current_month(self):
        from unittest.mock import patch
        from datetime import datetime
        import pytz
        now = pytz.utc.localize(datetime(2026, 10, 31, 6))
        with patch("core.views.astro_views.timezone") as clock:
            clock.now.return_value = now
            names = [m["name"] for m in self.client.get("/festivals/2026/").context["months"]]
        self.assertEqual(names[:4], ["October", "November", "December", "January"])
        self.assertEqual(names[-1], "September")


class PanchangMonthTests(TestCase):
    def test_lunar_month_is_not_the_solar_month(self):
        from datetime import datetime
        from core.utils.astro_calculations import lunar_month_names
        self.assertEqual(lunar_month_names(datetime(2026, 10, 31, 6)), ("Ashwina", "Kartika"))
        self.assertEqual(lunar_month_names(datetime(2026, 3, 10, 6)), ("Phalguna", "Chaitra"))


class GrahanTests(TestCase):
    def test_catalogue(self):
        from core.utils import grahan as gr
        got = {e["slug"]: e["subtype"] for e in gr.eclipses_in_year(2026)}
        self.assertEqual(got, {"2026-02-17-surya-grahan": "Annular", "2026-03-03-chandra-grahan": "Total",
                               "2026-08-12-surya-grahan": "Total", "2026-08-28-chandra-grahan": "Partial"})

    def test_sutak_only_where_visible(self):
        from core.utils import grahan as gr
        delhi = (28.61, 77.21, "Asia/Kolkata")
        holi = gr.local_view(gr.find("2026-03-03-chandra-grahan"), *delhi)
        self.assertTrue(holi["sutak_applies"])
        self.assertEqual(holi["sutak_hours"], 9)
        self.assertEqual((holi["sparsha"] - holi["sutak_start"]).total_seconds(), 9 * 3600)
        self.assertEqual(holi["sutak_end"], holi["moksha"])
        self.assertFalse(gr.local_view(gr.find("2026-08-12-surya-grahan"), *delhi)["sutak_applies"])

    def test_penumbral_has_no_sutak(self):
        from core.utils import grahan as gr
        view = gr.local_view(gr.find("2027-02-20-chandra-grahan"), 28.61, 77.21, "Asia/Kolkata")
        self.assertTrue(view["visible"])
        self.assertFalse(view["sutak_applies"])

    def test_pages(self):
        for url in ("/grahan/", "/grahan/2027/", "/grahan/2027-08-02-surya-grahan/", "/aahaar/"):
            self.assertEqual(self.client.get(url).status_code, 200, url)
        self.assertEqual(self.client.get("/grahan/2027-08-03-surya-grahan/").status_code, 404)


class KundaliPrivacyTests(TestCase):
    def setUp(self):
        from django.contrib.auth.models import User
        from core.models import Kundali
        self.owner = User.objects.create_user("o", "o@example.com", "pw-12345!")
        self.other = User.objects.create_user("x", "x@example.com", "pw-12345!")
        self.kundali = Kundali.objects.create(
            user=self.owner, name="Saved", birth_date="1990-01-01 12:00:00", birth_place="Delhi", birth_lat=28.6,
            birth_lon=77.2, birth_timezone="Asia/Kolkata", kundali_type="groom",
            planetary_positions={"Moon": {"sign": "Taurus"}}, divisional_charts={"d1": {}},
            ascendant={"sign_sidereal": "Leo", "degree_in_sign": 10}, dashas=[], houses={}, gunmilan={})

    def test_list_and_detail_for_owner(self):
        self.client.force_login(self.owner)
        listing = self.client.get("/my-kundalis/")
        self.assertContains(listing, "Saved")
        self.assertNotContains(listing, "const planetsData")
        detail = self.client.get(f"/kundali/{self.kundali.id}/")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(len(detail.context["current_transits"]["rows"]), 9)

    def test_other_users_are_refused(self):
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(f"/kundali/{self.kundali.id}/").status_code, 404)
        self.assertEqual(self.client.get(f"/api/kundali/{self.kundali.id}/").status_code, 404)

    def test_login_shows_preview_for_kundali_pages(self):
        self.assertContains(self.client.get("/accounts/login/?next=/my-kundalis/"), "kt-card")
        self.assertNotContains(self.client.get("/accounts/login/"), "kt-card")


class YogaLocalTimeTests(TestCase):
    def test_sunrise_edges_move_between_cities(self):
        from core.utils import muhurat as mu
        start, end = date(2026, 11, 1), date(2026, 11, 2)
        mumbai = mu._special_yogas(start, end, 19.076, 72.8777, "Asia/Kolkata")[0]
        kolkata = mu._special_yogas(start, end, 22.5726, 88.3639, "Asia/Kolkata")[0]
        self.assertTrue(mumbai["start_sunrise"])
        self.assertNotEqual(mumbai["start"], kolkata["start"])
        self.assertEqual(mumbai["end"], kolkata["end"])          # a nakshatra ends at one instant
        self.assertNotEqual(mumbai["end_solar"], kolkata["end_solar"])


class MuhuratRuleTests(TestCase):
    DELHI = (28.61, 77.21, "Asia/Kolkata")

    def test_no_capital_goods_on_days_that_forbid_them(self):
        from core.utils import muhurat as mu
        for key in ("vehicle", "property", "machinery", "business", "appliances"):
            self.assertFalse(mu.PURPOSES[key]["weekdays"] & {0, 2, 6}, key)
        for word in ("machinery", "tractor"):
            self.assertNotIn(word, mu.WEEKDAY_GUIDE[6]["buy"])
            self.assertTrue(mu.WEEKDAY_SHOPPING[6]["capital"].startswith("no purchase"))

    def test_vivah_skips_every_blackout(self):
        from core.utils import muhurat as mu
        start, end = date(2027, 1, 1), date(2027, 12, 31)
        dates = [x["date"] for x in mu.muhurat_dates("vivah", start, end, *self.DELHI)]
        self.assertTrue(dates)
        blocks = mu.blocked_periods(start, end, "vivah", *self.DELHI)
        self.assertEqual({"Kharmas", "Holashtak", "Chaturmas", "Pitru Paksha", "Grahan", "Guru Asta", "Shukra Asta"},
                         {b[2] for b in blocks})
        for d in dates:
            self.assertFalse(any(b[0] <= d <= b[1] for b in blocks), d)

    def test_chaturmas_stops_marriage_but_not_groceries(self):
        from core.utils import muhurat as mu
        start, end = date(2027, 8, 20), date(2027, 8, 28)
        self.assertEqual(mu.muhurat_dates("vivah", start, end, *self.DELHI), [])
        self.assertTrue(mu.muhurat_dates("groceries", date(2027, 8, 1), date(2027, 8, 31), *self.DELHI))


class NamaksharTests(TestCase):
    def test_syllables(self):
        from core.utils.namakshar import from_name
        for name, nak, rashi in (("Rahul", "Chitra", "Tula"), ("राहुल", "Chitra", "Tula"), ("Karan", "Mrigashira", "Mithun"),
                                 ("Neha", "Anuradha", "Vrishchik"), ("टीना", "Purva Phalguni", "Simha"), ("Krishna", "Mrigashira", "Mithun")):
            hit = from_name(name)
            self.assertEqual((hit["nakshatra"], hit["rashi"]), (nak, rashi), name)

    def test_milan_by_name_needs_no_birth_details_and_gives_no_dosha_verdict(self):
        import json
        res = self.client.post("/compatibility/calculate/", json.dumps({"mode": "name", "person1_name": "Rahul", "person2_name": "Priya"}),
                               content_type="application/json").json()
        self.assertTrue(res["success"])
        self.assertEqual(len(res["ashtakoot"]["koot_details"]), 8)
        self.assertEqual(res["doshas"], {})


class RemovedRouteTests(TestCase):
    def test_old_eclipse_urls_are_gone(self):
        self.assertEqual(self.client.get("/eclipses/update/").status_code, 404)
        self.assertEqual(self.client.get("/eclipses/1/path/").status_code, 404)

    def test_guest_charts_are_private_to_their_browser(self):
        # Owner's rule (2026-11-18): no sign-up is needed to make a kundali. A guest's chart is saved without a
        # user and only the browser that made it can open it (see KundaliSearchPagesTests for the full flow).
        from core.models import Kundali
        res = self.client.post("/kundali/generate", {"name": "X", "birth_date": "2000-01-01", "birth_time": "06:00",
                                                     "lat": "25.3", "lon": "83.0", "timezone": "Asia/Kolkata"})
        self.assertEqual(res.status_code, 302)
        self.assertIsNone(Kundali.objects.get().user)
        self.assertEqual(self.client_class().get(res["Location"]).status_code, 404)


class HindiSiteTests(TestCase):
    def test_hindi_lives_under_its_own_url_and_english_is_unchanged(self):
        en, hi = self.client.get("/aahaar/"), self.client.get("/hi/aahaar/")
        self.assertEqual((en.status_code, hi.status_code), (200, 200))
        self.assertContains(en, "Aahaar and Ritucharya")
        self.assertContains(hi, "आहार और ऋतुचर्या")
        self.assertContains(hi, '<html lang="hi">')
        self.assertContains(hi, 'hreflang="en"')


# ---------------------------------------------------------------------------
# Paid PDFs, festival puja muhurats, money muhurats, Aahaar rhythm, Grahan years
# ---------------------------------------------------------------------------

from datetime import datetime, timedelta  # noqa: E402

from django.contrib.auth.models import User  # noqa: E402
from django.test import RequestFactory, override_settings  # noqa: E402

TEST_KEYS = dict(RAZORPAY_KEY_ID="rzp_test_x", RAZORPAY_KEY_SECRET="secret", RAZORPAY_WEBHOOK_SECRET="hooksecret",
                 PHONEPE_CLIENT_ID="", PHONEPE_CLIENT_SECRET="", PHONEPE_WEBHOOK_USER="u", PHONEPE_WEBHOOK_PASSWORD="p")


def _kundali(user, name="Test Native"):
    import pytz
    from core.kundali_calculator import KundaliCalculator
    from core.models import Kundali
    from core.view_kundali import save_dashas_to_database
    tz = pytz.timezone("Asia/Kolkata")
    dt = tz.localize(datetime(1991, 10, 22, 9, 5))
    data = KundaliCalculator(dt, 19.076, 72.8777, 5.5).calculate_all_data()
    k = Kundali.objects.create(user=user, name=name, birth_date=dt.replace(tzinfo=None), birth_place="Mumbai",
                               birth_lat=19.076, birth_lon=72.8777, birth_timezone="Asia/Kolkata",
                               planetary_positions=data["d1_chart"], divisional_charts=data["divisional_charts"],
                               houses=data["houses"], ascendant=data["ascendant"], dashas=data["structured_dashas"])
    save_dashas_to_database(k, data["structured_dashas"])
    return k


class CurrencyTests(TestCase):
    def setUp(self):
        self.rf = RequestFactory()

    def _req(self, **meta):
        from django.contrib.sessions.backends.db import SessionStore
        cookies = meta.pop("cookies", {})
        r = self.rf.get("/", **meta)
        r.session = SessionStore()
        r.COOKIES.update(cookies)
        return r

    def test_india_pays_rupees_and_the_world_pays_dollars(self):
        from core.utils.payments import detect_currency, format_price
        self.assertEqual(detect_currency(self._req(HTTP_CF_IPCOUNTRY="IN")), "INR")
        self.assertEqual(detect_currency(self._req(HTTP_CF_IPCOUNTRY="US")), "USD")
        self.assertEqual(detect_currency(self._req(cookies={"va_tz": "Asia%2FKolkata"})), "INR")
        self.assertEqual(detect_currency(self._req(cookies={"va_tz": "America%2FNew_York"})), "USD")
        self.assertEqual((format_price("kundali_pdf", "INR"), format_price("kundali_pdf", "USD")), ("₹250", "$10"))
        self.assertEqual((format_price("aahaar_pdf", "INR"), format_price("aahaar_pdf", "USD")), ("₹100", "$5"))

    def test_country_header_decides_and_cannot_be_switched(self):
        from core.utils.payments import currency_from_country, detect_currency
        r = self._req(HTTP_CF_IPCOUNTRY="IN", QUERY_STRING="currency=USD")
        self.assertEqual(detect_currency(r), "INR")
        self.assertEqual(currency_from_country(r), "INR")
        self.assertIsNone(currency_from_country(self._req()))       # no CDN header: the switch is offered
        self.assertEqual(detect_currency(self._req(QUERY_STRING="currency=USD")), "USD")

    def test_phonepe_is_never_offered_for_dollars(self):
        from core.utils.payments import gateways_for
        with override_settings(DEBUG=False, PHONEPE_CLIENT_ID="id", PHONEPE_CLIENT_SECRET="s", RAZORPAY_KEY_ID="k",
                               RAZORPAY_KEY_SECRET="s"):
            self.assertEqual(gateways_for("INR"), ["razorpay", "phonepe"])
            self.assertEqual(gateways_for("USD"), ["razorpay"])


@override_settings(DEBUG=True, **TEST_KEYS)
class PaymentFlowTests(TestCase):
    def setUp(self):
        import tempfile
        from django.conf import settings
        self._pdf_dir = tempfile.TemporaryDirectory()
        stores = dict(settings.STORAGES, pdfs={"BACKEND": "django.core.files.storage.FileSystemStorage",
                                               "OPTIONS": {"location": self._pdf_dir.name, "base_url": None}})
        self._override = override_settings(STORAGES=stores)
        self._override.enable()

    def tearDown(self):
        self._override.disable()
        self._pdf_dir.cleanup()

    def test_pdf_is_saved_once_and_served_from_storage_until_purged(self):
        from core.models import Purchase
        from core.utils import pdf_store
        from django.core.files.storage import storages
        from django.utils import timezone
        self._buy_aahaar(self.client)
        p = Purchase.objects.get()
        first = self.client.get(f"/pay/order/{p.token}/download/").content
        name = pdf_store.path_for(p, "en")
        self.assertTrue(storages["pdfs"].exists(name))
        self.assertEqual(self.client.get(f"/pay/order/{p.token}/download/").content, first)   # same file again
        Purchase.objects.filter(pk=p.pk).update(paid_at=timezone.now() - timedelta(days=60))
        self.assertEqual(pdf_store.purge_expired(30)[0], 1)
        self.assertFalse(storages["pdfs"].exists(name))

    def _buy_aahaar(self, client, gateway="dev"):
        return client.post("/pay/aahaar/?currency=INR", {"date": "2026-11-10", "name": "Asha", "email": "asha@example.com",
                                                         "lang": "en", "gateway": gateway})

    def test_guest_buys_aahaar_and_only_the_buyer_downloads(self):
        from core.models import Purchase
        res = self._buy_aahaar(self.client)
        p = Purchase.objects.get()
        self.assertEqual((p.status, p.amount, p.currency, p.product), ("paid", 10000, "INR", "aahaar_pdf"))
        self.assertRedirects(res, f"/pay/order/{p.token}/")
        pdf = self.client.get(f"/pay/order/{p.token}/download/")
        self.assertEqual(pdf["Content-Type"], "application/pdf")
        self.assertTrue(pdf.content.startswith(b"%PDF"))
        import io
        import pikepdf
        doc = pikepdf.open(io.BytesIO(pdf.content))
        self.assertTrue(doc.is_encrypted)
        self.assertFalse(doc.allow.extract)
        self.assertTrue(doc.allow.print_highres)
        self.assertEqual(str(doc.docinfo["/OrderRef"]), p.ref)
        stranger = self.client_class()
        self.assertEqual(stranger.get(f"/pay/order/{p.token}/download/").status_code, 302)
        self.assertEqual(stranger.post(f"/pay/order/{p.token}/", {"email": "nope@example.com"}).status_code, 403)
        self.assertContains(stranger.post(f"/pay/order/{p.token}/", {"email": "ASHA@example.com"}), "Download PDF")

    def test_downloads_stop_at_the_limit(self):
        from core.models import Purchase
        from core.utils.payments import DOWNLOAD_LIMIT
        self._buy_aahaar(self.client)
        p = Purchase.objects.get()
        Purchase.objects.filter(pk=p.pk).update(download_count=DOWNLOAD_LIMIT)
        self.assertRedirects(self.client.get(f"/pay/order/{p.token}/download/"), f"/pay/order/{p.token}/")

    def test_checkout_rejects_a_bad_email_and_states_the_price(self):
        res = self.client.get("/pay/aahaar/?currency=USD")
        self.assertContains(res, "$5")
        res = self.client.post("/pay/aahaar/", {"name": "A", "email": "not-an-email", "gateway": "dev"})
        self.assertEqual(res.status_code, 400)

    def test_razorpay_needs_a_valid_signature(self):
        import hashlib
        import hmac
        from unittest import mock
        from core.models import Purchase
        with mock.patch("core.utils.payments.razorpay_create_order", return_value="order_ABC"):
            res = self._buy_aahaar(self.client, gateway="razorpay")
        self.assertContains(res, "checkout.razorpay.com")
        p = Purchase.objects.get()
        self.assertEqual(p.status, "created")
        bad = self.client.post("/pay/razorpay/verify/", {"token": p.token, "razorpay_order_id": "order_ABC",
                                                         "razorpay_payment_id": "pay_1", "razorpay_signature": "forged"})
        self.assertEqual(bad.status_code, 400)
        p.refresh_from_db()
        self.assertEqual(p.status, "created")
        sig = hmac.new(b"secret", b"order_ABC|pay_1", hashlib.sha256).hexdigest()
        self.client.post("/pay/razorpay/verify/", {"token": p.token, "razorpay_order_id": "order_ABC",
                                                   "razorpay_payment_id": "pay_1", "razorpay_signature": sig})
        p.refresh_from_db()
        self.assertEqual((p.status, p.gateway_payment_id), ("paid", "pay_1"))

    def test_webhooks_check_their_signatures_and_the_amount(self):
        import hashlib
        import hmac
        import json
        from unittest import mock
        from core.models import Purchase
        with mock.patch("core.utils.payments.razorpay_create_order", return_value="order_W"):
            self._buy_aahaar(self.client, gateway="razorpay")
        p = Purchase.objects.get()

        def hook(amount):
            body = json.dumps({"event": "payment.captured", "payload": {"payment": {"entity": {
                "id": "pay_W", "order_id": "order_W", "amount": amount, "currency": "INR"}}}}).encode()
            sig = hmac.new(b"hooksecret", body, hashlib.sha256).hexdigest()
            return self.client.post("/pay/webhook/razorpay/", body, content_type="application/json",
                                    HTTP_X_RAZORPAY_SIGNATURE=sig)
        self.assertEqual(self.client.post("/pay/webhook/razorpay/", b"{}", content_type="application/json",
                                          HTTP_X_RAZORPAY_SIGNATURE="x").status_code, 400)
        hook(100)                                  # wrong amount: ignored
        p.refresh_from_db()
        self.assertEqual(p.status, "created")
        hook(10000)
        p.refresh_from_db()
        self.assertEqual(p.status, "paid")
        self.assertEqual(self.client.post("/pay/webhook/phonepe/", b"{}", content_type="application/json",
                                          HTTP_AUTHORIZATION="wrong").status_code, 400)

    def test_kundali_report_is_for_its_owner_only(self):
        owner = User.objects.create_user("owner", "owner@example.com", "pw-12345!")
        other = User.objects.create_user("other", "other@example.com", "pw-12345!")
        k = _kundali(owner)
        self.assertEqual(self.client.get(f"/pay/kundali/{k.id}/").status_code, 302)       # login first
        self.client.force_login(other)
        self.assertEqual(self.client.get(f"/pay/kundali/{k.id}/").status_code, 404)
        self.client.force_login(owner)
        self.assertContains(self.client.get(f"/pay/kundali/{k.id}/?currency=INR"), "₹250")
        self.client.post(f"/pay/kundali/{k.id}/", {"name": "Test Native", "email": "owner@example.com", "lang": "hi",
                                                   "gateway": "dev"})
        from core.models import Purchase
        p = Purchase.objects.get()
        self.assertEqual((p.amount, p.kundali_id, p.language), (25000, k.id, "hi"))
        pdf = self.client.get(f"/pay/order/{p.token}/download/")
        self.assertTrue(pdf.content.startswith(b"%PDF"))
        self.client.force_login(other)
        self.assertEqual(self.client.get(f"/pay/order/{p.token}/download/").status_code, 302)


class KundaliReportTests(TestCase):
    def test_report_has_every_varga_dashas_and_both_languages(self):
        from core.pdf import kundali_report as kr
        k = _kundali(None)
        data = kr.collect(k, datetime(2026, 11, 10, 12, 0))
        self.assertEqual(len(data["vargas"]), 17)
        self.assertEqual(data["asc_sign"], 7)                  # Scorpio lagna
        self.assertEqual(data["current"]["md"]["planet"], "Venus")
        self.assertEqual(len(data["current"]["pds"]), 9)
        self.assertAlmostEqual((data["current"]["pds"][-1]["end_date"] - data["current"]["ad"]["end_date"]).total_seconds(), 0, delta=5)
        for lang in ("en", "hi"):
            self.assertTrue(kr.build(k, lang=lang, licensee="T", email="t@example.com", order_ref="VA1").startswith(b"%PDF"))


class FestivalPujaMuhuratTests(TestCase):
    """Delhi timings checked against published panchang timings."""
    DELHI = (28.6139, 77.2090, "Asia/Kolkata")

    def _best(self, slug, d):
        from core.utils import festival_muhurat as fm
        res = fm._compute(slug, fm.RECIPES[slug], d, *self.DELHI)
        w = next(w for w in res["windows"] if w["best"])
        return w["spans"][0]["start"], w["spans"][0]["end"]

    def assertNear(self, dt, hhmm, minutes=3):
        h, m = map(int, hhmm.split(":"))
        target = dt.replace(hour=h, minute=m, second=0, microsecond=0)
        if abs((dt - target).total_seconds()) > 12 * 3600:
            target += timedelta(days=1 if dt > target else -1)
        self.assertLessEqual(abs((dt - target).total_seconds()), minutes * 60, f"{dt:%H:%M} vs {hhmm}")

    def test_diwali_2025_lakshmi_puja(self):
        a, b = self._best("diwali", date(2025, 10, 20))
        self.assertNear(a, "19:08")
        self.assertNear(b, "20:18")

    def test_holika_dahan_2025_waits_for_bhadra_and_ends_at_madhya_ratri(self):
        a, b = self._best("holika-dahan", date(2025, 3, 13))
        self.assertNear(a, "23:26")
        self.assertNear(b, "00:30")

    def test_raksha_bandhan_2025_runs_from_sunrise_to_purnima_end(self):
        a, b = self._best("raksha-bandhan", date(2025, 8, 9))
        self.assertNear(a, "05:47")
        self.assertNear(b, "13:24")

    def test_janmashtami_uses_the_whole_nishita_kaal(self):
        a, b = self._best("krishna-janmashtami", date(2026, 9, 4))
        self.assertGreaterEqual((b - a).total_seconds(), 40 * 60)

    def test_festival_page_shows_the_puja_time(self):
        res = self.client.get("/festivals/2025/diwali/?city=New+Delhi")
        self.assertContains(res, "Puja muhurat in")
        self.assertContains(res, "19:08")


class MoneyMuhuratAndColourTests(TestCase):
    def test_no_borrowing_on_tuesday_and_no_lending_on_tuesday_or_wednesday(self):
        from core.utils import muhurat as mu
        start, end = date(2026, 1, 1), date(2026, 3, 31)
        loan = mu.muhurat_dates("loan", start, end, 28.61, 77.21, "Asia/Kolkata")
        lend = mu.muhurat_dates("lending", start, end, 28.61, 77.21, "Asia/Kolkata")
        self.assertTrue(loan and lend)
        self.assertNotIn("Tuesday", {d["weekday"] for d in loan})
        self.assertFalse({"Tuesday", "Wednesday"} & {d["weekday"] for d in lend})

    def test_colours_follow_day_ritu_and_maas(self):
        from core.utils.muhurat import colour_guide
        g = colour_guide(4, "Vasanta", "Magha")
        self.assertEqual(g["day"]["wear"][0][0], "Yellow")
        self.assertTrue(g["ritu_wear"] and g["maas_wear"])

    def test_shubh_muhurat_page_has_money_and_colours(self):
        res = self.client.get("/shubh-muhurat/?date=2026-11-12")
        self.assertContains(res, "What to wear today")
        self.assertContains(res, "Taking a Loan (Rin Grahan)")
        self.assertEqual(self.client.get("/shubh-muhurat/investment/2026/").status_code, 200)


class AahaarAndGrahanTests(TestCase):
    def test_eight_pahars_cover_sunrise_to_sunrise(self):
        from core.utils.aahaar import daily_rhythm
        r = daily_rhythm(date(2026, 11, 10), 28.61, 77.21, "Asia/Kolkata")
        self.assertEqual(len(r["pahars"]), 8)
        self.assertEqual(r["pahars"][0]["start"], r["sunrise"])
        self.assertEqual(r["pahars"][-1]["end"], r["next_sunrise"])
        for a, b in zip(r["pahars"], r["pahars"][1:]):
            self.assertEqual(a["end"], b["start"])

    def test_aahaar_page_states_the_pdf_price_before_the_click(self):
        res = self.client.get("/aahaar/?currency=USD")
        self.assertContains(res, "Download PDF · $5")
        for section in ("pahar-bar", "region-grid", "food-chip", "Pregnant women", "Before workout"):
            self.assertContains(res, section)

    def test_grahan_lists_the_last_ten_years(self):
        from django.utils import timezone
        res = self.client.get("/grahan/")
        this_year = timezone.now().year
        self.assertContains(res, f'value="{this_year - 10}"')
        self.assertContains(res, f"/grahan/{this_year + 5}/")


class ParashariVargaTests(TestCase):
    """Jagannatha Hora's default 'Traditional Parasara' vargas (BPHS ch. 6)."""
    def test_rules_at_known_points(self):
        from core.utils.varga import varga_sign
        # D-2 is JHora's default Uma-Shambhu hora ("D-2 (US)")
        self.assertEqual(varga_sign(5, 2), 0)          # Aries 1st half: Aries
        self.assertEqual(varga_sign(20, 2), 1)         # Aries 2nd half: Taurus
        self.assertEqual(varga_sign(35, 2), 3)         # Taurus (even) 1st half: Cancer
        self.assertEqual(varga_sign(50, 2), 2)         # Taurus 2nd half: Gemini
        self.assertEqual(varga_sign(95, 2), 7)         # Cancer 1st half: Scorpio
        self.assertEqual(varga_sign(335, 2), 11)       # Pisces 1st half: Pisces
        self.assertEqual(varga_sign(25, 3), 8)         # Aries 25°: 9th from Aries (Sagittarius)
        self.assertEqual(varga_sign(32, 10), 9)        # Taurus 2°: even sign starts from the 9th (Capricorn)
        self.assertEqual(varga_sign(32, 30), 1)        # Taurus 2°: Venus' trimsamsha (Taurus)
        self.assertEqual(varga_sign(3, 30), 0)         # Aries 3°: Mars (Aries)
        self.assertEqual(varga_sign(29.9, 60), 11)     # Aries, last shashtiamsha: 60th part from Aries
        self.assertEqual(varga_sign(90.5, 24), 3)      # Cancer (even) starts from Cancer

    def test_d9_and_d27_match_the_cyclic_formula(self):
        from core.utils.varga import varga_sign
        for lon in [x * 0.37 for x in range(970)]:
            s, d = int(lon // 30), lon % 30
            for n in (7, 9, 16, 20, 27):
                self.assertEqual(varga_sign(lon, n), (s * n + int(d // (30 / n))) % 12)


class KundaliUrlGuessingTests(TestCase):
    def test_no_route_serves_another_users_kundali(self):
        from django.contrib.auth.models import User
        from core.models import Kundali
        owner = User.objects.create_user("own", "own@example.com", "pw-12345!")
        guest = User.objects.create_user("guess", "g@example.com", "pw-12345!")
        k = Kundali.objects.create(user=owner, name="Private", birth_date="1990-01-01 12:00:00", birth_place="Delhi",
                                   birth_lat=28.6, birth_lon=77.2, planetary_positions={}, divisional_charts={},
                                   ascendant={}, dashas=[], houses={}, gunmilan={})
        self.client.force_login(guest)
        for url in (f"/kundali/{k.id}/", f"/api/kundali/{k.id}/", f"/pay/kundali/{k.id}/"):
            self.assertEqual(self.client.get(url).status_code, 404, url)
        self.client.post(f"/kundali/{k.id}/delete/")
        self.assertTrue(Kundali.objects.filter(id=k.id).exists())
        self.client.logout()
        self.assertNotEqual(self.client.get(f"/kundali/{k.id}/").status_code, 200)


class DoshaPariharaTests(TestCase):
    def test_mangal_exceptions_and_jupiter_aspect(self):
        from core.utils.dosha_remedies import mangal_dosha
        base = {"Sun": 0, "Moon": 5, "Venus": 5, "Jupiter": 2, "Saturn": 10, "Mercury": 1, "Rahu": 2, "Ketu": 8}
        lons = {k: v * 30 + 15 for k, v in base.items()}
        # Mars in Libra in the 12th from a Scorpio lagna: listed sign-house exception
        r = mangal_dosha({**base, "Mars": 6}, {**lons, "Mars": 195}, 7, refs=("Lagna",))
        self.assertTrue(r["present"] and r["cancelled"])
        # Mars in Gemini, 8th from a Scorpio lagna, with Jupiter in Aquarius: Mars is 5th from Jupiter
        r = mangal_dosha({**base, "Mars": 2, "Jupiter": 10}, {**lons, "Mars": 75}, 7, refs=("Lagna",))
        self.assertIn("jup_aspect", [k for k, _ in r["parihara"]])
        # Mars in Gemini in the 7th from Sagittarius lagna, Jupiter in Leo (Mars 11th from it): no parihara
        r = mangal_dosha({**base, "Mars": 2, "Jupiter": 4, "Sun": 9}, {**lons, "Mars": 75, "Sun": 285}, 8,
                         refs=("Lagna",))
        self.assertTrue(r["present"] and not r["cancelled"])

    def test_both_partners_manglik_balance_out(self):
        from core.utils.kundali_milan import MangalDoshaAnalyzer

        class K:
            def __init__(self):
                self.planets = {"Mars": {"house": 7, "zodiac_sign": "Mithun", "longitude": 75},
                                "Jupiter": {"house": 11, "zodiac_sign": "Simha", "longitude": 135},
                                "Sun": {"house": 10, "zodiac_sign": "Kark", "longitude": 105},
                                "Moon": {"house": 1, "zodiac_sign": "Dhanu", "longitude": 245}}
        report = MangalDoshaAnalyzer.analyze_cancellation(K(), K())
        self.assertTrue(report["partner1_manglik"] and report["partner2_manglik"])
        self.assertTrue(report["mutual_cancellation"] and report["cancelled"])

    def test_gand_mool(self):
        from core.utils.dosha_remedies import gand_mool
        self.assertTrue(gand_mool(2)["present"])                       # Ashwini pada 1
        self.assertEqual(gand_mool(2)["severity"], "high")
        self.assertFalse(gand_mool(50)["present"])                     # Rohini
        self.assertEqual(gand_mool(359)["nakshatra"], "Revati")


class MoneyDayTextTests(TestCase):
    def test_text_changes_with_the_weekday(self):
        from core.utils import muhurat as mu
        tue = {m["key"]: m for m in mu.day_guidance(date(2026, 11, 10), 28.61, 77.21, "Asia/Kolkata")["money"]}
        wed = {m["key"]: m for m in mu.day_guidance(date(2026, 11, 11), 28.61, 77.21, "Asia/Kolkata")["money"]}
        self.assertIn("best day to repay", tue["repay"]["today"])
        self.assertIn("never borrow", tue["loan"]["today"])
        self.assertNotEqual(tue["repay"]["today"], wed["repay"]["today"])


class RegionalAahaarTests(TestCase):
    def test_every_region_has_three_full_seasons(self):
        from core.utils.aahaar_foods import REGIONS
        for r in REGIONS:
            for season in ("winter", "summer", "monsoon"):
                for field in ("dishes", "grains", "dals", "vegetables", "fruits", "spices", "avoid"):
                    self.assertTrue(r["seasons"][season][field], (r["key"], season, field))

    def test_sayings_stay_in_their_region(self):
        from core.utils.aahaar import sayings_for
        south = " ".join(s["text"] for s in sayings_for("tamilnadu"))
        self.assertNotIn("चैते गुड़", south)
        self.assertIn("நொறுங்கத்", south)
        self.assertIn("चैते गुड़", " ".join(s["text"] for s in sayings_for("up")))

    def test_page_defaults_to_the_visitors_region_and_one_currency(self):
        from core.utils.aahaar_regions import region_for_place
        self.assertEqual(region_for_place("Chennai"), "tamilnadu")
        self.assertEqual(region_for_place("Dharwad town", 15.46, 75.0), "karnataka")
        self.assertEqual(region_for_place("Coimbatore"), "tamilnadu")
        self.assertIsNone(region_for_place("London", 51.5, -0.1))
        session = self.client.session
        session.update({"lat": 9.93, "lon": 76.26, "city": "Kochi", "timezone": "Asia/Kolkata"})
        session.save()
        res = self.client.get("/aahaar/?currency=INR")
        self.assertEqual(res.context["my_region"], "kerala")
        self.assertContains(res, "What not to eat")
        self.assertNotContains(res, "$5")


class NaamkaranTests(TestCase):
    def test_pada_syllables_and_rashi_letters(self):
        from core.utils import naamkaran as nk
        span = 360 / 27
        r = nk.reading(0.5)                                  # Ashwini pada 1
        self.assertEqual((r["nakshatra"], r["pada"], r["letter"]), ("Ashwini", 1, "चु"))
        r = nk.reading(26 * span + 3.5 * span / 4)           # Revati pada 4
        self.assertEqual(r["letter"], "ची")
        self.assertEqual(r["rashi"][0], "Meena")
        self.assertEqual([d for d, _ in nk.rashi_letters(0)], "चु चे चो ला ली लू ले लो अ".split())

    def test_names_match_by_first_sound(self):
        from core.utils.naamkaran import akshara_key, names_for
        self.assertEqual(akshara_key("कमल"), akshara_key("का"))      # short and long a are one sound
        self.assertEqual(akshara_key("आदित्य"), "अ")
        self.assertEqual(akshara_key("प्रिया"), "पि")                  # conjunct: first consonant + cluster vowel
        self.assertEqual(akshara_key("कृष्ण"), "कि")                   # कृ read as कि
        self.assertEqual(akshara_key("ऋषभ"), "रि")
        self.assertEqual(akshara_key("कौशल्या"), "को")                 # औ ~ ओ
        self.assertEqual(akshara_key("बकुल"), "व")                    # ब ~ व
        self.assertEqual(akshara_key("शिव"), "सि")                    # श + vowel joins the स row
        self.assertEqual(akshara_key("शशांक"), "श")                   # bare श stays with Hasta's ष
        self.assertTrue(all(n["gender"] == "f" for n in names_for(["अ"], "f")))
        self.assertIn("Arjun", [n["roman"] for n in names_for(["अ"])])

    def test_every_name_can_be_shown_and_none_is_listed_twice(self):
        from core.utils import naamkaran as nk
        heads = {nk.akshara_key(s)[0] for n in nk.NAKSHATRAS for s in n[3].split()}
        self.assertEqual([n[0] for n in nk.NAMES if nk.akshara_key(n[0])[0] not in heads], [])
        self.assertEqual(len({n[0] for n in nk.NAMES}), len(nk.NAMES))
        self.assertTrue(all(n[2] in "mf" and n[3] == n[3].strip() and n[3] for n in nk.NAMES))

    def test_page(self):
        res = self.client.get("/naamkaran/?nak=12&pada=1&gender=m")   # Hasta pada 1: पू
        self.assertContains(res, "पू")
        self.assertContains(res, "Pushkar")
        self.assertNotContains(res, "Pooja")                         # a girl's name, filtered out


class PreferenceTests(TestCase):
    def test_visitor_preferences_live_in_the_session(self):
        res = self.client.post("/preferences/", {"food_region": "up", "month_system": "amanta", "next": "/aahaar/"})
        self.assertEqual(res["Location"], "/aahaar/")
        res = self.client.get("/aahaar/")
        self.assertContains(res, 'aria-selected="true" data-key="up"')

    def test_native_state_picks_the_region_and_is_saved_on_the_profile(self):
        from django.contrib.auth.models import User
        u = User.objects.create_user("roots", password="x-pass-123")
        self.client.force_login(u)
        self.client.post("/preferences/", {"native_state": "Jaunpur", "next": "/"})   # not a state: ignored
        u.profile.refresh_from_db()
        self.assertEqual(u.profile.native_state, "")
        self.client.post("/preferences/", {"native_state": "Uttar Pradesh", "next": "/"})
        u.profile.refresh_from_db()
        self.assertEqual(u.profile.native_state, "Uttar Pradesh")
        res = self.client.get("/aahaar/?city=Pune")                  # lives in Maharashtra, roots in UP
        self.assertContains(res, 'aria-selected="true" data-key="up"')

    def test_month_in_system(self):
        from core.utils.prefs import month_in_system
        self.assertEqual(month_in_system("Kartika", True, "amanta"), "Ashwina")      # Krishna paksha: previous month
        self.assertEqual(month_in_system("Kartika", False, "amanta"), "Kartika")     # Shukla: same name
        self.assertEqual(month_in_system("Chaitra", True, "amanta"), "Phalguna")
        self.assertEqual(month_in_system("Kartika", True, "purnimanta"), "Kartika")

    def test_aahaar_shows_the_chosen_month_system(self):
        self.client.post("/preferences/", {"month_system": "amanta", "next": "/"})
        self.assertContains(self.client.get("/aahaar/?date=2026-11-01"), "(Amanta)")
        self.assertContains(self.client.get("/aahaar/?date=2026-11-01"), "Drik (sayana)")

    def test_unknown_values_and_foreign_redirects_are_ignored(self):
        res = self.client.post("/preferences/", {"food_region": "atlantis", "next": "https://example.com/"})
        self.assertEqual(res["Location"], "/")
        self.assertEqual(self.client.session.get("pref_food_region"), "")


class WelcomePageTests(TestCase):
    def test_landing_page_is_home_and_panchang_moved(self):
        res = self.client.get("/")
        self.assertContains(res, "Tithi")
        self.assertContains(res, "landing/grahan-globe.webp")
        self.assertContains(res, "/kundali/create")
        self.assertContains(res, 'href="/panchang/"')
        self.assertNotContains(res, "Tested against Kashi")
        self.assertRedirects(self.client.get("/welcome/"), "/", status_code=301)
        self.assertContains(self.client.get("/panchang/"), "date-picker-form")

    def test_templates_are_not_served_as_static_files(self):
        from django.contrib.staticfiles import finders
        self.assertIsNone(finders.find("base.html"))


class AccountTests(TestCase):
    PW = "Xk9!account-Long"

    def _user(self, email="a@example.com"):
        from django.contrib.auth.models import User
        from .models import Kundali
        user = User.objects.create_user(username=email.split("@")[0], email=email, password=self.PW)
        Kundali.objects.create(user=user, name="K", birth_date=datetime(1990, 1, 1, 10, 0), birth_place="Delhi",
                               birth_lat=28.6, birth_lon=77.2)
        return user

    def test_delete_account_needs_password_and_confirmation_then_removes_everything(self):
        from django.contrib.auth.models import User
        from .models import Kundali, UserProfile
        user = self._user()
        self.client.force_login(user)
        self.client.post("/account/delete/", {"password": self.PW, "confirm": "nope"})
        self.client.post("/account/delete/", {"password": "wrong", "confirm": "DELETE"})
        self.assertTrue(User.objects.filter(pk=user.pk).exists())
        res = self.client.post("/account/delete/", {"password": self.PW, "confirm": "DELETE"})
        self.assertRedirects(res, "/", fetch_redirect_response=False)
        self.assertFalse(User.objects.filter(pk=user.pk).exists())
        self.assertFalse(Kundali.objects.filter(user_id=user.pk).exists())
        self.assertFalse(UserProfile.objects.filter(user_id=user.pk).exists())

    def test_register_after_a_deleted_account_does_not_collide(self):
        from django.contrib.auth.models import User
        User.objects.create_user(username="dup", email="dup@example.com", password=self.PW)
        User.objects.create_user(username="dup2", email="x@example.com", password=self.PW)
        User.objects.get(username="dup").delete()
        res = self.client.post("/register/", {"full_name": "D", "email": "dup2@example.com", "password1": self.PW,
                                              "password2": self.PW})
        self.assertEqual(User.objects.filter(email="dup2@example.com").count(), 1)
        self.assertEqual(res.status_code, 302)

    def test_email_check(self):
        self._user("taken@example.com")
        self.assertEqual(self.client.get("/register/check-email/?email=TAKEN@example.com").json()["available"], False)
        self.assertEqual(self.client.get("/register/check-email/?email=free@example.com").json()["available"], True)
        self.assertEqual(self.client.get("/register/check-email/?email=nonsense").json()["valid"], False)

    def test_login_is_throttled_after_ten_failures(self):
        from django.core.cache import cache
        cache.clear()
        for _ in range(10):
            self.assertEqual(self.client.post("/accounts/login/", {"username": "z@example.com", "password": "x"}).status_code, 200)
        self.assertEqual(self.client.post("/accounts/login/", {"username": "z@example.com", "password": "x"}).status_code, 429)
        cache.clear()

    def test_anonymous_kundali_delete_and_bad_coordinates_are_refused(self):
        self.assertEqual(self.client.post("/kundali/1/delete/").status_code, 302)   # to login, not a 500
        self.client.force_login(self._user())
        self.client.post("/profile/update-location/", {"city": "X", "latitude": "999", "longitude": "nan"})
        from .models import UserProfile
        self.assertNotEqual(UserProfile.objects.get(user__email="a@example.com").latitude, 999)

    def test_panchang_api_does_not_leak_tracebacks(self):
        res = self.client.get("/api/panchang/2025/13/40/25/70/abc/def/x")
        self.assertNotIn("Traceback", res.content.decode())



import re  # noqa: E402


class HardeningTests(TestCase):
    def test_csp_header_and_nonced_scripts(self):
        res = self.client.get("/")
        csp = res["Content-Security-Policy"]
        nonce = re.search(r"nonce-([\w-]+)", csp).group(1)
        self.assertIn("'strict-dynamic'", csp)
        self.assertIn("object-src 'none'", csp)
        for tag in re.findall(r"<script[^>]*>", res.content.decode()):
            self.assertIn(f'nonce="{nonce}"', tag)
        self.assertNotIn(' onclick="', res.content.decode())

    def test_admin_moved(self):
        from django.conf import settings
        self.assertEqual(self.client.get("/admin/").status_code, 404)
        self.assertEqual(self.client.get("/" + settings.ADMIN_URL).status_code, 302)

    def test_heavy_endpoints_are_rate_limited(self):
        from django.core.cache import cache
        cache.clear()
        codes = [self.client.post("/compatibility/calculate/", '{"mode":"name","person1_name":"Ram","person2_name":"Sita"}',
                                  content_type="application/json").status_code for _ in range(22)]
        self.assertIn(429, codes)
        cache.clear()

    def test_impossible_date_is_404_not_500(self):
        self.assertEqual(self.client.get("/panchang/2025/2/30/10/").status_code, 404)

    def test_spoofed_forwarded_for_is_ignored(self):
        from django.test import RequestFactory, override_settings
        from .views.user_views import client_ip
        req = RequestFactory().get("/", HTTP_X_FORWARDED_FOR="6.6.6.6, 203.0.113.9", REMOTE_ADDR="10.0.0.1")
        with override_settings(NUM_PROXIES=1):
            self.assertEqual(client_ip(req), "203.0.113.9")
        with override_settings(NUM_PROXIES=0):
            self.assertEqual(client_ip(req), "10.0.0.1")

    def test_google_button_posts(self):
        html = self.client.get("/register/").content.decode()
        self.assertRegex(html, r'<form method="post" action="/accounts/google/login/')


class AahaarAuditTests(TestCase):
    """The November 2026 audit of the Aahaar PDF: rule clashes, ritu frame, regions and ingredients."""

    def test_clashing_rules_are_named_and_resolved(self):
        from core.utils.aahaar import day_guidance
        g = day_guidance("Hemanta", "Kartika", "Shukla Chaturthi", "Friday")
        text = " ".join(c["text"] for c in g["clashes"])
        self.assertIn("Radish", text)                    # month verse favours it, Chaturthi sets it aside
        self.assertIn("leave radish out today", text)
        self.assertIn("leave dals out until Devutthana Ekadashi", text)
        self.assertIn("buttermilk", text)                # Friday curd vs Kartika buttermilk
        self.assertEqual([x["rank"] for x in g["layers"]], sorted(x["rank"] for x in g["layers"]))
        self.assertEqual(len(g["precedence"]), 4)

    def test_chaturmas_ends_on_devutthana_ekadashi(self):
        from core.utils.aahaar import chaturmas_item
        self.assertEqual(chaturmas_item("Kartika", "Shukla Ekadashi"), "dals (dvidala)")
        self.assertIsNone(chaturmas_item("Kartika", "Shukla Dwadashi"))
        self.assertIsNone(chaturmas_item("Kartika", "Purnima"))
        self.assertEqual(chaturmas_item("Kartika", "Krishna Dwadashi"), "dals (dvidala)")

    def test_ritus_are_dated_by_the_sayana_sun_not_lunar_months(self):
        from core.utils.aahaar import RITU
        for name, r in RITU.items():
            self.assertIn("sayana", r["months"], name)
            self.assertNotIn("Kartika", r["months"], name)  # the lunar names live in "named" only

    def test_ingredients_carry_their_classical_basis(self):
        from core.utils.aahaar_foods import INGREDIENT_GROUPS, ingredient_rows
        rows = {x["name"]: x for g in INGREDIENT_GROUPS for x in ingredient_rows(g)}
        self.assertIn("Bael, unripe (kachcha bel)", rows)
        self.assertIn("doṣalaṃ", rows["Bael, ripe (bel)"]["note"])
        self.assertIn("Bhavaprakasha", rows["Clove (laung)"]["note"])

    def test_pdf_names_home_and_current_region(self):
        from core.pdf import aahaar_report
        from core.views.grahan_views import aahaar_context
        ctx = aahaar_context(date(2026, 11, 13), 19.076, 72.8777, "Asia/Kolkata", "Mumbai", region="up")
        self.assertEqual((ctx["my_region"], ctx["local_region"], ctx["ritu_name"]), ("up", "maharashtra", "Hemanta"))
        pdf = aahaar_report.build({"date": "2026-11-13", "lat": 19.076, "lon": 72.8777, "city": "Mumbai", "region": "up"},
                                  lang="en", licensee="T", email="t@example.com", order_ref="T1")
        self.assertTrue(pdf.startswith(b"%PDF"))


class SiteLaunchPagesTests(TestCase):
    """Contact form, articles, policies and FAQ needed for the payment-gateway website review."""

    def test_contact_form_saves_and_honeypot_drops_bots(self):
        from core.models import ContactMessage
        data = {"kind": "date", "name": "Asha", "email": "asha@example.com", "message": "Ekadashi differs in Pune."}
        res = self.client.post("/contact/", data)
        self.assertEqual(res.status_code, 302)
        self.assertEqual(ContactMessage.objects.get().kind, "date")
        self.client.post("/contact/", {**data, "website": "spam.example"})
        self.assertEqual(ContactMessage.objects.count(), 1)
        res = self.client.post("/contact/", {**data, "email": "nope"})
        self.assertEqual(res.status_code, 200)              # form shown again with the error

    def test_contact_mail_goes_to_owner_when_configured(self):
        from django.core import mail
        import threading
        with self.settings(CONTACT_EMAIL="owner@example.com", EMAIL_READY=True):
            self.client.post("/contact/", {"kind": "order", "name": "A", "email": "a@example.com",
                                           "order_ref": "VA-1", "message": "No download"})
            for t in threading.enumerate():
                if t.name == "contact-mail":
                    t.join(5)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].reply_to, ["a@example.com"])

    def test_contact_form_answers_even_when_mail_service_fails(self):
        import threading
        from unittest import mock
        from core.models import ContactMessage
        with self.settings(CONTACT_EMAIL="owner@example.com", EMAIL_READY=True), \
                mock.patch("django.core.mail.EmailMessage.send", side_effect=OSError("Network is unreachable")), \
                self.assertLogs("core.views.page_views", level="ERROR"):
            res = self.client.post("/contact/", {"kind": "feedback", "name": "B", "email": "b@example.com",
                                                 "message": "Hello"})
            for t in threading.enumerate():
                if t.name == "contact-mail":
                    t.join(5)
        self.assertEqual(res.status_code, 302)
        self.assertTrue(ContactMessage.objects.filter(email="b@example.com").exists())

    def test_signup_mail_failure_is_logged_not_a_server_error(self):
        from unittest import mock
        from django.test import RequestFactory
        from core.adapters import SafeMailAccountAdapter
        adapter = SafeMailAccountAdapter(RequestFactory().get("/"))
        with mock.patch("allauth.account.adapter.DefaultAccountAdapter.send_mail", side_effect=OSError("down")), \
                self.assertLogs("core.adapters", level="ERROR"):
            adapter.send_mail("account/email/email_confirmation", "x@example.com", {})

    def test_drafts_stay_hidden_until_published(self):
        from django.contrib.auth.models import User
        from core.models import Article
        a = Article.objects.create(title="Diwali 2026", slug="diwali-2026", summary="s", body="Hello\n\n- one\n- two")
        self.assertEqual(self.client.get("/blog/diwali-2026/").status_code, 404)
        self.assertNotContains(self.client.get("/blog/"), "Diwali 2026")
        staff = User.objects.create_user("s", "s@example.com", "pw", is_staff=True)
        self.client.force_login(staff)
        self.assertContains(self.client.get("/blog/diwali-2026/"), "Draft preview")
        a.status = "published"
        a.save()
        self.assertIsNotNone(a.published_at)
        self.client.logout()
        res = self.client.get("/blog/diwali-2026/")
        self.assertContains(res, "<li>one</li>", html=True)
        self.assertContains(self.client.get("/blog/"), "Diwali 2026")

    def test_body_formatter_escapes_html(self):
        from core.utils.articles import render_body
        html = render_body("## Title\n\n<script>x</script>")
        self.assertIn("<h2>Title</h2>", html)
        self.assertNotIn("<script>", html)

    def test_festival_drafts_are_made_once(self):
        from core.models import Article
        from core.utils.articles import draft_upcoming
        made = draft_upcoming(start=date(2026, 11, 13), days=10)
        self.assertTrue(made)
        self.assertTrue(all(a.status == "draft" and "[Owner:" in a.body for a in made))
        self.assertEqual(draft_upcoming(start=date(2026, 11, 13), days=10), [])
        self.assertEqual(Article.objects.count(), len(made))

    def test_policy_and_faq_pages(self):
        import json
        for url in ("/terms/", "/privacy/", "/refund-policy/", "/shipping-policy/", "/contact/", "/faq/", "/blog/"):
            self.assertEqual(self.client.get(url).status_code, 200, url)
        self.assertContains(self.client.get("/terms/"), "Grievance officer")
        html = self.client.get("/faq/").content.decode()
        blocks = [json.loads(x.split("</script>", 1)[0]) for x in html.split('type="application/ld+json">')[1:]]
        faq = next(b for b in blocks if b.get("@type") == "FAQPage")
        self.assertGreater(len(faq["mainEntity"]), 15)

    def test_panchang_page_is_not_branded_jyotish(self):
        html = self.client.get("/panchang/").content.decode()
        self.assertNotIn("Sthana", html)
        self.assertNotIn("Jyotish Panchanga", html)
        self.assertIn('class="two-col"', html)


class HindiSiteTests(TestCase):
    """The /hi/ site: Aahaar data, festival text and page chrome come out in Hindi."""

    def test_every_aahaar_string_has_hindi(self):
        from core.utils import aahaar as ah, aahaar_foods as foods
        from core.utils.aahaar_hi import missing
        gaps = set()
        for data in (ah.RITU, ah.MAAS, ah.VAAR, ah.DOSHA, ah.MEAL_RULES, ah.CLASSICAL_SOURCES, ah.DISCLAIMER,
                     ah.RITU_NAMES_NOTE, ah.PRECEDENCE, ah.TITHI_AVOID, ah.CHATURMAS, foods.AGE_GROUPS, foods.FITNESS,
                     foods.WORKOUT_TIMING, [{**r, "name": ""} for r in foods.REGIONS], [p[1] for p in ah.PAHARS]):
            missing(data, found=gaps)
        for group in foods.INGREDIENTS.values():
            missing([row[5] for row in group], found=gaps)
        self.assertEqual(sorted(gaps), [], "add these to core/utils/aahaar_hi_*.py")

    def test_festival_names_notes_and_rules_have_hindi(self):
        import re
        from core.utils import festival_calculations as fc
        from core.utils.festival_names_hi import hindi_name
        from core.utils.festival_text_hi import note_hi, rule_hi
        for f in fc.get_festivals_between(date(2026, 1, 1), date(2026, 12, 31)):
            for text in (hindi_name(f["name"]), note_hi(f["note"]), rule_hi(f["rule"])):
                english = re.sub(r"\d{1,2} \w{3} \d{4}, \d\d:\d\d [AP]M", "", text)
                self.assertNotRegex(english, r"[A-Za-z]{4,}", f["name"])

    def test_hindi_pages_render_in_hindi(self):
        for url in ("/hi/", "/hi/panchang/", "/hi/aahaar/", "/hi/festivals/2026/", "/hi/terms/", "/hi/how-it-works/"):
            res = self.client.get(url)
            self.assertEqual(res.status_code, 200, url)
            self.assertContains(res, "वाराणसी पंचांग")
        self.assertContains(self.client.get("/hi/aahaar/"), "हेमन्त")

    def test_aahaar_guidance_in_hindi(self):
        from core.utils.aahaar import day_guidance
        g = day_guidance("Hemanta", "Kartika", "Shukla Chaturthi", "Friday", lang="hi")
        self.assertTrue(all("मूली" in c["text"] or "दाल" in c["text"] or "दही" in c["text"] for c in g["clashes"]))

    def test_kundali_pdf_for_a_birth_before_1900(self):
        from datetime import datetime
        import pytz
        from django.contrib.auth.models import User
        from core.models import Kundali
        from core.pdf import kundali_report
        from core.kundali_calculator import KundaliCalculator
        from core.view_kundali import save_dashas_to_database
        user = User.objects.create_user("old", "old@example.com", "pw-12345!")
        dt = pytz.timezone("Asia/Kolkata").localize(datetime(1869, 10, 2, 7, 12))
        data = KundaliCalculator(dt, 21.64, 69.6, 5.5).calculate_all_data()
        k = Kundali.objects.create(user=user, name="Old", birth_date=dt.replace(tzinfo=None), birth_place="Porbandar",
                                   birth_lat=21.64, birth_lon=69.6, birth_timezone="Asia/Kolkata",
                                   planetary_positions=data["d1_chart"], divisional_charts=data["divisional_charts"],
                                   houses=data["houses"], ascendant=data["ascendant"], dashas=data["structured_dashas"])
        save_dashas_to_database(k, data["structured_dashas"])
        pdf = kundali_report.build(k, lang="hi", licensee="T", email="t@example.com", order_ref="T1")
        self.assertTrue(pdf.startswith(b"%PDF"))


# ---------------------------------------------------------------------------
# Kundali yogas, nitya-yoga tyajya parts and Bhadra loka (2026-11-14)
# ---------------------------------------------------------------------------

class KundaliYogaTests(TestCase):
    @staticmethod
    def _find(signs, asc, lons=None):
        from core.utils import kundali_yogas as ky
        lons = lons or {p: s * 30 + 15 for p, s in signs.items()}
        return {y["key"]: y for y in ky.find_yogas(signs, lons, asc)}

    BASE = {"Sun": 0, "Moon": 3, "Mars": 1, "Mercury": 1, "Jupiter": 3, "Venus": 1, "Saturn": 4,
            "Rahu": 2, "Ketu": 8}

    def test_mahapurusha_needs_kendra_and_dignity(self):
        signs = dict(self.BASE, Mercury=5)          # Mercury exalted in Virgo
        self.assertIn("bhadra", self._find(signs, asc=5))       # Virgo Lagna: 1st house
        self.assertNotIn("bhadra", self._find(signs, asc=4))    # Leo Lagna: 2nd house

    def test_gaja_kesari_weak_when_jupiter_debilitated(self):
        y = self._find(dict(self.BASE, Moon=9, Jupiter=9), asc=0)["gaja_kesari"]
        self.assertEqual(y["strength"], "weak")
        self.assertIn("gaja_kesari", self._find(dict(self.BASE, Moon=0, Jupiter=3), asc=0))
        self.assertNotIn("gaja_kesari", self._find(dict(self.BASE, Moon=0, Jupiter=4), asc=0))

    def test_budha_aditya_skips_combust_mercury(self):
        signs = dict(self.BASE, Sun=0, Mercury=0)
        lons = {p: s * 30 + 15 for p, s in signs.items()}
        self.assertNotIn("budha_aditya", self._find(signs, 0, dict(lons, Sun=10, Mercury=20)))
        self.assertIn("budha_aditya", self._find(signs, 0, dict(lons, Sun=2, Mercury=28)))

    def test_raj_yoga_and_yogakaraka(self):
        # Taurus Lagna: Saturn rules 9 and 10; in Capricorn (9th) it is yogakaraka.
        found = self._find(dict(self.BASE, Saturn=9), asc=1)
        self.assertIn("yogakaraka", found)
        # Aries Lagna: Mars (1st lord) with Jupiter (9th lord) in one sign is a Raj yoga.
        self.assertIn("raj", self._find(dict(self.BASE, Mars=6, Jupiter=6), asc=0))

    def test_neecha_bhanga_and_shakata_cancel(self):
        # Sun debilitated in Libra, Venus (its sign lord) in a kendra from an Aries Lagna.
        self.assertIn("neecha_bhanga", self._find(dict(self.BASE, Sun=6, Venus=3), asc=0))
        # Moon 6th from Jupiter but in a kendra from the Lagna: Shakata cancelled.
        y = self._find(dict(self.BASE, Jupiter=10, Moon=3), asc=0)["shakata"]
        self.assertEqual(y["strength"], "cancelled")

    def test_yogas_name_their_planets_nature_and_strength(self):
        # Moon in Cancer, Saturn alone in Leo (next sign): Sunapha formed by a malefic -> "mixed"
        signs = dict(self.BASE, Moon=3, Jupiter=3, Saturn=4, Mars=1, Mercury=1, Venus=1)
        y = self._find(signs, asc=0)["sunapha"]
        self.assertEqual(y["strength"], "mixed")
        self.assertEqual(y["planets"], ["Saturn"])
        self.assertIn("malefic", y["reasons"][-1][0])
        self.assertTrue(y["strength_notes"])
        raj = self._find(dict(self.BASE, Mars=6, Jupiter=6), asc=0)["raj"]
        self.assertIn("Mars", raj["planets"])
        self.assertIn("Jupiter", raj["planets"])

    def test_sade_sati_matches_saturn_ingresses(self):
        # Moon in Capricorn: Sade Sati 2017-2025 (Saturn entered sidereal Capricorn 24 Jan 2020, Pisces 29 Mar 2025)
        from core.utils import shani
        rows = shani.lifetime(datetime(1990, 1, 1, 6, 0), 9)
        sade = [r for r in rows if r["key"] == "sade" and r["start"].year == 2017][0]
        self.assertEqual(sade["end"], date(2025, 3, 29))
        self.assertEqual(sade["phases"][1]["start"], date(2020, 1, 24))
        self.assertEqual({r["key"] for r in rows}, {"sade", "kantak", "ashtama"})

    def test_shani_guide_picks_life_stage_and_phase_lines(self):
        from core.utils import shani, shani_guide as G
        self.assertEqual(G.stage(10)[0][0], "Childhood (under 18)")
        self.assertEqual(G.stage(45)[0][0], "Middle years (35 to 59)")
        self.assertEqual(G.stage(85)[0][0], "Later years (60 and above)")
        rows = shani.lifetime(datetime(1990, 1, 1, 6, 0), 9)
        sade = [r for r in rows if r["key"] == "sade" and r["start"].year == 2017][0]
        self.assertEqual(len(G.touches(sade)), 3)
        kantak = [r for r in rows if r["key"] == "kantak"][0]
        self.assertIn("Kantak", G.touches(kantak)[0][0])

    def test_sagittarius_example_reads_like_a_full_analysis(self):
        # Sagittarius Lagna; Sun, Mercury (own sign, 8.7 deg from the Sun), Jupiter in Gemini (7th); Moon in Cancer;
        # Venus in Taurus (6th); Saturn and Rahu in Capricorn (2nd)
        from core.utils import kundali_yogas as ky
        lons = {"Sun": 75.0, "Moon": 100.0, "Mars": 340.0, "Mercury": 83.7, "Jupiter": 70.0, "Venus": 45.0,
                "Saturn": 285.0, "Rahu": 290.0, "Ketu": 110.0}
        signs = {k: int(v // 30) for k, v in lons.items()}
        found = {y["key"]: y for y in ky.find_yogas(signs, lons, 8)}
        self.assertEqual(set(found["dharma_karma"]["planets"]), {"Mercury", "Sun"})
        self.assertNotIn("Mercury [lord of the 7th house: partner, partnerships and 10th house: career, status] and "
                         "Sun", " ".join(r[0] for r in found["raj"]["reasons"]))
        dhana = " ".join(r[0] for r in found["dhana"]["reasons"])
        self.assertIn("Saturn, lord of the 2nd house", dhana)
        self.assertIn("Rahu in the same house", dhana)
        self.assertIn("sits in the 6th house", dhana)
        self.assertIn("also rules the 11th house", found["harsha"]["reasons"][1][0])
        self.assertEqual(found["bhadra"]["strength"], "mixed")
        self.assertTrue(found["sarala"] and found["anapha"] and found["vasi"])
        overview = " ".join(l[0] for l in ky.overview(signs, lons, 8, list(found.values())))
        self.assertIn("Sun, Mercury, Jupiter together in the 7th house", overview)
        self.assertIn("Career and status: Dharma-Karmadhipati Yoga", overview)
        self.assertIn("Saturn (Capricorn, 2nd house)", overview)

    def test_bhadra_yoga_text_is_not_vishti(self):
        from core.utils.kundali_yogas import INFO
        self.assertIn("Vishti", INFO["bhadra"][2][0])


class NityaYogaAndBhadraTests(TestCase):
    VARANASI = (25.3176, 82.9739, "Asia/Kolkata")

    def test_tyajya_parts(self):
        from datetime import datetime as dt
        from core.utils import muhurat as mu
        s, e = dt(2026, 1, 1, 6, 0), dt(2026, 1, 2, 6, 0)
        seg = {"yoga_start": s, "yoga_end": e}
        self.assertEqual(mu.yoga_tyajya(dict(seg, yoga="Shoola")), (s, s + timedelta(hours=2)))
        self.assertEqual(mu.yoga_tyajya(dict(seg, yoga="Parigha")), (s, s + timedelta(hours=12)))
        self.assertEqual(mu.yoga_tyajya(dict(seg, yoga="Vaidhriti")), (s, e))
        self.assertIsNone(mu.yoga_tyajya(dict(seg, yoga="Siddhi")))

    def test_no_window_inside_a_tyajya_part(self):
        from core.utils import muhurat as mu
        start, end = date(2026, 11, 1), date(2026, 12, 31)
        days = mu.day_segments(start, end, *self.VARANASI)
        bad = [mu.yoga_tyajya(s) for d in days for s in d["segments"]]
        bad = [b for b in bad if b]
        for purpose in ("buy", "gold", "vehicle", "griha-pravesh", "mundan"):
            if purpose not in mu.PURPOSES:
                continue
            for w in mu.find_muhurats(purpose, start, end, *self.VARANASI, days=days):
                self.assertFalse(any(w["start"] < b1 and w["end"] > b0 for b0, b1 in bad), (purpose, w))

    def test_bhadra_named_by_loka(self):
        from core.utils import muhurat as mu
        self.assertEqual({mu.BHADRA_LOKA[s] for s in (3, 4, 10, 11)}, {"mrityu"})
        g = mu.day_guidance(date(2026, 11, 17), *self.VARANASI)
        keys = [c["key"] for c in g["cautions"]]
        self.assertIn("Bhadra on earth (Mrityu lok)", keys)
        self.assertIn("Bhadra in Patala lok", keys)


class StressFindingsTests(TestCase):
    """Bugs found by the 2026-11-14 load test."""

    def test_old_create_url_saves_a_kundali(self):
        from core.models import DashaPeriod, Kundali
        u = User.objects.create_user("st", "st@example.com", "x-pass-12345")
        self.client.force_login(u)
        body = dict(name="A", birth_date="1990-05-17", birth_time="10:30", birth_place="Varanasi", lat=25.3, lon=82.9,
                    timezone="Asia/Kolkata")
        res = self.client.post("/kundali/create", body)
        self.assertEqual(res.status_code, 302)
        k = Kundali.objects.get(user=u)
        self.assertEqual(DashaPeriod.objects.filter(kundali=k, dasha_type="mahadasha").count(), 9)
        self.assertGreater(DashaPeriod.objects.filter(kundali=k, dasha_type="antardasha").count(), 9)

    def test_throttle_counter_keeps_its_own_timeout(self):
        from django.core.cache import cache
        from core.views.user_views import bump
        cache.clear()
        for _ in range(3):
            n = bump("throttle:test", 60)
        self.assertEqual(n, 3)
        if hasattr(cache, "_expire_info"):
            import time
            self.assertLess(cache._expire_info[cache.make_key("throttle:test")] - time.time(), 61)


class BirthTimeRoundTripTests(TestCase):
    """Birth details must come back from the database exactly as entered (local civil time + zone), on SQLite and on
    PostgreSQL (whose session runs in UTC on hosted servers), and the charts built from them must not move."""
    CASES = [
        # (place, lat, lon, date, time, expected zone)
        ("Varanasi", 25.3176, 82.9739, "1990-05-17", "10:30", "Asia/Kolkata"),
        ("Varanasi midnight", 25.3176, 82.9739, "2000-01-01", "00:00", "Asia/Kolkata"),
        ("Varanasi 23:59", 25.3176, 82.9739, "1999-12-31", "23:59", "Asia/Kolkata"),
        ("New York", 40.7128, -74.0060, "1985-07-04", "21:15", "America/New_York"),
        ("London winter", 51.5072, -0.1276, "1975-01-15", "00:05", "Europe/London"),
        ("Sydney", -33.8688, 151.2093, "2010-03-01", "05:45", "Australia/Sydney"),
    ]

    def test_round_trip_and_chart(self):
        import pytz
        from core.kundali_calculator import KundaliCalculator
        from core.models import Kundali
        from core.pdf import kundali_report
        u = User.objects.create_user("rt", "rt@example.com", "x-pass-12345")
        self.client.force_login(u)
        for place, lat, lon, d, t, zone in self.CASES:
            with self.subTest(place):
                res = self.client.post("/kundali/generate", dict(name=place, birth_date=d, birth_time=t,
                                                                  birth_place=place, lat=lat, lon=lon,
                                                                  timezone="Asia/Kolkata"))
                self.assertEqual(res.status_code, 302)
                k = Kundali.objects.get(user=u, name=place)       # fresh read from the database
                self.assertEqual(k.birth_timezone, zone)
                self.assertEqual(k.birth_date.replace(tzinfo=None), datetime.strptime(f"{d} {t}", "%Y-%m-%d %H:%M"))
                local = pytz.timezone(zone).localize(datetime.strptime(f"{d} {t}", "%Y-%m-%d %H:%M"))
                direct = KundaliCalculator(local, lat, lon, local.utcoffset().total_seconds() / 3600).calculate_all_data()
                moon_direct = direct["d1_chart"]["Moon"]["longitude_sidereal"]
                self.assertAlmostEqual(k.planetary_positions["Moon"]["longitude_sidereal"], moon_direct, places=6)
                data = kundali_report.collect(k, local)               # what the PDF uses
                self.assertAlmostEqual(data["planets"]["Moon"]["lon"], moon_direct, places=6)
                self.assertEqual(data["birth"].utcoffset(), local.utcoffset())
        pdf = kundali_report.build(Kundali.objects.get(user=u, name="Varanasi midnight"), lang="en",
                                   licensee="T", email="t@example.com", order_ref="RT1")
        self.assertTrue(pdf.startswith(b"%PDF"))


class PdfBuildSlotTests(TestCase):
    def test_simultaneous_downloads_build_once(self):
        import tempfile, threading, time as _t
        from types import SimpleNamespace
        from core.utils import pdf_store
        calls = []

        def slow_build():
            calls.append(1)
            _t.sleep(0.5)
            return b"%PDF-test"
        from unittest import mock
        from django.core.files.storage import FileSystemStorage
        order = SimpleNamespace(ref="SLOT1", created_at=datetime(2026, 11, 14))
        with tempfile.TemporaryDirectory() as d, mock.patch.object(pdf_store, "_storage",
                                                                    lambda: FileSystemStorage(location=d)):
            out = []
            ths = [threading.Thread(target=lambda: out.append(pdf_store.get_or_build(order, "en", slow_build)))
                   for _ in range(4)]
            [t.start() for t in ths]
            [t.join() for t in ths]
        self.assertEqual(len(calls), 1)
        self.assertEqual(out, [b"%PDF-test"] * 4)


class DailyJobTests(TestCase):
    def test_daily_clears_expired_sessions_and_is_safe_to_repeat(self):
        from django.contrib.sessions.models import Session
        from django.core.management import call_command
        from django.utils import timezone
        Session.objects.create(session_key="old" * 10, session_data="x", expire_date=timezone.now() - timedelta(days=1))
        Session.objects.create(session_key="new" * 10, session_data="x", expire_date=timezone.now() + timedelta(days=1))
        from unittest import mock
        from core.utils import grahan as gr
        with mock.patch.object(gr, "globe_data") as globe:
            call_command("daily", stdout=__import__("io").StringIO())
            call_command("daily", stdout=__import__("io").StringIO())
        self.assertEqual(list(Session.objects.values_list("session_key", flat=True)), ["new" * 10])
        self.assertTrue(globe.called)       # grahan globe cache is refilled nightly, so no visitor waits for it

    def test_web_purge_runs_once_a_day_across_workers(self):
        from unittest import mock
        from django.core.cache import cache
        from core.utils import pdf_store
        cache.clear()
        with mock.patch.object(pdf_store, "purge_expired", return_value=(0, 0)) as purge:
            self.assertTrue(pdf_store.run_daily_purge())
            self.assertFalse(pdf_store.run_daily_purge())       # another worker, same day: skipped
        self.assertEqual(purge.call_count, 1)

    def test_web_purge_failure_lets_a_later_check_retry(self):
        from unittest import mock
        from django.core.cache import cache
        from core.utils import pdf_store
        cache.clear()
        with mock.patch.object(pdf_store, "purge_expired", side_effect=OSError("volume gone")), \
                self.assertLogs("core.utils.pdf_store", level="ERROR"):
            self.assertFalse(pdf_store.run_daily_purge())
        with mock.patch.object(pdf_store, "purge_expired", return_value=(1, 10)) as purge:
            self.assertTrue(pdf_store.run_daily_purge())
        self.assertEqual(purge.call_count, 1)

    def test_request_hook_starts_at_most_one_check_an_hour(self):
        from unittest import mock
        from core.utils import pdf_store
        with mock.patch.object(pdf_store, "_next_purge_check", 0.0), \
                mock.patch.object(pdf_store.threading, "Thread") as thread:
            for _ in range(50):
                pdf_store.maybe_purge_in_background()
        self.assertEqual(thread.call_count, 1)
        thread.return_value.start.assert_called_once()




@override_settings(DEBUG=False, RAZORPAY_KEY_ID="rzp_test_x", RAZORPAY_KEY_SECRET="s", SECURE_SSL_REDIRECT=False,
                   RAZORPAY_WEBHOOK_SECRET="whsec")
class StaffAndAdminOrderTests(TestCase):
    def _post(self, user, gateway):
        k = _kundali(user)
        self.client.force_login(user)
        return k, self.client.post(f"/pay/kundali/{k.id}/", {"name": "N", "email": "n@example.com", "lang": "en",
                                                             "gateway": gateway})

    def _order(self, status="created", gateway="razorpay"):
        from core.models import Purchase
        buyer = User.objects.create_user(f"b{Purchase.objects.count()}", "b@example.com", "x-pass-12345")
        return Purchase.objects.create(product="kundali_pdf", user=buyer, kundali=_kundali(buyer), currency="INR",
                                       amount=25000, gateway=gateway, gateway_order_id="order_1", status=status,
                                       gateway_payment_id="pay_1" if status == "paid" else "",
                                       buyer_name="B", buyer_email="b@example.com")

    def _admin(self):
        from django.conf import settings
        self.client.force_login(User.objects.create_superuser("root", "root@example.com", "x-pass-12345"))
        return f"/{settings.ADMIN_URL}core/purchase/"

    def test_only_the_owner_gets_a_free_copy(self):
        from core.models import Purchase
        owner = User.objects.create_superuser("boss", "boss@example.com", "x-pass-12345")
        k, res = self._post(owner, "comp")
        p = Purchase.objects.get(kundali=k)
        self.assertRedirects(res, f"/pay/order/{p.token}/", fetch_redirect_response=False)
        self.assertEqual((p.status, p.amount, p.gateway), ("paid", 0, "comp"))
        for name, staff in (("helper", True), ("buyer", False)):        # plain staff and customers: refused
            u = User.objects.create_user(name, f"{name}@example.com", "x-pass-12345", is_staff=staff)
            k2, res2 = self._post(u, "comp")
            self.assertEqual(res2.status_code, 400)
            self.assertFalse(Purchase.objects.filter(kundali=k2).exists())
            self.assertNotContains(self.client.get(f"/pay/kundali/{k2.id}/"), 'value="comp"')

    def test_owner_copy_is_preselected_and_has_no_download_limit(self):
        from core.models import Purchase
        from core.utils import payments as pay
        from django.utils import timezone
        owner = User.objects.create_superuser("boss2", "boss2@example.com", "x-pass-12345")
        k = _kundali(owner)
        self.client.force_login(owner)
        page = self.client.get(f"/pay/kundali/{k.id}/").content.decode()
        self.assertIn('value="comp" checked', page)                                  # pre-selected
        p = Purchase.objects.create(product="kundali_pdf", user=owner, kundali=k, currency="INR", amount=0,
                                    gateway="comp", status="paid", paid_at=timezone.now() - timedelta(days=90),
                                    download_count=pay.DOWNLOAD_LIMIT + 5, buyer_name="B", buyer_email="b@example.com")
        from core.views.payment_views import _download_state
        self.assertEqual(_download_state(p), "ok")

    def test_confirm_needs_a_reason_and_the_gateway(self):
        from unittest import mock
        from django.contrib.admin.models import LogEntry
        p, url = self._order(), self._admin()
        page = self.client.post(url, {"action": "confirm_paid", "_selected_action": [p.pk]})
        self.assertContains(page, "Nothing can be marked paid by hand")         # asks first, changes nothing
        p.refresh_from_db()
        self.assertEqual(p.status, "created")
        with mock.patch("core.utils.payments.gateway_verify_paid", return_value=None):    # gateway: not captured
            self.client.post(url, {"action": "confirm_paid", "_selected_action": [p.pk], "apply": "1",
                                   "reason": "customer says paid"})
        p.refresh_from_db()
        self.assertEqual(p.status, "created")
        with mock.patch("core.utils.payments.gateway_verify_paid", return_value=("pay_9", 100, "INR")):  # wrong amount
            self.client.post(url, {"action": "confirm_paid", "_selected_action": [p.pk], "apply": "1",
                                   "reason": "customer says paid"})
        p.refresh_from_db()
        self.assertEqual(p.status, "created")
        with mock.patch("core.utils.payments.gateway_verify_paid", return_value=("pay_9", 25000, "INR")):
            self.client.post(url, {"action": "confirm_paid", "_selected_action": [p.pk], "apply": "1",
                                   "reason": "email from buyer 14 Nov"})
        p.refresh_from_db()
        self.assertEqual((p.status, p.gateway_payment_id), ("paid", "pay_9"))
        entry = LogEntry.objects.get(object_id=str(p.pk))
        self.assertEqual(entry.user.username, "root")
        self.assertIn("email from buyer 14 Nov", entry.get_change_message())

    def test_refund_needs_refund_id_and_a_real_gateway_refund(self):
        from unittest import mock
        p, url = self._order(status="paid"), self._admin()
        body = {"action": "mark_refunded", "_selected_action": [p.pk], "apply": "1", "reason": "charged twice"}
        self.assertContains(self.client.post(url, body), "refund id")          # no refund id: form again
        with mock.patch("core.utils.payments.razorpay_refunded", return_value=False):
            self.client.post(url, dict(body, refund_ref="rfnd_1"))
        p.refresh_from_db()
        self.assertEqual(p.status, "paid")                                      # Razorpay shows no refund yet
        with mock.patch("core.utils.payments.razorpay_refunded", return_value=True):
            self.client.post(url, dict(body, refund_ref="rfnd_1"))
        p.refresh_from_db()
        self.assertEqual(p.status, "refunded")

    def test_repeated_webhooks_do_not_duplicate(self):
        import hashlib, hmac, json as _json
        from core.models import Purchase
        p = self._order()
        body = _json.dumps({"event": "payment.captured", "payload": {"payment": {"entity": {
            "id": "pay_5", "order_id": "order_1", "amount": 25000, "currency": "INR"}}}}).encode()
        sig = hmac.new(b"whsec", body, hashlib.sha256).hexdigest()
        for _ in range(3):
            self.client.post("/pay/webhook/razorpay/", body, content_type="application/json",
                             HTTP_X_RAZORPAY_SIGNATURE=sig)
        p.refresh_from_db()
        first_paid = p.paid_at
        self.client.post("/pay/webhook/razorpay/", body, content_type="application/json", HTTP_X_RAZORPAY_SIGNATURE=sig)
        p.refresh_from_db()
        self.assertEqual((p.status, Purchase.objects.count(), p.paid_at), ("paid", 1, first_paid))


@override_settings(DEBUG=False, ADMINS=[("Owner", "owner@example.com")])
class CrashReportPrivacyTests(TestCase):
    def test_crash_email_has_no_personal_data(self):
        import logging
        from django.core import mail
        from django.test import RequestFactory
        req = RequestFactory().post("/kundali/generate", {"name": "Asha Verma", "birth_date": "1990-05-17",
                                                          "lat": "25.3176", "email": "asha@example.com"})
        req.COOKIES["sessionid"] = "s3ss10nk3yvalue"
        req.META["HTTP_X_FORWARDED_FOR"] = "203.0.113.9"
        birth_place = "Varanasi-secret-place"       # a local variable in the crashing frame
        try:
            raise ValueError("boom")
        except ValueError:
            logging.getLogger("django.request").error("Internal Server Error: /kundali/generate", exc_info=True,
                                                      extra={"status_code": 500, "request": req})
        self.assertEqual(len(mail.outbox), 1)
        body = mail.outbox[0].body
        self.assertIn("ValueError", body)                                        # still useful for fixing
        for secret in ("Asha Verma", "1990-05-17", "asha@example.com", "s3ss10nk3yvalue", "203.0.113.9",
                       birth_place):
            self.assertNotIn(secret, body)


class KundaliSearchPagesTests(TestCase):
    """Kundali Milan and Janam Kundali pages are readable by search engines, in English and Hindi."""

    def test_old_compatibility_address_redirects_permanently(self):
        self.assertRedirects(self.client.get("/compatibility/"), "/kundali-milan/", status_code=301)
        self.assertRedirects(self.client.get("/hi/compatibility/"), "/hi/kundali-milan/", status_code=301)

    def test_milan_page_has_reading_text_and_faq_in_both_languages(self):
        en = self.client.get("/kundali-milan/").content.decode()
        self.assertIn('"FAQPage"', en)
        self.assertIn("How Many Gunas Should Match?", en)
        hi = self.client.get("/hi/kundali-milan/").content.decode()
        self.assertIn("कुंडली मिलान", hi)
        self.assertIn("आठ कूट और उनके 36 गुण", hi)

    def test_create_kundali_form_is_open_to_everyone(self):
        page = self.client.get("/kundali/create").content.decode()
        self.assertIn('"FAQPage"', page)
        self.assertIn('name="birth_date"', page)
        self.assertIn("1942", page)

    BIRTH = {"name": "Guest", "birth_date": "1943-06-01", "birth_time": "10:30", "birth_place": "Varanasi",
             "lat": "25.3176", "lon": "82.9739", "timezone": "Asia/Kolkata"}

    def test_guest_can_make_and_see_a_kundali_and_claims_it_on_sign_in(self):
        from django.contrib.auth import get_user_model
        from core.models import Kundali
        r = self.client.post("/kundali/generate", self.BIRTH)
        self.assertEqual(r.status_code, 302)
        k = Kundali.objects.get()
        self.assertIsNone(k.user)
        self.assertEqual(self.client.get(r["Location"]).status_code, 200)
        # war time: 10:30 in Varanasi on 1 June 1943 was UTC+6:30 (04:00 UTC); the Moon was then at ~26.1° sidereal
        # Aries, and would be ~26.6° had the usual +5:30 been used.
        self.assertAlmostEqual(k.planetary_positions["Moon"]["longitude_sidereal"], 26.1, delta=0.15)
        self.assertEqual(self.client_class().get(r["Location"]).status_code, 404)   # another browser cannot see it
        user = get_user_model().objects.create_user("claimer", password="x" * 12)
        self.client.login(username="claimer", password="x" * 12)
        k.refresh_from_db()
        self.assertEqual(k.user, user)
        self.assertEqual(self.client.get(r["Location"]).status_code, 200)

    def test_old_guest_kundalis_are_purged(self):
        from datetime import timedelta
        from django.utils import timezone
        from core.models import Kundali
        from core.view_kundali import purge_guest_kundalis
        self.client.post("/kundali/generate", self.BIRTH)
        Kundali.objects.update(created_at=timezone.now() - timedelta(days=31))
        self.assertGreaterEqual(purge_guest_kundalis(), 1)
        self.assertFalse(Kundali.objects.exists())

    def test_sitemap_lists_hindi_pages_and_kundali(self):
        xml = self.client.get("/sitemap-static.xml").content.decode()
        for path in ("/kundali-milan/", "/hi/kundali-milan/", "/kundali/create", "/hi/kundali/create"):
            self.assertIn(path + "</loc>", xml)
        self.assertIn('hreflang="hi"', xml)

    def test_sitemap_index_lastmod_has_timezone(self):
        """Search Console rejects a <lastmod> time without an offset ("Invalid date")."""
        import re
        from core.models import Article
        Article.objects.create(title="T", slug="t", summary="s", body="b", status="published")
        xml = self.client.get("/sitemap.xml").content.decode()
        stamps = re.findall(r"<lastmod>([^<]+)</lastmod>", xml)
        self.assertTrue(stamps)
        for s in stamps:
            self.assertRegex(s, r"^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2}(\.\d+)?([+-]\d{2}:\d{2}|Z))?$")


class KundaliMilanHindiTests(TestCase):
    """On /hi/ the whole milan report is Hindi; new English text in the report fails here until it gets Hindi."""

    def setUp(self):
        from core.models import City
        for gid, name, lat, lon in ((1253405, "Varanasi", 25.3176, 82.9739), (1273294, "Delhi", 28.6519, 77.2315)):
            City.objects.create(geoname_id=gid, name=name, ascii_name=name, search_name=name.lower(), state="",
                                country="India", country_code="IN", latitude=lat, longitude=lon,
                                timezone="Asia/Kolkata", population=1000000, slug=name.lower())

    def _post(self, url, body, n):
        import json
        ip = f"10.20.{n // 200}.{n % 200 + 1}"
        return self.client.post(url, json.dumps(body), content_type="application/json", REMOTE_ADDR=ip,
                                HTTP_X_FORWARDED_FOR=ip).json()

    def test_hindi_report_has_no_english_left(self):
        import random
        import re
        from core.utils import milan_hi
        rnd = random.Random(5)
        english = set()

        def walk(node):
            if isinstance(node, dict):
                for k, v in node.items():
                    if k not in milan_hi._KEEP:
                        walk(v)
            elif isinstance(node, list):
                for v in node:
                    walk(v)
            elif isinstance(node, str) and re.search(r"[A-Za-z]{3,}", node):
                english.add(node)

        for i in range(40):
            day = lambda: f"{rnd.randint(1955, 2005)}-{rnd.randint(1, 12):02d}-{rnd.randint(1, 28):02d}"
            hm = lambda: f"{rnd.randint(0, 23):02d}:{rnd.randint(0, 59):02d}"
            report = self._post("/hi/compatibility/calculate/", {
                "person1_name": "A", "person1_birth_date": day(), "person1_birth_time": hm(), "person1_birth_place": "Varanasi",
                "person2_name": "B", "person2_birth_date": day(), "person2_birth_time": hm(), "person2_birth_place": "Delhi"}, i)
            self.assertTrue(report["success"])
            walk(report)
        for i, name in enumerate(["Ram", "Sita", "Govind", "Meera"]):
            walk(self._post("/hi/compatibility/calculate/", {"mode": "name", "person1_name": name, "person2_name": "Priya"}, 300 + i))
        self.assertEqual(english, set())
        self.assertEqual(milan_hi.untranslated(), set())

    def test_english_report_stays_english(self):
        report = self._post("/compatibility/calculate/", {
            "person1_name": "A", "person1_birth_date": "1990-05-01", "person1_birth_time": "10:00", "person1_birth_place": "Varanasi",
            "person2_name": "B", "person2_birth_date": "1992-08-15", "person2_birth_time": "18:30", "person2_birth_place": "Delhi"}, 400)
        self.assertIn(report["ashtakoot"]["match_status"], ("excellent", "good", "average", "poor"))
        self.assertEqual(report["person1"]["planets"]["Moon"]["planet"], "Moon")

    def test_hindi_page_posts_to_hindi_address_with_hindi_labels(self):
        page = self.client.get("/hi/kundali-milan/").content.decode()
        self.assertIn("fetch('/hi/compatibility/calculate/'", page)
        self.assertIn('id="milan-labels"', page)


class RobotsAiAgentsTests(TestCase):
    def test_ai_assistants_may_fetch_but_ai_crawlers_are_kept_out(self):
        txt = self.client.get("/robots.txt").content.decode()
        groups = [g for g in txt.split("\n\n") if g.strip()]
        users = next(g for g in groups if "User-agent: ChatGPT-User" in g)
        self.assertIn("User-agent: Claude-User", users)
        self.assertNotIn("Disallow: /\n", users + "\n")
        self.assertIn("Disallow: /admin/", users)
        bots = next(g for g in groups if "User-agent: GPTBot" in g)
        for ua in ("ClaudeBot", "OAI-SearchBot", "Claude-SearchBot", "DeepSeekBot"):
            self.assertIn(f"User-agent: {ua}", bots)
        self.assertIn("Disallow: /", bots)


class MarkdownArticleTests(TestCase):
    """articles/*.md: the top block becomes meta fields (never page text), FAQ becomes FAQPage, muhurat pages link back."""

    MD = """---
seo_title: "Short SEO title"
meta_description: "The search snippet."
slug: test-article
h1: "The Long Page Heading"
primary_keyword: "kw one"
secondary_keywords:
  - kw two
publish_date: 2026-11-19
faq_schema: true   # mark up the FAQ
---

# The Long Page Heading

Intro with a [Vivah Muhurat](/shubh-muhurat/vivah/2026/) link and a <b>tag</b>.

| A | B |
|---|---|
| 1 | 2 |

- [ ] Tick me

## Frequently Asked Questions (FAQs)

### 1. Is it **true**?

Yes, see the [panchang](/panchang/).

## Conclusion

Done.
"""

    def _import(self, today):
        import tempfile
        from pathlib import Path
        from core.utils.articles import import_article_files
        with tempfile.TemporaryDirectory() as d:
            Path(d, "x.md").write_text(self.MD, encoding="utf-8")
            return import_article_files(d, today=today)[0]

    def test_waits_for_publish_date(self):
        self.assertEqual(self._import(date(2026, 11, 18)).status, "draft")
        self.assertEqual(self.client.get("/blog/test-article/").status_code, 404)

    def test_page_meta_faq_and_links(self):
        import json
        import re
        a = self._import(date(2026, 11, 19))
        self.assertEqual((a.status, a.title, a.seo_title, a.keywords), ("published", "The Long Page Heading",
                                                                       "Short SEO title", "kw one, kw two"))
        self.assertEqual(a.faq, [["Is it true?", "Yes, see the panchang."]])
        self.assertEqual(a.muhurat_purposes, ["vivah"])
        html = self.client.get("/blog/test-article/").content.decode()
        self.assertIn("<title>Short SEO title |", html)
        self.assertIn('content="The search snippet."', html)
        self.assertNotIn("faq_schema", html)
        self.assertNotIn("primary_keyword", html)
        self.assertEqual(html.count("The Long Page Heading</h1>"), 1)      # the file's own '# ' line is not repeated
        self.assertIn("<table>", html)
        self.assertIn("\u2610 Tick me", html)
        blocks = [json.loads(b) for b in re.findall(r'application/ld\+json">(.*?)</script>', html, re.S)]
        faq = next(b for b in blocks if b["@type"] == "FAQPage")
        self.assertEqual(faq["mainEntity"][0]["name"], "Is it true?")
        back = self.client.get("/shubh-muhurat/vivah/2026/").content.decode()
        self.assertIn('href="/blog/test-article/"', back)


class SanskarMuhuratTests(TestCase):
    """Griha pravesh and the sanskars: their own blackouts, Uttarayana for upanayan, pages in English and Hindi."""
    VARANASI = (25.3176, 82.9739, "Asia/Kolkata")
    KEYS = ("griha-pravesh", "mundan", "namkaran", "annaprashan", "upanayan")

    def test_ceremonies_wait_through_chaturmas_and_kharmas(self):
        from core.utils import muhurat as mu
        start, end = date(2026, 1, 1), date(2026, 12, 31)
        blocked = [b for b in mu.blocked_periods(start, end, "sanskar", *self.VARANASI)
                   if b[2] in ("Chaturmas", "Kharmas")]
        self.assertTrue(any(b[2] == "Chaturmas" for b in blocked))
        for key in self.KEYS:
            for d in mu.muhurat_dates(key, start, end, *self.VARANASI):
                self.assertFalse(any(b[0] <= d["date"] <= b[1] for b in blocked), (key, d["date"]))

    def test_upanayan_only_in_uttarayana(self):
        from core.utils import muhurat as mu
        self.assertEqual(mu.muhurat_dates("upanayan", date(2026, 7, 20), date(2027, 1, 14), *self.VARANASI), [])
        self.assertTrue(mu.muhurat_dates("upanayan", date(2027, 1, 15), date(2027, 6, 30), *self.VARANASI))

    def test_pages_and_hub_links(self):
        hub = self.client.get("/shubh-muhurat/").content.decode()
        for key in self.KEYS:
            self.assertIn(f"/shubh-muhurat/{key}/", hub)
            self.assertEqual(self.client.get(f"/shubh-muhurat/{key}/2027/").status_code, 200)
        hi = self.client.get("/hi/shubh-muhurat/griha-pravesh/2027/").content.decode()
        self.assertIn("गृह प्रवेश", hi)

    def test_griha_pravesh_only_first_half_of_dhanishta(self):
        """Owner's acharya: Dhanishta's second half (Moon in Kumbha) is Panchak, so no griha pravesh then."""
        from core.utils import muhurat as mu
        from core.utils.constants import NAKSHATRA_NAMES
        self.assertNotIn(NAKSHATRA_NAMES.index("Shatabhisha"), mu.PURPOSES["griha-pravesh"]["nakshatras"])   # all Panchak
        start, end = date(2027, 1, 1), date(2028, 12, 31)
        days = mu.day_segments(start, end, *self.VARANASI)
        kumbha_dhanishta = [(s["start"], s["end"]) for d in days for s in d["segments"]
                            if s["nak_name"] == "Dhanishta" and s["moon_sign"] == 10]
        self.assertTrue(kumbha_dhanishta)
        for w in mu.find_muhurats("griha-pravesh", start, end, *self.VARANASI, days=days):
            self.assertFalse(any(w["start"] < b and w["end"] > a for a, b in kumbha_dhanishta), w)


class AajKaPanchangTests(TestCase):
    """/aaj-ka-panchang/: stored once a day (05:30 IST job), stamped with the real time it was computed."""

    def test_muhurat_rahu_kaal_matches_the_panchang(self):
        # muhurat.RAHU_KAAL_PART once counted from 0 and then subtracted 1, putting Rahu Kaal an eighth too early.
        import pytz
        from datetime import datetime, timedelta as td
        from core.utils import muhurat as mu
        from core.utils.astro_calculations import get_panchang
        lat, lon, tz = 28.6139, 77.2090, "Asia/Kolkata"
        for i in range(7):                                  # one of each weekday
            d = date(2026, 11, 22) + td(days=i)
            day = mu.day_segments(d, d, lat, lon, tz)[0]
            p = get_panchang(target_date=pytz.timezone(tz).localize(datetime.combine(d, datetime.min.time()) + td(hours=12)),
                             lat=lat, lon=lon, timezone_str=tz, city_name="Delhi")
            self.assertEqual(day["rahu_kaal"][0].strftime("%H:%M")[:4], p["rahukaalstart"][:4], d)

    def test_page_in_both_languages_with_the_stored_time(self):
        from datetime import datetime
        from unittest import mock
        import pytz
        from django.core.cache import cache
        from core.utils import aaj_panchang as ap
        cache.clear()
        at = pytz.utc.localize(datetime(2026, 11, 25, 0, 0, 30))          # 05:30 IST
        snap = ap.build(date(2026, 11, 25), now=at)
        with mock.patch.object(ap, "today_ist", return_value=date(2026, 11, 25)):
            res = self.client.get("/aaj-ka-panchang/")
            hi = self.client.get("/hi/aaj-ka-panchang/")
        self.assertEqual(snap["date"], date(2026, 11, 25))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Aaj Ka Panchang 25 November 2026")
        self.assertContains(res, "25 November 2026, 05:30 IST")
        self.assertContains(res, '"dateModified":"2026-11-25T05:30:30+05:30"')
        self.assertEqual(res["Last-Modified"], "Wed, 25 Nov 2026 00:00:30 GMT")
        for text in ("Varanasi", "Delhi", "Rahu Kaal", "Gulika Kaal", "Disha Shool", "Kharmas", "Sade Sati", "/kundali/create"):
            self.assertContains(res, text)
        self.assertNotContains(res, "Choghadiya")
        self.assertContains(hi, "आज का पंचांग 25 नवम्बर 2026")
        self.assertContains(hi, "साढ़े साती")

    def test_visitors_get_the_stored_page_not_a_new_build(self):
        from unittest import mock
        from django.core.cache import cache
        from core.utils import aaj_panchang as ap
        cache.clear()
        first = ap.today_snapshot()
        with mock.patch.object(ap, "build") as build:
            self.assertEqual(ap.today_snapshot()["computed_at"], first["computed_at"])
        build.assert_not_called()

    def test_shani_rows_and_unfavourable_periods(self):
        from core.utils import aaj_panchang as ap
        rows = ap._shani(date(2026, 11, 25))
        self.assertEqual({(r["sign"], r["key"]) for r in rows},
                         {("Mesh", "sade"), ("Kumbh", "sade"), ("Meen", "sade"), ("Simha", "ashtama"), ("Dhanu", "kantak")})
        periods, bhadra = ap._unfavourable(date(2026, 11, 25))
        names = [r["name"] for r in periods]
        self.assertIn("Kharmas", names)
        self.assertIn("Panchak", names)
        self.assertTrue(bhadra)

    def test_city_search_is_computed_live_and_canonical_to_the_main_page(self):
        res = self.client.get("/aaj-ka-panchang/?city=Mumbai")
        self.assertEqual(res.status_code, 200)
        self.assertNotIn("Last-Modified", res)
        self.assertContains(res, 'rel="canonical" href="http')
        self.assertContains(res, '/aaj-ka-panchang/"')


class PanchangTimeRuleTests(TestCase):
    """Textbook rules for the day's periods, checked for every weekday (audit of 2026-11-24)."""
    RAHU = [8, 2, 7, 5, 6, 4, 3]          # which eighth of daytime, Sunday first
    YAMA = [5, 4, 3, 2, 1, 7, 6]
    GULIKA = [7, 6, 5, 4, 3, 2, 1]
    DAY_FIRST = ["Udveg", "Amrit", "Rog", "Labh", "Shubh", "Char", "Kaal"]
    DAY_SEQ = ["Udveg", "Char", "Labh", "Amrit", "Kaal", "Shubh", "Rog"]
    HORA_SEQ = ["Sun", "Venus", "Mercury", "Moon", "Saturn", "Jupiter", "Mars"]
    LORD = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]

    def _day(self, d):
        import pytz
        from datetime import datetime, timedelta as td
        from core.utils.astro_calculations import get_panchang
        tz = pytz.timezone("Asia/Kolkata")
        p = get_panchang(target_date=tz.localize(datetime.combine(d, datetime.min.time()) + td(hours=12)),
                         lat=28.6139, lon=77.2090, timezone_str="Asia/Kolkata", city_name="Delhi")
        minutes = lambda hm: int(hm[:2]) * 60 + int(hm[3:5])
        return p, minutes

    def test_rahu_yama_gulika_choghadiya_and_hora_every_weekday(self):
        from datetime import timedelta as td
        for i in range(7):
            d = date(2026, 11, 22) + td(days=i)
            v = (d.weekday() + 1) % 7
            p, m = self._day(d)
            sr, ss = m(p["sunrise"]), m(p["sunset"])
            part = (ss - sr) / 8
            for key, table in (("rahukaalstart", self.RAHU), ("yamakaalstart", self.YAMA), ("gulikakaalstart", self.GULIKA)):
                self.assertAlmostEqual(m(p[key]), sr + part * (table[v] - 1), delta=2, msg=(d, key))
            ch = p["choghadiya"]
            names = [x["name"] for x in sorted(ch["day_ausp"] + ch["day_inausp"], key=lambda x: x["start"])]
            k = self.DAY_SEQ.index(self.DAY_FIRST[v])
            self.assertEqual(names, [self.DAY_SEQ[(k + j) % 7] for j in range(8)], d)
            k = self.HORA_SEQ.index(self.LORD[v])
            self.assertEqual([h["planet"] for h in p["day_horas"] + p["night_horas"]],
                             [self.HORA_SEQ[(k + j) % 7] for j in range(24)], d)

    def test_moonrise_and_moonset_use_the_local_day(self):
        # astral gave "No moonset" on 23 Nov 2026 although the Moon set at about 05:11 in Delhi
        import pytz
        from datetime import datetime
        from core.utils.astro_calculations import get_panchang
        p, _ = self._day(date(2026, 11, 23))
        self.assertEqual(p["moonset"][:4], "05:1")
        tz = pytz.timezone("Asia/Kolkata")
        early = get_panchang(target_date=tz.localize(datetime(2026, 11, 23, 1, 0)), lat=28.6139, lon=77.2090,
                             timezone_str="Asia/Kolkata", city_name="Delhi")      # 01:00 IST is still 22 Nov in UTC
        self.assertEqual(early["moonset"], p["moonset"])
        self.assertEqual(early["moonrise"], p["moonrise"])


class KumbhMelaTests(TestCase):
    """/kumbh-mela/: announced snan dates, Guru's sign windows, and the links into festival pages and the calendar."""

    def test_guru_windows_match_known_kumbh(self):
        from core.utils import kumbh
        w = kumbh.guru_windows(date(2020, 1, 1), years=20)
        # Nashik Simhastha: flags up 31 Oct 2026, down 24 Jul 2028 - exactly Guru's stay in Simha
        self.assertIn((date(2026, 10, 31), date(2028, 7, 24)), w[4])
        self.assertTrue(any(a <= date(2021, 4, 12) <= b for a, b in w[10]))     # Haridwar Kumbh 2021
        self.assertTrue(any(a <= date(2025, 1, 29) <= b for a, b in w[1]))      # Prayagraj Maha Kumbh 2025
        self.assertTrue(any(a <= date(2037, 1, 20) <= b for a, b in w[1]))      # Prayagraj 2037
        self.assertTrue(any(a <= date(2033, 4, 14) <= b for a, b in w[10]))     # Haridwar 2033

    def test_snans_agree_with_our_festival_dates(self):
        from core.utils import kumbh
        for m in kumbh.MELAS:
            for s in m["snans"]:
                if s["slug"]:
                    rows = fc.get_festival_by_slug(s["slug"], s["date"].year)
                    self.assertTrue(any(abs((f["date"] - s["date"]).days) <= 1 for f in rows), (m["key"], s["name"]))

    def test_page_in_both_languages(self):
        r = self.client.get("/kumbh-mela/")
        self.assertContains(r, "Haridwar Ardh Kumbh 2027")
        self.assertContains(r, '"@type":"Event"')
        self.assertContains(r, "/festivals/2027/mauni-amavasya/")
        r = self.client.get("/hi/kumbh-mela/")
        self.assertContains(r, "हरिद्वार अर्ध कुम्भ 2027")
        self.assertContains(r, "अगला कुम्भ मेला कब है?")

    def test_festival_page_and_calendar_link_to_kumbh(self):
        r = self.client.get("/festivals/2027/makar-sankranti/")
        self.assertContains(r, "This day is also a snan of the")
        self.assertContains(r, "14 or 15 January?")
        self.assertContains(self.client.get("/hi/festivals/2027/mauni-amavasya/"), "मौन क्यों?")
        cal = self.client.get("/festivals/2027/").content.decode()
        self.assertIn('href="/kumbh-mela/#haridwar-2027"', cal)
        cal = self.client.get("/festivals/2026/").content.decode()
        self.assertNotIn("/festivals/2026/kedarnath-dham-kapat/", cal)   # shrine windows have no festival page
