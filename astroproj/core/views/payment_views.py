# core/views/payment_views.py
"""
Paid PDFs: checkout, Razorpay and PhonePe callbacks and webhooks, and the owner-only download.

Owner-only means: the logged-in buyer for kundali reports; for guest Aahaar purchases, the browser session that
paid, or anyone who opens the order link and proves the purchase email. Every PDF carries the buyer's name,
email and order number on each page, and downloads stop after DOWNLOAD_LIMIT or DOWNLOAD_DAYS.
"""
import json
import logging
from datetime import date, timedelta

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.http import Http404, HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone, translation
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from ..models import Kundali, Purchase
from ..utils import payments as pay
from .seo_views import user_location

logger = logging.getLogger(__name__)


def _session_key(request):
    if not request.session.session_key:
        request.session.save()
    return request.session.session_key


def _owns(request, p):
    if p.user_id:
        return request.user.is_authenticated and request.user.id == p.user_id
    if p.session_key and p.session_key == request.session.session_key:
        return True
    return p.ref in request.session.get("unlocked_orders", [])


def _price_context(request, product):
    currency = pay.detect_currency(request)
    other = "USD" if currency == "INR" else "INR"
    return {
        "product": product, "info": pay.PRODUCTS[product], "currency": currency,
        "price": pay.format_price(product, currency), "other_currency": other,
        "other_price": pay.format_price(product, other), "gateways": pay.gateways_for(currency) + (["comp"] if request.user.is_superuser else []),
        "lang": translation.get_language() or "en",
    }


def _start_payment(request, purchase):
    """Create the gateway order and hand the buyer over to it."""
    if purchase.gateway == "dev":
        pay.mark_paid(purchase.id, "TEST-" + purchase.ref)
        return redirect("order_status", token=purchase.token)
    if purchase.gateway == "comp":
        if not request.user.is_superuser:
            raise Http404("Unknown gateway")
        pay.mark_paid(purchase.id, "COMP-" + purchase.ref)
        logger.warning("AUDIT complimentary %s %s by %s", purchase.product, purchase.ref, request.user.username)
        return redirect("order_status", token=purchase.token)
    try:
        if purchase.gateway == "razorpay":
            purchase.gateway_order_id = pay.razorpay_create_order(purchase)
            purchase.save(update_fields=["gateway_order_id"])
            return render(request, "payments/razorpay.html", {
                "p": purchase, "key_id": settings.RAZORPAY_KEY_ID, "info": pay.PRODUCTS[purchase.product]})
        if purchase.gateway == "phonepe":
            back = request.build_absolute_uri(reverse("phonepe_return", args=[purchase.token]))
            order_id, url = pay.phonepe_create_payment(purchase, back)
            purchase.gateway_order_id = order_id or purchase.ref
            purchase.save(update_fields=["gateway_order_id"])
            return redirect(url)
    except Exception:
        logger.exception("Could not start %s payment for %s", purchase.gateway, purchase.ref)
        purchase.status = "failed"
        purchase.save(update_fields=["status"])
        return render(request, "payments/order.html", {
            "p": purchase, "error": "The payment gateway could not be reached. Nothing was charged; please try again."},
            status=502)
    raise Http404("Unknown gateway")


def _checkout(request, product, kundali=None, params=None):
    ctx = _price_context(request, product)
    ctx.update({"kundali": kundali, "params": params or {}})
    user = request.user if request.user.is_authenticated else None
    if request.method == "GET":
        ctx["form"] = {"name": (kundali.name if kundali else "") or (user.get_full_name() if user else ""),
                       "email": user.email if user else "", "phone": "", "lang": ctx["lang"]}
        return render(request, "payments/checkout.html", ctx)

    form = {k: request.POST.get(k, "").strip() for k in ("name", "email", "phone", "lang", "gateway")}
    ctx["form"] = form
    errors = []
    if not form["name"]:
        errors.append("Please enter the name to print on the report.")
    try:
        validate_email(form["email"])
    except ValidationError:
        errors.append("Please enter a valid email: it is printed on the PDF and unlocks your download.")
    if form["gateway"] not in ctx["gateways"]:
        errors.append("Please choose a payment method.")
    if errors:
        ctx["errors"] = errors
        return render(request, "payments/checkout.html", ctx, status=400)
    purchase = Purchase.objects.create(
        product=product, user=user, session_key=_session_key(request), kundali=kundali, params=params or {},
        language=form["lang"] if form["lang"] in ("en", "hi") else "en",
        currency=ctx["currency"], gateway=form["gateway"],
        amount=0 if form["gateway"] == "comp" else pay.price(product, ctx["currency"]),
        buyer_name=form["name"][:100], buyer_email=form["email"], buyer_phone=form["phone"][:20],
    )
    return _start_payment(request, purchase)


@login_required
def buy_kundali_pdf(request, kundali_id):
    kundali = get_object_or_404(Kundali, id=kundali_id, user=request.user)
    paid = Purchase.objects.filter(kundali=kundali, user=request.user, product="kundali_pdf", status="paid").first()
    if paid and request.method == "GET" and not request.GET.get("again"):
        return redirect("order_status", token=paid.token)
    return _checkout(request, "kundali_pdf", kundali=kundali)


def buy_aahaar_pdf(request):
    lat, lon, tz, city = user_location(request)
    try:
        d = date.fromisoformat(request.GET.get("date") or request.POST.get("date") or "")
    except ValueError:
        d = timezone.now().date()
    from ..utils import prefs
    params = {"date": d.isoformat(), "city": city, "lat": lat, "lon": lon, "tz": tz,
              "region": prefs.food_region(request, city, lat, lon), "month_system": prefs.month_system(request)}
    return _checkout(request, "aahaar_pdf", params=params)


@require_POST
def razorpay_verify(request):
    p = get_object_or_404(Purchase, token=request.POST.get("token", ""), gateway="razorpay")
    order_id = request.POST.get("razorpay_order_id", "")
    if order_id != p.gateway_order_id or not pay.razorpay_signature_ok(
            order_id, request.POST.get("razorpay_payment_id", ""), request.POST.get("razorpay_signature", "")):
        logger.warning("Razorpay signature check failed for %s", p.ref)
        return render(request, "payments/order.html", {
            "p": p, "error": "We could not verify this payment. If money was debited, it will be confirmed "
                             "automatically within a few minutes, or refunded."}, status=400)
    pay.mark_paid(p.id, request.POST.get("razorpay_payment_id", ""))
    return redirect("order_status", token=p.token)


def phonepe_return(request, token):
    """The buyer comes back from PhonePe: ask PhonePe's server what happened (the redirect itself proves nothing)."""
    p = get_object_or_404(Purchase, token=token, gateway="phonepe")
    if p.status != "paid":
        try:
            state, amount, txn = pay.phonepe_order_status(p.ref)
            if state == "COMPLETED":
                pay.mark_paid(p.id, txn, amount=amount)
            elif state == "FAILED":
                Purchase.objects.filter(pk=p.pk, status="created").update(status="failed")
        except Exception:
            logger.exception("PhonePe status check failed for %s", p.ref)
    return redirect("order_status", token=p.token)


@csrf_exempt
@require_POST
def razorpay_webhook(request):
    if not pay.razorpay_webhook_ok(request.body, request.headers.get("X-Razorpay-Signature", "")):
        return HttpResponseBadRequest("bad signature")
    event = json.loads(request.body or b"{}")
    if event.get("event") in ("payment.captured", "order.paid"):
        entity = (event.get("payload", {}).get("payment") or {}).get("entity") or {}
        p = Purchase.objects.filter(gateway="razorpay", gateway_order_id=entity.get("order_id", "")).first()
        if p:
            pay.mark_paid(p.id, entity.get("id", ""), amount=entity.get("amount"), currency=entity.get("currency"))
    return JsonResponse({"ok": True})


@csrf_exempt
@require_POST
def phonepe_webhook(request):
    if not pay.phonepe_webhook_ok(request.headers.get("Authorization", "")):
        return HttpResponseBadRequest("bad authorization")
    event = json.loads(request.body or b"{}")
    ref = (event.get("payload") or {}).get("merchantOrderId", "")
    p = Purchase.objects.filter(gateway="phonepe", ref=ref).first()
    if p and p.status != "paid":
        try:   # confirm with the status API rather than trusting the webhook body alone
            state, amount, txn = pay.phonepe_order_status(p.ref)
            if state == "COMPLETED":
                pay.mark_paid(p.id, txn, amount=amount)
            elif state == "FAILED":
                Purchase.objects.filter(pk=p.pk, status="created").update(status="failed")
        except Exception:
            logger.exception("PhonePe webhook status check failed for %s", ref)
    return JsonResponse({"ok": True})


def _download_state(p):
    if not p.is_paid:
        return "unpaid"
    if p.paid_at and timezone.now() > p.paid_at + timedelta(days=pay.DOWNLOAD_DAYS):
        return "expired"
    if p.download_count >= pay.DOWNLOAD_LIMIT:
        return "limit"
    return "ok"


def order_status(request, token):
    p = get_object_or_404(Purchase, token=token)
    owner = _owns(request, p)
    if request.method == "POST" and not owner:          # unlock on another device with the purchase email
        if request.POST.get("email", "").strip().lower() == p.buyer_email.lower():
            request.session["unlocked_orders"] = request.session.get("unlocked_orders", []) + [p.ref]
            owner = True
        else:
            return render(request, "payments/order.html", {"p": p, "owner": False,
                                                           "error": "That email does not match this order."},
                          status=403)
    if p.gateway == "phonepe" and p.status == "created" and owner:
        return phonepe_return(request, token)
    return render(request, "payments/order.html", {
        "p": p, "owner": owner, "state": _download_state(p), "info": pay.PRODUCTS[p.product],
        "left": max(0, pay.DOWNLOAD_LIMIT - p.download_count),
        "until": p.paid_at + timedelta(days=pay.DOWNLOAD_DAYS) if p.paid_at else None,
    })


def order_download(request, token):
    p = get_object_or_404(Purchase, token=token)
    if not _owns(request, p):
        return redirect("order_status", token=token)
    state = _download_state(p)
    if state != "ok":
        return redirect("order_status", token=token)
    lang = request.GET.get("lang") if request.GET.get("lang") in ("en", "hi") else p.language
    from ..utils import pdf_store
    if p.product == "kundali_pdf":
        if not p.kundali:
            raise Http404("The kundali for this order was deleted")
        from ..pdf import kundali_report
        data = pdf_store.get_or_build(p, lang, lambda: kundali_report.build(
            p.kundali, lang=lang, licensee=p.buyer_name, email=p.buyer_email, order_ref=p.ref))
        filename = f"Kundali-{p.kundali.name}-{p.ref}.pdf"
    else:
        from ..pdf import aahaar_report
        data = pdf_store.get_or_build(p, lang, lambda: aahaar_report.build(
            p.params, lang=lang, licensee=p.buyer_name, email=p.buyer_email, order_ref=p.ref))
        filename = f"Aahaar-{p.params.get('date', '')}-{p.ref}.pdf"
    Purchase.objects.filter(pk=p.pk).update(download_count=p.download_count + 1, last_download_at=timezone.now())
    safe = "".join(c if c.isalnum() or c in "-_." else "-" for c in filename)
    res = HttpResponse(data, content_type="application/pdf")
    res["Content-Disposition"] = f'attachment; filename="{safe}"'
    res["Cache-Control"] = "private, no-store"
    res["X-Robots-Tag"] = "noindex"
    return res


@login_required
def my_orders(request):
    return render(request, "payments/my_orders.html", {
        "orders": Purchase.objects.filter(user=request.user).select_related("kundali")})


def refund_policy(request):
    from ..utils.localized import localized
    return render(request, localized("static_pages/refund_policy.html"), {
        "prices": [(v["title"], pay.format_price(k, "INR"), pay.format_price(k, "USD"), v.get("title_hi", v["title"]))
                   for k, v in pay.PRODUCTS.items()],
        "limit": pay.DOWNLOAD_LIMIT, "days": pay.DOWNLOAD_DAYS,
    })
