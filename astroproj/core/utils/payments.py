# core/utils/payments.py
"""
Prices, currency choice and the two payment gateways (Razorpay and PhonePe).

Money is always in minor units (paise / cents) and is set here on the server: the browser never
tells us what to charge. A purchase is marked paid only after the gateway confirms it:
  * Razorpay: HMAC signature of the order and payment ids (checkout callback), or a signed webhook
  * PhonePe: the server-to-server Order Status API (the redirect alone proves nothing), or a webhook
    whose Authorization header is sha256("username:password") as set in the PhonePe dashboard

PhonePe takes INR only, so dollar prices go through Razorpay (international cards must be enabled
on the Razorpay account).
"""
import hashlib
import hmac
import logging
import time
from urllib.parse import unquote

import requests
from django.conf import settings
from django.db import transaction
from django.utils import timezone

logger = logging.getLogger(__name__)

PRODUCTS = {
    "kundali_pdf": {
        "title": "Complete Kundali Report (PDF)",
        "title_hi": "सम्पूर्ण कुण्डली रिपोर्ट (PDF)",
        "blurb": "All divisional charts D1 to D60, the transit chart, planet details, Vimshottari Mahadasha, "
                 "Antardasha and Pratyantar dasha, and dosha analysis with remedies, in a printed-book layout.",
        "price": {"INR": 25000, "USD": 1000},
        "login": True,
    },
    "aahaar_pdf": {
        "title": "Aahaar and Ritucharya Guide (PDF)",
        "title_hi": "आहार और ऋतुचर्या मार्गदर्शिका (PDF)",
        "blurb": "Today's seasonal guidance for your city, the daily rhythm by pahar, regional foods of India, "
                 "diet by age, pregnancy, weight loss, gym and yoga, in a printed-book layout.",
        "price": {"INR": 10000, "USD": 500},
        "login": False,
    },
}
CURRENCIES = {"INR": "₹", "USD": "$"}
INDIA_TIMEZONES = {"Asia/Kolkata", "Asia/Calcutta"}
DOWNLOAD_LIMIT = 10
DOWNLOAD_DAYS = 30


def price(product, currency):
    return PRODUCTS[product]["price"][currency]


def format_price(product, currency):
    value = price(product, currency) / 100
    return f"{CURRENCIES[currency]}{value:,.0f}" if value == int(value) else f"{CURRENCIES[currency]}{value:,.2f}"


def currency_from_country(request):
    """INR or USD from the CDN's visitor-country header (Cloudflare CF-IPCountry), or None when it is absent."""
    header = getattr(settings, "COUNTRY_HEADER", "HTTP_CF_IPCOUNTRY")
    country = (request.META.get(header) or "").upper()
    if len(country) == 2 and country not in ("XX", "T1"):
        return "INR" if country == "IN" else "USD"
    return None


def detect_currency(request):
    """
    INR for visitors in India, USD for everyone else.
    Order: the CDN's country header (final when present: visitors cannot switch then), an explicit choice
    (?currency=), the browser's own time zone (cookie set by base.html), the Accept-Language region, then INR.
    """
    known = currency_from_country(request)
    if known:                       # the CDN knows the country: that decides, and no switch is offered
        return known
    chosen = (request.GET.get("currency") or "").upper()
    if chosen in CURRENCIES:
        request.session["currency"] = chosen
        return chosen
    if request.session.get("currency") in CURRENCIES:
        return request.session["currency"]
    tz = unquote(request.COOKIES.get("va_tz", ""))
    if tz:
        return "INR" if tz in INDIA_TIMEZONES else "USD"
    lang = request.META.get("HTTP_ACCEPT_LANGUAGE", "").lower()
    if "-in" in lang or lang.startswith("hi") or ",hi" in lang:
        return "INR"
    return "INR"


def gateways_for(currency):
    """Gateways that are configured and accept this currency, best first."""
    out = []
    if settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_SECRET:
        out.append("razorpay")
    if currency == "INR" and settings.PHONEPE_CLIENT_ID and settings.PHONEPE_CLIENT_SECRET:
        out.append("phonepe")
    if settings.DEBUG and getattr(settings, "PAYMENTS_ALLOW_TEST", True):
        out.append("dev")
    return out


def mark_paid(purchase_id, gateway_payment_id="", amount=None, currency=None):
    """Idempotent: flips a purchase to paid once. Refuses if the confirmed amount does not match."""
    from ..models import Purchase
    with transaction.atomic():
        p = Purchase.objects.select_for_update().get(pk=purchase_id)
        if p.status == "paid":
            return p
        if amount is not None and int(amount) != p.amount:
            logger.error("Amount mismatch for %s: paid %s, expected %s", p.ref, amount, p.amount)
            return p
        if currency and currency.upper() != p.currency:
            logger.error("Currency mismatch for %s: %s vs %s", p.ref, currency, p.currency)
            return p
        p.status = "paid"
        p.paid_at = timezone.now()
        if gateway_payment_id:
            p.gateway_payment_id = gateway_payment_id[:80]
        p.save(update_fields=["status", "paid_at", "gateway_payment_id"])
        return p


# ---------------------------------------------------------------------------
# Razorpay
# ---------------------------------------------------------------------------

def _razorpay():
    import razorpay
    return razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


def razorpay_create_order(purchase):
    order = _razorpay().order.create({
        "amount": purchase.amount, "currency": purchase.currency, "receipt": purchase.ref,
        "notes": {"ref": purchase.ref, "product": purchase.product},
    })
    return order["id"]


def razorpay_captured(order_id):
    """(payment id, amount, currency) of a captured payment on this Razorpay order, asked from Razorpay; else None."""
    items = (_razorpay().order.payments(order_id) or {}).get("items") or []
    for it in items:
        if it.get("status") == "captured":
            return it.get("id", ""), it.get("amount"), it.get("currency")
    return None


def razorpay_refunded(payment_id):
    """True when Razorpay says this payment was refunded in full."""
    pay = _razorpay().payment.fetch(payment_id) or {}
    return pay.get("refund_status") == "full" or (pay.get("amount_refunded") or 0) >= (pay.get("amount") or 1)


def gateway_verify_paid(purchase):
    """Ask the gateway (never the admin user) whether this order was paid. (payment id, amount, currency) or None."""
    if purchase.gateway == "razorpay" and purchase.gateway_order_id:
        return razorpay_captured(purchase.gateway_order_id)
    if purchase.gateway == "phonepe":
        state, amount, txn = phonepe_order_status(purchase.ref)
        if state == "COMPLETED":
            return txn, amount, purchase.currency
    return None


def razorpay_signature_ok(order_id, payment_id, signature):
    """Checkout callback: HMAC-SHA256(order_id|payment_id) with the key secret."""
    if not (order_id and payment_id and signature):
        return False
    digest = hmac.new(settings.RAZORPAY_KEY_SECRET.encode(), f"{order_id}|{payment_id}".encode(),
                      hashlib.sha256).hexdigest()
    return hmac.compare_digest(digest, signature)


def razorpay_webhook_ok(body, signature):
    secret = settings.RAZORPAY_WEBHOOK_SECRET
    if not (secret and signature):
        return False
    digest = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(digest, signature)


# ---------------------------------------------------------------------------
# PhonePe Standard Checkout v2 (paths from PhonePe's own SDK)
# ---------------------------------------------------------------------------

PHONEPE_HOSTS = {
    "PRODUCTION": ("https://api.phonepe.com/apis/pg", "https://api.phonepe.com/apis/identity-manager"),
    "SANDBOX": ("https://api-preprod.phonepe.com/apis/pg-sandbox", "https://api-preprod.phonepe.com/apis/pg-sandbox"),
}
_phonepe_token = {"value": None, "expires": 0}


def _phonepe_hosts():
    return PHONEPE_HOSTS.get(settings.PHONEPE_ENV.upper(), PHONEPE_HOSTS["SANDBOX"])


def _phonepe_auth():
    """'O-Bearer <token>', refreshed when the cached one is near expiry."""
    if _phonepe_token["value"] and time.time() < _phonepe_token["expires"] - 120:
        return _phonepe_token["value"]
    _, oauth = _phonepe_hosts()
    res = requests.post(f"{oauth}/v1/oauth/token", data={
        "client_id": settings.PHONEPE_CLIENT_ID, "client_secret": settings.PHONEPE_CLIENT_SECRET,
        "client_version": str(settings.PHONEPE_CLIENT_VERSION), "grant_type": "client_credentials",
    }, timeout=20)
    res.raise_for_status()
    data = res.json()
    _phonepe_token["value"] = f"{data.get('token_type', 'O-Bearer')} {data['access_token']}"
    _phonepe_token["expires"] = float(data.get("expires_at") or time.time() + 600)
    return _phonepe_token["value"]


def phonepe_create_payment(purchase, redirect_url):
    """Returns PhonePe's hosted checkout URL to send the buyer to."""
    pg, _ = _phonepe_hosts()
    res = requests.post(f"{pg}/checkout/v2/pay", json={
        "merchantOrderId": purchase.ref, "amount": purchase.amount, "expireAfter": 1200,
        "metaInfo": {"udf1": purchase.product},
        "paymentFlow": {"type": "PG_CHECKOUT", "message": PRODUCTS[purchase.product]["title"],
                        "merchantUrls": {"redirectUrl": redirect_url}},
    }, headers={"Authorization": _phonepe_auth(), "Content-Type": "application/json"}, timeout=20)
    res.raise_for_status()
    data = res.json()
    return data.get("orderId", ""), data["redirectUrl"]


def phonepe_order_status(merchant_order_id):
    """(state, amount, transaction id). state is COMPLETED, FAILED or PENDING."""
    pg, _ = _phonepe_hosts()
    res = requests.get(f"{pg}/checkout/v2/order/{merchant_order_id}/status",
                       headers={"Authorization": _phonepe_auth()}, timeout=20)
    res.raise_for_status()
    data = res.json()
    details = data.get("paymentDetails") or [{}]
    return data.get("state", "PENDING"), data.get("amount"), details[-1].get("transactionId", "")


def phonepe_webhook_ok(authorization):
    user, pwd = settings.PHONEPE_WEBHOOK_USER, settings.PHONEPE_WEBHOOK_PASSWORD
    if not (user and pwd and authorization):
        return False
    expected = hashlib.sha256(f"{user}:{pwd}".encode()).hexdigest()
    return hmac.compare_digest(expected, authorization.strip())
