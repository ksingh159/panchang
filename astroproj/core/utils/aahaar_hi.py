# core/utils/aahaar_hi.py
"""Hindi for everything the Aahaar page and PDF show, keyed by the English text in aahaar*.py.

    localize(obj, skip)   a copy of obj (dicts, lists, tuples, strings) with every known English string in Hindi;
                          values under the keys in ``skip`` are left alone (CSS classes, lookup keys, codes)
    hi(text)              one string

The source data stays English; the Hindi tables live in aahaar_hi_core, aahaar_hi_foods and aahaar_hi_regions.
"""
from .aahaar_hi_core import HI as _CORE
from .aahaar_hi_foods import HI as _FOODS
from .aahaar_hi_regions import HI as _REGIONS

HI = {**_REGIONS, **_FOODS, **_CORE}

# Values that drive code or CSS, never shown as prose
SKIP = frozenset({"key", "focus", "dosha_class", "nature", "season", "effect_code", "doshas", "lang", "text", "icon",
                  "kind", "start", "end", "is_day", "n", "width", "calms"})


def hi(text):
    return HI.get(text, text) if isinstance(text, str) else text


def localize(obj, skip=SKIP):
    if isinstance(obj, str):
        return HI.get(obj, obj)
    if isinstance(obj, dict):
        return {k: (v if k in skip else localize(v, skip)) for k, v in obj.items()}
    if isinstance(obj, tuple):
        return tuple(localize(x, skip) for x in obj)
    if isinstance(obj, list):
        return [localize(x, skip) for x in obj]
    return obj


def missing(obj, skip=SKIP, found=None):
    """English strings in obj with no Hindi entry: for tests and for checking new content."""
    import re
    found = set() if found is None else found
    if isinstance(obj, str):
        if obj not in HI and re.search(r"[A-Za-z]{3,}", obj) and not re.fullmatch(r"[a-z_]+", obj):
            found.add(obj)
    elif isinstance(obj, dict):
        for k, v in obj.items():
            if k not in skip:
                missing(v, skip, found)
    elif isinstance(obj, (list, tuple)):
        for x in obj:
            missing(x, skip, found)
    return found
