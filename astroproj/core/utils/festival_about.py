# core/utils/festival_about.py
"""What a festival page shows besides its date: the panchang of the day at Varanasi, and reading text.

    day_panchang(date)       vaar, tithi, nakshatra, yoga, karana, month and sun times at Varanasi sunrise
    moment_panchang(dt)      tithi and nakshatra in force at an instant (e.g. the Sun's ingress)
    ABOUT[slug]              {"sections": [((h_en, h_hi), (p_en, p_hi)), ...], "faq": [((q_en, q_hi), (a_en, a_hi)), ...],
                              "muhurat": [purpose, ...]} - reading text in both languages, shown with |pick

Owner's tone rule: reading text reassures, never frightens.
"""
from datetime import datetime

import pytz

from . import festival_calculations as fc
from . import panchang_store as ps

VAAR = ["Somawar", "Mangalwar", "Budhwar", "Guruwar", "Shukrawar", "Shaniwar", "Raviwar"]


def _utc(dt):
    return dt.astimezone(pytz.utc).replace(tzinfo=None)


def _span(kind, at_utc):
    e = ps.event_at(kind, at_utc)
    return ps.as_local(e, fc.TZ) if e else None


def moment_panchang(at):
    """Tithi and nakshatra in force at the aware datetime ``at``."""
    u = _utc(at)
    return {"at": at, "tithi": _span("tithi", u), "nakshatra": _span("nakshatra", u)}


def day_panchang(d, month_system="Purnimanta"):
    """The panchang at Varanasi sunrise on local date ``d`` (Kashi reckons the day from sunrise)."""
    info = fc.day_info(d)
    u = _utc(info["sunrise"])
    lm = ps.lunar_month_at(u) or {}
    return {
        "date": d,
        "weekday": fc.WEEKDAY_NAMES[d.weekday()],
        "vaar": VAAR[d.weekday()],
        "sunrise": info["sunrise"],
        "sunset": info["sunset"],
        "tithi": _span("tithi", u),
        "nakshatra": _span("nakshatra", u),
        "yoga": _span("yoga", u),
        "karana": _span("karana", u),
        "masa": lm.get("amanta" if month_system == "Amanta" else "purnimanta"),
        "adhik": lm.get("adhik"),
    }


def parse_moment(value):
    return datetime.fromisoformat(value).astimezone(fc.TZ) if value else None


ABOUT = {
    "kharmas": {
        "sections": [
            (("What is Kharmas?", "खरमास क्या है?"),
             ("Kharmas, also called Malmas, is the month or so when the Sun moves through Dhanu (Sagittarius) or "
              "Meena (Pisces), the two signs ruled by Guru (Jupiter). It comes twice every year: from Dhanu Sankranti "
              "in mid-December to Makar Sankranti in mid-January, and from Meena Sankranti in mid-March to Mesha "
              "Sankranti in mid-April. Kashi panchangs, like most panchangs of North India, keep this month free of "
              "new beginnings such as weddings and griha pravesh.",
              "खरमास, जिसे मलमास भी कहते हैं, वह लगभग एक महीना है जब सूर्य धनु या मीन राशि में रहते हैं; ये दोनों राशियाँ "
              "गुरु (बृहस्पति) की हैं। यह हर वर्ष दो बार आता है: दिसम्बर के मध्य में धनु संक्रान्ति से जनवरी के मध्य में मकर "
              "संक्रान्ति तक, और मार्च के मध्य में मीन संक्रान्ति से अप्रैल के मध्य में मेष संक्रान्ति तक। काशी के पंचांग, उत्तर "
              "भारत के अधिकांश पंचांगों की तरह, इस महीने में विवाह और गृह प्रवेश जैसे नए शुभारम्भ नहीं रखते।")),
            (("Why is it called Kharmas?", "इसे खरमास क्यों कहते हैं?"),
             ("'Khar' means donkey. A Puranic story tells that the seven horses of Surya's chariot grew tired and "
              "thirsty, and Surya, who may never stop, yoked two donkeys to the chariot for a month while the horses "
              "rested. The chariot moved slowly, and so the Sun's strength in this month is said to be gentle. In "
              "panchang terms, when the Sun sits in Guru's own sign, the support that Surya and Guru together give "
              "to marriages and samskaras is held to be weaker, so families wait for the Sun to move on.",
              "'खर' का अर्थ है गधा। पुराणों की एक कथा के अनुसार सूर्य के रथ के सातों घोड़े थककर प्यासे हो गए। सूर्य कभी रुक "
              "नहीं सकते, इसलिए घोड़ों के विश्राम तक उन्होंने एक महीने के लिए रथ में दो खर (गधे) जोत लिए। रथ धीमा चला, "
              "इसलिए इस महीने सूर्य का तेज मन्द माना जाता है। पंचांग की दृष्टि से, जब सूर्य गुरु की राशि में होते हैं तो विवाह "
              "और संस्कारों को सूर्य और गुरु से मिलने वाला बल कम माना जाता है, इसलिए परिवार सूर्य के राशि बदलने की "
              "प्रतीक्षा करते हैं।")),
            (("What is usually postponed", "क्या टाला जाता है"),
             ("Vivah (marriage) and sagai, griha pravesh, bhoomi pujan for a new house, mundan, upanayan (janeu) and "
              "karnavedh, and big new commitments such as buying a house, land or a vehicle or opening a new business. "
              "Our muhurat pages leave Kharmas out for these, so the dates you see there already respect it.",
              "विवाह और सगाई, गृह प्रवेश, नए घर का भूमि पूजन, मुण्डन, उपनयन (जनेऊ) और कर्णवेध, तथा घर, ज़मीन या वाहन "
              "ख़रीदना या नया व्यापार शुरू करना जैसे बड़े नए काम। हमारे मुहूर्त पेज इन कामों के लिए खरमास को छोड़ देते हैं, "
              "इसलिए वहाँ दिखने वाली तिथियाँ पहले से इसका ध्यान रखती हैं।")),
            (("What is good to do in Kharmas", "खरमास में क्या करना शुभ है"),
             ("Kharmas is not an unlucky time: it is a month for worship. Offer arghya to Surya at sunrise, worship "
              "Vishnu and read or hear the Bhagavat, Ramayan or Gita, do japa, and give daan - til, gur, warm clothes "
              "and blankets, and food are traditional in the winter Kharmas. A Ganga snan in Kashi in this month is "
              "held especially meritorious. Daily life goes on as usual: work, travel, exams, festivals and everyday "
              "shopping are not affected.",
              "खरमास कोई अशुभ समय नहीं है: यह उपासना का महीना है। सूर्योदय पर सूर्य को अर्घ्य दें, विष्णु की पूजा करें और "
              "भागवत, रामायण या गीता का पाठ करें या सुनें, जप करें, और दान दें - शीत ऋतु के खरमास में तिल, गुड़, गरम कपड़े, "
              "कम्बल और अन्न का दान परम्परा है। इस महीने काशी में गंगा स्नान विशेष पुण्यदायी माना गया है। रोज़ का जीवन "
              "सामान्य रूप से चलता है: नौकरी, यात्रा, परीक्षा, त्योहार और रोज़ की ख़रीदारी पर कोई रोक नहीं है।")),
            (("Kharmas, Malmas and Adhik maas", "खरमास, मलमास और अधिक मास"),
             ("Some calendars use the word Malmas for Adhik maas (Purushottam maas), the extra lunar month that comes "
              "about once in three years. The two are different: Kharmas follows the Sun's sign and comes twice every "
              "year, while Adhik maas follows the Moon and comes only in some years. In both, new beginnings wait and "
              "worship is encouraged.",
              "कुछ पंचांग 'मलमास' शब्द अधिक मास (पुरुषोत्तम मास) के लिए भी लिखते हैं, जो लगभग तीन वर्ष में एक बार आने "
              "वाला अतिरिक्त चान्द्र मास है। दोनों अलग हैं: खरमास सूर्य की राशि से चलता है और हर वर्ष दो बार आता है, जबकि "
              "अधिक मास चन्द्रमा से चलता है और कुछ ही वर्षों में आता है। दोनों में नए शुभारम्भ रुकते हैं और उपासना को "
              "बढ़ावा दिया जाता है।")),
            (("When Kharmas ends", "खरमास कब समाप्त होता है"),
             ("Kharmas ends the moment the Sun enters Makara (Makar Sankranti) or Mesha (Mesha Sankranti). Wedding and "
              "griha pravesh muhurats start again in the days after that, once the tithi, nakshatra and lagna also "
              "suit. For the final date and lagna, please talk to your family pandit.",
              "सूर्य के मकर (मकर संक्रान्ति) या मेष (मेष संक्रान्ति) में प्रवेश करते ही खरमास समाप्त हो जाता है। इसके बाद के "
              "दिनों में, जब तिथि, नक्षत्र और लग्न भी अनुकूल हों, विवाह और गृह प्रवेश के मुहूर्त फिर शुरू होते हैं। अन्तिम "
              "तिथि और लग्न के लिए कृपया अपने कुल-पण्डित से बात करें।")),
        ],
        "faq": [
            (("Is Kharmas inauspicious?", "क्या खरमास अशुभ है?"),
             ("No. Only new beginnings such as marriage, griha pravesh and samskaras wait. Worship, daan and daily "
              "life go on, and the month is considered good for spiritual practice.",
              "नहीं। केवल विवाह, गृह प्रवेश और संस्कार जैसे नए शुभारम्भ रुकते हैं। पूजा, दान और रोज़ का जीवन चलता रहता है, "
              "और यह महीना साधना के लिए अच्छा माना जाता है।")),
            (("Can we buy a house, land or vehicle in Kharmas?", "क्या खरमास में घर, ज़मीन या वाहन ख़रीद सकते हैं?"),
             ("Most panchangs advise waiting until Kharmas ends for big purchases. If it cannot wait, your family "
              "pandit can suggest a suitable day; everyday shopping is fine.",
              "अधिकांश पंचांग बड़ी ख़रीद के लिए खरमास समाप्त होने तक रुकने की सलाह देते हैं। यदि रुकना सम्भव न हो तो कुल-पण्डित "
              "कोई उपयुक्त दिन बता सकते हैं; रोज़ की ख़रीदारी में कोई बाधा नहीं है।")),
            (("Can griha pravesh or marriage be done in Kharmas?", "क्या खरमास में गृह प्रवेश या विवाह हो सकता है?"),
             ("Traditionally no; both wait for the Sun to leave Dhanu or Meena. Our vivah and griha pravesh muhurat "
              "pages list only the dates after Kharmas.",
              "परम्परा से नहीं; दोनों के लिए सूर्य के धनु या मीन से निकलने की प्रतीक्षा की जाती है। हमारे विवाह और गृह प्रवेश "
              "मुहूर्त पेज केवल खरमास के बाद की तिथियाँ दिखाते हैं।")),
        ],
        "muhurat": ["vivah", "griha-pravesh", "mundan", "vehicle", "property"],
    },
}
