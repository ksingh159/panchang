# core/pdf/calendar_pdf.py
"""
The free printable Hindu calendar: one month on one A4 landscape page (/hindu-calendar/<year>/<month>/pdf/).

    render(year, month, hindi, site_url) -> PDF bytes

Same data as the web page (core/utils/hindu_calendar.py). Devanagari is shaped with HarfBuzz (fpdf2 text shaping),
the same fonts as the paid books (core/pdf/book.py).
"""
import calendar
from pathlib import Path

from django.utils import translation
from fpdf import FPDF

from ..utils import hindu_calendar as hc

VERSION = 1            # bump to rebuild cached PDFs after a layout change
FONT_DIR = Path(__file__).resolve().parent.parent / "data" / "fonts"

INK = (43, 33, 28)
MAROON = (110, 31, 26)
BROWN = (139, 69, 19)
SAFFRON = (204, 102, 26)
GREY = (110, 100, 92)
LINE = (226, 210, 186)
SHUKLA = (255, 253, 247)
KRISHNA = (244, 237, 226)
GREEN = (46, 107, 58)
RED = (192, 57, 43)


class CalendarPDF(FPDF):
    def __init__(self, hindi):
        super().__init__(orientation="L", unit="mm", format="A4")
        self.hindi = hindi
        self.set_auto_page_break(False)
        self.set_margins(10, 10, 10)
        self.add_font("sans", "", str(FONT_DIR / "NotoSans-Regular.ttf"))
        self.add_font("sans", "B", str(FONT_DIR / "NotoSans-Bold.ttf"))
        self.add_font("deva", "", str(FONT_DIR / "NotoSerifDevanagari-Regular.ttf"))
        self.add_font("deva", "B", str(FONT_DIR / "NotoSerifDevanagari-Bold.ttf"))
        self.set_fallback_fonts(["sans"] if hindi else ["deva"])
        self.set_text_shaping(True)

    def font(self, size, style=""):
        self.set_font("deva" if self.hindi else "sans", style, size)

    def fit(self, text, width):
        """Shorten text with an ellipsis until it fits the width."""
        if self.get_string_width(text) <= width:
            return text
        while text and self.get_string_width(text + "…") > width:
            text = text[:-1]
        return text.rstrip(" /,") + "…"

    def text_at(self, x, y, w, text, size, style="", color=INK, align="L"):
        self.font(size, style)
        self.set_text_color(*color)
        self.set_xy(x, y)
        self.cell(w, size * 0.42, self.fit(text, w), align=align)


def _moon(pdf, x, y, kind):
    """Purnima: open circle; Amavasya: filled circle; Ekadashi: small saffron dot."""
    if kind == "purnima":
        pdf.set_draw_color(*BROWN); pdf.set_fill_color(255, 248, 220); pdf.set_line_width(0.35)
        pdf.ellipse(x - 2.2, y, 4.4, 4.4, style="DF")
    elif kind == "amavasya":
        pdf.set_fill_color(*INK)
        pdf.ellipse(x - 2.2, y, 4.4, 4.4, style="F")
    elif kind == "ekadashi":
        pdf.set_fill_color(*SAFFRON)
        pdf.ellipse(x - 1.5, y + 0.7, 3, 3, style="F")


def render(year, month, hindi, site_url=""):
    from ..templatetags.vp import fest, t
    cal = hc.month(year, month)
    lang = "hi" if hindi else "en"
    i = 1 if hindi else 0
    with translation.override(lang):
        pdf = CalendarPDF(hindi)
        pdf.add_page()
        W = pdf.w - 20
        label = f"{hc.MONTHS_HI[month - 1]} {year}" if hindi else f"{calendar.month_name[month]} {year}"
        title = f"हिन्दू कैलेंडर {label}" if hindi else f"Hindu Calendar {label}"
        masas = []
        for purn, _ in cal["masas"]:
            if purn and t(purn) not in masas:
                masas.append(t(purn))

        # header
        pdf.text_at(10, 9, W * 0.62, title, 20, "B", MAROON)
        sep = "  |  "                 # plain ASCII: "·" and "→" are missing from the Devanagari font
        sub = ((("हिन्दू मास (पूर्णिमान्त): " if hindi else "Hindu month (purnimanta): ") + " - ".join(masas) + sep)
               if masas else "")
        sub += ("तिथि और नक्षत्र वाराणसी के सूर्योदय पर" + sep + "त्योहार काशी के नियमों से" if hindi
                else "Tithi and nakshatra at Varanasi sunrise" + sep + "festivals by Kashi rules")
        pdf.text_at(10, 19, W, sub, 9, "", GREY)
        from django.conf import settings
        brand = getattr(settings, "SITE_NAME_HI" if hindi else "SITE_NAME", "")
        pdf.text_at(10 + W * 0.62, 10, W * 0.38, brand, 12, "B", BROWN, align="R")

        # weekday header
        top = 26
        cw = W / 7
        pdf.set_fill_color(*BROWN)
        pdf.rect(10, top, W, 7, style="F")
        for k, wd in enumerate(hc.WEEKDAYS_LONG):
            pdf.text_at(10 + k * cw, top + 1.6, cw, wd[i], 9.5, "B", (255, 255, 255), align="C")
        top += 7

        rows = len(cal["weeks"])
        bottom = pdf.h - 20
        ch = (bottom - top) / rows
        today = None
        for r, week in enumerate(cal["weeks"]):
            for k, x in enumerate(week):
                cx, cy = 10 + k * cw, top + r * ch
                pdf.set_draw_color(*LINE)
                pdf.set_line_width(0.3)
                if not x:
                    pdf.set_fill_color(250, 247, 242)
                    pdf.rect(cx, cy, cw, ch, style="DF")
                    continue
                pdf.set_fill_color(*(KRISHNA if x["paksha"] == "Krishna" else SHUKLA))
                pdf.rect(cx, cy, cw, ch, style="DF")
                pdf.text_at(cx + 1.8, cy + 1.6, 12, str(x["day"]), 15, "B", RED if k == 0 else MAROON)
                kind = "purnima" if x["purnima"] else "amavasya" if x["amavasya"] else "ekadashi" if x["ekadashi"] else ""
                if kind:
                    _moon(pdf, cx + cw - 4, cy + 2, kind)
                inner = cw - 3.6
                tithi = f"{t(x['paksha'])} {t(x['tithi'])}" if x["tithi"] not in ("Purnima", "Amavasya") else t(x["tithi"])
                y = cy + 9.2
                pdf.text_at(cx + 1.8, y, inner, tithi, 8.2, "B", BROWN)
                y += 3.9
                pdf.text_at(cx + 1.8, y, inner, t(x["nakshatra"]), 7.2, "", GREY)
                y += 3.7
                room = int((cy + ch - 1.5 - y) // 3.5)
                shown = x["festivals"][:max(room, 0)]
                for n, f in enumerate(shown):
                    extra = len(x["festivals"]) - len(shown)
                    text = fest(f["name"])
                    if n == len(shown) - 1 and extra > 0:
                        text = pdf.fit(text, inner - 7) + f" +{extra}"
                    pdf.text_at(cx + 1.8, y, inner, text, 7.2, "B" if f["high"] else "", MAROON if f["high"] else GREEN)
                    y += 3.5

        # footer: legend, periods, link
        y = bottom + 2
        x = 12
        for kind, name in (("purnima", "पूर्णिमा" if hindi else "Purnima"), ("amavasya", "अमावस्या" if hindi else "Amavasya"),
                           ("ekadashi", "एकादशी" if hindi else "Ekadashi")):     # the cells' marks, drawn, not glyphs
            _moon(pdf, x + 2.2, y + 0.4, kind)
            pdf.font(8)
            w = pdf.get_string_width(name) + 2
            pdf.text_at(x + 5, y + 0.6, w, name, 8, "", GREY)
            x += w + 9
        for fill, name in ((SHUKLA, "शुक्ल पक्ष" if hindi else "Shukla paksha"),
                           (KRISHNA, "कृष्ण पक्ष" if hindi else "Krishna paksha")):
            pdf.set_fill_color(*fill)
            pdf.set_draw_color(*LINE)
            pdf.rect(x, y + 0.6, 4.4, 4, style="DF")
            pdf.font(8)
            w = pdf.get_string_width(name) + 2
            pdf.text_at(x + 6, y + 0.6, w, name, 8, "", GREY)
            x += w + 10
        if cal["periods"]:
            per = ("अवधि: " if hindi else "Periods: ") + "; ".join(
                f"{fest(p['name'])} {p['start'].day}/{p['start'].month} - {p['end'].day}/{p['end'].month}" for p in cal["periods"])
            pdf.text_at(10 + W * 0.55, y, W * 0.45, per, 8, "", GREY, align="R")
        url = f"{site_url}/{'hi/' if hindi else ''}hindu-calendar/{year}/{hc.MONTH_SLUGS[month - 1]}/"
        foot = (f"मुफ़्त: प्रिंट करें और बाँटें  |  हर दिन का पूरा पंचांग: {url}" if hindi else
                f"Free to print and share  |  every day's full panchang: {url}")
        pdf.text_at(10, y + 6, W, foot, 8, "", BROWN)
        pdf.set_title(title)
        pdf.set_creator(brand)
        return bytes(pdf.output())
