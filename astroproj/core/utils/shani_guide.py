# core/utils/shani_guide.py
"""
What to expect and how to prepare for Shani Sade Sati and Dhaiya, for the PDF report.

There is no controlled statistical study of what people actually go through in these periods. The "what it
touches" lines are what the classical texts and practising astrologers commonly describe (they agree closely).
Every preparation step is chosen to be useful on its own (savings, health checks, skills, conduct), so it helps
whether or not the transit acts as described. Every entry is a pair (English, Hindi).
"""

HONEST = (
    "No controlled statistical study has measured what people actually go through in Sade Sati or Dhaiya. The "
    "difficulties listed here are what the classical texts and practising astrologers commonly describe, and they "
    "agree closely. So every step in this chapter is chosen to be useful on its own: savings, health checks, skills "
    "and good conduct help whether or not Saturn's transit acts as described.",
    "साढ़े साती या ढैया में लोगों के वास्तविक अनुभव का कोई नियंत्रित सांख्यिकीय अध्ययन उपलब्ध नहीं है। यहाँ दी गई "
    "कठिनाइयाँ वे हैं जो शास्त्र और अनुभवी ज्योतिषी सामान्यतः बताते हैं, और इनमें काफ़ी सहमति है। इसलिए इस अध्याय का "
    "हर सुझाव अपने-आप में उपयोगी चुना गया है: बचत, स्वास्थ्य जाँच, कौशल और अच्छा आचरण हर स्थिति में लाभ देते हैं, "
    "शनि का गोचर बताए अनुसार फल दे या न दे।",
)

TOUCHES = {
    "rising": ("Rising phase (Saturn in the 12th from the Moon): expenses rise, sleep and rest suffer, travel or a "
               "move away from home, and pressure on the father's health or on the family budget.",
               "आरोही चरण (शनि चन्द्र से बारहवें): खर्च बढ़ना, नींद और विश्राम में कमी, यात्रा या घर से दूर जाना, पिता के "
               "स्वास्थ्य या परिवार के बजट पर दबाव।"),
    "peak": ("Peak phase (Saturn over the Moon): the most demanding phase in most texts. Low mood and fatigue, "
             "slow promotions or setbacks at work, strain in close relationships, and more care needed for health.",
             "शिखर चरण (शनि चन्द्र पर): अधिकांश ग्रन्थों में सबसे कठिन चरण। मन उदास और थकान, काम में रुकावट या "
             "पदोन्नति में देरी, निकट सम्बन्धों में खिंचाव, और स्वास्थ्य पर अधिक ध्यान की आवश्यकता।"),
    "setting": ("Setting phase (Saturn in the 2nd from the Moon): money, savings, family and speech. Family "
                "disagreements and teeth, eye or face complaints are mentioned; it is also when lost ground is "
                "slowly recovered, and the gentlest phase in most accounts.",
                "अवरोही चरण (शनि चन्द्र से दूसरे): धन, बचत, परिवार और वाणी। पारिवारिक मतभेद और दाँत, आँख या चेहरे की "
                "तकलीफ़ बताई जाती है; इसी चरण में खोया हुआ धीरे-धीरे वापस मिलता है, और अधिकतर मतों में यह सबसे हल्का चरण है।"),
    "kantak": ("Kantak Shani (Saturn in the 4th from the Moon): home, mother, property, vehicles and peace of mind. "
               "House moves, repairs or property disputes, the mother's health, and a restless mind are mentioned.",
               "कण्टक शनि (शनि चन्द्र से चौथे): घर, माता, सम्पत्ति, वाहन और मन की शान्ति। घर बदलना, मरम्मत या "
               "सम्पत्ति विवाद, माता का स्वास्थ्य और मन की अशान्ति बताई जाती है।"),
    "ashtama": ("Ashtama Shani (Saturn in the 8th from the Moon): the stronger Dhaiya. Sudden events, long or "
                "hidden illness, accidents, debts and obstacles that delay work are mentioned.",
                "अष्टम शनि (शनि चन्द्र से आठवें): अधिक प्रभावी ढैया। आकस्मिक घटनाएँ, लम्बी या छिपी बीमारी, दुर्घटना, "
                "ऋण और काम में देरी करने वाली बाधाएँ बताई जाती हैं।"),
}

# Life stages: a child's period is felt mostly through the family; an adult's through work, money and marriage;
# an elder's through health. Texts do not separate men and women; where medicine does (bone loss), it is said.
STAGES = (
    (18, ("Childhood (under 18)", "बचपन (18 से कम)"),
     ("studies, routine, illness, and the family's health and money",
      "पढ़ाई, दिनचर्या, बीमारी, और परिवार का स्वास्थ्य व धन"),
     [("A fixed study routine; check progress every term and get help early if marks fall.",
       "पढ़ाई की निश्चित दिनचर्या; हर सत्र में प्रगति देखें और अंक घटें तो जल्दी सहायता लें।"),
      ("Regular check-ups, vaccinations, eyes and teeth; outdoor play and morning sun for strong bones.",
       "नियमित जाँच, टीके, आँख और दाँत; मज़बूत हड्डियों के लिए बाहर खेलना और सुबह की धूप।"),
      ("Calcium-rich food every day: milk, curd, paneer, ragi, sesame (til), green leafy vegetables.",
       "रोज़ कैल्शियम युक्त भोजन: दूध, दही, पनीर, रागी, तिल, हरी पत्तेदार सब्ज़ियाँ।"),
      ("Parents: keep an emergency fund and family health insurance in place before the period begins.",
       "माता-पिता: अवधि शुरू होने से पहले आपातकालीन कोष और पारिवारिक स्वास्थ्य बीमा तैयार रखें।"),
      ("Teach the child to share and help: feeding birds and animals, giving to those in need.",
       "बच्चे को बाँटना और सहायता करना सिखाएँ: पक्षियों व पशुओं को भोजन, ज़रूरतमन्दों को दान।")]),
    (35, ("Young adult (18 to 34)", "युवा (18 से 34)"),
     ("studies, first jobs, marriage and money habits", "पढ़ाई, पहली नौकरी, विवाह और धन की आदतें"),
     [("If a marriage is planned around this time, many families prefer to settle it before the period starts. "
       "If it falls inside, match the two charts (Kundali Milan) rather than simply avoid it.",
       "यदि इस समय के आसपास विवाह की योजना है, तो कई परिवार अवधि शुरू होने से पहले विवाह करना पसन्द करते हैं। यदि "
       "विवाह इसी अवधि में आए, तो टालने के बजाय दोनों कुण्डलियों का मिलान करवाएँ।"),
      ("Build skills and certificates before the period; keep your CV and contacts current, and do not quit a job "
       "without a written offer in hand.",
       "अवधि से पहले कौशल और प्रमाणपत्र बढ़ाएँ; बायोडाटा और सम्पर्क अद्यतन रखें, और हाथ में लिखित ऑफ़र के बिना नौकरी न छोड़ें।"),
      ("Save at least six months of expenses; avoid large loans, standing guarantee for others and speculative trading.",
       "कम से कम छह महीने के खर्च की बचत रखें; बड़े ऋण, दूसरों की ज़मानत और सट्टा व्यापार से बचें।"),
      ("Make exercise and sleep a habit; avoid alcohol, tobacco and risky driving.",
       "व्यायाम और नींद को आदत बनाएँ; शराब, तम्बाकू और जोखिम भरी ड्राइविंग से बचें।")]),
    (60, ("Middle years (35 to 59)", "मध्य आयु (35 से 59)"),
     ("career, loans, children's needs and parents' health", "करियर, ऋण, बच्चों की ज़रूरतें और माता-पिता का स्वास्थ्य"),
     [("Hold six to twelve months of expenses in reserve; take health and term insurance and cut debt before the "
       "period begins.",
       "छह से बारह महीने का खर्च सुरक्षित रखें; अवधि शुरू होने से पहले स्वास्थ्य और टर्म बीमा लें और ऋण घटाएँ।"),
      ("Keep job options open (updated profile, contacts, an offer or two in view); plan big job changes or a new "
       "business carefully, especially in the peak phase.",
       "नौकरी के विकल्प खुले रखें (अद्यतन प्रोफ़ाइल, सम्पर्क, एक-दो ऑफ़र नज़र में); बड़ा बदलाव या नया व्यापार, विशेषकर "
       "शिखर चरण में, सोच-समझकर करें।"),
      ("A yearly check-up: blood pressure, sugar, vitamin D, joints, teeth and bone density. Women lose bone faster "
       "after menopause, so calcium, vitamin D and weight-bearing exercise matter even more.",
       "हर वर्ष जाँच: रक्तचाप, शुगर, विटामिन D, जोड़, दाँत और हड्डियों का घनत्व। रजोनिवृत्ति के बाद महिलाओं की हड्डियाँ "
       "तेज़ी से कमज़ोर होती हैं, इसलिए कैल्शियम, विटामिन D और वज़न उठाने वाला व्यायाम और भी ज़रूरी है।"),
      ("Plan ahead for parents' medical costs and children's education fees.",
       "माता-पिता के इलाज और बच्चों की पढ़ाई के खर्च की पहले से योजना बनाएँ।")]),
    (200, ("Later years (60 and above)", "वृद्धावस्था (60 और अधिक)"),
     ("health, bones and joints, savings and loneliness", "स्वास्थ्य, हड्डियाँ और जोड़, बचत और अकेलापन"),
     [("Bones and joints: calcium, vitamin D, 15-20 minutes of morning sun, a daily walk and simple balance exercises.",
       "हड्डियाँ और जोड़: कैल्शियम, विटामिन D, सुबह 15-20 मिनट धूप, रोज़ टहलना और सरल संतुलन व्यायाम।"),
      ("Prevent falls at home: non-slip mats, night lights, grab rails in the bathroom.",
       "घर में गिरने से बचाव: फिसलन-रोधी चटाई, रात की रोशनी, स्नानघर में पकड़ने की रेलिंग।"),
      ("Keep medicines, check-ups, medical insurance, the will and property papers in order.",
       "दवाइयाँ, जाँच, चिकित्सा बीमा, वसीयत और सम्पत्ति के कागज़ व्यवस्थित रखें।"),
      ("Keep savings safe: avoid lending large sums and risky investments.",
       "बचत सुरक्षित रखें: बड़ी रकम उधार देने और जोखिम भरे निवेश से बचें।"),
      ("Stay connected: a daily routine, satsang, friends and family; these periods are linked with loneliness.",
       "जुड़े रहें: नियमित दिनचर्या, सत्संग, मित्र और परिवार; इन अवधियों को अकेलेपन से जोड़ा जाता है।")]),
)

PREPARE = (
    (("Money", "धन"),
     [("Build an emergency fund before the period starts and keep it untouched.",
       "अवधि शुरू होने से पहले आपातकालीन कोष बनाएँ और उसे न छुएँ।"),
      ("Avoid lending, standing guarantee, speculation and non-essential big purchases during the period.",
       "अवधि में उधार देना, ज़मानत लेना, सट्टा और अनावश्यक बड़ी खरीदारी से बचें।"),
      ("Keep taxes, contracts and loans clean and on time; Saturn is the planet of rules and accounts.",
       "कर, अनुबन्ध और ऋण साफ़ और समय पर रखें; शनि नियम और हिसाब का ग्रह है।")]),
    (("Work", "कार्य"),
     [("Be punctual and steady; the tradition says Saturn rewards patient, honest work and punishes shortcuts.",
       "समय के पाबन्द और स्थिर रहें; परम्परा कहती है शनि धैर्य और ईमानदार परिश्रम का फल देता है, शॉर्टकट का दण्ड।"),
      ("Keep a job offer or a fallback ready and your skills current before the peak phase.",
       "शिखर चरण से पहले एक ऑफ़र या विकल्प तैयार रखें और कौशल अद्यतन रखें।"),
      ("Respect your boss and seniors, and treat the people who work under you fairly.",
       "अपने अधिकारी और वरिष्ठों का सम्मान करें, और अपने अधीन काम करने वालों के साथ न्याय करें।")]),
    (("Health", "स्वास्थ्य"),
     [("Daily exercise and good posture; Saturn rules bones, joints, teeth and nerves.",
       "रोज़ व्यायाम और सही मुद्रा; शनि हड्डियों, जोड़ों, दाँतों और नसों का कारक है।"),
      ("Calcium and vitamin D: milk, curd, ragi, til, green leafy vegetables, and morning sun.",
       "कैल्शियम और विटामिन D: दूध, दही, रागी, तिल, हरी पत्तेदार सब्ज़ियाँ और सुबह की धूप।"),
      ("Sleep on time, avoid alcohol and tobacco, and get a yearly check-up.",
       "समय पर सोएँ, शराब और तम्बाकू से बचें, और हर वर्ष जाँच करवाएँ।")]),
    (("Family", "परिवार"),
     [("Respect and serve parents, grandparents, elders and your guru.",
       "माता-पिता, दादा-दादी, बड़ों और गुरु का सम्मान और सेवा करें।"),
      ("Speak gently in disagreements; the setting phase is linked with family disputes over money and words.",
       "मतभेद में नम्रता से बोलें; अवरोही चरण को धन और वाणी से जुड़े पारिवारिक विवादों से जोड़ा जाता है।")]),
    (("Good karma", "शुभ कर्म"),
     [("Pay workers, labourers and helpers fairly and on time, and help the elderly and disabled.",
       "मज़दूरों, कर्मचारियों और सहायकों को उचित और समय पर भुगतान करें, और वृद्धों व दिव्यांगों की सहायता करें।"),
      ("Feed dogs, crows and cows, especially on Saturdays; plant and care for trees.",
       "कुत्तों, कौओं और गायों को भोजन दें, विशेषकर शनिवार को; पेड़ लगाएँ और उनकी देखभाल करें।"),
      ("Start these habits before the period begins; the tradition counts steady good deeds, not a last-minute rush.",
       "ये आदतें अवधि शुरू होने से पहले अपनाएँ; परम्परा नियमित शुभ कर्म को महत्त्व देती है, अन्तिम समय की जल्दबाज़ी को नहीं।")]),
)

REMEDIES = [
    ("Hanuman Chalisa on Tuesdays and Saturdays.", "मंगलवार और शनिवार को हनुमान चालीसा।"),
    ("Shani mantra on Saturdays, 108 times: Om Sham Shanaishcharaya Namah.",
     "शनिवार को शनि मन्त्र 108 बार: ॐ शं शनैश्चराय नमः।"),
    ("On Saturdays give mustard oil, black sesame, black urad or warm clothes to the needy.",
     "शनिवार को ज़रूरतमन्दों को सरसों का तेल, काले तिल, काली उड़द या गर्म कपड़े दान करें।"),
    ("Light a sesame-oil lamp under a peepal tree on Saturday evenings.",
     "शनिवार की शाम पीपल के नीचे तिल के तेल का दीपक जलाएँ।"),
    ("Never wear a blue sapphire (neelam) without a full reading by a qualified acharya.",
     "योग्य आचार्य से पूरी कुण्डली दिखाए बिना नीलम कभी न पहनें।"),
]


def stage(age):
    """(label, focus, steps) for the life stage at ``age``."""
    for upto, label, focus, steps in STAGES:
        if age < upto:
            return label, focus, steps
    return STAGES[-1][1:]


def touches(period):
    """The 'what it touches' lines for one period from shani.lifetime()."""
    if period["key"] == "sade":
        return [TOUCHES[k] for k in ("rising", "peak", "setting")
                if any(ph["name"][0] == k for ph in period["phases"])]
    return [TOUCHES[period["key"]]]


def next_period(periods):
    """The running period, else the next one to come, else None."""
    return next((p for p in periods if p["running"]), None) or next((p for p in periods if not p["past"]), None)
