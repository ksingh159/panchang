from django import forms
from django.utils.translation import gettext_lazy as _

from .models import ContactMessage


class ContactForm(forms.ModelForm):
    # Hidden from people by CSS; bots that fill every field give themselves away.
    website = forms.CharField(required=False, label=_("Leave this empty"))

    class Meta:
        model = ContactMessage
        fields = ["kind", "name", "email", "order_ref", "message", "page"]
        labels = {"kind": _("About"), "order_ref": _("Order number (if about a PDF)"), "message": _("Your message")}
        widgets = {"message": forms.Textarea(attrs={"rows": 6, "maxlength": 4000}),
                   "page": forms.HiddenInput()}
