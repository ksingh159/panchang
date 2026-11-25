# core/utils/rashifal_text.py
"""
Wording for the daily rashifal (core/utils/rashifal.py). Every entry is an (English, Hindi) pair.

The engine decides; this file only words the decision. Several variants per slot are picked by a hash of
(date, rashi, slot), so the same sky always gives the same text and consecutive days read differently.
Tone (owner's rule): reassure, never frighten; say "may", "likely", "a good day to". Never predict illness,
accidents or loss as facts. Readings need an acharya's review before they are treated as final.
"""

# Overall headline by star rating (2-5)
HEADLINES = {
    5: [("An excellent day: things are likely to go your way.", "बहुत अच्छा दिन: काम आपके पक्ष में जाने की सम्भावना है।"),
        ("A very favourable day for new efforts.", "नए प्रयासों के लिए बहुत अनुकूल दिन।"),
        ("A bright day: make the most of it.", "उजला दिन: इसका पूरा लाभ उठाएँ।")],
    4: [("A good day with steady support.", "अच्छा दिन, लगातार साथ मिलता रहेगा।"),
        ("A favourable day; most things should move smoothly.", "अनुकूल दिन; ज़्यादातर काम आसानी से चलने चाहिए।"),
        ("A positive day for work and relationships.", "काम और रिश्तों के लिए सकारात्मक दिन।")],
    3: [("A mixed day: steady effort works best.", "मिला-जुला दिन: लगातार मेहनत सबसे अच्छी रहेगी।"),
        ("An average day; plan well and stay flexible.", "सामान्य दिन; अच्छी योजना बनाएँ और लचीले रहें।"),
        ("A balanced day with a few slow spots.", "सन्तुलित दिन, कहीं-कहीं थोड़ी धीमी गति।")],
    2: [("A day for patience: keep things simple.", "धैर्य का दिन: काम सरल रखें।"),
        ("A quiet day; go slowly and take care.", "शान्त दिन; धीरे चलें और ध्यान रखें।"),
        ("A day to rest and recharge rather than push.", "ज़ोर लगाने के बजाय आराम करने और ऊर्जा जुटाने का दिन।")],
}

# The Moon's house from the rashi (Chandra gochar): one short line, shown under the headline
MOON_HOUSE = {
    1: ("The Moon is in your own sign: comfort and a clear mind.", "चन्द्रमा आपकी ही राशि में: सुख और साफ़ मन।"),
    2: ("The Moon in your 2nd house: watch spending and speak softly.", "चन्द्रमा दूसरे भाव में: खर्च पर ध्यान दें और मीठा बोलें।"),
    3: ("The Moon in your 3rd house: courage and effort pay off.", "चन्द्रमा तीसरे भाव में: साहस और मेहनत का फल।"),
    4: ("The Moon in your 4th house: the mind may feel busy; time at home helps.", "चन्द्रमा चौथे भाव में: मन व्यस्त रह सकता है; घर पर समय बिताना अच्छा।"),
    5: ("The Moon in your 5th house: good for study and ideas, not for risks.", "चन्द्रमा पाँचवें भाव में: पढ़ाई और विचारों के लिए अच्छा, जोखिम के लिए नहीं।"),
    6: ("The Moon in your 6th house: obstacles give way.", "चन्द्रमा छठे भाव में: बाधाएँ हटेंगी।"),
    7: ("The Moon in your 7th house: good for partnerships and people.", "चन्द्रमा सातवें भाव में: साझेदारी और मेल-जोल के लिए अच्छा।"),
    8: ("The Moon in your 8th house: go slowly and avoid risks.", "चन्द्रमा आठवें भाव में: धीरे चलें और जोखिम से बचें।"),
    9: ("The Moon in your 9th house: good for faith; luck moves slowly.", "चन्द्रमा नौवें भाव में: आस्था के लिए अच्छा; भाग्य धीमा।"),
    10: ("The Moon in your 10th house: work gets done and noticed.", "चन्द्रमा दसवें भाव में: काम पूरा होगा और सराहा जाएगा।"),
    11: ("The Moon in your 11th house: gains and good news.", "चन्द्रमा ग्यारहवें भाव में: लाभ और शुभ समाचार।"),
    12: ("The Moon in your 12th house: rest, give and recharge.", "चन्द्रमा बारहवें भाव में: आराम, दान और नई ऊर्जा।"),
}

# The Moon is in a good house but another graha in its vedha house blocks it
MOON_VEDHA = ("The Moon is in your {n} house, usually a good place, but {planet} in your {v} house blocks it (vedha): results need more effort today.",
              "चन्द्रमा आपके {n} भाव में हैं, जो सामान्यतः शुभ है, पर आपके {v} भाव में {planet} इसे रोक रहे हैं (वेध): आज फल के लिए अधिक प्रयास चाहिए।")


# Area readings by level: good / mixed / care, three variants each
AREAS = {
    "career": {
        "good": [("Work is likely to move well today; a good time to present ideas or take the lead on a task.",
                  "आज काम अच्छी तरह चलने की सम्भावना है; अपने विचार रखने या किसी काम की कमान सँभालने का अच्छा समय।"),
                 ("Efforts at work tend to be noticed today. Follow up on pending matters.",
                  "आज काम में की गई मेहनत पर ध्यान जाएगा। अटके मामलों को आगे बढ़ाएँ।"),
                 ("A productive day for work; decisions taken with care are likely to hold.",
                  "काम के लिए उपयोगी दिन; सोच-समझकर लिए फ़ैसले टिकने की सम्भावना है।")],
        "mixed": [("Work goes on at a steady pace; some replies may take longer than you hope.",
                   "काम सामान्य गति से चलेगा; कुछ जवाब उम्मीद से देर से आ सकते हैं।"),
                  ("An ordinary day at work. Finish what is in hand before starting something new.",
                   "काम में सामान्य दिन। नया शुरू करने से पहले हाथ का काम पूरा करें।"),
                  ("Progress is possible, but plan the day and keep some buffer for delays.",
                   "प्रगति हो सकती है, पर दिन की योजना बनाएँ और देरी के लिए थोड़ी गुंजाइश रखें।")],
        "care": [("Work may feel slow or scattered; stick to routine tasks and keep notes.",
                  "काम धीमा या बिखरा लग सकता है; रोज़ के काम करें और बातें लिखते चलें।"),
                 ("Double-check papers and messages today, and keep big decisions for a calmer day.",
                  "आज काग़ज़ और सन्देश दोबारा जाँचें, और बड़े फ़ैसले किसी शान्त दिन के लिए रखें।"),
                 ("Patience helps at work today; avoid arguments and give yourself extra time.",
                  "आज काम में धैर्य काम आएगा; बहस से बचें और अपने लिए अतिरिक्त समय रखें।")],
    },
    "money": {
        "good": [("Money matters look supportive; a reasonable day for planned purchases or collecting dues.",
                  "धन के मामले अनुकूल दिखते हैं; सोची हुई खरीदारी या बकाया वसूलने के लिए ठीक दिन।"),
                 ("Gains through effort or contacts are possible today.", "आज मेहनत या जान-पहचान से लाभ हो सकता है।"),
                 ("A steady day for finances; savings and sensible investments are favoured.",
                  "धन के लिए स्थिर दिन; बचत और समझदारी भरा निवेश अनुकूल है।")],
        "mixed": [("Spending and income may roughly balance; keep a little margin.",
                   "खर्च और आमदनी लगभग बराबर रह सकते हैं; थोड़ी गुंजाइश रखें।"),
                  ("Fine for routine expenses; give bigger financial decisions some more thought.",
                   "रोज़ के खर्च के लिए ठीक; बड़े आर्थिक फ़ैसलों पर थोड़ा और सोचें।"),
                  ("Avoid lending or speculative bets today; steady saving is the safer path.",
                   "आज उधार देने या सट्टे जैसे दाँव से बचें; धीरे-धीरे बचत करना सुरक्षित रास्ता है।")],
        "care": [("Unplanned expenses are possible; keep track and avoid impulse buying.",
                  "बिना सोचे खर्च हो सकते हैं; हिसाब रखें और जल्दबाज़ी की खरीदारी से बचें।"),
                 ("Not the best day for risky investments or standing guarantee for others.",
                  "जोखिम भरे निवेश या किसी की ज़मानत लेने के लिए यह सबसे अच्छा दिन नहीं है।"),
                 ("Go easy on spending today and postpone what can wait.", "आज खर्च कम रखें और जो रुक सकता है उसे टाल दें।")],
    },
    "family": {
        "good": [("Warm time with family or your partner is likely; a good day for plans together.",
                  "परिवार या जीवनसाथी के साथ अच्छा समय बीतने की सम्भावना है; साथ में योजना बनाने का अच्छा दिन।"),
                 ("Relationships feel easy today; reach out to someone you have been meaning to call.",
                  "आज रिश्ते सहज रहेंगे; जिसे फ़ोन करने की सोच रहे थे, उससे बात कर लें।"),
                 ("Harmony at home is favoured; small gestures will be appreciated.",
                  "घर में मेल-जोल के योग; छोटी-छोटी बातों की भी सराहना होगी।")],
        "mixed": [("Family life is steady; listen first and small misunderstandings clear quickly.",
                   "पारिवारिक जीवन स्थिर है; पहले सुनें तो छोटी गलतफ़हमियाँ जल्दी दूर होंगी।"),
                  ("Give time to family matters that need attention; patience helps.",
                   "जिन पारिवारिक बातों पर ध्यान चाहिए, उन्हें समय दें; धैर्य काम आएगा।"),
                  ("An ordinary day at home; keep your words gentle.", "घर पर सामान्य दिन; अपनी बात नरमी से कहें।")],
        "care": [("Tempers may run short at home; choose kind words and avoid old arguments.",
                  "घर में गुस्सा जल्दी आ सकता है; प्यार भरे शब्द चुनें और पुरानी बहसों से बचें।"),
                 ("Someone close may need more patience from you today.", "आज किसी अपने को आपसे ज़्यादा धैर्य की ज़रूरत हो सकती है।"),
                 ("Keep expectations simple with family today; a quiet evening helps.",
                  "आज परिवार से उम्मीदें सरल रखें; शान्त शाम अच्छी रहेगी।")],
    },
    "health": {
        "good": [("Energy is likely to be good; a walk, yoga or exercise will feel rewarding.",
                  "ऊर्जा अच्छी रहने की सम्भावना है; सैर, योग या व्यायाम से अच्छा लगेगा।"),
                 ("You may feel fresh and active; keep meals on time to stay that way.",
                  "आप ताज़ा और सक्रिय महसूस कर सकते हैं; ऐसा बने रहने के लिए भोजन समय पर करें।"),
                 ("A good day to start a healthy routine.", "अच्छी दिनचर्या शुरू करने के लिए अच्छा दिन।")],
        "mixed": [("Energy may go up and down; rest when you need to.", "ऊर्जा ऊपर-नीचे हो सकती है; ज़रूरत हो तो आराम करें।"),
                  ("Eat light and on time, and keep water handy.", "हल्का और समय पर खाएँ, और पानी पास रखें।"),
                  ("Avoid overdoing it today; balance work with short breaks.", "आज ज़रूरत से ज़्यादा न करें; काम के बीच छोटे विराम लें।")],
        "care": [("Take things easy; rest well and avoid needless travel.", "आराम से चलें; अच्छी तरह आराम करें और बेवजह यात्रा से बचें।"),
                 ("Look after yourself today: sleep early and choose light food.", "आज अपना ध्यान रखें: जल्दी सोएँ और हल्का भोजन लें।"),
                 ("Go slowly and drive carefully; a calm routine suits the day.", "धीरे चलें और वाहन सावधानी से चलाएँ; शान्त दिनचर्या आज के लिए ठीक है।")],
    },
}

# Planet in a house from the rashi: what it supports (good) or asks for (care). {n} = ordinal house.
PLANET_LINES = {
    "Sun": (("The Sun in your {n} house supports authority: dealings with seniors and official work tend to go well.",
             "सूर्य आपके {n} भाव में अधिकार का साथ देते हैं: वरिष्ठों और सरकारी कामों में सफलता की सम्भावना।"),
            ("The Sun in your {n} house asks you to keep pride in check with seniors and to pace your energy.",
             "सूर्य आपके {n} भाव में: वरिष्ठों के साथ अहं से बचें और अपनी ऊर्जा सँभालकर खर्च करें।")),
    "Mars": (("Mars in your {n} house gives drive and courage; competitive work goes your way.",
              "मंगल आपके {n} भाव में जोश और साहस देते हैं; प्रतियोगिता वाले कामों में बढ़त।"),
             ("Mars in your {n} house can make tempers short; pause before you reply.",
              "मंगल आपके {n} भाव में गुस्सा जल्दी ला सकते हैं; जवाब देने से पहले रुकें।")),
    "Mercury": (("Mercury in your {n} house helps business, writing and quick decisions.",
                 "बुध आपके {n} भाव में व्यापार, लेखन और जल्दी फ़ैसलों में मदद करते हैं।"),
                ("Mercury in your {n} house: read messages and papers twice before you act.",
                 "बुध आपके {n} भाव में: कोई कदम उठाने से पहले सन्देश और काग़ज़ दो बार पढ़ें।")),
    "Jupiter": (("Jupiter in your {n} house supports growth, savings and good advice.",
                 "गुरु आपके {n} भाव में उन्नति, बचत और अच्छी सलाह का साथ देते हैं।"),
                ("Jupiter in your {n} house: growth is slower for now; lean on patience and the advice of elders.",
                 "गुरु आपके {n} भाव में: अभी उन्नति धीमी है; धैर्य और बड़ों की सलाह का सहारा लें।")),
    "Venus": (("Venus in your {n} house brings comfort, pleasant company and good buys.",
               "शुक्र आपके {n} भाव में सुख, अच्छी संगति और अच्छी खरीदारी देते हैं।"),
              ("Venus in your {n} house: keep spending on comforts and luxuries in check.",
               "शुक्र आपके {n} भाव में: सुख-सुविधा और विलासिता पर खर्च सीमित रखें।")),
    "Saturn": (("Saturn in your {n} house rewards steady, honest work.", "शनि आपके {n} भाव में लगातार, ईमानदार मेहनत का फल देते हैं।"),
               ("Saturn in your {n} house asks for patience and discipline; results come, but slowly.",
                "शनि आपके {n} भाव में धैर्य और अनुशासन माँगते हैं; फल मिलेगा, पर धीरे।")),
    "Rahu": (("Rahu in your {n} house can bring sudden openings, often through technology or people from afar.",
              "राहु आपके {n} भाव में अचानक अवसर दे सकते हैं, अक्सर तकनीक या दूर के लोगों से।"),
             ("Rahu in your {n} house: avoid shortcuts and check anything that sounds too good.",
              "राहु आपके {n} भाव में: शॉर्टकट से बचें और जो बहुत अच्छा लगे उसे परख लें।")),
    "Ketu": (("Ketu in your {n} house helps you let go of what is not needed and focus.",
              "केतु आपके {n} भाव में अनावश्यक चीज़ें छोड़ने और ध्यान केन्द्रित करने में मदद करते हैं।"),
             ("Ketu in your {n} house may leave you a little detached; stay present in conversations.",
              "केतु आपके {n} भाव में थोड़ी उदासीनता दे सकते हैं; बातचीत में पूरा ध्यान रखें।")),
}

# The Moon's company today (same sky for everyone)
MOON_WITH = {
    "Jupiter": ("The Moon travels with Jupiter today (Gaja Kesari in the sky): good for wisdom, worship and kind decisions.",
                "आज चन्द्रमा गुरु के साथ हैं (आकाश में गजकेसरी): ज्ञान, पूजा और उदार फ़ैसलों के लिए अच्छा।"),
    "Venus": ("The Moon is with Venus today: good for arts, comfort and pleasant company.",
              "आज चन्द्रमा शुक्र के साथ हैं: कला, सुख और अच्छी संगति के लिए अच्छा।"),
    "Mercury": ("The Moon is with Mercury today: quick thinking and good for trade and talks.",
                "आज चन्द्रमा बुध के साथ हैं: तेज़ सोच, व्यापार और बातचीत के लिए अच्छा।"),
    "Mars": ("The Moon is with Mars today: plenty of energy, but keep impatience in check.",
             "आज चन्द्रमा मंगल के साथ हैं: ऊर्जा भरपूर, पर अधीरता पर काबू रखें।"),
    "Saturn": ("The Moon is with Saturn today (Vish yoga in the sky): moods may feel heavy; a steady routine helps.",
               "आज चन्द्रमा शनि के साथ हैं (आकाश में विष योग): मन भारी लग सकता है; नियमित दिनचर्या मदद करेगी।"),
    "Rahu": ("The Moon is with Rahu today (Grahan yoga in the sky): avoid big decisions when unsure.",
             "आज चन्द्रमा राहु के साथ हैं (आकाश में ग्रहण योग): असमंजस में बड़े फ़ैसले न लें।"),
    "Ketu": ("The Moon is with Ketu today (Grahan yoga in the sky): a good day for prayer and quiet work.",
             "आज चन्द्रमा केतु के साथ हैं (आकाश में ग्रहण योग): प्रार्थना और शान्त काम के लिए अच्छा।"),
    "Sun": ("The Moon is close to the Sun (around Amavasya): keep the day simple and rest well.",
            "चन्द्रमा सूर्य के पास हैं (अमावस्या के आसपास): दिन सरल रखें और अच्छी तरह आराम करें।"),
}
JUPITER_ASPECTS_MOON = ("Jupiter's gaze falls on the Moon today, which softens the day's difficulties.",
                        "आज गुरु की दृष्टि चन्द्रमा पर है, जो दिन की कठिनाइयों को हल्का करती है।")
JUPITER_ASPECTS_RASHI = ("Jupiter's gaze falls on your sign: a protective influence through this period.",
                         "गुरु की दृष्टि आपकी राशि पर है: इस अवधि में रक्षा करने वाला प्रभाव।")
SATURN_ASPECTS_RASHI = ("Saturn's gaze falls on your sign: steady effort and patience are rewarded.",
                        "शनि की दृष्टि आपकी राशि पर है: लगातार मेहनत और धैर्य का फल मिलेगा।")
MARS_ASPECTS_RASHI = ("Mars's gaze falls on your sign: keep calm in heated moments.",
                      "मंगल की दृष्टि आपकी राशि पर है: गरम माहौल में शान्त रहें।")
VAKRI = ("{planet} is retrograde (vakri): matters it rules may need a second look.",
         "{planet} वक्री हैं: उनसे जुड़े मामलों पर दोबारा ध्यान दें।")

SHANI = {
    "sade": ("Shani is in your {n} house, part of Sade Sati: a season for patience, discipline and care with health and money, not for fear.",
             "शनि आपके {n} भाव में हैं, साढ़े साती का भाग: यह धैर्य, अनुशासन और स्वास्थ्य व धन में सावधानी का समय है, डरने का नहीं।"),
    "dhaiya": ("Shani is in your {n} house (Dhaiya): go steadily, keep commitments simple and look after your health.",
               "शनि आपके {n} भाव में हैं (ढैया): स्थिरता से चलें, ज़िम्मेदारियाँ सरल रखें और स्वास्थ्य का ध्यान रखें।"),
}

# Tarabalam: the day's nakshatra counted from the birth nakshatra
TARAS = {
    1: ("Janma", "जन्म", "mixed"), 2: ("Sampat", "सम्पत्", "good"), 3: ("Vipat", "विपत्", "care"),
    4: ("Kshema", "क्षेम", "good"), 5: ("Pratyari", "प्रत्यरि", "care"), 6: ("Sadhaka", "साधक", "good"),
    7: ("Vadha", "वध", "care"), 8: ("Mitra", "मित्र", "good"), 9: ("Ati-mitra", "अति-मित्र", "good"),
}
TARA_LEVEL = {"good": ("favourable", "अनुकूल"), "mixed": ("mixed", "मिश्रित"), "care": ("go gently", "सावधानी")}

SEGMENT = {
    "until": ("Until {time}", "{time} तक"), "from": ("From {time}", "{time} से"),
}
