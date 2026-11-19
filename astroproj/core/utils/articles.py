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


# ---------------------------------------------------------------------------
# Articles written as Markdown files in articles/*.md
#
# The file starts with a block between '---' lines: the page's meta fields (seo_title, meta_description, slug, h1,
# primary_keyword, secondary_keywords, publish_date, faq_schema, optional topic). It is never shown as page text.
# ---------------------------------------------------------------------------

import re

ARTICLES_DIR_NAME = "articles"
_MUHURAT_LINK = re.compile(r"\]\(/shubh-muhurat/([a-z_]+)/\d{4}/\)")


def _scalar(v):
    v = v.strip()
    if v[:1] in "\"'":
        q = v[0]
        return v[1:v.index(q, 1)] if q in v[1:] else v[1:]
    v = re.sub(r"\s+#.*$", "", v).strip()          # trailing comment on an unquoted value
    return {"true": True, "false": False}.get(v.lower(), v)


def parse_front_matter(text):
    """Split '---' meta block from the body. Handles the simple YAML used in articles/: key: value and '- item' lists."""
    text = text.replace("\r\n", "\n").lstrip("\ufeff")
    if not text.startswith("---\n"):
        return {}, text
    end = text.index("\n---", 4)
    meta, key = {}, None
    for line in text[4:end].split("\n"):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.lstrip().startswith("- ") and key:
            meta.setdefault(key, [])
            if isinstance(meta[key], list):
                meta[key].append(_scalar(line.lstrip()[2:]))
            continue
        k, _, v = line.partition(":")
        key = k.strip()
        meta[key] = _scalar(v) if v.strip() else []
    return meta, text[end + 4:].lstrip("\n")


def _strip_md(s):
    """Markdown inline -> plain text (for FAQ answers in JSON-LD)."""
    s = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", s)
    s = re.sub(r"[*_`]{1,3}([^*_`]+)[*_`]{1,3}", r"\1", s)
    return re.sub(r"\s+", " ", s).strip()


def extract_faq(body):
    """Questions are the '### ' headings under the '## ...FAQ...' / 'Frequently Asked Questions' section."""
    m = re.search(r"^## [^\n]*(Frequently Asked Questions|FAQ)[^\n]*\n(.*?)(?=^## |\Z)", body, re.M | re.S | re.I)
    if not m:
        return []
    faq = []
    for part in re.split(r"^### ", m.group(2), flags=re.M)[1:]:
        q, _, a = part.partition("\n")
        q = re.sub(r"^\d+[.)]\s*", "", q.strip())
        if q and a.strip():
            faq.append([_strip_md(q), _strip_md(a)])
    return faq


def render_markdown(body):
    """Article Markdown -> HTML: tables, '- [ ]' checklists, and every external link opening safely."""
    import markdown
    body = re.sub(r"^\s*# [^\n]*\n", "", body.replace("\r\n", "\n"), count=1)    # the H1 comes from the meta block
    body = re.sub(r"^- \[ \] ", "- \u2610 ", body, flags=re.M)
    body = re.sub(r"^- \[[xX]\] ", "- \u2611 ", body, flags=re.M)
    html = markdown.markdown(body, extensions=["tables", "sane_lists"], output_format="html")
    html = re.sub(r'<a href="(https?://)', r'<a rel="noopener" target="_blank" href="\1', html)
    return mark_safe(html)


def article_from_file(path):
    """Field values for one articles/*.md file."""
    from pathlib import Path
    path = Path(path)
    meta, body = parse_front_matter(path.read_text(encoding="utf-8"))
    slug = meta.get("slug") or slugify(path.stem)
    h1 = meta.get("h1") or re.search(r"^# (.+)$", body, re.M).group(1)
    kw = [meta.get("primary_keyword") or ""] + list(meta.get("secondary_keywords") or [])
    pub = meta.get("publish_date")
    return {
        "slug": slug, "title": h1[:160], "seo_title": (meta.get("seo_title") or "")[:160],
        "summary": (meta.get("meta_description") or "")[:300], "keywords": ", ".join(k for k in kw if k)[:400],
        "topic": meta.get("topic") or "festival", "body": body, "body_format": "markdown",
        "source_file": f"{ARTICLES_DIR_NAME}/{path.name}",
        "faq": extract_faq(body) if meta.get("faq_schema") is True else [],
        "muhurat_purposes": list(dict.fromkeys(_MUHURAT_LINK.findall(body))),     # in reading order
        "publish_date": date.fromisoformat(str(pub)) if pub else None,
        "related_url": meta.get("related_url") or "",
    }


def _ist_date(dt, ist):
    return dt.astimezone(ist).date() if dt.tzinfo else dt.date()


def import_article_files(directory, today=None):
    """Create or update an Article for every .md file. Published once its publish_date has come (IST)."""
    from datetime import datetime, time
    from pathlib import Path
    from zoneinfo import ZoneInfo
    from django.conf import settings
    from ..models import Article
    ist = ZoneInfo("Asia/Kolkata")
    today = today or datetime.now(ist).date()
    done = []
    for path in sorted(Path(directory).glob("*.md")):
        data = article_from_file(path)
        pub = data.pop("publish_date")
        a = Article.objects.filter(slug=data["slug"]).first() or Article(slug=data["slug"])
        for k, v in data.items():
            setattr(a, k, v)
        live = pub is None or pub <= today
        a.status = "published" if live else "draft"
        if live and pub and (not a.published_at or _ist_date(a.published_at, ist) != pub):
            at = datetime.combine(pub, time(6, 0))          # 6 am IST on the publish date
            a.published_at = at.replace(tzinfo=ist) if settings.USE_TZ else at
        a.save()
        done.append(a)
    return done
