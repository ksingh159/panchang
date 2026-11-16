"""Template helpers for the Hindi site.

    {% load vp %}
    {{ tithi|t }}            panchang words (tithi, nakshatra, month, weekday, ritu, planets, signs) in Hindi on /hi/
    {{ pair|pick }}          an ("English", "Hindi") pair -> the one for the current language
    {% if hindi %}           hindi is True on /hi/ pages (from the context processor)
"""
from django import template
from django.utils.translation import get_language

from ..pdf import i18n

register = template.Library()

# Spellings the calculators use that the PDF tables do not cover
EXTRA_HI = {
    "Mesh": "मेष", "Mesha": "मेष", "Vrishabh": "वृषभ", "Vrishabha": "वृषभ", "Mithun": "मिथुन", "Mithuna": "मिथुन",
    "Kark": "कर्क", "Karka": "कर्क", "Simha": "सिंह", "Kanya": "कन्या", "Tula": "तुला", "Vrishchik": "वृश्चिक",
    "Vrishchika": "वृश्चिक", "Dhanu": "धनु", "Makar": "मकर", "Makara": "मकर", "Kumbh": "कुम्भ", "Kumbha": "कुम्भ",
    "Meen": "मीन", "Meena": "मीन",
    "North": "उत्तर", "South": "दक्षिण", "East": "पूर्व", "West": "पश्चिम", "Northeast": "ईशान (उत्तर-पूर्व)",
    "Northwest": "वायव्य (उत्तर-पश्चिम)", "Southeast": "आग्नेय (दक्षिण-पूर्व)", "Southwest": "नैऋत्य (दक्षिण-पश्चिम)",
    "Surya": "सूर्य", "Chandra": "चन्द्र", "Mangal": "मंगल", "Budh": "बुध", "Guru": "गुरु", "Shukra": "शुक्र",
    "Shani": "शनि", "Shoola": "शूल", "Variyana": "वरीयान",
    "January": "जनवरी", "February": "फ़रवरी", "March": "मार्च", "April": "अप्रैल", "May": "मई", "June": "जून",
    "July": "जुलाई", "August": "अगस्त", "September": "सितम्बर", "October": "अक्टूबर", "November": "नवम्बर",
    "December": "दिसम्बर",
}


def _lang():
    return "hi" if (get_language() or "").startswith("hi") else "en"


@register.filter
def t(value):
    """Panchang terms, planet, sign and nakshatra names in the current language."""
    if _lang() != "hi" or value in (None, ""):
        return value
    text = str(value)
    if text in EXTRA_HI:
        return EXTRA_HI[text]
    if "," in text:                     # lists such as "North, West"
        return ", ".join(t(x.strip()) for x in text.split(","))
    for en, (_, hi) in i18n.PLANETS.items():
        if text == en:
            return hi
    for en, hi in i18n.SIGNS:
        if text == en:
            return hi
    nak = i18n.nakshatra(text, "hi")
    if nak != text:
        return nak
    return i18n.terms(text, "hi")


@register.filter
def fest(value):
    """A festival name or category in the current language."""
    if _lang() != "hi" or not value:
        return value
    from ..utils.festival_names_hi import hindi_name
    return hindi_name(str(value))


@register.filter
def fnote(value):
    """A festival note or puja-muhurat label in the current language."""
    if _lang() != "hi" or not value:
        return value
    from ..utils.festival_text_hi import note_hi
    return note_hi(str(value))


@register.filter
def frule(value):
    """A festival's date rule ("Kartika Shukla 6 - sunset vyapini") in the current language."""
    if _lang() != "hi" or not value:
        return value
    from ..utils.festival_text_hi import rule_hi
    return rule_hi(str(value))


@register.filter
def pick(pair):
    """("English", "Hindi") -> the current language's text."""
    if isinstance(pair, (list, tuple)) and len(pair) >= 2:
        return pair[1] if _lang() == "hi" and pair[1] else pair[0]
    return pair
