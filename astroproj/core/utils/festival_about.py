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
    "makar-sankranti": {
        "sections": [
            (("What is Makar Sankranti?", "मकर संक्रान्ति क्या है?"),
             ("Makar Sankranti is the day the Sun enters Makara (Capricorn) in the sidereal zodiac. Panchangs count "
              "Uttarayan, the Sun's auspicious northern course, from this moment, and the winter Kharmas ends with it. "
              "Because it follows the Sun and not the Moon, it falls on almost the same date every year: 14 or 15 "
              "January. It is one festival with many names - Khichdi in Uttar Pradesh and Bihar, Pongal in Tamil "
              "Nadu, Uttarayan in Gujarat, Magh Bihu in Assam - and Lohri is kept on its eve.",
              "मकर संक्रान्ति वह दिन है जब सूर्य निरयण राशिचक्र में मकर राशि में प्रवेश करते हैं। पंचांग इसी क्षण से सूर्य के शुभ "
              "उत्तरायण की गणना करते हैं, और शीत ऋतु का खरमास इसी के साथ समाप्त होता है। यह चन्द्रमा से नहीं, सूर्य से चलता है, "
              "इसलिए लगभग हर वर्ष एक ही तारीख़ को आता है: 14 या 15 जनवरी। एक ही पर्व के अनेक नाम हैं - उत्तर प्रदेश और बिहार "
              "में खिचड़ी, तमिलनाडु में पोंगल, गुजरात में उत्तरायण, असम में माघ बिहू - और इसकी पूर्व सन्ध्या पर लोहड़ी मनाई "
              "जाती है।")),
            (("14 or 15 January?", "14 या 15 जनवरी?"),
             ("The festival is kept on the day of its punya kaal, the holy hours after the Sun's entry. If the Sun enters "
              "Makara during the day, the punya kaal is that same day. If it enters after sunset, Kashi panchangs, "
              "following Nirnaya Sindhu, keep the punya kaal on the next morning. That is why some years show 14 "
              "January and others 15 January; the exact entry time is given above. Any snan and daan done with "
              "devotion on either day brings its blessing.",
              "पर्व उस दिन मनाया जाता है जिस दिन इसका पुण्य काल हो, यानी सूर्य के प्रवेश के बाद के पवित्र घण्टे। यदि सूर्य दिन में "
              "मकर में प्रवेश करें तो पुण्य काल उसी दिन होता है। यदि सूर्यास्त के बाद प्रवेश हो तो काशी के पंचांग, निर्णय सिन्धु के "
              "अनुसार, पुण्य काल अगले दिन प्रातः मानते हैं। इसी कारण किसी वर्ष 14 जनवरी और किसी वर्ष 15 जनवरी होती है; प्रवेश "
              "का ठीक समय ऊपर दिया है। श्रद्धा से किसी भी दिन किया गया स्नान और दान फलदायी है।")),
            (("Snan, daan and khichdi", "स्नान, दान और खिचड़ी"),
             ("Bathe early, in the Ganga if you can - at Kashi, at the Prayag Sangam where the Magh Mela begins, or at "
              "Gangasagar - and offer arghya to Surya with water, red flowers, til and gur. Til (sesame) and gur "
              "(jaggery) are the gifts of the day: til-gur laddoos, khichdi of new rice and urad dal, warm clothes and "
              "blankets are given to the needy and to brahmins, and the same khichdi is eaten at home. At Gorakhpur, "
              "khichdi is offered to Guru Gorakhnath. Kites fill the sky in Gujarat and Rajasthan.",
              "सुबह जल्दी स्नान करें, हो सके तो गंगा में - काशी में, प्रयाग संगम पर जहाँ माघ मेला शुरू होता है, या गंगासागर में - "
              "और जल, लाल फूल, तिल और गुड़ से सूर्य को अर्घ्य दें। तिल और गुड़ इस दिन के उपहार हैं: तिल-गुड़ के लड्डू, नए चावल "
              "और उड़द दाल की खिचड़ी, गरम कपड़े और कम्बल ज़रूरतमन्दों और ब्राह्मणों को दिए जाते हैं, और वही खिचड़ी घर में भी खाई "
              "जाती है। गोरखपुर में गुरु गोरखनाथ को खिचड़ी चढ़ाई जाती है। गुजरात और राजस्थान में आकाश पतंगों से भर जाता है।")),
            (("Uttarayan and the end of Kharmas", "उत्तरायण और खरमास की समाप्ति"),
             ("With the Sun in Makara the winter Kharmas is over, and wedding, griha pravesh and mundan muhurats begin "
              "again in the following days, once the tithi, nakshatra and lagna also suit. Bhishma Pitamah waited on "
              "his bed of arrows for Uttarayan, and the season is held to be especially good for new beginnings and "
              "for spiritual effort.",
              "सूर्य के मकर में आते ही शीत ऋतु का खरमास समाप्त हो जाता है, और अगले दिनों में, जब तिथि, नक्षत्र और लग्न भी "
              "अनुकूल हों, विवाह, गृह प्रवेश और मुण्डन के मुहूर्त फिर शुरू हो जाते हैं। भीष्म पितामह ने शरशय्या पर उत्तरायण की "
              "प्रतीक्षा की थी, और यह समय नए शुभारम्भ और साधना के लिए विशेष अच्छा माना जाता है।")),
            (("A Kumbh and Magh Mela snan", "कुम्भ और माघ मेले का स्नान"),
             ("Makar Sankranti is the first great snan of the Prayag Magh Mela every year, and of every Kumbh held at "
              "Prayagraj and Haridwar in the winter. In 2027 it opens the Haridwar Ardh Kumbh.",
              "मकर संक्रान्ति हर वर्ष प्रयाग माघ मेले का और सर्दियों में प्रयागराज और हरिद्वार में लगने वाले हर कुम्भ का पहला "
              "बड़ा स्नान है। 2027 में इसी से हरिद्वार अर्ध कुम्भ आरम्भ होता है।")),
        ],
        "faq": [
            (("Why is Makar Sankranti on 14 or 15 January every year?", "मकर संक्रान्ति हर वर्ष 14 या 15 जनवरी को ही क्यों होती है?"),
             ("Because it follows the Sun's entry into Makara, which the solar year brings round to the same date. The "
              "date moves forward by about one day in seventy years: a century ago it fell on 13-14 January.",
              "क्योंकि यह सूर्य के मकर प्रवेश से चलती है, जो सौर वर्ष में लगभग उसी तारीख़ को आता है। यह तारीख़ लगभग सत्तर वर्ष "
              "में एक दिन आगे खिसकती है: सौ वर्ष पहले यह 13-14 जनवरी को पड़ती थी।")),
            (("What should be donated on Makar Sankranti?", "मकर संक्रान्ति पर क्या दान करें?"),
             ("Til, gur, khichdi (rice and urad dal), ghee, warm clothes and blankets are traditional. Give what you "
              "can, with a glad heart.",
              "तिल, गुड़, खिचड़ी (चावल और उड़द दाल), घी, गरम कपड़े और कम्बल परम्परागत दान हैं। जो सम्भव हो, प्रसन्न मन से दें।")),
            (("Do weddings start after Makar Sankranti?", "क्या मकर संक्रान्ति के बाद विवाह शुरू होते हैं?"),
             ("Yes. Kharmas ends when the Sun enters Makara, and wedding muhurats resume in the following days on dates "
              "where the tithi, nakshatra and lagna also suit; see the vivah muhurat page.",
              "हाँ। सूर्य के मकर में आते ही खरमास समाप्त होता है, और अगले दिनों में जहाँ तिथि, नक्षत्र और लग्न भी अनुकूल हों, "
              "विवाह मुहूर्त फिर शुरू हो जाते हैं; विवाह मुहूर्त पेज देखें।")),
            (("Why is khichdi eaten on Makar Sankranti?", "मकर संक्रान्ति पर खिचड़ी क्यों खाते हैं?"),
             ("The new rice and urad dal of the season are cooked together and first offered and given away, then eaten "
              "as prasad. It is light, warming food for the cold, which is why the festival itself is called Khichdi "
              "in Uttar Pradesh and Bihar.",
              "मौसम के नए चावल और उड़द दाल साथ पकाकर पहले भोग लगाया और दान किया जाता है, फिर प्रसाद के रूप में खाया जाता है। "
              "यह ठण्ड में हल्का और गरम भोजन है, इसीलिए उत्तर प्रदेश और बिहार में पर्व को ही खिचड़ी कहते हैं।")),
        ],
        "muhurat": ["vivah", "griha-pravesh", "mundan"],
    },
    "mauni-amavasya": {
        "sections": [
            (("What is Mauni Amavasya?", "मौनी अमावस्या क्या है?"),
             ("Mauni Amavasya is the Amavasya of Magha, the holiest month for river snan. Its name comes from mauna, "
              "silence: the day is kept with a vow of silence, and many traditions also remember it as the birthday of "
              "Manu, the first man. It is the greatest snan of the year at the Prayag Sangam, and Kashi panchangs keep "
              "it on the day the Amavasya prevails at sunrise.",
              "मौनी अमावस्या माघ मास की अमावस्या है, और माघ नदी स्नान का सबसे पवित्र महीना है। इसका नाम मौन से है: यह दिन मौन "
              "व्रत के साथ मनाया जाता है, और अनेक परम्पराएँ इसे आदि पुरुष मनु का जन्मदिन भी मानती हैं। यह प्रयाग संगम पर वर्ष "
              "का सबसे बड़ा स्नान है, और काशी के पंचांग इसे उस दिन रखते हैं जिस दिन सूर्योदय पर अमावस्या हो।")),
            (("Why silence?", "मौन क्यों?"),
             ("Speech spends the mind's energy, and a day of silence gathers it back for japa and meditation. The "
              "tradition is to bathe in silence, ideally before sunrise, and to stay silent through the puja. If a full "
              "day of silence does not suit your work or family, keep it until after your snan and puja, and speak "
              "gently and little for the rest of the day; the bhava is what matters.",
              "बोलने में मन की ऊर्जा ख़र्च होती है, और मौन का एक दिन उसे जप और ध्यान के लिए फिर से समेट देता है। परम्परा है कि "
              "स्नान मौन रहकर, हो सके तो सूर्योदय से पहले, किया जाए और पूजा तक मौन रखा जाए। यदि पूरे दिन का मौन काम या परिवार "
              "के कारण सम्भव न हो, तो स्नान और पूजा तक मौन रखें और बाकी दिन कम और मधुर बोलें; भाव ही मुख्य है।")),
            (("Snan, tarpan and daan", "स्नान, तर्पण और दान"),
             ("Bathe in the Ganga or add Ganga jal to your bath water at home, offer arghya to Surya, and, as on every "
              "Amavasya, offer tarpan of water and til to your ancestors. Til, gur, blankets, warm clothes, food and a "
              "meal for a cow are the usual daan. Many keep a phalahar fast until the snan and puja are over.",
              "गंगा में स्नान करें या घर पर नहाने के पानी में गंगाजल मिलाएँ, सूर्य को अर्घ्य दें, और हर अमावस्या की तरह पितरों को "
              "जल और तिल से तर्पण दें। तिल, गुड़, कम्बल, गरम कपड़े, अन्न और गाय को भोजन सामान्य दान हैं। बहुत से लोग स्नान और "
              "पूजा पूरी होने तक फलाहार व्रत रखते हैं।")),
            (("The chief snan of the Kumbh", "कुम्भ का प्रमुख स्नान"),
             ("At the Prayag Magh Mela and at every Prayagraj Kumbh, Mauni Amavasya draws the largest crowd of all: the "
              "main Amrit Snan of the 2025 Maha Kumbh was on Mauni Amavasya. In 2027 it is also a snan day of the "
              "Haridwar Ardh Kumbh. On such a day the smaller ghats carry the same river and the same punya, with far "
              "less crowd.",
              "प्रयाग माघ मेले और प्रयागराज के हर कुम्भ में मौनी अमावस्या पर सबसे अधिक भीड़ होती है: 2025 के महाकुम्भ का प्रमुख "
              "अमृत स्नान मौनी अमावस्या को ही था। 2027 में यह हरिद्वार अर्ध कुम्भ का भी स्नान पर्व है। ऐसे दिन छोटे घाटों पर भी "
              "वही नदी और वही पुण्य है, और भीड़ बहुत कम।")),
            (("When it falls on a Monday or Saturday", "जब सोमवार या शनिवार को पड़े"),
             ("A Mauni Amavasya on a Monday is a Somvati Amavasya, held especially good for Shiva puja and for the "
              "long life of the husband. On a Saturday it is a Shanishchari Amavasya, a good day for Shani puja, til "
              "and oil daan and Hanuman Chalisa.",
              "सोमवार को पड़ने वाली मौनी अमावस्या सोमवती अमावस्या होती है, जो शिव पूजा और पति की दीर्घायु के लिए विशेष शुभ मानी "
              "जाती है। शनिवार को यह शनैश्चरी अमावस्या होती है, जो शनि पूजा, तिल और तेल के दान और हनुमान चालीसा के लिए "
              "अच्छा दिन है।")),
        ],
        "faq": [
            (("Is it compulsory to stay silent all day on Mauni Amavasya?", "क्या मौनी अमावस्या पर पूरे दिन मौन रखना ज़रूरी है?"),
             ("No. A full day's silence is the ideal, but silence until the snan and puja are done is the common "
              "practice, and speaking little and kindly for the rest of the day keeps the spirit of the vow.",
              "नहीं। पूरे दिन का मौन आदर्श है, पर स्नान और पूजा पूरी होने तक मौन रखना आम परम्परा है, और बाकी दिन कम और मधुर "
              "बोलना भी व्रत की भावना को बनाए रखता है।")),
            (("What should be donated on Mauni Amavasya?", "मौनी अमावस्या पर क्या दान करें?"),
             ("Til, gur, blankets and warm clothes, grain, and food for cows and the needy. Til offered in tarpan to the "
              "ancestors is also traditional.",
              "तिल, गुड़, कम्बल और गरम कपड़े, अन्न, और गायों तथा ज़रूरतमन्दों के लिए भोजन। पितरों को तर्पण में तिल अर्पित करना "
              "भी परम्परा है।")),
            (("Can I do the snan at home?", "क्या स्नान घर पर कर सकते हैं?"),
             ("Yes. Add a few drops of Ganga jal to your bath water before sunrise, remember the Sangam or Ganga in your "
              "sankalp, offer arghya to Surya and give daan. Elderly and unwell family members can join fully this way.",
              "हाँ। सूर्योदय से पहले नहाने के पानी में गंगाजल की कुछ बूँदें मिलाएँ, संकल्प में संगम या गंगा का स्मरण करें, सूर्य "
              "को अर्घ्य दें और दान करें। घर के बुज़ुर्ग और अस्वस्थ सदस्य भी इसी तरह पूरी तरह जुड़ सकते हैं।")),
        ],
        "muhurat": [],
    },
}
