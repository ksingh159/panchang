from django.contrib import admin

from .models import Article, ContactMessage


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("created_at", "kind", "name", "email", "order_ref", "handled")
    list_filter = ("handled", "kind")
    search_fields = ("name", "email", "order_ref", "message")
    list_editable = ("handled",)
    readonly_fields = ("created_at", "user", "page")


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ("title", "topic", "status", "published_at", "updated_at")
    list_filter = ("status", "topic")
    search_fields = ("title", "summary", "body")
    prepopulated_fields = {"slug": ("title",)}
    actions = ["publish"]

    @admin.action(description="Publish the selected articles")
    def publish(self, request, queryset):
        for a in queryset:
            if "[Owner:" in a.body:
                self.message_user(request, f"Not published: '{a.title}' still has the [Owner: ...] placeholder.",
                                  level="warning")
                continue
            a.status = "published"
            a.save()

    def save_model(self, request, obj, form, change):
        if obj.status == "published" and "[Owner:" in obj.body:
            obj.status = "draft"
            self.message_user(request, "Kept as draft: replace the [Owner: ...] placeholder first.", level="warning")
        super().save_model(request, obj, form, change)




import logging

from django import forms
from django.contrib import messages
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.template.response import TemplateResponse

from .models import Purchase

audit = logging.getLogger("core.audit")


class OrderActionForm(forms.Form):
    reason = forms.CharField(widget=forms.Textarea(attrs={"rows": 3, "cols": 70}), max_length=500,
                             help_text="Why you are doing this (customer message, ticket, what you checked).")
    refund_ref = forms.CharField(required=False, max_length=80, label="Gateway refund id",
                                 help_text="The refund id from the Razorpay or PhonePe dashboard (rfnd_... for "
                                           "Razorpay).")


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    """Orders are read-only here: they are the accounting record. Every action asks for a reason first; the reason,
    the staff user and the time are saved in the order's History and written as an AUDIT log line."""
    list_display = ("ref", "created_at", "product", "status", "gateway", "price", "download_count")
    list_filter = ("status", "gateway", "product", "currency")
    search_fields = ("ref", "buyer_email", "buyer_name", "buyer_phone", "gateway_order_id", "gateway_payment_id")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
    actions = ["confirm_paid", "mark_refunded", "rebuild_pdf"]

    def get_readonly_fields(self, request, obj=None):
        return [f.name for f in self.model._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(description="Amount")
    def price(self, obj):
        return f"{'₹' if obj.currency == 'INR' else '$'}{obj.amount / 100:.2f}"

    # -- shared confirmation step ----------------------------------------------------------------------------
    def _ask(self, request, queryset, action, title, warning, need_refund_ref=False):
        """The reason form. Returns the valid form once submitted, otherwise the page to show."""
        form = OrderActionForm(request.POST if "apply" in request.POST else None)
        if form.is_bound and form.is_valid():
            if not need_refund_ref or form.cleaned_data["refund_ref"].strip():
                return form
            form.add_error("refund_ref", "Enter the gateway's refund id: refund the money in the gateway first.")
        return TemplateResponse(request, "admin/core/purchase/order_action.html", {
            **self.admin_site.each_context(request), "title": title, "warning": warning, "orders": queryset,
            "form": form, "action": action, "need_refund_ref": need_refund_ref, "opts": self.model._meta,
            "action_checkbox_name": ACTION_CHECKBOX_NAME,
        })

    def _record(self, request, p, what, reason):
        self.log_change(request, p, f"{what}. Reason: {reason}")
        audit.warning("AUDIT %s %s by %s", what, p.ref, request.user.username)

    # -- actions -------------------------------------------------------------------------------------------
    @admin.action(description="Confirm payment (checked with Razorpay / PhonePe)")
    def confirm_paid(self, request, queryset):
        form = self._ask(request, queryset, "confirm_paid", "Confirm payment with the gateway",
                         "Each order is checked with Razorpay or PhonePe. Only an order the gateway reports as "
                         "captured, for the right amount, is marked paid. Nothing can be marked paid by hand.")
        if not isinstance(form, OrderActionForm):
            return form
        from .utils import payments
        done, refused = [], []
        for p in queryset.exclude(status__in=("paid", "refunded")):
            try:
                found = payments.gateway_verify_paid(p)
            except Exception:
                found = None
                logging.getLogger(__name__).exception("Gateway check failed for %s", p.ref)
            if found:
                payment_id, amount, currency = found
                payments.mark_paid(p.id, payment_id, amount=amount, currency=currency)
                p.refresh_from_db()
            if found and p.status == "paid":
                self._record(request, p, f"Payment confirmed with {p.gateway} ({p.gateway_payment_id})",
                             form.cleaned_data["reason"])
                done.append(p.ref)
            else:
                refused.append(p.ref)
        if done:
            self.message_user(request, f"Confirmed with the gateway: {', '.join(done)}.")
        if refused:
            self.message_user(request, "The gateway does not show a captured payment of the right amount for: "
                              f"{', '.join(refused)}. Left unchanged.", level=messages.WARNING)

    @admin.action(description="Mark refunded (only after refunding in the gateway)")
    def mark_refunded(self, request, queryset):
        form = self._ask(request, queryset, "mark_refunded", "Record a refund",
                         "This does NOT send any money back. First refund the payment in the Razorpay or PhonePe "
                         "dashboard, then enter its refund id here. Razorpay refunds are checked with Razorpay "
                         "before the order is marked. Downloads stop and saved PDFs are deleted.",
                         need_refund_ref=True)
        if not isinstance(form, OrderActionForm):
            return form
        from .utils import payments, pdf_store
        done, refused = [], []
        for p in queryset.filter(status="paid"):
            if p.gateway == "razorpay":
                try:
                    ok = payments.razorpay_refunded(p.gateway_payment_id)
                except Exception:
                    ok = False
                    logging.getLogger(__name__).exception("Refund check failed for %s", p.ref)
                if not ok:
                    refused.append(p.ref)
                    continue
            Purchase.objects.filter(pk=p.pk).update(status="refunded")
            pdf_store.forget(p)
            self._record(request, p, f"Marked refunded (gateway refund {form.cleaned_data['refund_ref'].strip()})",
                         form.cleaned_data["reason"])
            done.append(p.ref)
        if done:
            self.message_user(request, f"Recorded as refunded: {', '.join(done)}. This site moved no money.")
        if refused:
            self.message_user(request, "Razorpay does not show a full refund yet for: " + ", ".join(refused) +
                              ". Refund it in the Razorpay dashboard first.", level=messages.WARNING)

    @admin.action(description="Rebuild PDF on next download (after fixing a report bug)")
    def rebuild_pdf(self, request, queryset):
        form = self._ask(request, queryset, "rebuild_pdf", "Rebuild saved PDFs",
                         "The saved PDFs of these orders are deleted; the next download builds a fresh copy.")
        if not isinstance(form, OrderActionForm):
            return form
        from .utils import pdf_store
        for p in queryset:
            pdf_store.forget(p)
            self._record(request, p, "Saved PDF deleted for rebuild", form.cleaned_data["reason"])
        self.message_user(request, "Saved PDFs deleted. The next download builds a fresh copy.")
