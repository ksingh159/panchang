# core/utils/faq_content.py
"""The FAQ, grouped. One source for the page and its FAQPage structured data. Answers are plain text."""

FAQ = [
    ("Panchang and dates", [
        ("Why do festival dates differ between calendars?",
         "A tithi can span two civil days and its clock time differs by place. Calendars also follow different rules "
         "(Amanta or Purnimanta months, Smarta or Vaishnava). We follow Kashi (Varanasi) rules and name the rule that "
         "decided each date on its festival page."),
        ("What is the difference between Amanta and Purnimanta months?",
         "Amanta months end on Amavasya (Maharashtra, Gujarat and the South); Purnimanta months end on Purnima (Kashi "
         "and North India). Only the Krishna paksha changes its month name. Choose which one is shown first on the "
         "panchang page or in your profile; the aahaar, grahan, festival and muhurat pages then use it too."),
        ("Smarta or Vaishnava Ekadashi?",
         "Smartas observe the day Ekadashi prevails at sunrise. Vaishnavas reject an Ekadashi touched by Dashami at "
         "Arunodaya (96 minutes before sunrise) and may fast a day later. We show both dates when they differ."),
        ("What is Adhik maas?",
         "An extra lunar month, roughly every 32 and a half months, in which the Sun does not change sign. Marriages, "
         "griha pravesh and major purchases are usually avoided in it; japa and daan are encouraged."),
        ("Why does the panchang show two ritus?",
         "The Vedic (nirayana) ritu follows the sidereal Sun and is used for puja, vrata and mantra. The Drik (sayana) "
         "ritu follows the Sun's real position against the solstices, which is what the weather follows, so Ayurveda's "
         "seasonal diet on the Aahaar page uses it. They differ by about three weeks."),
        ("Which ayanamsa do you use?",
         "Chitrapaksha (True Chitra) for the panchang, festivals, muhurat and grahan; Lahiri for kundali charts."),
        ("Can I look up any date?",
         "Yes. Every date from 1900 to 2200 works for any of more than 170,000 towns, and the Panchang Finder lists "
         "every occurrence of a tithi, nakshatra or maas in a year."),
    ]),
    ("Muhurat and grahan", [
        ("What are Tarabalam and Chandrabalam?",
         "Tarabalam counts from your birth nakshatra to the day's nakshatra (Sampat, Kshema, Sadhana, Mitra and Param "
         "Mitra are good). Chandrabalam is good when the Moon transits the 1st, 3rd, 6th, 7th, 10th or 11th sign from "
         "your birth Moon. Save your birth details to have muhurats filtered automatically."),
        ("Are grahan timings for my city?",
         "Yes. Each grahan page gives the contact times, the sutak period and whether the eclipse is visible from the "
         "city you have selected, with a map of where it can be seen."),
    ]),
    ("Kundali", [
        ("Is a Kundali Milan score below 18 bad?",
         "Traditionally 18 of 36 gunas is the minimum. Doshas such as Nadi or Bhakoot can be cancelled by other "
         "factors, so read the full dosha analysis and remedies, and consult an acharya for marriage decisions."),
        ("Do your divisional charts match Jagannatha Hora?",
         "Yes. The vargas follow the traditional Parashari rules, as Jagannatha Hora does by default. For D-2 we use the "
         "Uma-Shambhu hora described by P.V.R. Narasimha Rao, which Jagannatha Hora shows as D-2 (US)."),
    ]),
    ("Aahaar", [
        ("What is the Aahaar page based on?",
         "The ritu regimen of Charaka Samhita, Ashtanga Hridaya and Sushruta Samhita, with the folk month verse, "
         "Chaturmas and tithi customs marked as such. Regional foods follow your native state or the city you live in. "
         "It is general guidance, not medical advice."),
        ("Two rules on the Aahaar page disagree. Which one should I follow?",
         "Your own health comes first, then the season, then any observance you keep (Chaturmas, Ekadashi, tithi), then "
         "folk customs. The page lists today's clashes and says which rule wins."),
    ]),
    ("PDF reports and payments", [
        ("Is the site free?",
         "Every page is free to read. Only the downloadable PDF reports (the Kundali report and the Aahaar guide) are "
         "paid; the price is shown before you pay."),
        ("How do I get my PDF after paying?",
         "It appears on your order page within seconds of the payment being confirmed. You can download it up to 10 "
         "times within 30 days; signed-in buyers also find it under My PDF Orders. Nothing is shipped."),
        ("How do I pay, and is it safe?",
         "Through Razorpay or PhonePe, by UPI, card, net banking or wallet. Your card and bank details go only to the "
         "payment gateway; we never see them."),
        ("Can I get a refund?",
         "Only in two cases: money was deducted but the order shows as failed and no report was delivered, or the same "
         "order was charged twice. Write to us within 7 days with your order number and transaction reference. Once a "
         "report is delivered the sale is final; check your birth details before paying. See the Refund and "
         "Cancellation Policy."),
    ]),
    ("Your data", [
        ("What happens to my birth details?",
         "They are used only to compute your charts and muhurats, are saved only if you are signed in and choose to save "
         "them, and can be deleted from your profile at any time. We do not sell personal data."),
    ]),
]


def flat():
    return [qa for _, items in FAQ for qa in items]
