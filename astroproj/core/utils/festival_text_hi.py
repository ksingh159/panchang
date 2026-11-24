# core/utils/festival_text_hi.py
"""Hindi for the festival notes, date rules and puja-muhurat labels that festival_calculations and
festival_muhurat write in English. Exact sentences first, then patterns for the ones that carry a date or time."""
import re

from ..pdf.i18n import TERMS_HI

NOTES = {
    "Shiva puja at twilight.": "सन्ध्या के समय शिव पूजा।",
    "Vishnu puja and upvas.": "विष्णु पूजा और उपवास।",
    "Durga puja.": "दुर्गा पूजा।",
    "Pitru tarpan and daan.": "पितृ तर्पण और दान।",
    "Satyanarayan katha; snan-daan.": "सत्यनारायण कथा; स्नान-दान।",
    "Ganesha puja.": "गणेश पूजा।",
    "Ganesha vrat; break after moonrise.": "गणेश व्रत; चन्द्रोदय के बाद पारण।",
    "Monthly Shiva night.": "मासिक शिवरात्रि।",
    "Jalabhishek at Kashi Vishwanath.": "काशी विश्वनाथ में जलाभिषेक।",
    "Marriages, griha pravesh, mundan and new ventures are avoided.": "विवाह, गृह प्रवेश, मुण्डन और नए कार्य टाले जाते हैं।",
    "Nine nights of Durga upasana.": "दुर्गा उपासना की नौ रातें।",
    "Punjab harvest bonfire.": "पंजाब का फ़सल-उत्सव, अलाव के साथ।",
    "Silent Ganga snan; most important snan of Magha.": "मौन गंगा स्नान; माघ का सबसे महत्त्वपूर्ण स्नान।",
    "Saraswati puja; Panchami must prevail in Purvahna.": "सरस्वती पूजा; पूर्वाह्न में पंचमी होनी चाहिए।",
    "Tarpan for Bhishma Pitamah in Madhyahna.": "मध्याह्न में भीष्म पितामह का तर्पण।",
    "Surya jayanti; arghya to Surya at sunrise.": "सूर्य जयन्ती; सूर्योदय पर सूर्य को अर्घ्य।",
    "Ganga snan and daan; end of Magha snan / Kalpavas.": "गंगा स्नान और दान; माघ स्नान / कल्पवास की समाप्ति।",
    "Chaturdashi at Nishita kaal; night-long worship at Kashi Vishwanath.": "निशीथ काल में चतुर्दशी; काशी विश्वनाथ में रात भर पूजा।",
    "Eight days before Holi; auspicious ceremonies avoided.": "होली से पहले के आठ दिन; शुभ संस्कार टाले जाते हैं।",
    "Purnima in Pradosh, avoiding Bhadra (Vishti karana).": "प्रदोष में पूर्णिमा, भद्रा (विष्टि करण) को छोड़कर।",
    "Pratipada at sunrise; Hindu new year (Vikram Samvat), Gudi Padwa, Ugadi.": "सूर्योदय पर प्रतिपदा; हिन्दू नववर्ष (विक्रम संवत), गुड़ी पड़वा, उगादि।",
    "Navami in Madhyahna - the hour of Shri Rama's birth.": "मध्याह्न में नवमी - श्रीराम के जन्म का समय।",
    "Chaitra Purnima (North Indian tradition).": "चैत्र पूर्णिमा (उत्तर भारतीय परम्परा)।",
    "Tritiya in Purvahna; auspicious for gold, daan and new beginnings.": "पूर्वाह्न में तृतीया; सोना, दान और नए आरम्भ के लिए शुभ।",
    "Ganga's descent from Shiva's matted hair; Madhyahna puja.": "शिव की जटाओं से गंगा का अवतरण; मध्याह्न पूजा।",
    "Janaki jayanti; Madhyahna puja.": "जानकी जयन्ती; मध्याह्न पूजा।",
    "Chaturdashi at sunset (Sayankala).": "सूर्यास्त (सायंकाल) पर चतुर्दशी।",
    "Vaishakha Purnima - Buddha jayanti; Sarnath celebrations.": "वैशाख पूर्णिमा - बुद्ध जयन्ती; सारनाथ में उत्सव।",
    "Jyeshtha Amavasya (North Indian Purnimanta tradition).": "ज्येष्ठ अमावस्या (उत्तर भारतीय पूर्णिमान्त परम्परा)।",
    "Descent of Ganga; snan at Dashashwamedh ghat.": "गंगा अवतरण; दशाश्वमेध घाट पर स्नान।",
    "Ashadha Shukla Dwitiya.": "आषाढ़ शुक्ल द्वितीया।",
    "Shravana Shukla Tritiya.": "श्रावण शुक्ल तृतीया।",
    "Naga puja; Shravana Shukla Panchami (Kashi tradition).": "नाग पूजा; श्रावण शुक्ल पंचमी (काशी परम्परा)।",
    "Purnima in Aparahna free of Bhadra; else Pradosh.": "भद्रा रहित अपराह्न में पूर्णिमा; अन्यथा प्रदोष।",
    "Bhadrapada Krishna Tritiya (Purnimanta).": "भाद्रपद कृष्ण तृतीया (पूर्णिमान्त)।",
    "Tritiya at sunrise; Dwitiya-viddha day avoided.": "सूर्योदय पर तृतीया; द्वितीया-विद्धा दिन वर्जित।",
    "Chaturthi in Madhyahna; Ganapati sthapana.": "मध्याह्न में चतुर्थी; गणपति स्थापना।",
    "Saptarishi puja in Madhyahna.": "मध्याह्न में सप्तर्षि पूजा।",
    "Anant Vishnu puja; Ganesh visarjan.": "अनन्त विष्णु पूजा; गणेश विसर्जन।",
    "Shraddha and tarpan; new purchases and auspicious ceremonies are traditionally avoided.":
        "श्राद्ध और तर्पण; परम्परा से नई ख़रीदारी और शुभ संस्कार टाले जाते हैं।",
    "Pratipada shraddha; fortnight of ancestor rites.": "प्रतिपदा श्राद्ध; पितरों के कर्म का पखवाड़ा।",
    "Mahalaya; shraddha for all ancestors in Aparahna.": "महालया; अपराह्न में सभी पितरों का श्राद्ध।",
    "Pratipada at sunrise; Kalash sthapana in Pratah kaal.": "सूर्योदय पर प्रतिपदा; प्रातः काल में कलश स्थापना।",
    "Maha Ashtami; Kanya puja.": "महाष्टमी; कन्या पूजन।",
    "Navami puja and havan.": "नवमी पूजा और हवन।",
    "Dashami in Aparahna; Ramlila (Ramnagar) and Shami puja.": "अपराह्न में दशमी; रामलीला (रामनगर) और शमी पूजा।",
    "Purnima at moonrise; kheer under moonlight.": "चन्द्रोदय पर पूर्णिमा; चाँदनी में खीर।",
    "Chaturthi at moonrise; fast broken after moon sighting.": "चन्द्रोदय पर चतुर्थी; चन्द्र दर्शन के बाद व्रत खोला जाता है।",
    "Ashtami at sunset; star sighting.": "सूर्यास्त पर अष्टमी; तारा दर्शन।",
    "Trayodashi in Pradosh; Dhanvantari puja, Yama deepdaan, auspicious purchases.":
        "प्रदोष में त्रयोदशी; धन्वन्तरि पूजा, यम दीपदान, शुभ ख़रीदारी।",
    "Chaturdashi before sunrise (Abhyang snan); Choti Diwali.": "सूर्योदय से पहले चतुर्दशी (अभ्यंग स्नान); छोटी दीपावली।",
    "Amavasya in Pradosh; if both days, the day with greater Pradosh coverage (Kashi Vidvat Parishad).":
        "प्रदोष में अमावस्या; दोनों दिन हो तो जिस दिन प्रदोष में अधिक व्याप्ति हो (काशी विद्वत् परिषद्)।",
    "Pratipada in Pratah kaal; Annakut at Kashi temples.": "प्रातः काल में प्रतिपदा; काशी के मन्दिरों में अन्नकूट।",
    "Dwitiya in Aparahna; Chitragupta puja.": "अपराह्न में द्वितीया; चित्रगुप्त पूजा।",
    "First day of Chhath.": "छठ का पहला दिन।",
    "Kheer prasad after day-long fast.": "दिन भर के उपवास के बाद खीर का प्रसाद।",
    "Shashthi at sunset - evening arghya to Surya at the ghats.": "सूर्यास्त पर षष्ठी - घाटों पर सूर्य को सन्ध्या अर्घ्य।",
    "Arghya to the rising Sun; parana.": "उगते सूर्य को अर्घ्य; पारण।",
    "Amla tree puja.": "आँवले के वृक्ष की पूजा।",
    "Kartika Shukla Dwadashi.": "कार्तिक शुक्ल द्वादशी।",
    "Purnima in Pradosh; lakhs of diyas on the Varanasi ghats. Also Guru Nanak Jayanti.":
        "प्रदोष में पूर्णिमा; वाराणसी के घाटों पर लाखों दीये। गुरु नानक जयन्ती भी।",
    "Ashtami in the night (Pradosh); Kalabhairav is the Kotwal of Kashi.": "रात्रि (प्रदोष) में अष्टमी; कालभैरव काशी के कोतवाल हैं।",
    "Wedding anniversary of Shri Rama and Sita.": "श्रीराम और सीता के विवाह की वर्षगाँठ।",
    "Margashirsha Purnima - Mata Annapurna of Kashi.": "मार्गशीर्ष पूर्णिमा - काशी की माता अन्नपूर्णा।",
    "Festival of colours; Chaitra Krishna Pratipada.": "रंगों का त्योहार; चैत्र कृष्ण प्रतिपदा।",
    "Ashtami at Nishita (Smarta); Vaishnava may observe a day later.": "निशीथ में अष्टमी (स्मार्त); वैष्णव एक दिन बाद मना सकते हैं।",
    "Mal maas: marriages, griha pravesh and new purchases are avoided; japa, daan, vrata encouraged.":
        "मलमास: विवाह, गृह प्रवेश और नई ख़रीदारी टाली जाती है; जप, दान और व्रत शुभ।",
    "Purnima must prevail for 1 muhurta after sunrise, else the previous day.": "सूर्योदय के बाद 1 मुहूर्त पूर्णिमा होनी चाहिए, अन्यथा पिछला दिन।",
}

PUJA = {
    "Abhyang snan (before sunrise)": "अभ्यंग स्नान (सूर्योदय से पहले)",
    "After Bhadra ends (before madhya ratri)": "भद्रा समाप्त होने के बाद (मध्यरात्रि से पहले)",
    "Aparahna puja (Shami, Aparajita)": "अपराह्न पूजा (शमी, अपराजिता)",
    "Arghya to the rising Sun, then parana.": "उगते सूर्य को अर्घ्य, फिर पारण।",
    "Arghya to the setting Sun from the water.": "जल में खड़े होकर डूबते सूर्य को अर्घ्य।",
    "Bhadra Puchha, approx. last 3 ghati (only if Bhadra lasts past midnight)": "भद्रा पुच्छ, लगभग अन्तिम 3 घटी (केवल तब जब भद्रा मध्यरात्रि के बाद तक हो)",
    "Buying gold, silver and utensils (while Trayodashi lasts)": "सोना, चाँदी और बर्तन ख़रीदना (त्रयोदशी रहते)",
    "Deepdaan (Pradosh)": "दीपदान (प्रदोष)",
    "Dhanteras puja: Pradosh with Vrishabha lagna": "धनतेरस पूजा: प्रदोष में वृषभ लग्न",
    "Ganapati was born at Madhyahna. Avoid looking at the moon tonight (Mithya Dosha).": "गणपति का जन्म मध्याह्न में हुआ। आज रात चन्द्र दर्शन न करें (मिथ्या दोष)।",
    "Ganesh sthapana and puja (Madhyahna)": "गणेश स्थापना और पूजा (मध्याह्न)",
    "Ghatasthapana (first third of the day)": "घटस्थापना (दिन का पहला तिहाई भाग)",
    "Ghatasthapana in Abhijit muhurat": "अभिजित मुहूर्त में घटस्थापना",
    "Gold buying (while Tritiya lasts)": "सोना ख़रीदना (तृतीया रहते)",
    "Govardhan and Annakut puja in the morning, or in the evening.": "गोवर्धन और अन्नकूट पूजा प्रातः, या सायं।",
    "Guru puja (morning)": "गुरु पूजा (प्रातः)",
    "Hanuman puja (morning)": "हनुमान पूजा (प्रातः)",
    "Holi with colours is played in the morning after Holika Dahan; no puja muhurat is prescribed.": "होलिका दहन के बाद सुबह रंगों से होली खेली जाती है; कोई पूजा मुहूर्त निर्धारित नहीं है।",
    "Holika Dahan: Pradosh, Purnima, no Bhadra": "होलिका दहन: प्रदोष, पूर्णिमा, भद्रा रहित",
    "Holika is lit in Pradosh while Purnima prevails and Bhadra does not. If Bhadra runs past midnight, the dahan is done in Bhadra Puchha (its last 3 ghati), never in Bhadra Mukha.":
        "होलिका प्रदोष में जलाई जाती है जब पूर्णिमा हो और भद्रा न हो। भद्रा मध्यरात्रि के बाद तक हो तो दहन भद्रा पुच्छ (अन्तिम 3 घटी) में होता है, भद्रा मुख में कभी नहीं।",
    "Kalabhairav is worshipped at night.": "कालभैरव की पूजा रात्रि में होती है।",
    "Kalash sthapana in the morning while Pratipada prevails; if missed, use Abhijit muhurat.": "प्रतिपदा रहते सुबह कलश स्थापना; छूट जाए तो अभिजित मुहूर्त में।",
    "Karwa Chauth puja (evening)": "करवा चौथ पूजा (सायं)",
    "Keep kheer in the moonlight and take it as prasad the next morning.": "खीर चाँदनी में रखें और अगली सुबह प्रसाद के रूप में लें।",
    "Kheer under the moonlight (moonrise to midnight)": "चाँदनी में खीर (चन्द्रोदय से मध्यरात्रि तक)",
    "Lakshmi Puja: Pradosh with sthira Vrishabha lagna": "लक्ष्मी पूजा: प्रदोष में स्थिर वृषभ लग्न",
    "Lakshmi-Ganesh puja is done in Pradosh kaal while Amavasya prevails, best inside the fixed (sthira) Vrishabha lagna so that Lakshmi stays. Business owners do Chopda puja in the same window.":
        "लक्ष्मी-गणेश पूजा प्रदोष काल में अमावस्या रहते की जाती है, सबसे अच्छा स्थिर वृषभ लग्न में ताकि लक्ष्मी स्थिर रहें। व्यापारी इसी समय चोपड़ा पूजन करते हैं।",
    "Lamps are lit on the ghats in Pradosh kaal.": "प्रदोष काल में घाटों पर दीप जलाए जाते हैं।",
    "Light a four-wicked diya facing south for Yama at Pradosh. Purchases are auspicious throughout Trayodashi; avoid Rahu Kaal.":
        "प्रदोष में यम के लिए दक्षिण की ओर चार बत्तियों का दीया जलाएँ। पूरी त्रयोदशी में ख़रीदारी शुभ है; राहुकाल से बचें।",
    "Mahanishita kaal (Kali puja, sadhana)": "महानिशीथ काल (काली पूजा, साधना)",
    "Nishita kaal puja": "निशीथ काल पूजा",
    "Nishita puja (Krishna's birth)": "निशीथ पूजा (कृष्ण जन्म)",
    "Oil bath before sunrise while Chaturdashi prevails; light a Yama diya in the evening.": "चतुर्दशी रहते सूर्योदय से पहले तेल स्नान; शाम को यम दीया जलाएँ।",
    "Play colours (Dhulandi), morning": "रंग खेलना (धुलण्डी), प्रातः",
    "Pradosh kaal: Dhanvantari puja and Yama Deepdaan": "प्रदोष काल: धन्वन्तरि पूजा और यम दीपदान",
    "Pradosh, free of Bhadra": "प्रदोष, भद्रा रहित",
    "Pratah kaal muhurat": "प्रातः काल मुहूर्त",
    "Pratah kaal puja": "प्रातः काल पूजा",
    "Puja after sunset; the fast is broken after sighting the moon (moonrise below).": "सूर्यास्त के बाद पूजा; चन्द्र दर्शन के बाद व्रत खोला जाता है (चन्द्रोदय नीचे)।",
    "Puja and Sundarkand path in the morning.": "प्रातः पूजा और सुन्दरकाण्ड पाठ।",
    "Puja at Nishita kaal while Ashtami prevails. Parana is next morning after sunrise.": "अष्टमी रहते निशीथ काल में पूजा। पारण अगली सुबह सूर्योदय के बाद।",
    "Puja muhurat (Purvahna)": "पूजा मुहूर्त (पूर्वाह्न)",
    "Rakhi can be tied (Purnima, daytime, no Bhadra)": "राखी बाँधी जा सकती है (पूर्णिमा, दिन में, भद्रा रहित)",
    "Rakhi is never tied during Bhadra. When Bhadra covers the afternoon, tie it in Pradosh after Bhadra ends.": "भद्रा में राखी कभी नहीं बाँधी जाती। भद्रा अपराह्न तक रहे तो भद्रा के बाद प्रदोष में बाँधें।",
    "Rakhi muhurat: Aparahna, free of Bhadra": "राखी मुहूर्त: अपराह्न, भद्रा रहित",
    "Rama Navami puja (Madhyahna)": "राम नवमी पूजा (मध्याह्न)",
    "Ratri prahar 1": "रात्रि प्रहर 1", "Ratri prahar 2": "रात्रि प्रहर 2", "Ratri prahar 3": "रात्रि प्रहर 3",
    "Ratri prahar 4": "रात्रि प्रहर 4",
    "Sandhya arghya (at sunset)": "सन्ध्या अर्घ्य (सूर्यास्त पर)",
    "Saraswati puja (Purvahna)": "सरस्वती पूजा (पूर्वाह्न)",
    "Saraswati puja in the first half of the day while Panchami prevails; wear yellow.": "पंचमी रहते दिन के पहले भाग में सरस्वती पूजा; पीले वस्त्र पहनें।",
    "Sayankal muhurat": "सायंकाल मुहूर्त",
    "Shiva is worshipped in each of the four night prahars; Nishita kaal is the most important.": "रात्रि के चारों प्रहरों में शिव की पूजा होती है; निशीथ काल सबसे महत्त्वपूर्ण है।",
    "Shiva-Parvati puja in the morning or in Pradosh.": "शिव-पार्वती पूजा प्रातः या प्रदोष में।",
    "Shri Rama was born at the middle of the day; puja is done in Madhyahna.": "श्रीराम का जन्म दिन के मध्य में हुआ; पूजा मध्याह्न में होती है।",
    "Simha lagna (sthira, night)": "सिंह लग्न (स्थिर, रात्रि)",
    "Sisters apply tilak in Aparahna while Dwitiya prevails; Chitragupta puja on the same day.": "द्वितीया रहते अपराह्न में बहनें तिलक करती हैं; उसी दिन चित्रगुप्त पूजा।",
    "Start new work and do Shastra puja in Vijay muhurat; Ravan Dahan is after sunset.": "विजय मुहूर्त में नया कार्य आरम्भ और शस्त्र पूजा; रावण दहन सूर्यास्त के बाद।",
    "The whole of Akshaya Tritiya is auspicious; puja is done in Purvahna.": "पूरी अक्षय तृतीया शुभ है; पूजा पूर्वाह्न में होती है।",
    "Tilak muhurat (Aparahna)": "तिलक मुहूर्त (अपराह्न)",
    "Usha arghya (at sunrise)": "उषा अर्घ्य (सूर्योदय पर)",
    "Vijay muhurat": "विजय मुहूर्त",
    "Vrishabha lagna (sthira)": "वृषभ लग्न (स्थिर)",
    "Vyasa puja and guru puja in the morning.": "प्रातः व्यास पूजा और गुरु पूजा।",
}

RULES = {
    "Amavasya at sunrise": "सूर्योदय पर अमावस्या", "Ekadashi at sunrise (Smarta)": "सूर्योदय पर एकादशी (स्मार्त)",
    "Purnima at sunrise (snan-daan)": "सूर्योदय पर पूर्णिमा (स्नान-दान)", "Shukla Ashtami at sunrise": "सूर्योदय पर शुक्ल अष्टमी",
    "Shukla Chaturthi in Madhyahna": "मध्याह्न में शुक्ल चतुर्थी", "Krishna Chaturdashi at Nishita": "निशीथ में कृष्ण चतुर्दशी",
    "Krishna Chaturthi at moonrise": "चन्द्रोदय पर कृष्ण चतुर्थी", "Trayodashi in Pradosh": "प्रदोष में त्रयोदशी",
    "Day after Holika Dahan (shifted if a lunar eclipse falls that day)": "होलिका दहन के अगले दिन (उस दिन चन्द्र ग्रहण हो तो खिसकता है)",
    "Day before Sandhya Arghya": "सन्ध्या अर्घ्य से एक दिन पहले", "Two days before Sandhya Arghya": "सन्ध्या अर्घ्य से दो दिन पहले",
    "Morning after Sandhya Arghya": "सन्ध्या अर्घ्य के अगले प्रातः", "Eve of Makar Sankranti": "मकर संक्रान्ति की पूर्व सन्ध्या",
    "Lunar month without a sankranti": "संक्रान्ति रहित चान्द्र मास", "Monday in Shravana (Purnimanta)": "श्रावण (पूर्णिमान्त) का सोमवार",
    "Phalguna Shukla Ashtami to Purnima": "फाल्गुन शुक्ल अष्टमी से पूर्णिमा", "Pratipada to Navami": "प्रतिपदा से नवमी",
    "Bhadrapada Purnima to Ashwin Amavasya": "भाद्रपद पूर्णिमा से आश्विन अमावस्या",
    "Official shrine board announcement": "मन्दिर बोर्ड की आधिकारिक घोषणा",
    "Mela organisers' announcement": "मेला आयोजकों की घोषणा",
    "Sun's sidereal ingress; punya kaal next day if after sunset": "सूर्य का निरयण राशि प्रवेश; सूर्यास्त के बाद हो तो पुण्य काल अगले दिन",
}
KAAL = {"udaya": "उदय", "aparahna": "अपराह्न", "madhyahna": "मध्याह्न", "purvahna": "पूर्वाह्न", "pradosh": "प्रदोष",
        "nishita": "निशीथ", "moonrise": "चन्द्रोदय", "sunset": "सूर्यास्त", "arunodaya": "अरुणोदय",
        "guru purnima": "गुरु पूर्णिमा", "pradosh no bhadra": "भद्रा रहित प्रदोष", "aparahna no bhadra": "भद्रा रहित अपराह्न"}
TITHI = ["प्रतिपदा", "द्वितीया", "तृतीया", "चतुर्थी", "पंचमी", "षष्ठी", "सप्तमी", "अष्टमी", "नवमी", "दशमी", "एकादशी",
         "द्वादशी", "त्रयोदशी", "चतुर्दशी"]
SIGN = {"Mesh": "मेष", "Vrishabh": "वृषभ", "Mithun": "मिथुन", "Kark": "कर्क", "Simha": "सिंह", "Kanya": "कन्या",
        "Tula": "तुला", "Vrishchik": "वृश्चिक", "Dhanu": "धनु", "Makar": "मकर", "Kumbh": "कुम्भ", "Meen": "मीन"}


def _word(x):
    return TERMS_HI.get(x, SIGN.get(x, x))


def rule_hi(text):
    if not text:
        return text
    if text in RULES:
        return RULES[text]
    m = re.fullmatch(r"(\w+) (Shukla|Krishna) (\d+) - (.+) vyapini", text)
    if m:
        month, paksha, n, kaal = m.groups()
        n = int(n)
        tithi = ("पूर्णिमा" if paksha == "Shukla" else "अमावस्या") if n == 15 else TITHI[n - 1]
        return f"{_word(month)} {_word(paksha)} {tithi} - {KAAL.get(kaal, kaal)} व्यापिनी"
    m = re.fullmatch(r"Sun in (\w+)", text)
    if m:
        return f"सूर्य {_word(m.group(1))} राशि में"
    return text


def note_hi(text):
    if not text:
        return text
    if text == "Kumbh mela window.":
        return "कुम्भ मेले की अवधि।"
    if text == "Kumbh Amrit Snan.":
        return "कुम्भ अमृत स्नान।"
    if text in NOTES:
        return NOTES[text]
    if text in PUJA:
        return PUJA[text]
    dham = {"Yamunotri": "यमुनोत्री", "Gangotri": "गंगोत्री", "Kedarnath": "केदारनाथ", "Badrinath": "बद्रीनाथ"}
    m = re.fullmatch(r"(\w+) Dham open season\.", text)
    if m:
        return f"{dham.get(m.group(1), m.group(1))} धाम खुलने की अवधि।"
    if text == "Official Shri Amarnath Ji Yatra window.":
        return "श्री अमरनाथ जी यात्रा की आधिकारिक अवधि।"
    m = re.fullmatch(r"Sun enters (\w+) at (.+?)\.?", text)
    if m:
        return f"सूर्य {_word(m.group(1))} राशि में प्रवेश: {m.group(2)}।"
    m = re.fullmatch(r"(Ashtami at Nishita \(Smarta\); Vaishnava may observe a day later\.) Udaya-Ashtami "
                     r"\(Vaishnava / Mathura-Vrindavan\) observance on (.+?)\.?", text)
    if m:
        return NOTES[m.group(1)] + f" उदया-अष्टमी (वैष्णव / मथुरा-वृन्दावन) {m.group(2)} को।"
    m = re.fullmatch(r"(Festival of colours; Chaitra Krishna Pratipada\.) Moved a day because of the Chandra Grahan on (.+?)\.?", text)
    if m:
        return NOTES[m.group(1)] + f" {m.group(2)} के चन्द्र ग्रहण के कारण एक दिन आगे।"
    m = re.fullmatch(r"Purnima must prevail for (\d+) muhurta after sunrise, else the previous day\.", text)
    if m:
        return f"सूर्योदय के बाद {m.group(1)} मुहूर्त पूर्णिमा होनी चाहिए, अन्यथा पिछला दिन।"
    return text
