# core/utils/constants.py
# Astrological Constants

LAT, LON, TZ = 19.1142, 72.9358, 5.5  # Default Delhi, IST

TITHI_NAMES = [
    "Pratipada", "Dvitiya", "Tritiya", "Chaturthi", "Panchami",
    "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami",
    "Ekadashi", "Dvadashi", "Trayodashi", "Chaturdashi", "Purnima/Amavasya"
]

WEEKDAYS = ["Raviwar", "Somawar", "Mangalwar", "Budhwar", "Guruwar", "Shukrawar", "Shaniwar"]

NAKSHATRA_NAMES = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Moola", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]


SARVARATH_SIDDHIYOG = {
    "Raviwar": ["Ashwini", "Pushya", "Hasta", "Moola", "Uttara Phalguni", "Uttara Ashadha", "Uttara Bhadrapada"],
    "Somawar": ["Mrigashira", "Rohini", "Pushya", "Anuradha", "Shravana"],
    "Mangalwar": ["Ashwini", "Krittika", "Ashlesha", "Uttara Bhadrapada"],
    "Budhwar": ["Rohini", "Anuradha", "Mrigashira", "Hasta", "Krittika"],
    "Guruwar": ["Revati", "Anuradha", "Pushya", "Punarvasu", "Ashwini"],
    "Shukrawar": ["Revati", "Anuradha", "Ashwini", "Punarvasu", "Shravana"],
    "Shaniwar": ["Rohini", "Swati", "Shravana"],
}

AMRIT_SIDDHI_YOGA = {
    "Raviwar": ["Hasta"],
    "Somawar": ["Mrigashira"],
    "Mangalwar": ["Ashwini"],  
    "Budhwar": ["Anuradha"],
    "Guruwar": ["Pushya"],
    "Shukrawar": ["Revati"],
    "Shaniwar": ["Rohini"]
}

# Tripushkar Yoga: Specific Nakshatras + Bhadra Tithis + Specific Days
TRIPUSHKAR_YOGA = {
    "nakshatra": ["Krittika", "Punarvasu", "Uttara Phalguni", "Vishakha", "Uttara Ashadha", "Purva Bhadrapada"],
    "tithi": ["Dvitiya", "Saptami", "Dvadashi"],
    "vaar": ["Raviwar", "Mangalwar", "Shaniwar"]
}

# Dwipushkar Yoga: Specific Nakshatras + Bhadra Tithis + Specific Days
DWIPUSHKAR_YOGA = {
    "nakshatra": ["Mrigashira", "Chitra", "Dhanishta"],
    "tithi": ["Dvitiya", "Saptami", "Dvadashi"],
    "vaar": ["Raviwar", "Mangalwar", "Shaniwar"]
}

RAVI_PUSHYA_YOGA = {
    "nakshatra": ["Pushya"],
    "vaar": ["Raviwar"]
}

RAVI_YOGA = {
    4, 6, 9, 10, 13, 20 #Nakshatra difference between Sun and Moon
}

GURU_PUSHYA_YOGA = {
    "nakshatra": ["Pushya"],
    "vaar": ["Guruwar"]
}




YOGA_NAMES = [
    "Vishkumbha", "Priti", "Ayushman", "Saubhagya", "Shobhana", "Atiganda",
    "Sukarma", "Dhriti", "Shoola", "Ganda", "Vriddhi", "Dhruva",
    "Vyaghata", "Harshana", "Vajra", "Siddhi", "Vyatipata", "Variyana",
    "Parigha", "Shiva", "Siddha", "Sadhya", "Shubha", "Shukla",
    "Brahma", "Indra", "Vaidhriti"
]

KARANA_NAMES = [
    "Bhava", "Balava", "Kaulava", "Taitula", "Garaja", "Vanija", "Vishti",
    "Shakuni", "Chatushpada", "Nagava", "Kinstughna"
]



RAHU_KAAL   = [7, 1, 6, 4, 5, 3, 2]  # because we subtract 1 for 0-indexing
YAM_KAAL    = [4, 3, 2, 1, 0, 6, 5]
GULIKA_KAAL = [6, 5, 4, 3, 2, 1, 0]




DISHA_SHOOL_DIRECTIONS = {
    "Raviwar": "West, Southwest, Southeast",
    "Somawar": "East",
    "Mangalwar": "North, Northwest, Southeast",
    "Budhwar": "North, Northeast, Southeast",
    "Guruwar": "South",
    "Shukrawar": "Northeast, West, Southwest",
    "Shaniwar": "East"
}


DISHA_SHOOL_REMEDY = {
    "Raviwar": "Eat Sajjika/Rasala",
    "Somawar": "Eat Kheer",
    "Mangalwar": "Eat Kanji",
    "Budhwar": "Eat Milk",
    "Guruwar": "Eat Dahi",
    "Shukrawar": "Eat Milk",
    "Shaniwar": "Eat Sesame and rice"
}

AMANTA_MONTHS = [
    "Chaitra", "Vaishakha", "Jyeshtha", "Ashadha", "Shravana", "Bhadrapada",
    "Ashwina", "Kartika", "Margashirsha", "Pausha", "Magha", "Phalguna"
]
PURNIMANTA_MONTHS = AMANTA_MONTHS[:]

RITUS = [
    "Shishira (Winter)", "Vasanta (Spring)", "Grishma (Summer)",
    "Varsha (Monsoon)", "Sharad (Autumn)", "Hemanta (Pre-Winter)"
]

ZODIAC_SIGNS = [
    "Mesh", "Vrishabh", "Mithun", "Kark", 
    "Simha", "Kanya", "Tula", "Vrishchik", 
    "Dhanu", "Makar", "Kumbh", "Meen"
]

PANCHAK = [
    "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]

TARABALAM = {
    "Value": [1,2,3,4,5,6,7,8,9],
    "Tarabalam":["Janma Tara", "Sampat Tara", "Vipat Tara", "Kshema Tara", "Pratyak Tara", "Sadhana Tara", "Naidhana Tara", "Mitra Tara", "Param Mitra Tara"],
    "Meaning": ["Birth", "Wealth", "Danger", "Well-being", "Obstacles", "Success", "Death", "Friend", "Best Friend"],
    "Result": ["Bad", "Very Good", "Bad", "Good", "Very Bad", "Very Good", "Totally Bad", "Good", "Very Good"],

}

CHANDRABALAM = [
    1,3,6,7,10,11
]

PANCHAKA_MUHURAT = {
    1: "Mrityu Panchaka",
    2: "Agni Panchaka",
    4: "Raja Panchaka",
    6: "Chora Panchaka",
    8: "Roga Panchaka",
    3: "Good",
    5: "Good",
    7: "Good",
    0: "Good",
    9: "Good",

}