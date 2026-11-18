# core/utils/milan_hi.py
"""
Hindi for the Kundali Milan report (/hi/kundali-milan/). The calculation code writes its findings in English; when
the request comes from the Hindi site, translate_report() rewrites every displayed string of the JSON report.

Fixed words (yoni, varna, gana, rajju ...) are looked up in TERMS; planets, signs and nakshatras use the site's |t
filter. Sentences are matched against TEMPLATES: English patterns whose {PL1}, {SIGN1}, {NAK1}, {N1} ... slots are
filled back into the Hindi pattern, each slot translated on its own. A string that matches nothing stays English and
is reported by untranslated(), which KundaliMilanHindiTests uses to fail when new English text appears.
"""
import re

from django.utils import translation

from ..templatetags.vp import t as _t

TERMS = {
    # yoni (koota table, Sanskrit) and the animals named in Yoni Dosha reasons
    "Ashwa": "अश्व", "Gaja": "गज", "Gau": "गौ", "Mahisha": "महिष", "Marjara": "मार्जार", "Mesh": "मेष",
    "Mriga": "मृग", "Mushaka": "मूषक", "Nakul": "नकुल", "Sarpa": "सर्प", "Shwan": "श्वान", "Singha": "सिंह",
    "Vanara": "वानर", "Vyagrah": "व्याघ्र",
    "Horse": "अश्व", "Elephant": "गज", "Sheep": "मेष", "Goat": "मेष", "Serpent": "सर्प", "Snake": "सर्प",
    "Dog": "श्वान", "Cat": "मार्जार", "Rat": "मूषक", "Cow": "गौ", "Buffalo": "महिष", "Tiger": "व्याघ्र",
    "Deer": "मृग", "Monkey": "वानर", "Mongoose": "नकुल", "Lion": "सिंह",
    # varna, vashya, gana, nadi, rajju
    "Brahmin": "ब्राह्मण", "Kshatriya": "क्षत्रिय", "Vaishya": "वैश्य", "Shudra": "शूद्र",
    "Chatushpada": "चतुष्पद", "Jalchar": "जलचर", "Keeta": "कीट", "Nara": "नर", "Vanacara": "वनचर",
    "Deva": "देव", "Manushya": "मनुष्य", "Rakshasa": "राक्षस",
    "Aadi": "आदि", "Madhya": "मध्य", "Antya": "अन्त्य",
    "Kantha": "कण्ठ", "Kati": "कटि", "Nabhi": "नाभि", "Pada": "पाद", "Shiro": "शिरो",
    "Nadi": "नाड़ी", "Rajju": "रज्जु", "Vedha": "वेध", "Bhakoot": "भकूट", "Gana": "गण", "Yoni": "योनि",
    # graha maitri relationship, overall status, severity
    "Mutual Friends": "परस्पर मित्र", "Mutual Enemies": "परस्पर शत्रु", "Both Neutral": "दोनों सम",
    "Neutral": "सम", "Mixed (Friend-Neutral)": "मिश्रित (मित्र-सम)", "Mixed (Friend-Enemy)": "मिश्रित (मित्र-शत्रु)",
    "excellent": "उत्तम", "good": "शुभ", "average": "मध्यम", "poor": "कम",
    "high": "अधिक", "medium": "मध्यम", "low": "कम",
    "Lagna": "लग्न", "Boy": "वर", "Girl": "वधू",
}

_LIMITS = {
    "Only the Moon can be known from a name, so this is a Moon-to-Moon match of the eight kootas.":
        "नाम से केवल चन्द्रमा का पता चलता है, इसलिए यह आठ कूटों का चन्द्र-से-चन्द्र मिलान है।",
    "A name gives one of the four padas of a nakshatra, and spellings differ, so the score is indicative.":
        "नाम नक्षत्र के चार में से एक चरण बताता है, और वर्तनी अलग-अलग होती है, इसलिए अंक संकेत मात्र हैं।",
    "Mangal dosha, lagna, navamsha, dashas and the other planets cannot be checked.":
        "मंगल दोष, लग्न, नवांश, दशा और अन्य ग्रह नहीं जाँचे जा सकते।",
}

# (English pattern, Hindi pattern). Slots: PL planet, SIGN sign, NAK nakshatra, N number, Y yoni animal,
# RJ rajju name, GANA gana, LIST comma-separated dosha names. Numbered so Hindi may reorder them.
TEMPLATES = [
    # ---- overall verdict
    ("🎉 Excellent Compatibility! No major doshas found. This indicates a very favorable match for marriage.",
     "🎉 उत्तम मेल! कोई बड़ा दोष नहीं मिला। विवाह के लिए यह बहुत अनुकूल मेल है।"),
    ("✅ Good Compatibility! Minor doshas present but overall favorable. Consider simple remedies if needed.",
     "✅ अच्छा मेल! कुछ छोटे दोष हैं, पर कुल मिलाकर अनुकूल। आवश्यकता हो तो सरल उपाय कर सकते हैं।"),
    ("⚠️ Moderate Compatibility. Some doshas present. Recommended to consult with an astrologer for detailed analysis and remedies.",
     "⚠️ मध्यम मेल। कुछ दोष हैं। विस्तृत विश्लेषण और उपायों के लिए किसी ज्योतिषी से परामर्श करें।"),
    ("✅ {N1}/{N2} gunas: an acceptable match, above the traditional minimum of {N3}, with no serious dosha found in what was checked.",
     "✅ {N1}/{N2} गुण: स्वीकार्य मेल, परम्परागत न्यूनतम {N3} से अधिक, और जाँची गई बातों में कोई गम्भीर दोष नहीं मिला।"),
    ("⚠️ {N1}/{N2} gunas, but uncancelled {LIST1} Dosha present. See the remedies below and consult an acharya before deciding.",
     "⚠️ {N1}/{N2} गुण, पर {LIST1} दोष बिना परिहार के है। नीचे दिए उपाय देखें और निर्णय से पहले आचार्य जी से परामर्श करें।"),
    ("❌ Only {N1}/{N2} gunas match - below the traditional minimum of {N3}. Marriage is generally not advised without a detailed chart analysis and remedies.",
     "❌ केवल {N1}/{N2} गुण मिलते हैं - परम्परागत न्यूनतम {N3} से कम। विस्तृत कुंडली विश्लेषण और उपायों के बिना सामान्यतः विवाह की सलाह नहीं दी जाती।"),
    ("Remedies are traditional upayas; have them performed through a qualified acharya after a full chart reading.",
     "ये पारम्परिक उपाय हैं; पूरी कुंडली देखने के बाद किसी योग्य आचार्य से ही करवाएँ।"),
    # ---- dosha summary badges
    ("Partner{N1} Manglik", "साथी {N1} मांगलिक"),
    ("Boy: {X1}", "वर: {X1}"),
    ("Girl: {X1}", "वधू: {X1}"),
    ("Nadi Dosha present", "नाड़ी दोष है"), ("Bhakoot Dosha present", "भकूट दोष है"),
    ("Gana Dosha present", "गण दोष है"), ("Yoni Dosha present", "योनि दोष है"),
    ("Rajju Dosha present", "रज्जु दोष है"), ("Vedha Dosha present", "वेध दोष है"),
    # ---- titles
    ("Angarak Dosha", "अंगारक दोष"), ("Grahan Dosha", "ग्रहण दोष"), ("Guru Chandal Dosha", "गुरु चाण्डाल दोष"),
    ("Kaal Sarp Dosha", "काल सर्प दोष"), ("Kemadruma Yoga", "केमद्रुम योग"), ("Pitra Dosha", "पितृ दोष"),
    ("Shrapit Dosha", "शापित दोष"), ("Vish Yoga", "विष योग"), ("Gana Dosha", "गण दोष"), ("Yoni Dosha", "योनि दोष"),
    ("Rajju Dosha", "रज्जु दोष"), ("Vedha Dosha", "वेध दोष"), ("Mahendra Koota", "महेन्द्र कूट"),
    ("Stree Dirgha", "स्त्री दीर्घ"), ("Temperament mismatch (Gana Dosha)", "स्वभाव में अन्तर (गण दोष)"),
    ("Gana compatible", "गण अनुकूल"),
    # ---- Nadi
    ("✅ No Nadi Dosha: Different Nadi indicates good health compatibility for prospective children.",
     "✅ नाड़ी दोष नहीं: अलग नाड़ी सन्तान के स्वास्थ्य के लिए अच्छी अनुकूलता दर्शाती है।"),
    ("❌ Nadi Dosha Present: Same Nadi indicates potential health compatibility issues. Consider consulting an astrologer.",
     "❌ नाड़ी दोष है: एक ही नाड़ी स्वास्थ्य सम्बन्धी अनुकूलता में कमी दर्शा सकती है। किसी ज्योतिषी से परामर्श कर लें।"),
    ("Different Nadi → no dosha", "अलग नाड़ी → दोष नहीं"),
    ("Same Nadi → strong Nadi Dosha", "एक ही नाड़ी → प्रबल नाड़ी दोष"),
    ("Same {PL1} sign but different nakshatras - Nadi Dosha cancelled",
     "एक ही {PL1} राशि पर अलग नक्षत्र - नाड़ी दोष निरस्त"),
    ("Same nakshatra but different {PL1} signs - Nadi Dosha cancelled",
     "एक ही नक्षत्र पर अलग {PL1} राशि - नाड़ी दोष निरस्त"),
    ("Same nakshatra in different padas - Nadi Dosha cancelled", "एक ही नक्षत्र के अलग चरण - नाड़ी दोष निरस्त"),
    ("Nadi Dosha Nivaran puja with Maha Mrityunjaya jaap ({N1} lakh) by the couple's families",
     "दोनों परिवारों द्वारा महामृत्युंजय जाप ({N1} लाख) सहित नाड़ी दोष निवारण पूजा"),
    ("Daan of gold Nadi (a gold serpent / gold coin), grains and clothes to a Brahmin",
     "ब्राह्मण को स्वर्ण नाड़ी (सोने का नाग / सोने का सिक्का), अन्न और वस्त्र का दान"),
    ("Not applicable if the dosha is cancelled (same rashi with different nakshatra, same nakshatra with different rashi or pada)",
     "दोष निरस्त हो तो लागू नहीं (एक राशि पर अलग नक्षत्र, या एक नक्षत्र पर अलग राशि या चरण)"),
    ("Wearing a mangal sutra blessed with Mrityunjaya mantra; Shiva abhishek on Mondays",
     "मृत्युंजय मन्त्र से अभिमन्त्रित मंगलसूत्र धारण करना; सोमवार को शिव अभिषेक"),
    # ---- Bhakoot
    ("✅ No Bhakoot Dosha: Good score ({N1}/{N2}) indicates harmony in relationship and financial matters.",
     "✅ भकूट दोष नहीं: अच्छे अंक ({N1}/{N2}) सम्बन्ध और आर्थिक मामलों में सामंजस्य दर्शाते हैं।"),
    ("✅ Bhakoot Dosha was indicated but has been cancelled due to strong planetary friendship (Graha Maitri: {N1}/{N2}). This is favorable.",
     "✅ भकूट दोष बन रहा था, पर ग्रहों की प्रबल मित्रता (ग्रह मैत्री: {N1}/{N2}) से निरस्त हो गया है। यह अनुकूल है।"),
    ("⚠️ Bhakoot Dosha Present: Potential challenges in mutual understanding and prosperity. Graha Maitri score ({N1}/{N2}) is below cancellation threshold.",
     "⚠️ भकूट दोष है: आपसी समझ और समृद्धि में कुछ चुनौतियाँ हो सकती हैं। ग्रह मैत्री के अंक ({N1}/{N2}) परिहार की सीमा से कम हैं।"),
    ("Bhakoot score {N1} > {N2} → no dosha", "भकूट अंक {N1} > {N2} → दोष नहीं"),
    ("Bhakoot score {N1} → potential dosha", "भकूट अंक {N1} → सम्भावित दोष"),
    ("Graha Maitri {N1} ≥ {N2} → Bhakoot dosha cancelled", "ग्रह मैत्री {N1} ≥ {N2} → भकूट दोष निरस्त"),
    ("Graha Maitri {N1} < {N2} → dosha not cancelled", "ग्रह मैत्री {N1} < {N2} → दोष निरस्त नहीं"),
    ("Usually considered cancelled when the {PL1}-sign lords are the same or friends (strong Graha Maitri)",
     "जब दोनों {PL1} राशियों के स्वामी एक हों या मित्र हों (प्रबल ग्रह मैत्री), तो सामान्यतः निरस्त माना जाता है"),
    ("Recite mantras of both {PL1}-sign lords; donate items of the lords on their weekdays",
     "दोनों {PL1} राशियों के स्वामियों के मन्त्र जपें; उनके वार पर उनसे सम्बन्धित वस्तुओं का दान करें"),
    ("Donate wheat and jaggery ({PL1}) or rice and milk ({PL2}); {PL3}-{PL4} mantra jaap",
     "गेहूँ और गुड़ ({PL1}) या चावल और दूध ({PL2}) का दान; {PL3}-{PL4} मन्त्र जाप"),
    ("Donate red lentils and avoid anger-driven decisions; Mangal and {PL1} mantra jaap",
     "लाल मसूर का दान करें और क्रोध में निर्णय न लें; मंगल और {PL1} मन्त्र जाप"),
    # ---- Gana
    ("Boy {GANA1} gana, girl {GANA2} gana", "वर {GANA1} गण, वधू {GANA2} गण"),
    ("{PL1}-sign lords are friendly - Gana Dosha cancelled", "{PL1} राशियों के स्वामी मित्र हैं - गण दोष निरस्त"),
    ("Gana Dosha shanti puja; worship of Lord Ganesha with Ganapati Atharvashirsha",
     "गण दोष शान्ति पूजा; गणपति अथर्वशीर्ष के साथ भगवान गणेश की उपासना"),
    ("Recite Durga Saptashati or Navarna mantra for the Rakshasa-gana partner",
     "राक्षस गण वाले साथी के लिए दुर्गा सप्तशती या नवार्ण मन्त्र का पाठ"),
    ("If proceeding, perform Navagraha shanti and Vishnu Sahasranama path together",
     "आगे बढ़ें तो नवग्रह शान्ति और विष्णु सहस्रनाम पाठ साथ में करें"),
    # ---- Yoni
    ("Boy {Y1} yoni, girl {Y2} yoni - sworn enemies", "वर {Y1} योनि, वधू {Y2} योनि - परस्पर शत्रु योनि"),
    ("Boy {Y1} yoni, girl {Y2} yoni", "वर {Y1} योनि, वधू {Y2} योनि"),
    ("Yoni Dosha is mild - worship of the couple's Ishta Devata and Navagraha shanti",
     "योनि दोष हल्का है - दम्पति के इष्ट देवता की उपासना और नवग्रह शान्ति"),
    ("Donate food to the animal of the enemy yoni (e.g. feed cows, dogs) on auspicious days",
     "शुभ दिनों में शत्रु योनि के पशु को भोजन दें (जैसे गाय, कुत्ते को खिलाएँ)"),
    # ---- Rajju
    ("Boy {RJ1} Rajju, girl {RJ2} Rajju", "वर {RJ1} रज्जु, वधू {RJ2} रज्जु"),
    ("Same Rajju (Kantha): traditionally linked with the wife's health", "एक ही रज्जु (कण्ठ): परम्परा में पत्नी के स्वास्थ्य से जोड़ा गया"),
    ("Same Rajju (Kati): traditionally linked with financial strain", "एक ही रज्जु (कटि): परम्परा में आर्थिक कठिनाई से जोड़ा गया"),
    ("Same Rajju (Nabhi): traditionally linked with concerns about children", "एक ही रज्जु (नाभि): परम्परा में सन्तान सम्बन्धी चिन्ता से जोड़ा गया"),
    ("Same Rajju (Pada): traditionally linked with travel and time apart", "एक ही रज्जु (पाद): परम्परा में यात्रा / दूरी से जोड़ा गया"),
    ("Same Rajju (Shiro): traditionally linked with the husband's health", "एक ही रज्जु (शिरो): परम्परा में पति के स्वास्थ्य से जोड़ा गया"),
    ("Considered serious in South Indian tradition; cancelled if Rashi lords are friends or Rajju is 'Arohana' type per local custom",
     "दक्षिण भारतीय परम्परा में इसे गम्भीर माना जाता है; राशि स्वामी मित्र हों या स्थानीय रीति के अनुसार रज्जु 'आरोहण' प्रकार की हो तो निरस्त"),
    ("{PL1}-sign lords friendly / same nakshatra - Rajju Dosha mitigated",
     "{PL1} राशियों के स्वामी मित्र / एक ही नक्षत्र - रज्जु दोष कम"),
    ("Rajju Dosha shanti puja with Mrityunjaya homa", "मृत्युंजय होम सहित रज्जु दोष शान्ति पूजा"),
    # ---- Vedha
    ("{NAK1} and {NAK2} - no Vedha", "{NAK1} और {NAK2} - वेध नहीं"),
    ("{NAK1} and {NAK2} obstruct each other (Vedha pair)", "{NAK1} और {NAK2} परस्पर वेध करते हैं (वेध युग्म)"),
    ("Vedha Dosha has no lesser remedy - traditionally the match is avoided",
     "वेध दोष का कोई छोटा उपाय नहीं बताया गया - परम्परा में ऐसे मिलान से बचा जाता है"),
    # ---- Mahendra / Stree Dirgha
    ("Boy's star is {N1} from girl's - favourable", "वर का नक्षत्र वधू के नक्षत्र से {N1}वाँ है - अनुकूल"),
    ("Boy's star is {N1} from girl's - not favourable", "वर का नक्षत्र वधू के नक्षत्र से {N1}वाँ है - अनुकूल नहीं"),
    ("Boy's star is {N1} from girl's - less than {N2}", "वर का नक्षत्र वधू के नक्षत्र से {N1}वाँ है - {N2} से कम"),
    ("Mahendra is a positive koota; absence only reduces support for progeny and prosperity - Santana Gopala mantra may be recited",
     "महेन्द्र एक शुभ कूट है; इसके न होने से केवल सन्तान और समृद्धि का सहारा कुछ कम होता है - सन्तान गोपाल मन्त्र का जाप कर सकते हैं"),
    ("Absence of Stree Dirgha reduces the bride's wellbeing in the marriage - Lakshmi-Narayana puja is advised",
     "स्त्री दीर्घ न होने से विवाह में वधू की कुशलता का सहारा कुछ कम होता है - लक्ष्मी-नारायण पूजा की सलाह दी जाती है"),
    # ---- Mangal
    ("⚠️ Mangal Dosha is present. Consult an astrologer for detailed analysis.",
     "⚠️ मंगल दोष है। विस्तृत विश्लेषण के लिए किसी ज्योतिषी से परामर्श करें।"),
    ("✅ Mangal Dosha is cancelled due to strong planetary influences in both charts.",
     "✅ दोनों कुंडलियों में ग्रहों के प्रबल प्रभाव से मंगल दोष निरस्त है।"),
    ("✅ Both partners have Mangal Dosha, but it cancels out mutually due to favorable planetary combinations.",
     "✅ दोनों साथियों में मंगल दोष है, पर अनुकूल ग्रह योगों से यह परस्पर निरस्त हो जाता है।"),
    ("Both partners are Manglik, so the dosha balances out (Mangal samya).",
     "दोनों साथी मांगलिक हैं, इसलिए दोष सन्तुलित हो जाता है (मंगल साम्य)।"),
    ("For {SIGN1} Lagna, {PL1} is the yogakaraka and does not harm, which cancels Mangal Dosha.",
     "{SIGN1} लग्न के लिए {PL1} योगकारक है और हानि नहीं करता, इससे मंगल दोष निरस्त होता है।"),
    ("{PL1} aspects {PL2} ({PL3} is {N1}th from {PL4}), which cancels Mangal Dosha.",
     "{PL1} की {PL2} पर दृष्टि है ({PL3}, {PL4} से {N1}वें भाव में), इससे मंगल दोष निरस्त होता है।"),
    ("{PL1} in the Lagna protects the chart, which cancels Mangal Dosha.",
     "लग्न में {PL1} कुंडली की रक्षा करता है, इससे मंगल दोष निरस्त होता है।"),
    ("{PL1} in {SIGN1} ({SIGN2} or {SIGN3}) does not give the dosha, which cancels Mangal Dosha.",
     "{SIGN1} ({SIGN2} या {SIGN3}) में {PL1} दोष नहीं देता, इससे मंगल दोष निरस्त होता है।"),
    ("{PL1} in {SIGN1} in house {N1} is a listed exception, which cancels Mangal Dosha.",
     "{N1}वें भाव में {SIGN1} में {PL1} शास्त्रों में बताया गया अपवाद है, इससे मंगल दोष निरस्त होता है।"),
    ("{PL1} is combust, {N1}° from the {PL2}: this reduces Mangal Dosha but does not cancel it.",
     "{PL1} अस्त है, {PL2} से {N1}° पर: इससे मंगल दोष कम होता है, पर निरस्त नहीं।"),
    ("{PL1} is debilitated in {SIGN1} and weak: this reduces Mangal Dosha but does not cancel it.",
     "{PL1} {SIGN1} में नीच और निर्बल है: इससे मंगल दोष कम होता है, पर निरस्त नहीं।"),
    ("{PL1} is exalted in {SIGN1}, which cancels Mangal Dosha.", "{PL1} {SIGN1} में उच्च है, इससे मंगल दोष निरस्त होता है।"),
    ("{PL1} is in its own sign {SIGN1}, which cancels Mangal Dosha.",
     "{PL1} अपनी राशि {SIGN1} में है, इससे मंगल दोष निरस्त होता है।"),
    ("{PL1} is with {PL2} (Chandra-Mangal yoga): this reduces Mangal Dosha but does not cancel it.",
     "{PL1} {PL2} के साथ है (चन्द्र-मंगल योग): इससे मंगल दोष कम होता है, पर निरस्त नहीं।"),
    ("{PL1} is with {PL2}, which cancels Mangal Dosha.", "{PL1} {PL2} के साथ है, इससे मंगल दोष निरस्त होता है।"),
    ("Mangal Dosha Nivaran puja at Mangalnath (Ujjain) or a Navagraha temple",
     "मंगलनाथ (उज्जैन) या किसी नवग्रह मन्दिर में मंगल दोष निवारण पूजा"),
    ("Marriage is commonly advised with another Manglik, or after age {N1} when the dosha weakens",
     "सामान्यतः किसी मांगलिक से विवाह, या {N1} वर्ष की आयु के बाद जब दोष कमज़ोर हो जाता है, की सलाह दी जाती है"),
    ("Recite Hanuman Chalisa / Sundarkand on Tuesdays; Mangal Beej mantra 'Om Kraam Kreem Kraum Sah Bhaumaya Namah' ({N1},{N2} jaap)",
     "मंगलवार को हनुमान चालीसा / सुन्दरकाण्ड पाठ; मंगल बीज मन्त्र 'ॐ क्रां क्रीं क्रौं सः भौमाय नमः' ({N1},{N2} जाप)"),
    ("{SIGN1} Vivah (symbolic marriage with a clay pot) or Ark/Peepal vivah before the wedding",
     "विवाह से पहले {SIGN1} विवाह (मिट्टी के कलश से प्रतीकात्मक विवाह) या अर्क/पीपल विवाह"),
    ("Kumbh Vivah (symbolic marriage with a clay pot) or Ark/Peepal vivah before the wedding",
     "विवाह से पहले कुम्भ विवाह (मिट्टी के कलश से प्रतीकात्मक विवाह) या अर्क/पीपल विवाह"),
    ("Tuesday vrat; donate red lentils (masoor), jaggery and red cloth",
     "मंगलवार का व्रत; लाल मसूर, गुड़ और लाल वस्त्र का दान"),
    # ---- individual doshas: reasons
    ("All seven planets are hemmed between {PL1} and {PL2}", "सातों ग्रह {PL1} और {PL2} के बीच घिरे हैं"),
    ("{PL1} and {PL2} together in the {N1}th house", "{N1}वें भाव में {PL1} और {PL2} साथ हैं"),
    ("{PL1}/{PL2} in the {N1}th house (house of ancestors)", "{N1}वें भाव (पितृ भाव) में {PL1}/{PL2}"),
    ("{PL1} conjunct {PL2}/{PL3}", "{PL1} की {PL2}/{PL3} से युति"),
    ("{PL1} conjunct {PL2}", "{PL1} की {PL2} से युति"),
    ("No planet in the {N1}nd or {N2}th from the {PL1} (or with it)",
     "{PL1} से {N1}वें या {N2}वें भाव में (या उसके साथ) कोई ग्रह नहीं"),
    ("Benefic in a kendra cancels Kemadruma", "केन्द्र में शुभ ग्रह केमद्रुम को निरस्त करता है"),
    ("Dosha is reduced when {PL1}-sign lords are friends or Bhakoot / Nadi are favourable",
     "जब {PL1} राशियों के स्वामी मित्र हों या भकूट / नाड़ी अनुकूल हों, तो दोष कम होता है"),
    # ---- individual doshas: remedies
    ("Angarak Dosha puja at Mangalnath, Ujjain; Hanuman worship on Tuesdays",
     "मंगलनाथ, उज्जैन में अंगारक दोष पूजा; मंगलवार को हनुमान उपासना"),
    ("Grahan Dosha shanti puja on an eclipse day or Amavasya", "ग्रहण के दिन या अमावस्या को ग्रहण दोष शान्ति पूजा"),
    ("Guru Chandal Dosha nivaran puja; Brihaspati mantra 'Om Brim Brihaspataye Namah' on Thursdays",
     "गुरु चाण्डाल दोष निवारण पूजा; गुरुवार को बृहस्पति मन्त्र 'ॐ बृं बृहस्पतये नमः'"),
    ("Kaal Sarp Dosha nivaran puja at Trimbakeshwar (Nashik), Ujjain or Kalahasti",
     "त्र्यम्बकेश्वर (नासिक), उज्जैन या कालहस्ती में काल सर्प दोष निवारण पूजा"),
    ("Rudrabhishek on Nag Panchami / Mahashivratri; offer a silver Naag-Nagin pair",
     "नाग पंचमी / महाशिवरात्रि पर रुद्राभिषेक; चाँदी का नाग-नागिन जोड़ा अर्पित करें"),
    ("Recite Sarpa Suktam and Maha Mrityunjaya mantra; feed birds and fish",
     "सर्प सूक्त और महामृत्युंजय मन्त्र का पाठ; पक्षियों और मछलियों को दाना डालें"),
    ("Light a mustard-oil lamp under a Peepal tree on Saturdays; Hanuman Chalisa daily",
     "शनिवार को पीपल के नीचे सरसों के तेल का दीपक जलाएँ; प्रतिदिन हनुमान चालीसा"),
    ("Water a Peepal tree on Saturdays and light a sesame-oil lamp", "शनिवार को पीपल में जल दें और तिल के तेल का दीपक जलाएँ"),
    ("Narayan Bali, Tripindi Shraddha or Pind daan at Gaya, Varanasi (Pishach Mochan) or Trimbakeshwar",
     "गया, वाराणसी (पिशाच मोचन) या त्र्यम्बकेश्वर में नारायण बलि, त्रिपिण्डी श्राद्ध या पिण्ड दान"),
    ("Offer water and black sesame to ancestors on every Amavasya; feed crows, cows and Brahmins during Pitru Paksha",
     "हर अमावस्या को पितरों को जल और काले तिल अर्पित करें; पितृ पक्ष में कौओं, गायों और ब्राह्मणों को भोजन कराएँ"),
    ("Godaan (donation of a cow) or its equivalent seva at a gaushala", "गोदान या गौशाला में उसके बराबर सेवा"),
    ("Recite Hanuman Chalisa; donate black sesame and rice", "हनुमान चालीसा का पाठ; काले तिल और चावल का दान"),
    ("Shrapit Dosha shanti with Shani-{PL1} mantra jaap (Om Sham Shanaishcharaya Namah / Om Raam Rahave Namah)",
     "शनि-{PL1} मन्त्र जाप से शापित दोष शान्ति (ॐ शं शनैश्चराय नमः / ॐ रां राहवे नमः)"),
    ("Shiva-Parvati puja and Rudrabhishek on Mondays", "सोमवार को शिव-पार्वती पूजा और रुद्राभिषेक"),
    ("Surya / Chandra mantra jaap (Aditya Hridayam for {PL1}, Om Som Somaya Namah for {PL2})",
     "सूर्य / चन्द्र मन्त्र जाप ({PL1} के लिए आदित्य हृदय, {PL2} के लिए ॐ सों सोमाय नमः)"),
    ("Thursday vrat, donate yellow items, turmeric and chana dal; respect elders and teachers",
     "गुरुवार का व्रत, पीली वस्तुएँ, हल्दी और चना दाल दान करें; बड़ों और गुरुजनों का सम्मान करें"),
    ("Vish Yoga shanti: Shiva abhishek with milk on Mondays and Shani mantra on Saturdays",
     "विष योग शान्ति: सोमवार को दूध से शिव अभिषेक और शनिवार को शनि मन्त्र"),
    ("Wear silver, keep a silver square in the wallet, offer milk to Shivling on Mondays",
     "चाँदी धारण करें, बटुए में चाँदी का चौकोर टुकड़ा रखें, सोमवार को शिवलिंग पर दूध चढ़ाएँ"),
    ("Worship Lord Shiva and Mother Parvati on Mondays; Chandra mantra 'Om Shraam Shreem Shraum Sah Chandraya Namah'",
     "सोमवार को भगवान शिव और माता पार्वती की उपासना; चन्द्र मन्त्र 'ॐ श्रां श्रीं श्रौं सः चन्द्राय नमः'"),
]

_PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
_SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn",
          "Aquarius", "Pisces"]
_SLOT = {
    "PL": "|".join(_PLANETS), "SIGN": "|".join(_SIGNS), "NAK": r"[A-Z][A-Za-z ]+?", "N": r"\d+(?:\.\d+)?",
    "Y": r"[A-Z][a-z]+", "RJ": r"[A-Z][a-z]+", "GANA": "Deva|Manushya|Rakshasa", "LIST": r"[A-Za-z, ]+?",
    "X": r".+",
}


def _compile(pattern):
    out, pos = [], 0
    for m in re.finditer(r"\{([A-Z]+)(\d+)\}", pattern):
        out.append(re.escape(pattern[pos:m.start()]))
        out.append(f"(?P<{m.group(1)}{m.group(2)}>{_SLOT[m.group(1)]})")
        pos = m.end()
    out.append(re.escape(pattern[pos:]))
    return re.compile("^" + "".join(out) + "$")


_COMPILED = [(_compile(en), hi) for en, hi in TEMPLATES]
_missed = set()


def term(word):
    """One word or name in Hindi: our own TERMS, then the site's planet/sign/nakshatra filter."""
    if word in TERMS:
        return TERMS[word]
    hi = _t(word)
    # |t also swaps known words inside longer text; accept only a complete translation.
    return hi if hi != word and not re.search(r"[A-Za-z]", hi) else word


def sentence(text):
    """A report sentence in Hindi, or the English unchanged (and remembered) if no pattern fits."""
    if not isinstance(text, str) or not text.strip():
        return text
    if text in _LIMITS:
        return _LIMITS[text]
    if text in TERMS or term(text) != text:
        return term(text)
    for rx, hi in _COMPILED:
        m = rx.match(text)
        if m:
            def fill(slot):
                name = slot.group(1)
                value = m.group(name)
                kind = re.match(r"[A-Z]+", name).group(0)
                if kind == "N":
                    return value
                if kind == "LIST":
                    return ", ".join(term(v.strip()) for v in value.split(","))
                if kind == "X":
                    return sentence(value)
                return term(value)
            return re.sub(r"\{([A-Z]+\d+)\}", fill, hi)
    _missed.add(text)
    return text


# Report fields that hold data words or sentences. Names, places, coordinates, time zones and times stay as given.
_KEEP = {"name", "birth_place", "coordinates", "timezone", "mode", "zodiac_sign_end_time", "asc_zodiac_end_time",
         "sign_degree", "retrograde_status", "description"}


def _walk(node, key=None):
    if isinstance(node, dict):
        return {k: (v if k in _KEEP else _walk(v, k)) for k, v in node.items()}
    if isinstance(node, list):
        return [_walk(v, key) for v in node]
    if isinstance(node, str):
        return sentence(node)
    return node


def translate_report(data):
    """The whole compatibility JSON with every displayed string in Hindi (call only for the Hindi site)."""
    with translation.override("hi"):
        out = _walk(data)
    # Planet keys stay English: the page script looks planets up by these keys.
    return out


# Fixed words the page script writes itself, (English, Hindi). Sent to the page as JSON by milan_labels().
LABELS = {
    "groom": ("Groom", "वर"), "bride": ("Bride", "वधू"), "pada": ("pada", "चरण"), "rashi": ("rashi", "राशि"),
    "na": ("N/A", "उपलब्ध नहीं"), "noData": ("Data not available", "जानकारी उपलब्ध नहीं"), "retro": ("R", "व"),
    "noResults": ("No results found", "कोई परिणाम नहीं मिला"),
    "suggestError": ("Error loading suggestions", "सुझाव लोड नहीं हो सके"),
    "excellent": ("Excellent Match! This combination is highly favorable for a successful marriage.",
                  "उत्तम मेल! सफल विवाह के लिए यह जोड़ी बहुत अनुकूल है।"),
    "good": ("Good Match! The couple shares strong compatibility and understanding.",
             "अच्छा मेल! दोनों में अच्छी अनुकूलता और समझ है।"),
    "average": ("Average Match. The relationship may require mutual understanding and effort.",
                "मध्यम मेल। सम्बन्ध में आपसी समझ और प्रयास की आवश्यकता हो सकती है।"),
    "poor": ("Below the traditional benchmark. Look at the individual kootas and both full charts with your family "
             "pandit before deciding.",
             "परम्परागत न्यूनतम से कम। निर्णय से पहले अपने परिवार के पंडित जी के साथ अलग-अलग कूट और दोनों पूरी "
             "कुंडलियाँ देखें।"),
    "kootas": ({"varna": ["Varna", "Spiritual compatibility & Ego levels"],
                "vashya": ["Vashya", "Mutual attraction & Control"],
                "tara": ["Tara", "Birth star compatibility & Health"],
                "yoni": ["Yoni", "Physical & Sexual compatibility"],
                "graha_maitri": ["Graha Maitri", "Mental compatibility & Friendship"],
                "gana": ["Gana", "Temperament & Behavior"],
                "bhakoot": ["Bhakoot", "Love & Financial prosperity"],
                "nadi": ["Nadi", "Health & Progeny"]},
               {"varna": ["वर्ण", "आध्यात्मिक अनुकूलता और अहं"],
                "vashya": ["वश्य", "आपसी आकर्षण और प्रभाव"],
                "tara": ["तारा", "जन्म नक्षत्र की अनुकूलता और स्वास्थ्य"],
                "yoni": ["योनि", "शारीरिक अनुकूलता"],
                "graha_maitri": ["ग्रह मैत्री", "मानसिक अनुकूलता और मित्रता"],
                "gana": ["गण", "स्वभाव और व्यवहार"],
                "bhakoot": ["भकूट", "प्रेम और आर्थिक समृद्धि"],
                "nadi": ["नाड़ी", "स्वास्थ्य और सन्तान"]}),
    "doshaNames": ({"mangal": "Mangal", "nadi": "Nadi", "bhakoot": "Bhakoot", "gana": "Gana", "yoni": "Yoni",
                    "rajju": "Rajju", "vedha": "Vedha", "mahendra": "Mahendra", "stree_dirgha": "Stree Dirgha"},
                   {"mangal": "मंगल", "nadi": "नाड़ी", "bhakoot": "भकूट", "gana": "गण", "yoni": "योनि",
                    "rajju": "रज्जु", "vedha": "वेध", "mahendra": "महेन्द्र", "stree_dirgha": "स्त्री दीर्घ"}),
    "dosha": ("Dosha", "दोष"), "cancelled": ("Cancelled", "निरस्त"), "present": ("Present", "है"), "ok": ("OK", "ठीक"),
    "no": ("No", "कोई नहीं:"), "doshasFound": ("Doshas Found:", "पाए गए दोष:"),
    "remedies": ("Remedies (Upaya):", "उपाय:"), "details": ("Details:", "विवरण:"),
    "groomChart": ("Groom's Chart:", "वर की कुंडली:"), "brideChart": ("Bride's Chart:", "वधू की कुंडली:"),
    "mitigatedBy": ("Mitigated by", "कम करने वाला ग्रह:"),
    "groomChartIndividual": ("Groom's chart: individual doshas", "वर की कुंडली: व्यक्तिगत दोष"),
    "brideChartIndividual": ("Bride's chart: individual doshas", "वधू की कुंडली: व्यक्तिगत दोष"),
    "noIndividual": ("No Kaal Sarp, Pitra, Grahan, Guru Chandal, Shrapit, Angarak, Vish or Kemadruma dosha found.",
                     "काल सर्प, पितृ, ग्रहण, गुरु चाण्डाल, शापित, अंगारक, विष या केमद्रुम दोष नहीं मिला।"),
    "cancelledShort": (" (cancelled)", " (निरस्त)"),
    "notLoaded": ("Page not loaded properly. Please refresh.", "पेज ठीक से लोड नहीं हुआ। कृपया दोबारा खोलें।"),
    "calculating": ("Calculating...", "गणना हो रही है..."),
    "fillIn": ("Please fill in", "कृपया भरें:"),
    "fields": ({"person1_birth_date": "groom's date of birth", "person1_birth_time": "groom's time of birth",
                "person1_birth_place": "groom's place of birth", "person2_birth_date": "bride's date of birth",
                "person2_birth_time": "bride's time of birth", "person2_birth_place": "bride's place of birth"},
               {"person1_birth_date": "वर की जन्म तिथि", "person1_birth_time": "वर का जन्म समय",
                "person1_birth_place": "वर का जन्म स्थान", "person2_birth_date": "वधू की जन्म तिथि",
                "person2_birth_time": "वधू का जन्म समय", "person2_birth_place": "वधू का जन्म स्थान"}),
    "busy": ("Too many requests. Please wait a minute and try again.",
             "बहुत अधिक अनुरोध। कृपया एक मिनट रुककर फिर प्रयास करें।"),
    "serverError": ("Something went wrong. Please check the details and try again.",
                    "कुछ गड़बड़ हुई। कृपया विवरण जाँचकर फिर प्रयास करें।"),
    "error": ("Error: ", "त्रुटि: "),
}


def milan_labels():
    """LABELS in the active language, plus planet names, for the Kundali Milan page script."""
    hi = (translation.get_language() or "").startswith("hi")
    out = {k: (v[1] if hi else v[0]) for k, v in LABELS.items()}
    with translation.override("hi" if hi else "en"):
        out["planets"] = {p: (term(p) if hi else p) for p in _PLANETS}
    return out


def hindi_report(view):
    """View decorator: on the Hindi site, a successful compatibility JSON response is returned in Hindi."""
    import json
    from functools import wraps
    from django.http import JsonResponse

    @wraps(view)
    def wrapped(request, *args, **kwargs):
        response = view(request, *args, **kwargs)
        if (translation.get_language() or "").startswith("hi") and response.status_code == 200                 and response.get("Content-Type", "").startswith("application/json"):
            data = json.loads(response.content)
            if data.get("success"):
                return JsonResponse(translate_report(data))
        return response
    return wrapped


def untranslated():
    """English strings seen since start-up that no pattern matched (for tests)."""
    return set(_missed)
