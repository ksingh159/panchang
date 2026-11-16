# core/pdf/book.py
"""
A small book-style page engine on top of fpdf2.

  * Embedded Noto Serif + Noto Serif Devanagari with HarfBuzz shaping, so Hindi conjuncts print correctly
  * Cover, contents with dot leaders and PDF bookmarks, chapter openers, running header and folio
  * A personal watermark (buyer name, email, order number) on every page, under the text
  * protect(): AES-256 encryption with an owner password; printing allowed, copying and editing not
"""
import hashlib
import io
from pathlib import Path

from django.conf import settings
from fpdf import FPDF
from fpdf.enums import TableCellFillMode, XPos, YPos
from fpdf.fonts import FontFace

from . import i18n

FONT_DIR = Path(__file__).resolve().parent.parent / "data" / "fonts"
PLANET_IMG = Path(settings.BASE_DIR) / "static" / "planets"

# Palette: deep maroon and saffron on warm paper
INK = (43, 33, 28)
MAROON = (110, 31, 26)
SAFFRON = (204, 102, 26)
GOLD = (184, 141, 46)
PAPER = (253, 248, 238)
PAGE_TINT = (255, 252, 246)
SOFT = (246, 236, 218)
RULE = (224, 207, 180)
MUTED = (125, 108, 90)
GREEN = (46, 125, 80)
RED = (170, 52, 40)

PLANET_COLORS = {
    "Sun": (211, 84, 0), "Moon": (93, 109, 126), "Mars": (192, 57, 43), "Mercury": (30, 132, 73),
    "Jupiter": (183, 149, 11), "Venus": (194, 24, 91), "Saturn": (31, 58, 147), "Rahu": (74, 35, 90),
    "Ketu": (110, 44, 0), "Ascendant": MAROON,
}
PLANET_IMAGES = {"Sun": "sun", "Moon": "moon", "Mars": "mars", "Mercury": "mercury", "Jupiter": "jupiter",
                 "Venus": "venus", "Saturn": "saturn", "Rahu": "rahu", "Ketu": "ketu", "Ascendant": "asc"}
# soft fills by the sign's element: fire, earth, air, water
ELEMENT_FILL = [(253, 230, 208), (231, 243, 222), (228, 238, 250), (226, 242, 244)]


def planet_image(name):
    path = PLANET_IMG / f"{PLANET_IMAGES.get(name, 'asc')}.webp"
    return str(path) if path.exists() else None


class Book(FPDF):
    def __init__(self, *, lang, title, running_title, licensee, email, order_ref, printed_on):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.lang = lang if lang in i18n.LANGS else "en"
        self.book_title = title
        self.running_title = running_title
        self.licensee, self.email, self.order_ref, self.printed_on = licensee, email, order_ref, printed_on
        self.chapter_name = ""
        self.set_margins(20, 24, 20)
        self.set_auto_page_break(True, margin=26)
        self.add_font("serif", "", str(FONT_DIR / "NotoSerif-Regular.ttf"))
        self.add_font("serif", "B", str(FONT_DIR / "NotoSerif-Bold.ttf"))
        self.add_font("serif", "I", str(FONT_DIR / "NotoSerif-Italic.ttf"))
        self.add_font("deva", "", str(FONT_DIR / "NotoSerifDevanagari-Regular.ttf"))
        self.add_font("deva", "B", str(FONT_DIR / "NotoSerifDevanagari-Bold.ttf"))
        self.add_font("deva", "I", str(FONT_DIR / "NotoSerifDevanagari-Regular.ttf"))
        self.add_font("sans", "", str(FONT_DIR / "NotoSans-Regular.ttf"))
        self.add_font("sans", "B", str(FONT_DIR / "NotoSans-Bold.ttf"))
        self.add_font("symbols", "", str(FONT_DIR / "NotoSansSymbols-Regular.ttf"))
        scripts = {"guru": "Gurmukhi", "gujr": "Gujarati", "beng": "Bengali", "taml": "Tamil", "telu": "Telugu",
                   "knda": "Kannada", "mlym": "Malayalam"}
        for family, script in scripts.items():   # for regional sayings in their own script
            self.add_font(family, "", str(FONT_DIR / f"NotoSans{script}-Regular.ttf"))
        self.set_fallback_fonts(["deva", "symbols", *scripts], exact_match=False)
        self.set_text_shaping(True)
        self.set_title(title)
        self.set_author(i18n.w("site", "en"))
        self.set_subject(f"{i18n.w('licensed_to', 'en')} {licensee} <{email}> - {i18n.w('order', 'en')} {order_ref}")
        self.set_keywords(f"order:{order_ref}")
        self.set_creator(i18n.w("site", "en"))
        self.set_text_color(*INK)

    # -- helpers -----------------------------------------------------------------
    def t(self, key):
        return i18n.w(key, self.lang)

    @property
    def body_w(self):
        return self.w - self.l_margin - self.r_margin

    def font(self, size, style="", family="serif"):
        self.set_font(family, style, size)

    # -- page furniture ------------------------------------------------------------
    def watermark(self):
        text = f"{self.licensee}  ·  {self.order_ref}"
        with self.local_context(fill_opacity=0.07, text_color=SAFFRON):
            self.set_font("sans", "B", 22)
            for cy in (75, 150, 225):
                with self.rotation(32, self.w / 2, cy):
                    self.set_xy(0, cy - 6)
                    self.cell(self.w, 12, text, align="C")

    def frame(self):
        """The page wrapper: warm paper, a double gold rule and corner ornaments around the text block."""
        self.set_fill_color(*PAGE_TINT)
        self.rect(0, 0, self.w, self.h, style="F")
        self.set_draw_color(*GOLD)
        self.set_line_width(0.6)
        self.rect(8, 6, self.w - 16, self.h - 12)
        self.set_line_width(0.2)
        self.rect(9.6, 7.6, self.w - 19.2, self.h - 15.2)
        self.set_fill_color(*SAFFRON)
        for cx, cy in ((8, 6), (self.w - 8, 6), (8, self.h - 6), (self.w - 8, self.h - 6)):
            self.polygon([(cx, cy - 2), (cx + 2, cy), (cx, cy + 2), (cx - 2, cy)], style="F")
        # small lotus-diamond in the middle of the top and bottom rule
        for cy in (6, self.h - 6):
            self.set_fill_color(*PAGE_TINT)
            self.rect(self.w / 2 - 6, cy - 1.5, 12, 3, style="F")
            self.set_fill_color(*SAFFRON)
            self.polygon([(self.w / 2, cy - 1.6), (self.w / 2 + 1.6, cy), (self.w / 2, cy + 1.6),
                          (self.w / 2 - 1.6, cy)], style="F")
            self.set_fill_color(*GOLD)
            self.circle(self.w / 2 - 4, cy, 0.6, style="F")
            self.circle(self.w / 2 + 4, cy, 0.6, style="F")

    def header(self):
        if self.page_no() == 1:
            self.watermark()
            return
        self.frame()
        self.watermark()
        self.set_y(10)
        self.font(8)
        self.set_text_color(*MUTED)
        self.cell(self.body_w / 2, 5, self.running_title.upper() if self.lang == "en" else self.running_title)
        self.cell(self.body_w / 2, 5, self.chapter_name, align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_draw_color(*GOLD)
        self.set_line_width(0.4)
        self.line(self.l_margin, 16, self.w - self.r_margin, 16)
        self.set_line_width(0.15)
        self.line(self.l_margin, 16.9, self.w - self.r_margin, 16.9)
        self.set_text_color(*INK)
        self.set_y(self.t_margin)

    def footer(self):
        if self.page_no() == 1:
            return
        self.set_y(-21)
        self.set_draw_color(*RULE)
        self.set_line_width(0.2)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(1.5)
        self.font(7)
        self.set_text_color(*MUTED)
        third = self.body_w / 3
        self.cell(third, 4, f"{self.t('printed_on')} {self.printed_on}")
        self.cell(third, 4, f"{self.t('licensed_to')} {self.licensee}", align="C")
        self.cell(third, 4, f"{self.t('page')} {self.page_no()} / {{nb}}", align="R",
                  new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.mixed_cell(self.body_w, 3.6,
                        f"{self.email}  ·  {self.t('order')} {self.order_ref}  ·  {self.t('personal_copy')}", 7)
        self.set_text_color(*INK)

    def mixed_cell(self, width, height, text, size, style="", align="C"):
        """
        One line of mixed Latin and Devanagari drawn run by run with the matching font. fpdf2's font fallback
        can mis-size a Latin run that comes before Devanagari in a single cell, so lines like that use this.
        """
        runs = []
        for ch in text:
            deva = "ऀ" <= ch <= "ॿ" or ch in "‌‍"
            if ch == " " and runs:
                deva = runs[-1][0]
            if runs and runs[-1][0] == deva:
                runs[-1][1] += ch
            else:
                runs.append([deva, ch])
        widths = []
        for deva, chunk in runs:
            self.set_font("deva" if deva else "serif", style, size)
            widths.append(self.get_string_width(chunk))
        x = self.get_x()
        if align == "C":
            x += (width - sum(widths)) / 2
        elif align == "R":
            x += width - sum(widths)
        y = self.get_y()
        for (deva, chunk), cw in zip(runs, widths):
            self.set_font("deva" if deva else "serif", style, size)
            self.set_xy(x, y)
            self.cell(cw, height, chunk)
            x += cw
        self.set_font("serif", style, size)

    # -- cover and contents -------------------------------------------------------
    def cover(self, title, subtitle, name, lines, images=()):
        self.add_page()
        self.set_fill_color(*PAPER)
        self.rect(0, 0, self.w, self.h, style="F")
        self.set_draw_color(*GOLD)
        self.set_line_width(1.2)
        self.rect(10, 10, self.w - 20, self.h - 20)
        self.set_line_width(0.3)
        self.rect(13, 13, self.w - 26, self.h - 26)
        for cx, cy in ((13, 13), (self.w - 13, 13), (13, self.h - 13), (self.w - 13, self.h - 13)):
            self.set_fill_color(*SAFFRON)
            self.circle(cx, cy, 1.6, style="F")
        # planet medallions across the top
        imgs = [i for i in (planet_image(n) for n in images) if i]
        if imgs:
            size = 15
            gap = 4
            total = len(imgs) * size + (len(imgs) - 1) * gap
            x = (self.w - total) / 2
            for path in imgs:
                self.image(path, x=x, y=34, w=size, h=size)
                x += size + gap
        self.set_y(64)
        self.font(11)
        self.set_text_color(*SAFFRON)
        self.cell(0, 6, "॥ श्री गणेशाय नमः ॥", align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(10)
        self.font(34, "B")
        self.set_text_color(*MAROON)
        self.multi_cell(0, 15, title, align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.font(13, "I")
        self.set_text_color(*MUTED)
        self.multi_cell(0, 7, subtitle, align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(6)
        self.ornament(self.w / 2, self.get_y() + 2)
        self.ln(14)
        self.font(10)
        self.set_text_color(*MUTED)
        self.cell(0, 6, self.t("prepared_for"), align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.font(22, "B")
        self.set_text_color(*INK)
        self.multi_cell(0, 11, name, align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(4)
        self.font(11)
        for line in lines:
            self.multi_cell(0, 6.5, line, align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_y(-52)
        self.ornament(self.w / 2, self.get_y())
        self.ln(6)
        self.font(9)
        self.set_text_color(*MUTED)
        self.cell(0, 5, f"{self.t('printed_on')} {self.printed_on}  ·  {self.t('order')} {self.order_ref}",
                  align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.cell(0, 5, f"{self.t('licensed_to')} {self.licensee} ({self.email})", align="C",
                  new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.font(12, "B")
        self.set_text_color(*MAROON)
        self.cell(0, 8, self.t("site"), align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.font(9, "I")
        self.set_text_color(*GOLD)
        self.cell(0, 5, self.t("tagline"), align="C")
        self.set_text_color(*INK)

    def ornament(self, cx, cy, width=50):
        self.set_draw_color(*GOLD)
        self.set_line_width(0.3)
        if width:
            self.line(cx - width / 2, cy, cx - 4, cy)
            self.line(cx + 4, cy, cx + width / 2, cy)
        else:   # a diamond sitting on an existing rule: clear the rule behind it
            self.set_fill_color(*PAGE_TINT)
            self.rect(cx - 5, cy - 1, 10, 2, style="F")
        self.set_fill_color(*SAFFRON)
        self.polygon([(cx, cy - 2.4), (cx + 2.4, cy), (cx, cy + 2.4), (cx - 2.4, cy)], style="F")

    def colophon(self):
        """The closing block of a book: ornament, benediction and the publisher line."""
        self.need(42)
        self.ln(8)
        self.ornament(self.w / 2, self.get_y())
        self.ln(6)
        self.font(13, "B")
        self.set_text_color(*SAFFRON)
        self.cell(0, 8, "॥ इति शुभम् ॥", align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.font(9, "I")
        self.set_text_color(*MUTED)
        self.cell(0, 5, self.t("colophon"), align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.font(10, "B")
        self.set_text_color(*MAROON)
        self.cell(0, 6, self.t("site"), align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.font(8.5, "I")
        self.set_text_color(*MUTED)
        self.cell(0, 5, self.t("tagline"), align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_text_color(*INK)

    def contents_page(self):
        def render(pdf, outline):
            pdf.set_xy(pdf.l_margin, pdf.t_margin + 4)
            pdf.font(24, "B")
            pdf.set_text_color(*MAROON)
            pdf.cell(0, 14, pdf.t("contents"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.ornament(pdf.l_margin + 25, pdf.get_y() + 1)
            pdf.ln(10)
            for n, section in enumerate([s for s in outline if s.level == 0], 1):
                pdf.font(12)
                pdf.set_text_color(*SAFFRON)
                pdf.cell(12, 9, f"{n:02d}")
                pdf.set_text_color(*INK)
                name = section.name
                page = str(section.page_number)
                name_w = pdf.get_string_width(name)
                page_w = pdf.get_string_width(page)
                pdf.cell(name_w + 2, 9, name)
                dots_w = pdf.body_w - 12 - name_w - 2 - page_w - 2
                pdf.set_text_color(*RULE)
                dot = " ."
                pdf.cell(dots_w, 9, dot * max(0, int(dots_w / pdf.get_string_width(dot))), align="R")
                pdf.set_text_color(*INK)
                pdf.cell(page_w + 2, 9, page, align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.chapter_name = self.t("contents")
        self.add_page()
        # the placeholder keeps this page and moves on to a fresh one, so the next chapter must not add another
        self.chapter_name = ""   # the next page's header is drawn during the placeholder's page break
        self.insert_toc_placeholder(render, pages=1)
        self._page_ready = True

    def chapter(self, number, title, intro="", min_space=95):
        """A chapter opener. It continues on the current page when at least ``min_space`` mm are left, so short
        chapters do not leave half-empty pages behind them."""
        if getattr(self, "_page_ready", False):
            self._page_ready = False
            self.chapter_name = title
        elif self.page_no() <= 1 or self.get_y() + min_space > self.h - self.b_margin:
            self.chapter_name = title
            self.add_page()
        else:
            self.chapter_name = title   # the running header switches from the next page on
            self.ln(5)
            y = self.get_y()
            self.set_draw_color(*GOLD)
            self.set_line_width(0.3)
            self.line(self.l_margin, y, self.w - self.r_margin, y)
            self.ornament(self.w / 2, y, width=0)
            self.ln(7)
        self.start_section(title, level=0)
        self.font(10, "B")
        self.set_text_color(*SAFFRON)
        self.cell(0, 6, f"{number:02d}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.font(22, "B")
        self.set_text_color(*MAROON)
        self.multi_cell(0, 11, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_draw_color(*SAFFRON)
        self.set_line_width(0.8)
        self.line(self.l_margin, self.get_y() + 1, self.l_margin + 22, self.get_y() + 1)
        self.ln(6)
        if intro:
            self.font(10.5, "I")
            self.set_text_color(*MUTED)
            self.multi_cell(0, 5.6, intro, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            self.ln(3)
        self.set_text_color(*INK)

    # -- text blocks -----------------------------------------------------------------
    def need(self, height):
        """Start a new page unless ``height`` mm still fit."""
        if self.get_y() + height > self.h - self.b_margin:
            self.add_page()

    def h2(self, text, color=MAROON):
        self.need(34)
        self.ln(3)
        self.font(14, "B")
        self.set_text_color(*color)
        self.multi_cell(0, 7.5, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_draw_color(*RULE)
        self.set_line_width(0.2)
        self.line(self.l_margin, self.get_y() + 0.5, self.w - self.r_margin, self.get_y() + 0.5)
        self.ln(3)
        self.set_text_color(*INK)

    def h3(self, text, color=SAFFRON):
        self.need(26)   # never leave a heading alone at the foot of a page
        self.ln(1.5)
        self.font(11, "B")
        self.set_text_color(*color)
        self.multi_cell(0, 6, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_text_color(*INK)

    def para(self, text, size=10, style="", color=INK, align="J"):
        self.font(size, style)
        self.set_text_color(*color)
        self.multi_cell(0, size * 0.56, text, align=align, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(1.5)
        self.set_text_color(*INK)

    def bullets(self, items, size=10, color=SAFFRON, indent=4):
        self.font(size)
        for item in items:
            lines = self.multi_cell(self.body_w - indent - 1, size * 0.53, item, dry_run=True, output="LINES")
            self.need(len(lines) * size * 0.53 + 1)
            y = self.get_y()
            self.set_fill_color(*color)
            self.circle(self.l_margin + indent - 2, y + size * 0.28, 0.8, style="F")
            self.set_x(self.l_margin + indent + 1)
            self.multi_cell(self.body_w - indent - 1, size * 0.53, item, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            self.ln(0.8)
        self.ln(1)

    def callout(self, title, text, color=SAFFRON, fill=SOFT):
        self.font(10)
        lines = self.multi_cell(self.body_w - 10, 5.2, text, dry_run=True, output="LINES")
        height = 6 + (7 if title else 0) + len(lines) * 5.2
        self.need(height + 4)
        y = self.get_y()
        self.set_fill_color(*fill)
        self.rect(self.l_margin, y, self.body_w, height, style="F", round_corners=True, corner_radius=2)
        self.set_fill_color(*color)
        self.rect(self.l_margin, y, 1.6, height, style="F")
        self.set_xy(self.l_margin + 5, y + 3)
        if title:
            self.font(10.5, "B")
            self.set_text_color(*color)
            self.cell(0, 6, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            self.set_x(self.l_margin + 5)
        self.font(10)
        self.set_text_color(*INK)
        self.multi_cell(self.body_w - 10, 5.2, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_y(y + height + 4)

    def two_lists(self, left_title, left, right_title, right, colors=(GREEN, RED), size=9.4):
        """Side-by-side bullet lists (e.g. favour / reduce) in tinted panels."""
        col_w = (self.body_w - 6) / 2
        line_h = size * 0.52

        def height(items):
            self.font(size)
            n = sum(len(self.multi_cell(col_w - 10, line_h, it, dry_run=True, output="LINES")) for it in items)
            return 9 + n * line_h + len(items) * 1.2 + 3
        h = max(height(left), height(right))
        self.need(h + 3)
        y = self.get_y()
        for i, (title, items) in enumerate(((left_title, left), (right_title, right))):
            x = self.l_margin + i * (col_w + 6)
            color = colors[i]
            self.set_fill_color(*(tuple(int(c + (255 - c) * 0.9) for c in color)))
            self.rect(x, y, col_w, h, style="F", round_corners=True, corner_radius=2)
            self.set_xy(x + 4, y + 2.5)
            self.font(9.5, "B")
            self.set_text_color(*color)
            self.cell(col_w - 8, 5, title.upper() if self.lang == "en" else title)
            self.set_text_color(*INK)
            cy = y + 9
            for it in items:
                self.set_fill_color(*color)
                self.circle(x + 5, cy + line_h / 2, 0.7, style="F")
                self.set_xy(x + 7.5, cy)
                self.font(size)
                self.multi_cell(col_w - 10, line_h, it, align="L", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                cy = self.get_y() + 1.2
        self.set_y(y + h + 4)

    def timeline(self, segments, start_label="", end_label=""):
        """Horizontal bar: [(width share, colour, label, sublabel)] across the body width."""
        self.need(30)
        y = self.get_y() + 2
        x = self.l_margin
        total = sum(s[0] for s in segments)
        for share, color, label, sub in segments:
            w = self.body_w * share / total
            self.set_fill_color(*color)
            self.rect(x, y, w, 11, style="F")
            self.set_draw_color(255, 255, 255)
            self.set_line_width(0.6)
            self.line(x, y, x, y + 11)
            self.set_text_color(255, 255, 255)
            self.font(7.5, "B")
            self.set_xy(x, y + 1.2)
            self.cell(w, 4.2, label, align="C")
            self.font(6.8)
            self.set_xy(x, y + 5.6)
            self.cell(w, 4, sub, align="C")
            x += w
        self.set_text_color(*MUTED)
        self.font(7.5)
        self.set_xy(self.l_margin, y + 12)
        self.cell(self.body_w / 2, 4, start_label)
        self.cell(self.body_w / 2, 4, end_label, align="R")
        self.set_text_color(*INK)
        self.set_y(y + 19)

    def pill(self, text, color, x=None, y=None, size=8):
        self.font(size, "B")
        w = self.get_string_width(text) + 5
        x = self.get_x() if x is None else x
        y = self.get_y() if y is None else y
        self.set_fill_color(*color)
        self.rect(x, y, w, 5.2, style="F", round_corners=True, corner_radius=2.4)
        self.set_text_color(255, 255, 255)
        self.set_xy(x, y)
        self.cell(w, 5.2, text, align="C")
        self.set_text_color(*INK)
        return w

    def kv_table(self, rows, col=(55, None), size=9.5):
        widths = (col[0], self.body_w - col[0])
        self.need((len(rows) if len(rows) <= 8 else 3) * 7.6 + 4)   # keep short tables whole
        self.font(size)
        self.set_fill_color(255, 255, 255)   # fpdf2 tables take the current fill as their base style
        self.set_draw_color(*RULE)
        with self.table(col_widths=widths, width=self.body_w, line_height=5.6, first_row_as_headings=False,
                        borders_layout="HORIZONTAL_LINES", cell_fill_color=SOFT, cell_fill_mode=TableCellFillMode.ROWS,
                        padding=1.6) as table:
            for k, v in rows:
                row = table.row()
                row.cell(str(k), style=FontFace(emphasis="BOLD", color=MAROON))
                row.cell(str(v))
        self.ln(3)

    def grid_table(self, headings, rows, widths=None, size=8.8, highlight=None, align=None):
        """``highlight``: set of row indexes drawn in saffron tint."""
        highlight = highlight or set()
        head = FontFace(emphasis="BOLD", color=(255, 255, 255), fill_color=MAROON)
        self.need((len(rows) if len(rows) <= 8 else 3) * 7.2 + 10)
        self.font(size)
        self.set_fill_color(255, 255, 255)
        self.set_draw_color(*RULE)
        with self.table(col_widths=widths, width=self.body_w, line_height=5, headings_style=head,
                        borders_layout="HORIZONTAL_LINES", cell_fill_color=(251, 245, 234),
                        cell_fill_mode=TableCellFillMode.ROWS, padding=1.4,
                        text_align=align or "LEFT") as table:
            row = table.row()
            for h in headings:
                row.cell(h)
            for i, r in enumerate(rows):
                style = FontFace(emphasis="BOLD", fill_color=(255, 232, 196)) if i in highlight else None
                row = table.row()
                for value in r:
                    row.cell(str(value), style=style)
        self.ln(3)


# ---------------------------------------------------------------------------
# North Indian chart
# ---------------------------------------------------------------------------

_P = {"TL": (0, 0), "T": (.5, 0), "TR": (1, 0), "R": (1, .5), "BR": (1, 1), "B": (.5, 1), "BL": (0, 1), "L": (0, .5),
      "C": (.5, .5), "P1": (.25, .25), "P2": (.75, .25), "P3": (.75, .75), "P4": (.25, .75)}
HOUSE_POLY = {1: ("T", "P2", "C", "P1"), 2: ("TL", "T", "P1"), 3: ("TL", "P1", "L"), 4: ("L", "P1", "C", "P4"),
              5: ("L", "P4", "BL"), 6: ("BL", "P4", "B"), 7: ("B", "P4", "C", "P3"), 8: ("B", "P3", "BR"),
              9: ("BR", "P3", "R"), 10: ("R", "P3", "C", "P2"), 11: ("R", "P2", "TR"), 12: ("TR", "P2", "T")}
# (sign-number position, planet block centre, layout: k = kite, h = wide triangle, v = tall triangle)
HOUSE_LAYOUT = {1: ((.5, .41), (.5, .22), "k"), 2: ((.25, .19), (.25, .065), "h"), 3: ((.19, .25), (.075, .25), "v"),
                4: ((.41, .5), (.22, .5), "k"), 5: ((.19, .75), (.075, .75), "v"), 6: ((.25, .81), (.25, .935), "h"),
                7: ((.5, .59), (.5, .78), "k"), 8: ((.75, .81), (.75, .935), "h"), 9: ((.81, .75), (.925, .75), "v"),
                10: ((.59, .5), (.78, .5), "k"), 11: ((.81, .25), (.925, .25), "v"), 12: ((.75, .19), (.75, .065), "h")}


def draw_chart(pdf, x, y, size, asc_sign, placements, title="", subtitle="", font_size=None):
    """
    ``asc_sign``: 0-11 sign in the 1st house. ``placements``: {planet name: (sign index, retrograde)}.
    Draws a filled North Indian chart with sign numbers and coloured planet abbreviations.
    """
    fs = font_size or max(6.0, size / 10.5)
    auto, margin = pdf.auto_page_break, pdf.b_margin
    pdf.set_auto_page_break(False)   # a chart is placed absolutely; it must never trigger a page break
    pts = {k: (x + vx * size, y + vy * size) for k, (vx, vy) in _P.items()}
    for house, poly in HOUSE_POLY.items():
        sign = (asc_sign + house - 1) % 12
        fill = (255, 240, 196) if house == 1 else ELEMENT_FILL[sign % 4]
        pdf.set_fill_color(*fill)
        pdf.polygon([pts[p] for p in poly], style="F")
    pdf.set_draw_color(*MAROON)
    pdf.set_line_width(0.5)
    pdf.rect(x, y, size, size)
    pdf.set_line_width(0.3)
    pdf.line(*pts["TL"], *pts["BR"])
    pdf.line(*pts["TR"], *pts["BL"])
    pdf.polygon([pts["T"], pts["R"], pts["B"], pts["L"]], style="D")

    by_house = {h: [] for h in range(1, 13)}
    for name, (sign, retro) in placements.items():
        house = (sign - asc_sign) % 12 + 1
        by_house[house].append((name, retro))
    order = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
    for house, ((nx, ny), (cx, cy), shape) in HOUSE_LAYOUT.items():
        sign = (asc_sign + house - 1) % 12
        pdf.set_font("sans", "", fs * 0.8)
        pdf.set_text_color(*MUTED)
        pdf.set_xy(x + nx * size - 4, y + ny * size - 2)
        pdf.cell(8, 4, str(sign + 1), align="C")
        items = sorted(by_house[house], key=lambda p: order.index(p[0]) if p[0] in order else 99)
        if not items:
            continue
        per_row = {"k": 3, "h": 3, "v": 1}[shape]
        if shape == "v" and len(items) > 4:
            per_row = 2
        if shape == "k" and len(items) <= 2:
            per_row = 2
        rows = [items[i:i + per_row] for i in range(0, len(items), per_row)]
        line_h = fs * 0.46
        cell_w = fs * 1.15
        top = y + cy * size - len(rows) * line_h / 2
        for r, row in enumerate(rows):
            left = x + cx * size - len(row) * cell_w / 2
            for c, (name, retro) in enumerate(row):
                pdf.set_font("sans", "B", fs)
                pdf.set_text_color(*PLANET_COLORS.get(name, INK))
                label = i18n.planet_abbr(name, pdf.lang) + ("*" if retro and name not in ("Rahu", "Ketu") else "")
                pdf.set_xy(left + c * cell_w, top + r * line_h)
                pdf.cell(cell_w, line_h, label, align="C")
    pdf.set_text_color(*INK)
    if title:
        pdf.set_xy(x, y + size + 1.5)
        pdf.set_font("serif", "B", 10)
        pdf.set_text_color(*MAROON)
        pdf.cell(size, 5, title, align="C")
        if subtitle:
            pdf.set_xy(x, y + size + 6.5)
            pdf.set_font("serif", "I", 8)
            pdf.set_text_color(*MUTED)
            pdf.multi_cell(size, 3.8, subtitle, align="C")
        pdf.set_text_color(*INK)
    pdf.set_auto_page_break(auto, margin=margin)


# ---------------------------------------------------------------------------
# Copy protection
# ---------------------------------------------------------------------------

def owner_password():
    return settings.PDF_OWNER_PASSWORD or hashlib.sha256(f"pdf-owner:{settings.SECRET_KEY}".encode()).hexdigest()


def protect(pdf_bytes, order_ref, licensee, email):
    """Encrypt so readers allow printing but not copying text, editing, or assembling pages."""
    import pikepdf
    src = pikepdf.open(io.BytesIO(pdf_bytes))
    with src.open_metadata(set_pikepdf_as_editor=False) as meta:
        meta["dc:rights"] = f"Licensed to {licensee} <{email}>, order {order_ref}. Personal copy, not for redistribution."
    src.docinfo["/OrderRef"] = order_ref
    src.docinfo["/Subject"] = f"Licensed to {licensee} <{email}>, order {order_ref}"
    out = io.BytesIO()
    src.save(out, encryption=pikepdf.Encryption(
        owner=owner_password(), user="", R=6,
        allow=pikepdf.Permissions(accessibility=False, extract=False, modify_annotation=False, modify_assembly=False,
                                  modify_form=False, modify_other=False, print_lowres=True, print_highres=True),
    ))
    return out.getvalue()
