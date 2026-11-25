# core/utils/rashifal_llm.py
"""
Optional wording polish for the daily rashifal: an LLM may make the template sentences read more naturally,
but it never decides anything. Ratings, levels, houses, colours, numbers and times stay as the engine set them
and are not even sent for rewriting; only the four area sentences and the headline are.

Turned on by an API key in the environment; with no key (or on any error) the template wording is used.
    GEMINI_API_KEY   Google AI Studio (first choice: best Hindi)       GEMINI_MODEL  default gemini-2.5-flash
    GROQ_API_KEY     Groq Cloud (fallback)                             GROQ_MODEL    default llama-3.3-70b-versatile

One request per rashi per day (both languages in one JSON answer): 12 requests a day.
Every answer is checked (polish_ok) before it is used: same keys, Hindi in Devanagari, no new digits, no
frightening words, sensible length. A failed check keeps the template text for that rashi.
"""
import json
import logging
import os
import re
import urllib.request

logger = logging.getLogger(__name__)

SLOTS = ("headline", "career", "money", "family", "health")
FORBIDDEN = re.compile(r"\b(death|die|dying|accident|disaster|curse|doom|guarantee[ds]?|certainly|definitely)\b|"
                       r"मृत्यु|मौत|दुर्घटना|अनर्थ|श्राप|विनाश|निश्चित रूप से|गारंटी", re.I)
DEVANAGARI = re.compile(r"[ऀ-ॿ]")
LATIN_WORD = re.compile(r"[A-Za-z]{4,}")

PROMPT = """You polish a daily Vedic rashifal for {name} rashi. Rewrite each sentence so it reads naturally and warmly,
like a thoughtful family astrologer. Rules:
- Keep exactly the same meaning and the same level of positivity or caution. Do not add predictions, events,
  numbers, dates, times, colours, planets or remedies that are not in the input.
- Reassure, never frighten. Use "may", "likely", "a good day to". No absolute claims.
- One or two short sentences per item, at most {max_words} words each.
- English stays in simple Indian English. Hindi stays in simple, natural Hindi in Devanagari (no English words).
Return only JSON with the same keys: {{"en": {{...}}, "hi": {{...}}}}.

Input:
{payload}
"""


def _post(url, body, headers):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json", **headers})
    with urllib.request.urlopen(req, timeout=30) as res:
        return json.loads(res.read().decode())


def _gemini(prompt):
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        return None
    model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
    out = _post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                {"contents": [{"parts": [{"text": prompt}]}],
                 "generationConfig": {"temperature": 0.4, "responseMimeType": "application/json"}},
                {"x-goog-api-key": key})
    return out["candidates"][0]["content"]["parts"][0]["text"]


def _groq(prompt):
    key = os.environ.get("GROQ_API_KEY")
    if not key:
        return None
    model = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
    out = _post("https://api.groq.com/openai/v1/chat/completions",
                {"model": model, "temperature": 0.4, "response_format": {"type": "json_object"},
                 "messages": [{"role": "user", "content": prompt}]},
                {"Authorization": f"Bearer {key}"})
    return out["choices"][0]["message"]["content"]


def enabled():
    return bool(os.environ.get("GEMINI_API_KEY") or os.environ.get("GROQ_API_KEY"))


def _source(r):
    return {lang: {"headline": r["headline"][i], **{a: r["areas"][a]["text"][i] for a in SLOTS[1:]}}
            for i, lang in enumerate(("en", "hi"))}


def polish_ok(src, new):
    """True if `new` is a faithful rewrite of `src` (see module docstring)."""
    try:
        for lang in ("en", "hi"):
            if set(new[lang]) != set(src[lang]):
                return False
            for k, text in new[lang].items():
                if not isinstance(text, str) or not text.strip():
                    return False
                old = src[lang][k]
                if len(text) > 2 * len(old) + 80 or len(text) < 0.4 * len(old):
                    return False
                if set(re.findall(r"\d", text)) - set(re.findall(r"\d", old)):
                    return False
                if FORBIDDEN.search(text):
                    return False
                if lang == "hi" and (not DEVANAGARI.search(text) or LATIN_WORD.search(text)):
                    return False
                if lang == "en" and DEVANAGARI.search(text):
                    return False
        return True
    except (KeyError, TypeError, AttributeError):
        return False


def polish(r):
    """Polished {"en": {...}, "hi": {...}} for one reading, or None (no key, error or failed check)."""
    src = _source(r)
    prompt = PROMPT.format(name=r["name"][0], max_words=30, payload=json.dumps(src, ensure_ascii=False, indent=1))
    for call in (_gemini, _groq):
        try:
            text = call(prompt)
        except Exception as e:
            logger.warning("Rashifal polish via %s failed: %s", call.__name__, e)
            continue
        if not text:
            continue
        try:
            new = json.loads(re.sub(r"^```(?:json)?|```$", "", text.strip()).strip())
        except ValueError:
            continue
        if polish_ok(src, new):
            return new
        logger.warning("Rashifal polish for %s rejected by checks", r["slug"])
    return None


def polish_day(data):
    """Put polished wording on each reading as r["polished"] (template text stays in place as the fallback)."""
    if not enabled():
        return
    for r in data["readings"]:
        p = polish(r)
        if p:
            r["polished"] = p
