# core/utils/articles.py
"""Blog articles: a small safe formatter for the body, and drafts written from the site's own festival data.

Drafts are never published automatically. Search engines treat mass-produced pages as spam, so every draft
waits in the admin for the owner to read, add their own words, and press Publish.
"""
from datetime import date, timedelta

from django.utils.html import escape, format_html
from django.utils.safestring import mark_safe
from django.utils.text import slugify


def render_body(text):
    """Plain text -> HTML. Blank line = paragraph, '## ' = heading, '- ' = bullet. Everything else is escaped."""
    out = []
    for block in (text or "").replace("\r\n", "\n").split("\n\n"):
        lines = [x.rstrip() for x in block.strip().split("\n") if x.strip()]
        if not lines:
            continue
        if lines[0].startswith("## "):
            out.append(format_html("<h2>{}</h2>", lines[0][3:]))
            lines = lines[1:]
        if lines and all(x.startswith("- ") for x in lines):
            out.append("<ul>" + "".join(format_html("<li>{}</li>", x[2:]) for x in lines) + "</ul>")
        elif lines:
            out.append("<p>" + "<br>".join(escape(x) for x in lines) + "</p>")
    return mark_safe("\n".join(out))


def _hm(dt):
    return dt.strftime("%I:%M %p").lstrip("0")


def festival_draft(f):
    """Title, slug, summary and body for one festival row from festival_calculations."""
    from . import festival_calculations as fc, festival_muhurat as fm
    d = date.fromisoformat(str(f["date"]))
    v = fc.VARANASI
    lines = [f"{f['name']} falls on {f['weekday']}, {d:%d %B %Y}, by Kashi (Varanasi) panchang rules."]
    if f.get("note"):
        lines.append(f["note"])
    body = [" ".join(lines), "## How the date is decided",
            f"The rule: {f['rule']}." + (f" The month is {f['month']} (Purnimanta, as in Varanasi)." if f.get("month") else "")]
    details = f.get("details") or {}
    if details.get("tithi_start") and details.get("tithi_end"):
        body.append(f"The tithi runs from {details['tithi_start']} to {details['tithi_end']} (Varanasi time). "
                    "Where a tithi spans two days, the rule above decides which one is observed.")
    puja = fm.puja_muhurats(f["slug"], d, v["lat"], v["lon"], v["tz"])
    if puja and puja.get("windows"):
        rows = []
        for w in puja["windows"]:
            for s in w["spans"]:
                rows.append(f"- {w['label']}: {_hm(s['start'])} to {_hm(s['end'])}")
        if rows:
            body.append("## Puja muhurat in Varanasi")
            body.append("\n".join(rows))
            if puja.get("note"):
                body.append(puja["note"])
    has_puja = "## Puja muhurat in Varanasi" in body
    title = f"{f['name']} {d.year}: date, {'puja time' if has_puja else 'tithi timings'} and the rule behind it"
    body.append("## Your city")
    body.append("Sunrise, sunset and tithi times change with place. Open the festival page and pick your city for "
                "local timings.")
    body.append("## [Owner: add your own section here before publishing - the story, the puja vidhi your family "
                "follows, what is eaten that day. Delete this line.]")
    summary = (f"{f['name']} {d.year} is on {d:%d %B} ({f['weekday']}). The Kashi rule that fixes the date"
               + (", the tithi timings" if details.get("tithi_start") else "") + (" and the puja muhurat." if has_puja else "."))
    return {"title": title, "slug": slugify(f"{f['slug']}-{d.year}"), "summary": summary[:300],
            "body": "\n\n".join(body), "auto_source": f"festival:{f['slug']}:{d.year}",
            "related_url": f"/festivals/{d.year}/{f['slug']}/"}


def draft_upcoming(start=None, days=45):
    """Create drafts for the major festivals in the next ``days`` days. Returns the new Article objects."""
    from ..models import Article
    from . import festival_calculations as fc
    start = start or date.today()
    made = []
    for f in fc.get_festivals_between(start, start + timedelta(days=days)):
        if f["importance"] != "high":
            continue
        data = festival_draft(f)
        if Article.objects.filter(auto_source=data["auto_source"]).exists() or \
                Article.objects.filter(slug=data["slug"]).exists():
            continue
        made.append(Article.objects.create(topic="festival", status="draft", **data))
    return made
