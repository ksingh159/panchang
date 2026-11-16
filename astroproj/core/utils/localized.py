# core/utils/localized.py
"""Long pages (terms, privacy, policies, about) are written separately per language rather than string by string.

    render(request, localized("static_pages/terms.html"), ctx)

gives static_pages/hi/terms.html on the Hindi site when that file exists, else the English template.
"""
from django.template import TemplateDoesNotExist
from django.template.loader import get_template
from django.utils.translation import get_language


def localized(name):
    lang = (get_language() or "en").split("-")[0]
    if lang == "en":
        return name
    folder, _, file = name.rpartition("/")
    candidate = f"{folder}/{lang}/{file}" if folder else f"{lang}/{file}"
    try:
        get_template(candidate)
    except TemplateDoesNotExist:
        return name
    return candidate
