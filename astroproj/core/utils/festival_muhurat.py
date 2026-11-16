# core/utils/festival_muhurat.py
"""
Puja and activity muhurats for festivals, worked out for the visitor's own city.

The festival *date* comes from the Kashi rules in festival_calculations. On that date this module takes the
festival's tithi, intersects it with the kaal its puja prescribes (computed from local sunrise and sunset), and
removes Bhadra where the shastra requires it:

  Diwali / Dhanteras    Pradosh kaal with the sthira Vrishabha lagna; Mahanishita and Simha lagna for Kali puja
  Raksha Bandhan        Aparahna free of Bhadra, else Pradosh free of Bhadra
  Holika Dahan          Pradosh with Purnima and no Bhadra; Bhadra Puchha only if Bhadra lasts past midnight
  Janmashtami, Shivratri, Kalabhairav   Nishita kaal (the 8th muhurta of the night)
  Ganesh Chaturthi, Rama Navami         Madhyahna
  Navratri Ghatasthapana                First third of the day, or Abhijit muhurta
  Dussehra              Vijay muhurta (11th muhurta of the day) and Aparahna
  Karwa Chauth, Sharad Purnima          Evening puja and local moonrise
Kaal lengths follow festival_calculations (Pradosh = first fifth of the night, and so on).
"""
from datetime import timedelta

import pytz
import swisseph as swe

from . import panchang_engine as pe
from . import panchang_store as ps

SIGN_NAMES = ["Mesha", "Vrishabha", "Mithuna", "Karka", "Simha", "Kanya", "Tula", "Vrishchika", "Dhanu", "Makara",
              "Kumbha", "Meena"]


def T(paksha, n):
    return (n - 1) + (0 if paksha == "S" else 15)


# slug: (tithi, [(label, recipe, best)], note). Recipes are described in _window().
RECIPES = {
    "diwali": (T("K", 15), [
        ("Lakshmi Puja: Pradosh with sthira Vrishabha lagna", "pradosh+lagna:1", True),
        ("Pradosh kaal", "pradosh", False),
        ("Vrishabha lagna (sthira)", "lagna:1", False),
        ("Mahanishita kaal (Kali puja, sadhana)", "nishita", False),
        ("Simha lagna (sthira, night)", "lagna:4", False)],
        "Lakshmi-Ganesh puja is done in Pradosh kaal while Amavasya prevails, best inside the fixed (sthira) Vrishabha "
        "lagna so that Lakshmi stays. Business owners do Chopda puja in the same window."),
    "dhanteras": (T("K", 13), [
        ("Dhanteras puja: Pradosh with Vrishabha lagna", "pradosh+lagna:1", True),
        ("Pradosh kaal: Dhanvantari puja and Yama Deepdaan", "pradosh", False),
        ("Buying gold, silver and utensils (while Trayodashi lasts)", "tithi_day", False)],
        "Light a four-wicked diya facing south for Yama at Pradosh. Purchases are auspicious throughout Trayodashi; "
        "avoid Rahu Kaal."),
    "narak-chaturdashi": (T("K", 14), [("Abhyang snan (before sunrise)", "arunodaya", True)],
                          "Oil bath before sunrise while Chaturdashi prevails; light a Yama diya in the evening."),
    "govardhan-puja": (T("S", 1), [("Pratah kaal muhurat", "pratah", True), ("Sayankal muhurat", "sayahna", False)],
                       "Govardhan and Annakut puja in the morning, or in the evening."),
    "bhai-dooj": (T("S", 2), [("Tilak muhurat (Aparahna)", "aparahna", True)],
                  "Sisters apply tilak in Aparahna while Dwitiya prevails; Chitragupta puja on the same day."),
    "raksha-bandhan": (T("S", 15), [
        ("Rakhi muhurat: Aparahna, free of Bhadra", "aparahna-bhadra", True),
        ("Pradosh, free of Bhadra", "pradosh-bhadra", False),
        ("Rakhi can be tied (Purnima, daytime, no Bhadra)", "tithi_day-bhadra", False)],
        "Rakhi is never tied during Bhadra. When Bhadra covers the afternoon, tie it in Pradosh after Bhadra ends."),
    "holika-dahan": (T("S", 15), [
        ("Holika Dahan: Pradosh, Purnima, no Bhadra", "pradosh-bhadra", True),
        ("After Bhadra ends (before madhya ratri)", "after_bhadra", False),
        ("Bhadra Puchha, approx. last 3 ghati (only if Bhadra lasts past midnight)", "bhadra_puchha", False)],
        "Holika is lit in Pradosh while Purnima prevails and Bhadra does not. If Bhadra runs past midnight, the "
        "dahan is done in Bhadra Puchha (its last 3 ghati), never in Bhadra Mukha."),
    "holi": (None, [("Play colours (Dhulandi), morning", "morning", True)],
             "Holi with colours is played in the morning after Holika Dahan; no puja muhurat is prescribed."),
    "maha-shivaratri": (T("K", 14), [
        ("Nishita kaal puja", "nishita", True),
        ("Ratri prahar 1", "prahar:1", False), ("Ratri prahar 2", "prahar:2", False),
        ("Ratri prahar 3", "prahar:3", False), ("Ratri prahar 4", "prahar:4", False)],
        "Shiva is worshipped in each of the four night prahars; Nishita kaal is the most important."),
    "krishna-janmashtami": (T("K", 8), [("Nishita puja (Krishna's birth)", "nishita", True)],
                            "Puja at Nishita kaal while Ashtami prevails. Parana is next morning after sunrise."),
    "ganesh-chaturthi": (T("S", 4), [("Ganesh sthapana and puja (Madhyahna)", "madhyahna", True)],
                         "Ganapati was born at Madhyahna. Avoid looking at the moon tonight (Mithya Dosha)."),
    "rama-navami": (T("S", 9), [("Rama Navami puja (Madhyahna)", "madhyahna", True)],
                    "Shri Rama was born at the middle of the day; puja is done in Madhyahna."),
    "chaitra-navratri": (T("S", 1), [("Ghatasthapana (first third of the day)", "ghata", True),
                                     ("Ghatasthapana in Abhijit muhurat", "abhijit", False)],
                         "Kalash sthapana in the morning while Pratipada prevails; if missed, use Abhijit muhurat."),
    "sharad-navratri": (T("S", 1), [("Ghatasthapana (first third of the day)", "ghata", True),
                                    ("Ghatasthapana in Abhijit muhurat", "abhijit", False)],
                        "Kalash sthapana in the morning while Pratipada prevails; if missed, use Abhijit muhurat."),
    "vijaya-dashami": (T("S", 10), [("Vijay muhurat", "vijay", True), ("Aparahna puja (Shami, Aparajita)", "aparahna", False)],
                       "Start new work and do Shastra puja in Vijay muhurat; Ravan Dahan is after sunset."),
    "vasant-panchami": (T("S", 5), [("Saraswati puja (Purvahna)", "purvahna", True)],
                        "Saraswati puja in the first half of the day while Panchami prevails; wear yellow."),
    "akshaya-tritiya": (T("S", 3), [("Puja muhurat (Purvahna)", "purvahna", True),
                                    ("Gold buying (while Tritiya lasts)", "tithi_day", False)],
                        "The whole of Akshaya Tritiya is auspicious; puja is done in Purvahna."),
    "karwa-chauth": (T("K", 4), [("Karwa Chauth puja (evening)", "evening75", True)],
                     "Puja after sunset; the fast is broken after sighting the moon (moonrise below)."),
    "sharad-purnima": (T("S", 15), [("Kheer under the moonlight (moonrise to midnight)", "moon_to_midnight", True)],
                       "Keep kheer in the moonlight and take it as prasad the next morning."),
    "dev-deepawali": (T("S", 15), [("Deepdaan (Pradosh)", "pradosh", True)],
                      "Lamps are lit on the ghats in Pradosh kaal."),
    "chhath-puja-sandhya-arghya": (None, [("Sandhya arghya (at sunset)", "sunset_arghya", True)],
                                   "Arghya to the setting Sun from the water."),
    "chhath-usha-arghya": (None, [("Usha arghya (at sunrise)", "sunrise_arghya", True)],
                           "Arghya to the rising Sun, then parana."),
    "hartalika-teej": (T("S", 3), [("Pratah kaal puja", "pratah", True), ("Pradosh puja", "pradosh", False)],
                       "Shiva-Parvati puja in the morning or in Pradosh."),
    "guru-purnima": (T("S", 15), [("Guru puja (morning)", "pratah", True)], "Vyasa puja and guru puja in the morning."),
    "hanuman-jayanti": (T("S", 15), [("Hanuman puja (morning)", "pratah", True)], "Puja and Sundarkand path in the morning."),
    "kalabhairav-jayanti": (T("K", 8), [("Nishita puja", "nishita", True)], "Kalabhairav is worshipped at night."),
}


WHOLE_KAAL = {"nishita", "madhyahna", "vijay", "evening75", "sunset_arghya", "sunrise_arghya", "morning",
              "moon_to_midnight", "prahar:1", "prahar:2", "prahar:3", "prahar:4"}


def _local(dt_utc, tz):
    return pytz.utc.localize(dt_utc).astimezone(tz)


def _naive_utc(dt):
    return dt.astimezone(pytz.utc).replace(tzinfo=None)


def _intersect(a, b):
    out = []
    for x0, x1 in a:
        for y0, y1 in b:
            s, e = max(x0, y0), min(x1, y1)
            if e > s:
                out.append((s, e))
    return out


def _subtract(spans, cuts):
    for c0, c1 in cuts:
        nxt = []
        for s, e in spans:
            if c1 <= s or c0 >= e:
                nxt.append((s, e))
                continue
            if s < c0:
                nxt.append((s, c0))
            if c1 < e:
                nxt.append((c1, e))
        spans = nxt
    return [(s, e) for s, e in spans if (e - s) >= timedelta(minutes=5)]


def _lagna_spans(start, end, lat, lon, sign):
    """When the sidereal ascendant is in ``sign`` between two aware datetimes (2-minute scan, refined to ~10 s)."""
    swe.set_sid_mode(pe.SID_MODE)

    def asc(t):
        cusps, ascmc = swe.houses_ex(pe.dt_to_jd(t), lat, lon, b"P", swe.FLG_SIDEREAL)
        return int(ascmc[0] // 30) == sign

    def edge(a, b, inside_at_a):
        while (b - a) > timedelta(seconds=10):
            m = a + (b - a) / 2
            if asc(m) == inside_at_a:
                a = m
            else:
                b = m
        return b

    spans, t, step = [], start, timedelta(minutes=2)
    inside, opened = asc(t), (start if asc(start) else None)
    while t < end:
        n = min(t + step, end)
        now_in = asc(n)
        if now_in != inside:
            at = edge(t, n, inside)
            if now_in:
                opened = at
            elif opened:
                spans.append((opened, at))
                opened = None
            inside = now_in
        t = n
    if opened:
        spans.append((opened, end))
    return spans


def _day(d, lat, lon, tz):
    sr, ss = pe.sun_times(d, lat, lon, tz)
    nsr, _ = pe.sun_times(d + timedelta(days=1), lat, lon, tz)
    return sr, ss, nsr


def _tithi_span(index, d, sr, nsr, tz):
    """The occurrence of tithi ``index`` that touches the local day [sunrise - 1 day, next sunrise + 1 day]."""
    rows = ps.events_overlapping("tithi", _naive_utc(sr - timedelta(days=1)), _naive_utc(nsr + timedelta(days=1)))
    best = None
    for r in rows:
        if r.number != index:
            continue
        span = (_local(r.start_utc, tz), _local(r.end_utc, tz))
        overlap = min(span[1], nsr) - max(span[0], sr)
        if best is None or overlap > best[0]:
            best = (overlap, span)
    return best[1] if best else None


def _bhadra(start, end, tz):
    rows = ps.events_overlapping("karana", _naive_utc(start), _naive_utc(end))
    return [(_local(r.start_utc, tz), _local(r.end_utc, tz)) for r in rows if r.name == "Vishti"]


def puja_muhurats(slug, d, lat, lon, tz_name):
    """Puja windows for festival ``slug`` on local date ``d`` at this place, or None if there is no recipe."""
    recipe = RECIPES.get(slug)
    if not recipe:
        return None
    from .muhurat import _cached
    return _cached("fest-puja1", lambda: _compute(slug, recipe, d, float(lat), float(lon), tz_name),
                   slug, d, float(lat), float(lon), tz_name)


def _compute(slug, recipe, d, lat, lon, tz_name):
    tithi_index, items, note = recipe
    tz = pytz.timezone(tz_name)
    ps.ensure_years(d.year - 1 if d.month == 1 else d.year, d.year + 1 if d.month == 12 else d.year)
    sr, ss, nsr = _day(d, lat, lon, tz)
    if not (sr and ss and nsr):
        return {"windows": [], "note": note, "moments": [], "tithi": None}
    day, night = ss - sr, nsr - ss
    tithi = _tithi_span(tithi_index, d, sr, nsr, tz) if tithi_index is not None else None
    tithi_spans = [tithi] if tithi else [(sr - timedelta(hours=2), nsr + timedelta(hours=2))]
    bhadra = _bhadra(sr - timedelta(hours=12), nsr + timedelta(hours=12), tz)
    midnight = ss + night / 2      # madhya ratri: the Hindu midnight is the middle of the night, not 00:00
    kaal = {
        "pratah": (sr, sr + day / 5), "purvahna": (sr, sr + day / 2), "ghata": (sr, sr + day / 3),
        "madhyahna": (sr + day * 2 / 5, sr + day * 3 / 5), "aparahna": (sr + day * 3 / 5, sr + day * 4 / 5),
        "sayahna": (ss - day / 5, ss), "pradosh": (ss, ss + night / 5),
        "nishita": (ss + night * 7 / 15, ss + night * 8 / 15),
        "vijay": (sr + day * 10 / 15, sr + day * 11 / 15), "abhijit": (sr + day * 7 / 15, sr + day * 8 / 15),
        "arunodaya": (sr - timedelta(minutes=96), sr), "morning": (sr, sr + day / 2),
        "tithi_day": (sr, nsr), "evening75": (ss, ss + timedelta(minutes=75)),
        "sunset_arghya": (ss - timedelta(minutes=20), ss), "sunrise_arghya": (sr, sr + timedelta(minutes=20)),
    }
    for n in range(1, 5):
        kaal[f"prahar:{n}"] = (ss + night * (n - 1) / 4, ss + night * n / 4)
    moonrise = pe.moonrise_on(d, lat, lon, tz)
    if moonrise:
        kaal["moon_to_midnight"] = (moonrise, max(midnight, moonrise + timedelta(minutes=30)))

    windows = []
    for label, spec, best in items:
        spans = []
        cut_bhadra = spec.endswith("-bhadra")
        spec = spec.replace("-bhadra", "")
        if spec == "after_bhadra":
            night_bhadra = [b for b in bhadra if b[0] < midnight and b[1] > ss]
            if night_bhadra and ss < night_bhadra[-1][1] < midnight:
                end = night_bhadra[-1][1]
                spans = _intersect([(end, min(midnight, end + timedelta(minutes=72)))], tithi_spans)
        elif spec == "bhadra_puchha":
            night_bhadra = [b for b in bhadra if b[0] < nsr and b[1] > midnight]
            if night_bhadra:
                b0, b1 = night_bhadra[0]
                spans = _intersect([(b1 - timedelta(minutes=72), b1)], tithi_spans)
        else:
            parts = spec.split("+")
            # kaal-vyapti pujas use the whole kaal once the festival's tithi touches it (Janmashtami Nishita etc.)
            spans = tithi_spans if not WHOLE_KAAL.intersection(parts) else [kaal[next(iter(WHOLE_KAAL.intersection(parts)))]]
            for part in parts:
                if part.startswith("lagna:"):
                    window = kaal["pradosh"] if "pradosh" in parts else (ss, nsr)
                    spans = _intersect(spans, _lagna_spans(window[0], window[1], lat, lon, int(part.split(":")[1])))
                elif part in kaal:
                    spans = _intersect(spans, [kaal[part]])
        if cut_bhadra:
            spans = _subtract(spans, bhadra)
        spans = [(s, e) for s, e in spans if (e - s) >= timedelta(minutes=5)]
        if spans:
            windows.append({"label": label, "best": best, "spans": [{"start": s, "end": e} for s, e in spans]})

    moments = [("Sunrise", sr), ("Sunset", ss)]
    if slug in ("karwa-chauth", "sharad-purnima", "ganesh-chaturthi") and moonrise:
        moments.append(("Moonrise", moonrise))
    if slug in ("krishna-janmashtami", "maha-shivaratri"):
        moments.append(("Madhya ratri (midnight point)", ss + night / 2))
    if slug == "rama-navami":
        moments.append(("Madhyahna moment", sr + day / 2))
    night_bhadra = [b for b in bhadra if b[0] < nsr and b[1] > sr]
    bhadra_info = [{"start": b0, "end": b1} for b0, b1 in night_bhadra] if slug in ("raksha-bandhan", "holika-dahan") else []
    if windows and not any(w["best"] for w in windows):
        windows[0]["best"] = True
    return {"windows": windows, "note": note, "moments": moments, "bhadra": bhadra_info,
            "tithi": {"start": tithi[0], "end": tithi[1]} if tithi else None}


def best_window(slug, d, lat, lon, tz_name):
    """The first span of the best window, for one-line summaries in lists."""
    res = puja_muhurats(slug, d, lat, lon, tz_name)
    if not res:
        return None
    for w in res["windows"]:
        if w["best"]:
            return {"label": w["label"], **w["spans"][0]}
    return None
