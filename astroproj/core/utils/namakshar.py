# core/utils/namakshar.py
"""
Namakshar: the first syllable of a name gives a nakshatra pada, and through it the Moon sign.

This is the Avakahada Chakra used for naming a child and for Milan when birth details are not known.
Only the Moon is implied, so Ashtakoot works but Mangal dosha, lagna and dashas cannot be read.

Syllables are held in a simple key: consonant + one of a/i/u/e/o.  Capitals are retroflex (Ta = ट, Da = ड,
Na = ण, Sha = ष, Tha = ठ, Dha = ढ).  Latin spelling cannot show that difference, so Latin names read as
dental (t = त, d = द, n = न), which is the usual sound in names.
"""
from .constants import NAKSHATRA_NAMES, ZODIAC_SIGNS

CHAKRA = [
    ("chu", "che", "cho", "la"), ("li", "lu", "le", "lo"), ("a", "i", "u", "e"), ("o", "va", "vi", "vu"),
    ("ve", "vo", "ka", "ki"), ("ku", "gha", "nga", "chha"), ("ke", "ko", "ha", "hi"), ("hu", "he", "ho", "Da"),
    ("Di", "Du", "De", "Do"), ("ma", "mi", "mu", "me"), ("mo", "Ta", "Ti", "Tu"), ("Te", "To", "pa", "pi"),
    ("pu", "Sha", "Na", "Tha"), ("pe", "po", "ra", "ri"), ("ru", "re", "ro", "ta"), ("ti", "tu", "te", "to"),
    ("na", "ni", "nu", "ne"), ("no", "ya", "yi", "yu"), ("ye", "yo", "bha", "bhi"), ("bhu", "dha", "pha", "Dha"),
    ("bhe", "bho", "ja", "ji"), ("khi", "khu", "khe", "kho"), ("ga", "gi", "gu", "ge"), ("go", "sa", "si", "su"),
    ("se", "so", "da", "di"), ("du", "tha", "jha", "nya"), ("de", "do", "cha", "chi"),
]
LOOKUP = {syl: (nak, pada) for nak, row in enumerate(CHAKRA) for pada, syl in enumerate(row, 1)}
# Sounds the chakra does not list on their own
ALIAS = {"ba": "va", "bi": "vi", "bu": "vu", "be": "ve", "bo": "vo", "wa": "va", "wi": "vi", "wu": "vu", "we": "ve", "wo": "vo",
         "ju": "khi", "je": "khu", "jo": "khe", "kha": "kho", "fa": "pha", "shu": "su", "zhu": "su"}

DEVANAGARI = {"क": "k", "ख": "kh", "ग": "g", "घ": "gh", "ङ": "ng", "च": "ch", "छ": "chh", "ज": "j", "झ": "jh", "ञ": "ny",
              "ट": "T", "ठ": "Th", "ड": "D", "ढ": "Dh", "ण": "N", "त": "t", "थ": "th", "द": "d", "ध": "dh", "न": "n",
              "प": "p", "फ": "ph", "ब": "b", "भ": "bh", "म": "m", "य": "y", "र": "r", "ल": "l", "व": "v", "श": "s", "ष": "Sh",
              "स": "s", "ह": "h"}
INITIAL_VOWEL = {"अ": "a", "आ": "a", "इ": "i", "ई": "i", "उ": "u", "ऊ": "u", "ऋ": "i", "ए": "e", "ऐ": "e", "ओ": "o", "औ": "o"}
MATRA = {"ा": "a", "ि": "i", "ी": "i", "ु": "u", "ू": "u", "ृ": "i", "े": "e", "ै": "e", "ो": "o", "ौ": "o"}
VIRAMA = "्"
LATIN_HEADS = ("chh", "ch", "kh", "gh", "jh", "th", "dh", "ph", "bh", "sh", "ng", "ny")
LATIN_SOUND = {"sh": "s", "c": "k", "q": "k", "x": "k", "f": "ph", "z": "j", "w": "v"}
CONSONANTS = set("bcdfghjklmnpqrstvwxyz")


def _vowel(text):
    """First vowel sound of a Latin spelling, folded to a/i/u/e/o."""
    for pair, v in (("aa", "a"), ("ai", "e"), ("au", "o"), ("ee", "i"), ("ea", "i"), ("oo", "u"), ("ou", "u")):
        if text.startswith(pair):
            return v
    return text[:1] if text[:1] in "aiueo" else ("i" if text[:1] == "y" else "a")


def syllable_of(name):
    """Key for the first syllable of a Devanagari or Latin name, or None."""
    text = (name or "").strip()
    for title in ("shri ", "shree ", "sri ", "smt ", "mr ", "ms ", "mrs ", "dr "):
        if text.lower().startswith(title):
            text = text[len(title):].strip()
    if not text:
        return None
    first = text[0]
    if first in INITIAL_VOWEL:
        return INITIAL_VOWEL[first]
    if first in DEVANAGARI:
        head = DEVANAGARI[first]
        i = 1
        while i + 1 < len(text) and text[i] == VIRAMA and text[i + 1] in DEVANAGARI:   # conjunct: प्र, श्री
            i += 2
        return head + MATRA.get(text[i] if i < len(text) else "", "a")
    low = text.lower()
    if not low[0].isascii() or not low[0].isalpha():
        return None
    if low[0] in "aeiou":
        return "o" if low[:2] in ("oo", "au") or low[0] == "o" else _vowel(low)
    head = next((h for h in LATIN_HEADS if low.startswith(h)), low[0])
    rest = low[len(head):]
    while rest and rest[0] in CONSONANTS and rest[0] != "y":      # Krishna, Priya, Shravan: skip the cluster
        rest = rest[1:]
    if rest.startswith("y"):                                      # Pyari, Shyam
        rest = rest[1:]
    return LATIN_SOUND.get(head, head) + _vowel(rest)


def _pada_of(key):
    key = ALIAS.get(key, key)
    if key in LOOKUP:
        return LOOKUP[key]
    head = key[:-1]
    for vowel in "aiueo":
        if head + vowel in LOOKUP:
            return LOOKUP[head + vowel]
    return None


def from_name(name):
    """{'syllable', 'nakshatra', 'pada', 'rashi', 'moon_longitude'} for a name, or None if it cannot be read."""
    key = syllable_of(name)
    hit = _pada_of(key) if key else None
    return _result(hit[0], hit[1], key) if hit else None


def from_nakshatra(nakshatra, pada=None):
    """Same result when the family knows the janma nakshatra."""
    return _result(NAKSHATRA_NAMES.index(nakshatra), int(pada or 1), None)


def _result(nak, pada, key):
    lon = nak * 360 / 27 + (pada - .5) * 360 / 108
    return {"syllable": key, "nakshatra": NAKSHATRA_NAMES[nak], "pada": pada, "rashi": ZODIAC_SIGNS[int(lon // 30)],
            "moon_longitude": lon}


LIMITS = ["Only the Moon can be known from a name, so this is a Moon-to-Moon match of the eight kootas.",
          "Mangal dosha, lagna, navamsha, dashas and the other planets cannot be checked.",
          "A name gives one of the four padas of a nakshatra, and spellings differ, so the score is indicative."]
