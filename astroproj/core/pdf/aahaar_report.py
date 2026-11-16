# core/pdf/aahaar_report.py
"""The printed Aahaar and Ritucharya guide for one date and city."""
from datetime import date, datetime, time

import pytz

from . import i18n
from .book import GOLD, GREEN, INK, MAROON, MUTED, RED, SAFFRON, Book, protect

DOSHA_COLORS = {"Kapha": (63, 133, 121), "Pitta": (205, 105, 40), "Vata": (98, 108, 178)}
NATURE_COLORS = {"cooling": (40, 110, 160), "heating": (190, 70, 40), "balanced": GREEN}


def _fmt_date(d, lang):
    return d.strftime("%d.%m.%Y") if lang == "hi" else d.strftime("%d %B %Y")


def _hm(dt):
    return dt.strftime("%H:%M")


def build(params, *, lang, licensee, email, order_ref, now=None):
    from ..views.grahan_views import aahaar_context
    d = date.fromisoformat(params["date"])
    tz = params.get("tz") or "Asia/Kolkata"
    ctx = aahaar_context(d, float(params["lat"]), float(params["lon"]), tz, params.get("city", ""), now_time=time(12, 0),
                        region=params.get("region"), month_system=params.get("month_system", "purnimanta"), lang=lang)
    now = now or datetime.now(pytz.timezone(tz))
    W = lambda key: i18n.w(key, lang)
    P = lambda pair: i18n.pick(pair, lang)
    T = lambda text: i18n.terms(text, lang)
    L = lambda en, hi: hi if lang == "hi" else en

    pdf = Book(lang=lang, title=W("aahaar_title"), running_title=W("aahaar_title"), licensee=licensee, email=email,
               order_ref=order_ref, printed_on=_fmt_date(now.date(), lang))
    ritu = ctx["ritu"] or {}
    win = ctx["window"]
    ritu_label = ritu.get("hindi", "") if lang == "hi" else f"{ctx['ritu_name']} {ritu.get('hindi', '')}"
    pdf.cover(W("aahaar_title"), W("aahaar_sub"), licensee, [
        f"{ctx['city']}  ·  {_fmt_date(d, lang)}",
        f"{W('ritu')}: {ritu_label} ({L('Drik sayana', 'दृक् सायन')})  ·  {W('masa')}: {T(ctx['masa'])}",
        f"{W('weekday')}: {T(ctx['weekday'])}  ·  {W('tithi')}: {T(ctx['paksha_tithi'] or '')}",
    ], images=["Sun", "Moon"])
    pdf.contents_page()

    # 1. Today
    pdf.chapter(1, W("ch_today"))
    pdf.kv_table([
        (W("date"), f"{_fmt_date(d, lang)} ({T(ctx['weekday'])})"), (W("city"), ctx["city"]),
        (W("ritu"), f"{ritu_label}, {L('Drik (sayana)', 'दृक् (सायन)')}" +
         (f": {_fmt_date(win['start'].date(), lang)} - {_fmt_date(win['end'].date(), lang)}" if win else "") +
         (f". {L('Nirayana (puja calendar)', 'निरयण (पूजा कैलेंडर)')}: {T(ctx['nirayana_ritu'])}" if ctx["nirayana_ritu"] and
          ctx["nirayana_ritu"] != ctx["ritu_name"] else "")),
        (W("masa"), f"{T(ctx['masa'])} ({T(ctx['month_label'])})"),
        (W("tithi"), T(ctx["paksha_tithi"] or "")), (W("nakshatra"), i18n.nakshatra(ctx["nakshatra"] or "", lang)),
        (W("dosha"), f"{ritu.get('dosha', '')} ({L('season', 'ऋतु')})" if ritu else ""),
    ])
    if ritu:
        pdf.two_lists(W("eat"), ritu.get("eat", []), W("avoid"), ritu.get("avoid", []))
    g = ctx["guidance"]
    pdf.h2("Today's rules, by where they come from" if lang == "en" else "आज के नियम, स्रोत अनुसार")
    pdf.grid_table(["Rule" if lang == "en" else "नियम", "For" if lang == "en" else "किसके लिए", W("eat"), W("avoid")],
                   [[T(x["label"]), x["who"], x["favour"] or "-", x["avoid"] + (f". {x['note']}" if x["note"] else "")]
                    for x in g["layers"] if x["key"] != "ritu"], widths=(34, 26, 50, 60), size=8.2)
    if g["clashes"]:
        pdf.h3("Today's clashes, resolved" if lang == "en" else "आज के टकराव, समाधान सहित", color=SAFFRON)
        pdf.bullets([c["text"] for c in g["clashes"]], size=9.2)
    pdf.h3("Which rule wins" if lang == "en" else "कौन-सा नियम ऊपर", color=MAROON)
    pdf.bullets([f"{i}. {name}: {text}" for i, (name, text) in enumerate(g["precedence"], 1)], size=9)
    if ctx["window"] and ctx["window"].get("sandhi"):
        a, b = ctx["window"]["sandhi"]
        pdf.callout(L("Ritu Sandhi", "ऋतु सन्धि"), L(f"The season is changing from {a} to {b}. Move diet and habits across gradually.",
                                                     f"ऋतु {T(a)} से {T(b)} में बदल रही है। आहार और आदतें धीरे-धीरे बदलें।"))

    # 2. Daily rhythm
    r = ctx["rhythm"]
    pdf.chapter(2, W("ch_rhythm"),
                f"{W('sunrise')} {_hm(r['sunrise'])}  ·  {W('sunset')} {_hm(r['sunset'])}  ·  {ctx['city']}" if r else "")
    if r:
        segs = []
        for p in r["pahars"]:
            color = DOSHA_COLORS[p["doshas"][0]]
            if not p["is_day"]:
                color = tuple(int(c * 0.72) for c in color)
            segs.append((p["width"], color, f"{p['n']}", f"{_hm(p['start'])}"))
        pdf.timeline(segs, f"☀ {W('sunrise')} {_hm(r['sunrise'])}", ("Next sunrise " if lang == "en" else "अगला सूर्योदय ") + _hm(r["next_sunrise"]))
        pdf.font(8, "I")
        pdf.set_text_color(*MUTED)
        legend = "  ·  ".join(f"{(n if lang == 'en' else h)}" for n, h in (("Kapha", "कफ"), ("Pitta", "पित्त"), ("Vata", "वात")))
        pdf.cell(0, 4, legend + ("  (darker = night)" if lang == "en" else "  (गहरा = रात्रि)"),
                 new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(*INK)
        pdf.ln(2)
        rows = [[f"{_hm(p['start'])} - {_hm(p['end'])}", p["hindi"] if lang == "hi" else p["name"],
                 " → ".join(p["doshas_hi"] if lang == "hi" else p["doshas"]), p["tip"]] for p in r["pahars"]]
        pdf.grid_table([W("time"), W("pahar"), W("dosha"), W("what_to_do")], rows, widths=(25, 45, 25, 75), size=8.4)
        pdf.para("The doshas here are the day's own clock (Ashtanga Hridaya Su 1.8). They repeat every day and are "
                 "separate from the season's dosha in chapter 1." if lang == "en" else
                 "यहाँ दिए दोष दिन की घड़ी के हैं (अष्टांग हृदय सू 1.8), जो हर दिन दोहराते हैं; ये अध्याय 1 के ऋतु-दोष से अलग हैं।",
                 size=8.6, style="I", color=MUTED, align="L")
        pdf.h2(W("meals"))
        pdf.grid_table([W("time"), ""], [[f"{_hm(m['start'])} - {_hm(m['end'])}", m["hindi"] if lang == "hi" else m["name"]]
                                         for m in r["meals"]], widths=(40, 130), size=9)
        pdf.h3(W("principles"))
        pdf.bullets(ctx["meal_rules"], size=9.6)

    # 3. Season
    pdf.chapter(3, f"{W('ch_ritu')}: {T(ctx['ritu_name'])}")
    if ritu:
        pdf.kv_table([(L("Sun's position", "सूर्य की स्थिति"), ritu["months"]), (L("Named in the texts", "शास्त्रों में नाम"), ritu["named"]),
                      (L("Kaal", "काल"), ritu["kaal"]), (L("Agni (digestion)", "अग्नि (पाचन)"), ritu["agni"]),
                      (L("Bala (strength)", "बल"), ritu["bala"]), (L("Rasa", "रस"), ritu["rasa"]),
                      (L("Ritu Haritaki", "ऋतु हरीतकी"), ritu["haritaki"])])
        pdf.para(ctx["ritu_names_note"], size=8.6, style="I", color=MUTED, align="L")
        pdf.h3("Lifestyle" if lang == "en" else "दिनचर्या")
        pdf.bullets(ritu["lifestyle"])
    pdf.h2("All six ritus" if lang == "en" else "छहों ऋतुएँ")
    pdf.grid_table([W("ritu"), W("eat"), W("avoid")],
                   [[f"{T(n)}\n{x['months']}", "; ".join(x["eat"]), "; ".join(x["avoid"])] for n, x in ctx["all_ritus"].items()],
                   widths=(36, 67, 67), size=8)

    # 4. Regions: the buyer's own region in full, the rest at a glance
    season = ctx["season"]
    regions = {r["key"]: r for r in ctx["regions"]}
    mine = regions.get(ctx["my_region"]) or ctx["regions"][0]
    # The home kitchen (native state or chosen region) can differ from where the buyer lives now: name both.
    local = regions.get(ctx["local_region"]) if ctx["local_region"] != mine["key"] else None
    if local:
        sub = (f"Your home region, {P(mine['name'])} (from your profile), season by season; then where you live now, "
               f"{ctx['city']}" + (f" ({P(local['name'])})" if P(local['name']) not in ctx['city'] else "") + f"; then every other region in {P(ctx['season_info']).lower()}."
               if lang == "en" else
               f"आपका मूल क्षेत्र, {P(mine['name'])} (प्रोफ़ाइल से), ऋतु अनुसार; फिर आपका वर्तमान शहर, {ctx['city']} "
               f"({P(local['name'])}); फिर {P(ctx['season_info'])} में अन्य सभी क्षेत्र।")
    else:
        sub = (f"Your region, {P(mine['name'])}, season by season; then every other region in "
               f"{P(ctx['season_info']).lower()}." if lang == "en" else
               f"आपका क्षेत्र, {P(mine['name'])}, ऋतु अनुसार; फिर {P(ctx['season_info'])} में अन्य सभी क्षेत्र।")
    pdf.chapter(4, W("ch_regions"), sub)
    pdf.h2(P(mine["name"]))
    order = [season] + [k for k in ("winter", "summer", "monsoon") if k != season]
    for k in order:
        sv = mine["seasons"][k]
        pdf.need(70)
        pdf.callout(P(ctx["seasons"][k]), sv["dishes"], color=SAFFRON if k == season else GOLD)
        pdf.kv_table([(W("staples"), sv["grains"]), (W("dals"), sv["dals"]), (W("vegetables"), sv["vegetables"]),
                      (W("fruits"), sv["fruits"]), (W("spices"), sv["spices"])], col=(36, None), size=8.8)
        pdf.callout(W("avoid"), sv["avoid"], color=RED, fill=(253, 236, 232))
    if local:
        sv = local["seasons"][season]
        pdf.need(70)
        pdf.h2((f"Where you live now: {P(local['name'])}" if lang == "en" else f"वर्तमान शहर: {P(local['name'])}"))
        pdf.callout(P(ctx["seasons"][season]), sv["dishes"], color=SAFFRON)
        pdf.kv_table([(W("staples"), sv["grains"]), (W("dals"), sv["dals"]), (W("vegetables"), sv["vegetables"]),
                      (W("fruits"), sv["fruits"]), (W("spices"), sv["spices"])], col=(36, None), size=8.8)
        pdf.callout(W("avoid"), sv["avoid"], color=RED, fill=(253, 236, 232))
    pdf.h2("Other regions this season" if lang == "en" else "इस ऋतु में अन्य क्षेत्र")
    pdf.grid_table([W("region"), W("eat"), W("avoid")],
                   [[P(r["name"]), r["seasons"][season]["dishes"], r["seasons"][season]["avoid"]]
                    for r in ctx["regions"] if r["key"] not in (mine["key"], (local or {}).get("key"))], widths=(36, 72, 62), size=7.8)

    # 5. Ingredients
    pdf.chapter(5, W("ch_foods"), "Cooling, heating or balanced (virya), and the doshas each one calms (-) or raises (+)."
                if lang == "en" else "शीतल, उष्ण या सम (वीर्य), और कौन-से दोष शान्त (-) या वृद्धि (+) करते हैं।")
    season_word = {"winter": ("Winter", "शीत"), "summer": ("Summer", "ग्रीष्म"), "monsoon": ("Rains", "वर्षा"),
                   "all": ("All year", "सदैव")}
    for g in ctx["ingredient_groups"]:
        pdf.h2(P(g["label"]))
        code = (lambda c: c.replace("V", "वा").replace("P", "पि").replace("K", "क")) if lang == "hi" else (lambda c: c)
        rows = [[x["name"] + (f"\n{x['hindi']}" if x["hindi"] else ""), P(x["nature_label"]), code(x["effect_code"]), P(season_word[x["season"]]), x["note"]]
                for x in g["rows"]]
        pdf.grid_table([W("ingredient"), W("nature"), W("dosha"), W("best_season"), W("use")], rows, widths=(48, 20, 22, 20, 60), size=8)

    # 6. Age
    pdf.chapter(6, W("ch_age"))
    for a in ctx["age_groups"]:
        pdf.need(60)
        pdf.h2(P(a["name"]))
        pdf.para(a["stage"], size=9.6, style="I", color=MUTED, align="L")
        pdf.h3(W("principles"))
        pdf.bullets(a["principles"], size=9.4)
        pdf.two_lists(W("eat"), [a["eat"]], W("limit"), [a["limit"]])
        if a.get("months"):
            pdf.kv_table(a["months"], col=(32, None), size=9)
        pdf.h3(W("sample_day"))
        pdf.kv_table(a["day"], col=(32, None), size=9)

    # 7. Fitness
    pdf.chapter(7, W("ch_fitness"))
    for f in ctx["fitness"]:
        pdf.need(60)
        pdf.h2(P(f["name"]))
        pdf.bullets(f["principles"], size=9.4)
        pdf.two_lists(W("eat"), [f["eat"]], W("limit"), [f["limit"]])
        if f.get("before"):
            pdf.two_lists(W("before_workout"), [f["before"]], W("after_workout"), [f["after"]], colors=(SAFFRON, GREEN))
        pdf.h3(W("sample_day"))
        pdf.kv_table(f["day"], col=(32, None), size=9)
    pdf.h2("When you train" if lang == "en" else "व्यायाम का समय")
    pdf.kv_table(ctx["workout_timing"], col=(40, None), size=9)

    # 8. Doshas
    pdf.chapter(8, W("ch_dosha_guide"))
    for name, x in ctx["doshas"].items():
        pdf.h2(x["hindi"] if lang == "hi" else f"{name} · {x['hindi']}", color=DOSHA_COLORS[name])
        pdf.kv_table([(L("Nature", "प्रकृति"), f"{x['element']}: {x['qualities']}"), (L("Signs of excess", "बढ़ने के लक्षण"), x["signs"]),
                      (L("Pacified by", "शान्त करता है"), x["pacify"])], col=(36, None), size=9)
        pdf.two_lists(W("eat"), x["eat"], W("avoid"), x["avoid"])

    # 9. Calendar
    pdf.chapter(9, W("ch_calendar"))
    pdf.grid_table([W("masa"), W("avoid"), "", W("eat")],
                   [[T(m), row[0], row[1], row[2]] for m, row in ctx["maas_table"].items()],
                   widths=(26, 34, 60, 50), size=8.2, highlight={i for i, m in enumerate(ctx["maas_table"]) if m == ctx["masa"]})
    pdf.grid_table([W("weekday"), W("planet"), W("eat"), W("avoid")],
                   [[T(day), x["planet"], x["favour"], x["avoid"]] for day, x in ctx["vaar_table"].items()],
                   widths=(26, 20, 70, 54), size=8.2,
                   highlight={i for i, day in enumerate(ctx["vaar_table"]) if day == ctx["weekday"]})

    # 10. Sayings: only the buyer's region (and the pan-Indian Sanskrit line), never another region's
    pdf.chapter(10, W("ch_sayings"), min_space=70)
    for s in mine["sayings"]:
        pdf.need(36)
        if s.get("title"):
            pdf.h3(s["title"], color=MAROON)
        pdf.para(s["text"], size=12, color=(107, 52, 16), align="L")
        if s.get("roman"):
            pdf.para(s["roman"], size=9.4, style="I", color=MUTED, align="L")
        pdf.para(s["meaning"], size=9.6, align="L")
        pdf.para(s["source"], size=8, color=GOLD, align="L")
        pdf.ln(2)
    pdf.h2("Sources" if lang == "en" else "स्रोत")
    pdf.grid_table(["Topic" if lang == "en" else "विषय", "Text" if lang == "en" else "ग्रन्थ",
                    "Review" if lang == "en" else "समीक्षा"],
                   [list(row) for row in ctx["classical_sources"]], widths=(70, 70, 30), size=7.6)
    pdf.callout(W("disclaimer_title"), ctx["disclaimer"], color=RED)
    return protect(bytes(pdf.output()), order_ref, licensee, email)
