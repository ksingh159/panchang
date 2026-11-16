import swisseph as swe

# Ashtakoot Calculation
def _normalise_names(*kundalis):
    """Chart code says 'Moola', the koota tables say 'Mula' - unify before any lookup."""
    from .dosha_remedies import norm_nak
    for k in kundalis:
        if getattr(k, 'nakshatra', None):
            k.nakshatra = norm_nak(k.nakshatra)


# Bhakoot: girl's sign counted from boy's, 0-based forward distance (12 = same sign).
# Good: 1/1, 3/11, 4/10, 7/7.  Dosha: 2/12 (Dwi-dwadash), 5/9 (Nav-pancham), 6/8 (Shadashtak).
BHAKOOT_GOOD_DISTANCES = {12, 2, 10, 3, 9, 6}


def calculate_ashtakoot(kundali1, kundali2):
    """
    Calculate Ashtakoot Milan (8 aspects matching)
    Total 36 points
    """
    _normalise_names(kundali1, kundali2)
    koot_details = {}
    
    # 1. Varna Koota (1 point)
    varna_result = calculate_varna(kundali1.rashi, kundali2.rashi)
    koot_details['varna'] = {
        'score': varna_result['score'],
        'boy_varna': varna_result['boy_varna'],
        'girl_varna': varna_result['girl_varna'],
        'description': f"Boy: {varna_result['boy_varna']}, Girl: {varna_result['girl_varna']}"
    }
    
    # 2. Vashya Koota (2 points)
    vashya_result = calculate_vashya(kundali1.rashi, kundali1.moon_zodiac_degree, kundali2.rashi, kundali2.moon_zodiac_degree)
    koot_details['vashya'] = {
        'score': vashya_result['score'],
        'boy_vashya': vashya_result['boy_vashya'],
        'girl_vashya': vashya_result['girl_vashya'],
        'boy_rashi': kundali1.rashi,
        'girl_rashi': kundali2.rashi,
        'description': f"Boy: {kundali1.rashi} ({vashya_result['boy_vashya']}), Girl: {kundali2.rashi} ({vashya_result['girl_vashya']})"
    }
    
    # 3. Tara Koota (3 points)
    tara_result = calculate_tara(kundali1.nakshatra, kundali2.nakshatra)
    koot_details['tara'] = {
        'score': tara_result['score'],
        'boy_nakshatra': kundali1.nakshatra,
        'girl_nakshatra': kundali2.nakshatra,
        'distance': tara_result['distance'],
        'remainder': tara_result['remainder'],
        'description': f"Boy: {kundali1.nakshatra}, Girl: {kundali2.nakshatra}, Distance: {tara_result['distance']}, Remainder: {tara_result['remainder']}"
    }
    
    # 4. Yoni Koota (4 points)
    yoni_result = calculate_yoni(kundali1.nakshatra, kundali2.nakshatra)
    koot_details['yoni'] = {
        'score': yoni_result['score'],
        'boy_yoni': yoni_result['boy_yoni'],
        'girl_yoni': yoni_result['girl_yoni'],
        'boy_nakshatra': kundali1.nakshatra,
        'girl_nakshatra': kundali2.nakshatra,
        'description': f"Boy: {kundali1.nakshatra} ({yoni_result['boy_yoni']}), Girl: {kundali2.nakshatra} ({yoni_result['girl_yoni']})"
    }
    
    # 5. Graha Maitri Koota (5 points)
    graha_result = calculate_graha_maitri(kundali1.rashi, kundali2.rashi)
    koot_details['graha_maitri'] = {
        'score': graha_result['score'],
        'boy_lord': graha_result['boy_lord'],
        'girl_lord': graha_result['girl_lord'],
        'relationship': graha_result['relationship'],
        'description': f"Boy's Lord: {graha_result['boy_lord']}, Girl's Lord: {graha_result['girl_lord']}, Relationship: {graha_result['relationship']}"
    }
    
    # 6. Gana Koota (6 points)
    gana_result = calculate_gana(kundali1.nakshatra, kundali2.nakshatra)
    koot_details['gana'] = {
        'score': gana_result['score'],
        'boy_gana': gana_result['boy_gana'],
        'girl_gana': gana_result['girl_gana'],
        'boy_nakshatra': kundali1.nakshatra,
        'girl_nakshatra': kundali2.nakshatra,
        'description': f"Boy: {kundali1.nakshatra} ({gana_result['boy_gana']}), Girl: {kundali2.nakshatra} ({gana_result['girl_gana']})"
    }
    
    # 7. Bhakoot Koota (7 points)
    bhakoot_result = calculate_bhakoot(kundali1.rashi, kundali2.rashi)
    koot_details['bhakoot'] = {
        'score': bhakoot_result['score'],
        'boy_rashi': kundali1.rashi,
        'girl_rashi': kundali2.rashi,
        'distance': bhakoot_result['distance'],
        'description': f"Boy: {kundali1.rashi}, Girl: {kundali2.rashi}, Distance: {bhakoot_result['distance']}"
    }
    
    # 8. Nadi Koota (8 points)
    nadi_result = calculate_nadi(kundali1.nakshatra, kundali2.nakshatra)
    koot_details['nadi'] = {
        'score': nadi_result['score'],
        'boy_nadi': nadi_result['boy_nadi'],
        'girl_nadi': nadi_result['girl_nadi'],
        'boy_nakshatra': kundali1.nakshatra,
        'girl_nakshatra': kundali2.nakshatra,
        'description': f"Boy: {kundali1.nakshatra} ({nadi_result['boy_nadi']}), Girl: {kundali2.nakshatra} ({nadi_result['girl_nadi']})"
    }
    
    total_score = sum(koot['score'] for koot in koot_details.values())
    
    # Determine match status
    if total_score >= 30:
        match_status = "excellent"
    elif total_score >= 25:
        match_status = "good"
    elif total_score >= 18:
        match_status = "average"
    else:
        match_status = "poor"
    
    return {
        'total_score': total_score,
        'match_status': match_status,
        'koot_details': koot_details
    }

def calculate_varna(rashi1, rashi2):
    """Varna Koota - 1 point (hierarchical comparison)"""
    varna_groups = {
        'Brahmin': ['Kark', 'Meen'],
        'Kshatriya': ['Mesh', 'Simha', 'Dhanu'],
        'Vaishya': ['Vrishabh', 'Kanya', 'Makar'],
        'Shudra': ['Mithun', 'Tula', 'Vrishchik', 'Kumbh']
    }
    
    # Find varnas
    def get_varna(rashi):
        for varna, rashis in varna_groups.items():
            if rashi in rashis:
                return varna
        return 'Shudra'
    
    varna_order = {'Shudra': 1, 'Vaishya': 2, 'Kshatriya': 3, 'Brahmin': 4}
    
    boy_varna = get_varna(rashi1)
    girl_varna = get_varna(rashi2)
    
    # Boy's varna should be equal or higher
    score = 1 if varna_order[boy_varna] >= varna_order[girl_varna] else 0
    
    return {
        'score': score,
        'boy_varna': boy_varna,
        'girl_varna': girl_varna
    }

def calculate_vashya(rashi1, longitude1, rashi2, longitude2):
    """Vashya Koota - 2 points maximum with correct longitude-based splits"""
    
    def get_vashya(rashi, longitude):
        """Determine Vashya category for a single rashi based on longitude"""
        if rashi in ['Mesh', 'Vrishabh']:  # Aries, Taurus
            return 'Chatushpada'
        elif rashi in ['Mithun', 'Kanya', 'Tula', 'Kumbh']:  # Gemini, Virgo, Libra, Aquarius
            return 'Nara'
        elif rashi == 'Kark':  # Cancer
            return 'Jalchar'
        elif rashi == 'Simha':  # Leo
            return 'Vanacara'
        elif rashi == 'Vrishchik':  # Scorpio
            return 'Keeta'
        elif rashi == 'Dhanu':  # Sagittarius
            # Second half of Sagittarius = Chatushpada
            if 15 <= longitude <= 29.999:
                return 'Chatushpada'
            else:
                return 'Nara'  # First half = Nara
        elif rashi == 'Makar':  # Capricorn
            # First half of Capricorn = Chatushpada
            if 0 <= longitude < 15:
                return 'Chatushpada'
            else:
                return 'Jalchar'  # Second half = Jalchar
        elif rashi == 'Meen':  # Pisces
            return 'Jalchar'
        else:
            return 'Nara'  # Default
    
    boy_vashya = get_vashya(rashi1, longitude1)
    girl_vashya = get_vashya(rashi2, longitude2)
    
    # Compatibility matrix
    compatibility = {
        'Chatushpada': {'Chatushpada': 2, 'Nara': 1, 'Jalchar': 1, 'Vanacara': 0, 'Keeta': 1},
        'Nara': {'Chatushpada': 1, 'Nara': 2, 'Jalchar': 1.5, 'Vanacara': 0, 'Keeta': 1},
        'Jalchar': {'Chatushpada': 1, 'Nara': 1.5, 'Jalchar': 2, 'Vanacara': 1, 'Keeta': 1},
        'Vanacara': {'Chatushpada': 0, 'Nara': 0, 'Jalchar': 0, 'Vanacara': 2, 'Keeta': 0},
        'Keeta': {'Chatushpada': 1, 'Nara': 1, 'Jalchar': 1, 'Vanacara': 0, 'Keeta': 2}
    }
    
    score = compatibility[boy_vashya][girl_vashya]
    
    return {
        'score': score,
        'boy_vashya': boy_vashya,
        'girl_vashya': girl_vashya,
        'boy_longitude': longitude1,
        'girl_longitude': longitude2
    }

def calculate_tara(nakshatra1, nakshatra2):
    """Tara Koota - 3 points"""
    nakshatras = [
        'Ashwini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashira', 'Ardra',
        'Punarvasu', 'Pushya', 'Ashlesha', 'Magha', 'Purva Phalguni', 'Uttara Phalguni',
        'Hasta', 'Chitra', 'Swati', 'Vishakha', 'Anuradha', 'Jyeshtha',
        'Mula', 'Purva Ashadha', 'Uttara Ashadha', 'Shravana', 'Dhanishta',
        'Shatabhisha', 'Purva Bhadrapada', 'Uttara Bhadrapada', 'Revati'
    ]

    idx1 = nakshatras.index(nakshatra1)
    idx2 = nakshatras.index(nakshatra2)

    # Forward distance (1-based count)
    distance = abs(idx2 - idx1) + 1
    remainder = distance % 9
    bad_remainders = [3, 5, 7]  # Vipat, Pratyari, Vadha

    score = 0 if remainder in bad_remainders else 3

    return {
        'score': score,
        'distance': distance,
        'remainder': remainder,
        'is_favorable': remainder not in bad_remainders
    }

def calculate_yoni(nakshatra1, nakshatra2):
    """Yoni Koota - Efficient array-based system"""
    
    # Define Yoni types with indices for quick lookup
    YONI_TYPES = [
        'Ashwa',    # 0 - Horse
        'Gaja',     # 1 - Elephant
        'Mesh',     # 2 - Sheep
        'Sarpa',    # 3 - Serpent
        'Shwan',    # 4 - Dog
        'Marjara',  # 5 - Cat
        'Mushaka',  # 6 - Rat
        'Gau',      # 7 - Cow
        'Mahisha',  # 8 - Buffalo
        'Vyagrah',  # 9 - Tiger
        'Mriga',    # 10 - Deer
        'Vanara',   # 11 - Monkey
        'Nakul',    # 12 - Mongoose
        'Singha'    # 13 - Lion
    ]
    
    # Nakshatra to Yoni index mapping
    NAKSHATRA_YONI_MAP = {
        'Ashwini': 0,    # Ashwa
        'Bharani': 1,    # Gaja
        'Krittika': 2,   # Mesh
        'Rohini': 3,     # Sarpa
        'Mrigashira': 3, # Sarpa
        'Ardra': 4,      # Shwan
        'Punarvasu': 5,  # Marjara
        'Pushya': 2,     # Mesh
        'Ashlesha': 5,   # Marjara
        'Magha': 6,      # Mushaka
        'Purva Phalguni': 6, # Mushaka
        'Uttara Phalguni': 7, # Gau
        'Hasta': 8,      # Mahisha
        'Chitra': 9,     # Vyagrah
        'Swati': 8,      # Mahisha
        'Vishakha': 9,   # Vyagrah
        'Anuradha': 10,  # Mriga
        'Jyeshtha': 10,  # Mriga
        'Mula': 4,       # Shwan
        'Purva Ashadha': 11, # Vanara
        'Uttara Ashadha': 12, # Nakul
        'Shravana': 11,  # Vanara
        'Dhanishta': 13, # Singha
        'Shatabhisha': 0, # Ashwa
        'Purva Bhadrapada': 13, # Singha
        'Uttara Bhadrapada': 7, # Gau
        'Revati': 1      # Gaja
    }
    
    # Compatibility matrix as a 2D array (14x14)
    YONI_COMPATIBILITY = [
        # 0Ash 1Gaj 2Mes 3Sar 4Shw 5Mar 6Mus 7Gau 8Mah 9Vya 10Mrg 11Van 12Nak 13Sin
        [4,   3,   2,   1,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0],   # 0 Ashwa
        [3,   4,   3,   2,   1,   0,   0,   0,   0,   0,   0,   0,   0,   0],   # 1 Gaja
        [2,   3,   4,   3,   2,   1,   0,   0,   0,   0,   0,   0,   0,   0],   # 2 Mesh
        [1,   2,   3,   4,   3,   2,   1,   0,   0,   0,   0,   0,   0,   0],   # 3 Sarpa
        [0,   1,   2,   3,   4,   3,   2,   1,   0,   0,   0,   0,   0,   0],   # 4 Shwan
        [0,   0,   1,   2,   3,   4,   3,   2,   1,   0,   0,   0,   0,   0],   # 5 Marjara
        [0,   0,   0,   1,   2,   3,   4,   3,   2,   1,   0,   0,   0,   0],   # 6 Mushaka
        [0,   0,   0,   0,   1,   2,   3,   4,   3,   2,   1,   0,   0,   0],   # 7 Gau
        [0,   0,   0,   0,   0,   1,   2,   3,   4,   3,   2,   1,   0,   0],   # 8 Mahisha
        [0,   0,   0,   0,   0,   0,   1,   2,   3,   4,   3,   2,   1,   0],   # 9 Vyagrah
        [0,   0,   0,   0,   0,   0,   0,   1,   2,   3,   4,   3,   2,   1],   # 10 Mriga
        [0,   0,   0,   0,   0,   0,   0,   0,   1,   2,   3,   4,   3,   2],   # 11 Vanara
        [0,   0,   0,   0,   0,   0,   0,   0,   0,   1,   2,   3,   4,   3],   # 12 Nakul
        [0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   1,   2,   3,   4]    # 13 Singha
    ]
    
    # Get Yoni indices
    yoni_idx1 = NAKSHATRA_YONI_MAP.get(nakshatra1)
    yoni_idx2 = NAKSHATRA_YONI_MAP.get(nakshatra2)
    
    if yoni_idx1 is None or yoni_idx2 is None:
        return {
            'score': 0,
            'boy_yoni': 'Unknown',
            'girl_yoni': 'Unknown'
        }
    
    # Get compatibility score
    score = YONI_COMPATIBILITY[yoni_idx1][yoni_idx2]
    
    return {
        'score': score,
        'boy_yoni': YONI_TYPES[yoni_idx1],
        'girl_yoni': YONI_TYPES[yoni_idx2]
    }

def calculate_graha_maitri(rashi1, rashi2):
    """Graha Maitri Koota - 5 points (based on friendship between rashi lords)"""

    # Step 1: Rashi → Lord mapping
    rashi_lords = {
        'Mesh': 'Mars', 'Vrishabh': 'Venus', 'Mithun': 'Mercury',
        'Kark': 'Moon', 'Simha': 'Sun', 'Kanya': 'Mercury',
        'Tula': 'Venus', 'Vrishchik': 'Mars', 'Dhanu': 'Jupiter',
        'Makar': 'Saturn', 'Kumbh': 'Saturn', 'Meen': 'Jupiter'
    }

    # Step 2: Permanent friendships
    friends = {
        'Sun': ['Moon', 'Mars', 'Jupiter'],
        'Moon': ['Sun', 'Mercury'],
        'Mars': ['Sun', 'Moon', 'Jupiter'],
        'Mercury': ['Sun', 'Venus'],
        'Jupiter': ['Sun', 'Moon', 'Mars'],
        'Venus': ['Mercury', 'Saturn'],
        'Saturn': ['Mercury', 'Venus']
    }

    neutrals = {
        'Sun': ['Mercury'],
        'Moon': ['Mars', 'Jupiter', 'Venus', 'Saturn'],
        'Mars': ['Venus', 'Saturn'],
        'Mercury': ['Mars', 'Jupiter', 'Saturn'],
        'Jupiter': ['Saturn'],
        'Venus': ['Jupiter'],
        'Saturn': ['Jupiter']
    }

    enemies = {
        'Sun': ['Venus', 'Saturn'],
        'Moon': [],
        'Mars': ['Mercury'],
        'Mercury': ['Moon'],
        'Jupiter': ['Mercury', 'Venus'],
        'Venus': ['Sun', 'Moon', 'Mars'],
        'Saturn': ['Sun', 'Moon', 'Mars']
    }

    # Step 3: Get lords
    boy_lord = rashi_lords.get(rashi1, '')
    girl_lord = rashi_lords.get(rashi2, '')

    if not boy_lord or not girl_lord:
        return {
            'score': 0,
            'boy_lord': 'Unknown',
            'girl_lord': 'Unknown',
            'relationship': 'Unknown'
        }

    # Step 4: Evaluate relationship (mutual)
    def get_relation(lord_a, lord_b):
        if lord_b in friends[lord_a]:
            return 'Friend'
        elif lord_b in neutrals[lord_a]:
            return 'Neutral'
        elif lord_b in enemies[lord_a]:
            return 'Enemy'
        else:
            return 'Neutral'  # fallback

    rel1 = get_relation(boy_lord, girl_lord)
    rel2 = get_relation(girl_lord, boy_lord)

    # Step 5: Determine score and relationship description
    if rel1 == 'Friend' and rel2 == 'Friend':
        score = 5
        relationship = 'Mutual Friends'
    elif ('Friend' in [rel1, rel2]) and ('Neutral' in [rel1, rel2]):
        score = 4
        relationship = 'Mixed (Friend-Neutral)'
    elif rel1 == 'Neutral' and rel2 == 'Neutral':
        score = 3
        relationship = 'Both Neutral'
    elif ('Friend' in [rel1, rel2]) and ('Enemy' in [rel1, rel2]):
        score = 2
        relationship = 'Mixed (Friend-Enemy)'
    elif rel1 == 'Enemy' and rel2 == 'Enemy':
        score = 0
        relationship = 'Mutual Enemies'
    else:
        score = 3
        relationship = 'Neutral'

    return {
        'score': score,
        'boy_lord': boy_lord,
        'girl_lord': girl_lord,
        'relationship': relationship
    }

def calculate_gana(nakshatra1, nakshatra2):
    """Gana Koota - 6 points"""
    # Gana mapping for nakshatras
    nakshatra_gana = {
        'Ashwini': 'Deva', 'Bharani': 'Manushya', 'Krittika': 'Rakshasa',
        'Rohini': 'Manushya', 'Mrigashira': 'Deva', 'Ardra': 'Manushya',
        'Punarvasu': 'Deva', 'Pushya': 'Deva', 'Ashlesha': 'Rakshasa',
        'Magha': 'Rakshasa', 'Purva Phalguni': 'Manushya', 'Uttara Phalguni': 'Manushya',
        'Hasta': 'Deva', 'Chitra': 'Rakshasa', 'Swati': 'Deva',
        'Vishakha': 'Rakshasa', 'Anuradha': 'Deva', 'Jyeshtha': 'Rakshasa',
        'Mula': 'Rakshasa', 'Purva Ashadha': 'Manushya', 'Uttara Ashadha': 'Manushya',
        'Shravana': 'Deva', 'Dhanishta': 'Rakshasa', 'Shatabhisha': 'Rakshasa',
        'Purva Bhadrapada': 'Manushya', 'Uttara Bhadrapada': 'Manushya', 'Revati': 'Deva'
    }
    
    boy_gana = nakshatra_gana.get(nakshatra1, '')
    girl_gana = nakshatra_gana.get(nakshatra2, '')
    
    if boy_gana == girl_gana:
        score = 6
    elif (boy_gana == 'Deva' and girl_gana == 'Manushya') or (boy_gana == 'Manushya' and girl_gana == 'Deva'):
        score = 5
    elif (boy_gana == 'Deva' and girl_gana == 'Rakshasa'):
        score = 1
    elif (boy_gana == 'Rakshasa' and girl_gana == 'Manushya'):
        score = 1
    else:
        score = 0

    return {
        'score': score,
        'boy_gana': boy_gana,
        'girl_gana': girl_gana
    }

def calculate_bhakoot(boy_rashi, girl_rashi):
    """Bhakoot Koota - Count from boy's rashi as 1st house"""
    
    rashi_order = ['Mesh', 'Vrishabh', 'Mithun', 'Kark', 'Simha', 'Kanya', 
                   'Tula', 'Vrishchik', 'Dhanu', 'Makar', 'Kumbh', 'Meen']
    
    boy_idx = rashi_order.index(boy_rashi)
    girl_idx = rashi_order.index(girl_rashi)
    
    # Count distance from boy's rashi (1st house) to girl's rashi
    distance = (girl_idx - boy_idx) % 12
    if distance == 0:
        distance = 12
    
    compatible_distances = BHAKOOT_GOOD_DISTANCES
    score = 7 if distance in compatible_distances else 0

    return {
        'score': score,
        'distance': distance,
        'is_compatible': distance in compatible_distances
    }

def calculate_nadi(nakshatra1, nakshatra2):
    """Nadi Koota - 8 points (most important)"""
    # Nadi mapping for nakshatras
    nakshatra_nadi = {
        'Ashwini': 'Aadi', 'Ardra': 'Aadi', 'Punarvasu': 'Aadi', 
        'Uttara Phalguni': 'Aadi', 'Hasta': 'Aadi', 'Jyeshtha': 'Aadi',
        'Mula': 'Aadi', 'Shatabhisha': 'Aadi', 'Purva Bhadrapada': 'Aadi',
        
        'Bharani': 'Madhya', 'Mrigashira': 'Madhya', 'Pushya': 'Madhya',
        'Purva Phalguni': 'Madhya', 'Chitra': 'Madhya', 'Anuradha': 'Madhya',
        'Purva Ashadha': 'Madhya', 'Dhanishta': 'Madhya', 'Uttara Bhadrapada': 'Madhya',
        
        'Krittika': 'Antya', 'Rohini': 'Antya', 'Ashlesha': 'Antya',
        'Magha': 'Antya', 'Swati': 'Antya', 'Vishakha': 'Antya',
        'Uttara Ashadha': 'Antya', 'Shravana': 'Antya', 'Revati': 'Antya'
    }
    
    boy_nadi = nakshatra_nadi.get(nakshatra1, '')
    girl_nadi = nakshatra_nadi.get(nakshatra2, '')
    
    # Different nadi: 8 points, Same nadi: 0 points
    score = 8 if boy_nadi != girl_nadi else 0

    return {
        'score': score,
        'boy_nadi': boy_nadi,
        'girl_nadi': girl_nadi,
        'is_compatible': boy_nadi != girl_nadi
    }

# Name Matching based on Numerology
def calculate_name_match(user1, user2):
    """Calculate name compatibility based on numerology"""
    
    def name_to_number(name):
        """Convert name to numerical value"""
        numerology_map = {
            'a': 1, 'b': 2, 'c': 3, 'd': 4, 'e': 5, 'f': 8, 'g': 3, 'h': 5,
            'i': 1, 'j': 1, 'k': 2, 'l': 3, 'm': 4, 'n': 5, 'o': 7, 'p': 8,
            'q': 1, 'r': 2, 's': 3, 't': 4, 'u': 6, 'v': 6, 'w': 6, 'x': 5,
            'y': 1, 'z': 7
        }
        
        total = 0
        for char in name.lower():
            if char in numerology_map:
                total += numerology_map[char]
        
        # Reduce to single digit
        while total > 9 and total not in [11, 22, 33]:  # Master numbers
            total = sum(int(digit) for digit in str(total))
        
        return total
    
    name1 = f"{user1.first_name} {user1.last_name}".strip()
    name2 = f"{user2.first_name} {user2.last_name}".strip()
    
    num1 = name_to_number(name1)
    num2 = name_to_number(name2)
    
    # Calculate compatibility
    diff = abs(num1 - num2)
    
    if diff == 0:
        score = 95
        reason = "Excellent name vibration match"
    elif diff <= 2:
        score = 80
        reason = "Good name compatibility"
    elif diff <= 4:
        score = 65
        reason = "Moderate name match"
    else:
        score = 40
        reason = "Basic name compatibility"
    
    return {
        'score': score,
        'reason': reason,
        'user1_number': num1,
        'user2_number': num2
    }

# -------------------------------------------------------
# 💫 DOSHA EVALUATION MODULE (User-Friendly Version)
# -------------------------------------------------------
# Checks Mangal, Nadi, Bhakoot, Rajju, Vedha doshas
# Handles standard cancellation rules & mitigations
# Returns simple, understandable sentences for users
# -------------------------------------------------------

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
import json

# --- CONSTANTS ---
MANGAL_DOSHA_HOUSES = {1, 4, 7, 8, 12}
MARS_OWN_SIGNS = {'Mesh', 'Vrishchik'}
MARS_EXALTED_SIGN = 'Makar'
BENEFIC_PLANETS = {'Jupiter', 'Moon', 'Venus', 'Mercury'}
GRAHA_MAITRI_THRESHOLD = 4

# Rajju groups
RAJJU_GROUPS = {
    'Padarajju': ['Ashwini', 'Bharani', 'Krittika', 'Punarvasu', 'Pushya', 'Hasta',
                  'Anuradha', 'Jyeshtha', 'Mula', 'Purva Ashadha', 'Uttara Ashadha', 'Revati'],
    'Kati Rajju': ['Rohini', 'Mrigashira', 'Chitra', 'Swati', 'Vishakha', 'Shravana',
                   'Dhanishta', 'Shatabhisha', 'Purva Bhadrapada'],
    'Nabhi Rajju': ['Magha', 'Purva Phalguni', 'Uttara Phalguni'],
    'Kantha Rajju': ['Ashlesha', 'Uttara Bhadrapada'],
    'Sira Rajju': ['Ardra', 'Punarvasu']
}

# Vedha pairs
VEDHA_PAIRS = {
    'Ashwini': ['Jyeshtha'], 'Bharani': ['Anuradha'], 'Krittika': ['Vishakha'],
    'Rohini': ['Swati'], 'Mrigashira': ['Chitra'], 'Ardra': ['Hasta'],
    'Punarvasu': ['Magha'], 'Pushya': ['Purva Phalguni'], 'Ashlesha': ['Uttara Phalguni'],
    'Magha': ['Punarvasu'], 'Purva Phalguni': ['Pushya'], 'Uttara Phalguni': ['Ashlesha'],
    'Hasta': ['Ardra'], 'Chitra': ['Mrigashira'], 'Swati': ['Rohini'],
    'Vishakha': ['Krittika'], 'Anuradha': ['Bharani'], 'Jyeshtha': ['Ashwini'],
    'Mula': ['Revati'], 'Purva Ashadha': ['Uttara Bhadrapada'], 'Uttara Ashadha': ['Shatabhisha'],
    'Shravana': ['Purva Bhadrapada'], 'Dhanishta': ['Shravana'], 'Shatabhisha': ['Uttara Ashadha'],
    'Purva Bhadrapada': ['Shravana'], 'Uttara Bhadrapada': ['Purva Ashadha'], 'Revati': ['Mula']
}

# --- DATA STRUCTURES ---
@dataclass
class DoshaResult:
    present: bool
    cancelled: bool = False
    severity: str = None
    reasons: List[str] = None
    mitigations: List[str] = None
    user_message: str = ""
    
    def __post_init__(self):
        if self.reasons is None:
            self.reasons = []
        if self.mitigations is None:
            self.mitigations = []
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'present': self.present,
            'cancelled': self.cancelled,
            'severity': self.severity,
            'reasons': self.reasons,
            'mitigations': self.mitigations,
            'user_message': self.user_message
        }

@dataclass
class MangalAnalysis:
    partner1_manglik: bool
    partner2_manglik: bool
    cancelled: bool
    partner1_mitigations: List[str]
    partner2_mitigations: List[str]
    reasons: List[str]
    user_message: str = ""
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'partner1_manglik': self.partner1_manglik,
            'partner2_manglik': self.partner2_manglik,
            'cancelled': self.cancelled,
            'partner1_mitigations': self.partner1_mitigations,
            'partner2_mitigations': self.partner2_mitigations,
            'reasons': self.reasons,
            'user_message': self.user_message
        }

# --- COMPLETE MANGAL DOSHA ANALYZER ---
class MangalDoshaAnalyzer:
    
    # Comprehensive cancellation rules
    CANCELLATION_RULES = {
        'mars_own_sign': "Mars in own sign (Mesh/Vrishchik) cancels dosha",
        'mars_exalted': "Mars exalted in Makar cancels dosha", 
        'mars_debilitated': "Mars debilitated in Kark cancels dosha",
        'mars_combust': "Mars combust (within 8° of Sun) cancels dosha",
        'mars_movable_sign': "Mars in movable sign (Mesh, Kark, Tula, Makar) cancels dosha",
        'jupiter_aspect': "Jupiter aspecting Mars or 7th house cancels dosha",
        'moon_kendra': "Moon in Kendra (1,4,7,10) cancels dosha",
        'saturn_aspect': "Saturn aspecting Mars cancels dosha",
        'venus_conjunct': "Venus conjunct Mars cancels dosha",
        'mercury_conjunct': "Mercury conjunct Mars cancels dosha",
        'sun_conjunct': "Sun conjunct Mars cancels dosha",
        'mutual_manglik': "Both partners Manglik cancels dosha mutually"
    }
    
    @staticmethod
    def check_manglik_status(kundali, reference: str = 'lagna') -> Tuple[bool, Dict]:
        """Check if Mars causes Mangal Dosha with detailed analysis."""
        details = {
            'checked_from': reference, 
            'manglik': False, 
            'has_dosha_position': False,
            'house': None,
            'sign': None,
            'longitude': None,
            'cancellation_rules': [],  # Which rules apply
            'detailed_explanations': [],  # Full sentences like Prokerala
            'mitigating_planets': [],  # Planets causing cancellation
            'technical_reasons': []  # For debugging
        }
        
        try:
            planets = getattr(kundali, 'planets', {})
            mars = planets.get('Mars', {})
            
            if not mars:
                details['technical_reasons'].append('Mars data missing')
                return False, details

            # Extract Mars data
            mars_house = mars.get('house')
            mars_sign = mars.get('zodiac_sign', '')
            mars_longitude = mars.get('longitude', 0)
            
            details.update({
                'house': mars_house,
                'sign': mars_sign, 
                'longitude': mars_longitude
            })

            # Check if Mars is in dosha position
            if mars_house in MANGAL_DOSHA_HOUSES:
                details['has_dosha_position'] = True
                details['technical_reasons'].append(f'Mars in house {mars_house}')
                
                # Analyze ALL cancellation factors
                cancellation_analysis = MangalDoshaAnalyzer._analyze_cancellation_factors(
                    kundali, mars_house, mars_sign, mars_longitude
                )
                
                details.update(cancellation_analysis)
                
                # Final determination
                details['manglik'] = not bool(cancellation_analysis['cancellation_rules'])
                
            else:
                details['technical_reasons'].append(f'Mars in house {mars_house} - No dosha position')
                
        except Exception as e:
            details['technical_reasons'].append(f'Error: {str(e)}')
            
        return details['manglik'], details

    @staticmethod
    def _analyze_cancellation_factors(kundali, mars_house, mars_sign, mars_longitude):
        """Parihara (cancellation) rules shared with the printed kundali: see dosha_remedies.mangal_dosha."""
        from .dosha_remedies import RASHIS, mangal_dosha
        planets = getattr(kundali, 'planets', {})
        signs, lons = {}, {}
        for name, pdata in planets.items():
            if pdata and pdata.get('zodiac_sign') in RASHIS:
                signs[name] = RASHIS.index(pdata['zodiac_sign'])
                lons[name] = pdata.get('longitude')
        if 'Mars' not in signs:
            return {'cancellation_rules': [], 'detailed_explanations': [], 'mitigating_planets': [],
                    'reducing_factors': [], 'is_cancelled': False}
        asc_sign = (signs['Mars'] - (mars_house - 1)) % 12
        result = mangal_dosha(signs, lons, asc_sign, refs=("Lagna",))
        planet_of = {"jup_with": "Jupiter", "jup_aspect": "Jupiter", "jupiter_lagna": "Jupiter",
                     "venus_lagna": "Venus", "moon_with": "Moon", "combust": "Sun"}
        return {
            'cancellation_rules': [key for key, _ in result['parihara']],
            'detailed_explanations': [f"{text}, which cancels Mangal Dosha." for _, text in result['parihara']] +
                                     [f"{text}: this reduces Mangal Dosha but does not cancel it."
                                      for _, text in result['reducers']],
            'reducing_factors': [key for key, _ in result['reducers']],
            'mitigating_planets': sorted({planet_of.get(key, 'Mars') for key, _ in result['parihara'] + result['reducers']}),
            'is_cancelled': result['cancelled'],
        }

    @staticmethod
    def analyze_cancellation(k1, k2) -> Dict:
        """Final analysis with mutual cancellation check."""
        manglik1, details1 = MangalDoshaAnalyzer.check_manglik_status(k1)
        manglik2, details2 = MangalDoshaAnalyzer.check_manglik_status(k2)
        
        # Combine explanations
        all_explanations = details1.get('detailed_explanations', []) + details2.get('detailed_explanations', [])
        
        # Check mutual cancellation
        # Samya: when both partners are Manglik, the dosha of one balances the other
        mutual_cancellation = bool(manglik1 and manglik2)
        if mutual_cancellation:
            all_explanations.append("Both partners are Manglik, so the dosha balances out (Mangal samya).")
        
        # Build final result
        final_cancelled = mutual_cancellation or (not manglik1 and not manglik2)
        
        # User message
        if final_cancelled:
            if mutual_cancellation:
                user_message = "✅ Both partners have Mangal Dosha, but it cancels out mutually due to favorable planetary combinations."
            else:
                user_message = "✅ Mangal Dosha is cancelled due to strong planetary influences in both charts."
        else:
            if manglik1 or manglik2:
                user_message = "⚠️ Mangal Dosha is present. Consult an astrologer for detailed analysis."
            else:
                user_message = "✅ No Mangal Dosha found."

        return {
            'partner1_manglik': manglik1,
            'partner2_manglik': manglik2,
            'partner1_has_dosha_position': details1.get('has_dosha_position', False),
            'partner2_has_dosha_position': details2.get('has_dosha_position', False),
            'partner1_mitigating_planets': details1.get('mitigating_planets', []),
            'partner2_mitigating_planets': details2.get('mitigating_planets', []),
            'cancelled': final_cancelled,
            'mutual_cancellation': mutual_cancellation,
            'detailed_explanations': all_explanations,
            'user_message': user_message,
            'partner1_explanations': details1.get('detailed_explanations', []),
            'partner2_explanations': details2.get('detailed_explanations', [])
        }
    

# --- 2️⃣ NADI DOSHA ---
class NadiDoshaAnalyzer:
    @staticmethod
    def analyze(nadi_score: int) -> Dict:  # Returns Dict instead of DoshaResult
        """Interpret Nadi score."""
        if nadi_score == 0:
            user_message = "❌ Nadi Dosha Present: Same Nadi indicates potential health compatibility issues. Consider consulting an astrologer."
            return {
                'present': True,
                'cancelled': False,
                'severity': 'high',
                'reasons': ['Same Nadi → strong Nadi Dosha'],
                'mitigations': [],
                'user_message': user_message
            }
        else:
            user_message = "✅ No Nadi Dosha: Different Nadi indicates good health compatibility for prospective children."
            return {
                'present': False,
                'cancelled': False,
                'severity': None,
                'reasons': ['Different Nadi → no dosha'],
                'mitigations': [],
                'user_message': user_message
            }

# --- 3️⃣ BHAKOOT DOSHA ---
class BhakootDoshaAnalyzer:
    @staticmethod
    def analyze(bhakoot_score: int, kundali1, kundali2) -> Dict:
        """Bhakoot dosha and its cancellation conditions."""
        if bhakoot_score == 0:
            # Check Graha Maitri cancellation using actual calculation
            gm_score = BhakootDoshaAnalyzer._calculate_graha_maitri(kundali1, kundali2)
            if gm_score >= GRAHA_MAITRI_THRESHOLD:
                user_message = f"✅ Bhakoot Dosha was indicated but has been cancelled due to strong planetary friendship (Graha Maitri: {gm_score}/5). This is favorable."
                return {
                    'present': True,
                    'cancelled': True,
                    'severity': None,
                    'reasons': [
                        'Bhakoot score 0 → potential dosha',
                        f'Graha Maitri {gm_score} ≥ {GRAHA_MAITRI_THRESHOLD} → Bhakoot dosha cancelled'
                    ],
                    'mitigations': [],
                    'user_message': user_message
                }
            else:
                user_message = f"⚠️ Bhakoot Dosha Present: Potential challenges in mutual understanding and prosperity. Graha Maitri score ({gm_score}/5) is below cancellation threshold."
                return {
                    'present': True,
                    'cancelled': False,
                    'severity': None,
                    'reasons': [
                        'Bhakoot score 0 → potential dosha',
                        f'Graha Maitri {gm_score} < {GRAHA_MAITRI_THRESHOLD} → dosha not cancelled'
                    ],
                    'mitigations': [],
                    'user_message': user_message
                }
        else:
            user_message = f"✅ No Bhakoot Dosha: Good score ({bhakoot_score}/7) indicates harmony in relationship and financial matters."
            return {
                'present': False,
                'cancelled': False,
                'severity': None,
                'reasons': [f'Bhakoot score {bhakoot_score} > 0 → no dosha'],
                'mitigations': [],
                'user_message': user_message
            }

    @staticmethod
    def _calculate_graha_maitri(kundali1, kundali2) -> int:
        """Calculate actual Graha Maitri score between two kundalis."""
        rashi1 = getattr(kundali1, 'rashi', None)
        rashi2 = getattr(kundali2, 'rashi', None)
        
        if not rashi1 or not rashi2:
            return 0
            
        # Rashi → Lord mapping
        rashi_lords = {
            'Mesh': 'Mars', 'Vrishabh': 'Venus', 'Mithun': 'Mercury',
            'Kark': 'Moon', 'Simha': 'Sun', 'Kanya': 'Mercury',
            'Tula': 'Venus', 'Vrishchik': 'Mars', 'Dhanu': 'Jupiter',
            'Makar': 'Saturn', 'Kumbh': 'Saturn', 'Meen': 'Jupiter'
        }

        # Permanent friendships
        friends = {
            'Sun': ['Moon', 'Mars', 'Jupiter'],
            'Moon': ['Sun', 'Mercury'],
            'Mars': ['Sun', 'Moon', 'Jupiter'],
            'Mercury': ['Sun', 'Venus'],
            'Jupiter': ['Sun', 'Moon', 'Mars'],
            'Venus': ['Mercury', 'Saturn'],
            'Saturn': ['Mercury', 'Venus']
        }

        neutrals = {
            'Sun': ['Mercury'],
            'Moon': ['Mars', 'Jupiter', 'Venus', 'Saturn'],
            'Mars': ['Venus', 'Saturn'],
            'Mercury': ['Mars', 'Jupiter', 'Saturn'],
            'Jupiter': ['Saturn'],
            'Venus': ['Jupiter'],
            'Saturn': ['Jupiter']
        }

        enemies = {
            'Sun': ['Venus', 'Saturn'],
            'Moon': [],
            'Mars': ['Mercury'],
            'Mercury': ['Moon'],
            'Jupiter': ['Mercury', 'Venus'],
            'Venus': ['Sun', 'Moon', 'Mars'],
            'Saturn': ['Sun', 'Moon', 'Mars']
        }

        # Get lords
        lord1 = rashi_lords.get(rashi1, '')
        lord2 = rashi_lords.get(rashi2, '')

        if not lord1 or not lord2:
            return 0

        # Evaluate relationship (mutual)
        def get_relation(lord_a, lord_b):
            if lord_b in friends.get(lord_a, []):
                return 'friend'
            elif lord_b in neutrals.get(lord_a, []):
                return 'neutral'
            elif lord_b in enemies.get(lord_a, []):
                return 'enemy'
            else:
                return 'neutral'

        rel1 = get_relation(lord1, lord2)
        rel2 = get_relation(lord2, lord1)

        # Determine score
        if rel1 == 'friend' and rel2 == 'friend':
            return 5
        elif ('friend' in [rel1, rel2]) and ('neutral' in [rel1, rel2]):
            return 4
        elif rel1 == 'neutral' and rel2 == 'neutral':
            return 3
        elif ('friend' in [rel1, rel2]) and ('enemy' in [rel1, rel2]):
            return 2
        elif rel1 == 'enemy' and rel2 == 'enemy':
            return 0
        else:
            return 3

# --- 4️⃣ RAJJU DOSHA ---
class RajjuDoshaAnalyzer:
    def __init__(self):
        self.rajju_map = self._build_rajju_map()
    
    def _build_rajju_map(self) -> Dict:
        """Build comprehensive Rajju mapping."""
        rajju_map = {}
        rajju_cycle = ['Sira', 'Kantha', 'Nabhi', 'Kati', 'Pada'] * 6
        
        nakshatras = [
            'Ashwini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashira', 'Ardra',
            'Punarvasu', 'Pushya', 'Ashlesha', 'Magha', 'Purva Phalguni', 'Uttara Phalguni',
            'Hasta', 'Chitra', 'Swati', 'Vishakha', 'Anuradha', 'Jyeshtha',
            'Mula', 'Purva Ashadha', 'Uttara Ashadha', 'Shravana', 'Dhanishta',
            'Shatabhisha', 'Purva Bhadrapada', 'Uttara Bhadrapada', 'Revati'
        ]
        
        for i, nakshatra in enumerate(nakshatras):
            for pada in range(1, 5):
                cycle_index = (i * 4 + (pada - 1)) % len(rajju_cycle)
                rajju_map[(nakshatra, pada)] = rajju_cycle[cycle_index]
                
        return rajju_map
    
    def analyze(self, k1, k2) -> Dict:  # Returns Dict instead of DoshaResult
        """Check if both nakshatra+pada fall in same Rajju → dosha."""
        n1 = getattr(k1, 'nakshatra', None)
        p1 = getattr(k1, 'nakshatra_pada', None)
        n2 = getattr(k2, 'nakshatra', None)
        p2 = getattr(k2, 'nakshatra_pada', None)
        
        if not all([n1, p1, n2, p2]):
            user_message = "⚠️ Could not check Rajju Dosha due to missing nakshatra data."
            return {
                'present': False,
                'cancelled': False,
                'severity': None,
                'reasons': ['Nakshatra or pada missing → cannot check Rajju'],
                'mitigations': [],
                'user_message': user_message
            }
        
        r1 = self.rajju_map.get((n1, p1))
        r2 = self.rajju_map.get((n2, p2))
        
        if not r1 or not r2:
            user_message = "⚠️ Could not determine Rajju Dosha due to calculation limitations."
            return {
                'present': False,
                'cancelled': False,
                'severity': None,
                'reasons': ['Incomplete Rajju mapping'],
                'mitigations': [],
                'user_message': user_message
            }
            
        if r1 == r2:
            user_message = f"⚠️ Rajju Dosha Present: Same Rajju ({r1}) may indicate longevity concerns. Consider astrological consultation."
            return {
                'present': True,
                'cancelled': False,
                'severity': None,
                'reasons': [f'Same Rajju ({r1}) → Rajju Dosha (longevity concern)'],
                'mitigations': [],
                'user_message': user_message
            }
        else:
            user_message = "✅ No Rajju Dosha: Different Rajju indicates good compatibility for married life."
            return {
                'present': False,
                'cancelled': False,
                'severity': None,
                'reasons': ['Different Rajju → no dosha'],
                'mitigations': [],
                'user_message': user_message
            }

# --- 5️⃣ VEDHA DOSHA ---
class VedhaDoshaAnalyzer:
    @staticmethod
    def analyze(k1, k2) -> Dict:  # Returns Dict instead of DoshaResult
        """Check Vedha = obstruction between certain Nakshatra pairs."""
        n1 = getattr(k1, 'nakshatra', None)
        n2 = getattr(k2, 'nakshatra', None)
        
        if not n1 or not n2:
            user_message = "⚠️ Could not check Vedha Dosha due to missing nakshatra data."
            return {
                'present': False,
                'cancelled': False,
                'severity': None,
                'reasons': ['Nakshatra data missing'],
                'mitigations': [],
                'user_message': user_message
            }
            
        if n2 in VEDHA_PAIRS.get(n1, []):
            user_message = f"⚠️ Vedha Dosha Present: {n1} and {n2} form a Vedha pair indicating potential obstacles."
            return {
                'present': True,
                'cancelled': False,
                'severity': None,
                'reasons': [f'{n1} ↔ {n2} Vedha pair → dosha'],
                'mitigations': [],
                'user_message': user_message
            }
        else:
            user_message = "✅ No Vedha Dosha: No planetary obstruction between your nakshatras."
            return {
                'present': False,
                'cancelled': False,
                'severity': None,
                'reasons': ['No Vedha between nakshatras'],
                'mitigations': [],
                'user_message': user_message
            }

class DoshaEvaluator:
    def __init__(self):
        self.mangal_analyzer = MangalDoshaAnalyzer()
        self.nadi_analyzer = NadiDoshaAnalyzer()
        self.bhakoot_analyzer = BhakootDoshaAnalyzer()
        self.rajju_analyzer = RajjuDoshaAnalyzer()
        self.vedha_analyzer = VedhaDoshaAnalyzer()
    
    def evaluate_all(self, k1, k2, ashtakoot_results: Dict = None, with_charts: bool = True) -> Dict:
        """Main orchestrator combining all dosha checks."""
        from .dosha_remedies import enrich
        _normalise_names(k1, k2)
        
        # Extract scores from ashtakoot results if provided
        nadi_score = None
        bhakoot_score = None
        
        if ashtakoot_results and 'koot_details' in ashtakoot_results:
            koot_details = ashtakoot_results['koot_details']
            nadi_score = koot_details.get('nadi', {}).get('score')
            bhakoot_score = koot_details.get('bhakoot', {}).get('score')
        
        report = {
            'nadi': self._analyze_nadi(k1, k2, nadi_score),
            'bhakoot': self._analyze_bhakoot(k1, k2, bhakoot_score),
            'rajju': self.rajju_analyzer.analyze(k1, k2),
            'vedha': self.vedha_analyzer.analyze(k1, k2)
        }
        if with_charts:                 # a Milan by name has no Mars to read
            report['mangal'] = self.mangal_analyzer.analyze_cancellation(k1, k2)
        else:
            report['mangal'] = {'partner1_manglik': False, 'partner2_manglik': False, 'cancelled': False}

        enrich(report, k1, k2)
        report['summary'] = self._generate_summary(report)
        report['overall_message'] = self._generate_overall_message(report)
        total = (ashtakoot_results or {}).get('total_score')
        serious = [k for k in ('nadi', 'rajju', 'vedha')
                   if report.get(k, {}).get('present') and not report.get(k, {}).get('cancelled')]
        if total is not None and total < 18:
            report['overall_message'] = (f"❌ Only {total}/36 gunas match - below the traditional minimum of 18. "
                                         "Marriage is generally not advised without a detailed chart analysis and remedies.")
        elif total is not None and total < 25 and not serious:
            report['overall_message'] = (f"✅ {total}/36 gunas: an acceptable match, above the traditional minimum of 18, "
                                         "with no serious dosha found in what was checked.")
        elif serious:
            names = ', '.join(s.title() for s in serious)
            report['overall_message'] = (f"⚠️ {total}/36 gunas, but uncancelled {names} Dosha present. "
                                         "See the remedies below and consult an acharya before deciding.")
        
        if not with_charts:
            report.pop('mangal')
        return report
    
    def _analyze_nadi(self, k1, k2, nadi_score: Optional[int]) -> Dict:
        """Analyze Nadi dosha with fallback calculation."""
        if nadi_score is None:
            try:
                # Use the actual nakshatra data from kundalis
                nakshatra1 = getattr(k1, 'nakshatra', None)
                nakshatra2 = getattr(k2, 'nakshatra', None)
                nadi_score = self._calculate_nadi(nakshatra1, nakshatra2)
            except Exception as e:
                return {
                    'present': False,
                    'cancelled': False,
                    'severity': None,
                    'reasons': [f'Nadi calculation failed: {str(e)}'],
                    'mitigations': [],
                    'user_message': "⚠️ Could not calculate Nadi compatibility due to technical error."
                }
        
        return self.nadi_analyzer.analyze(nadi_score) if nadi_score is not None else {
            'present': False,
            'cancelled': False,
            'severity': None,
            'reasons': ['Nadi score unavailable'],
            'mitigations': [],
            'user_message': "⚠️ Nadi score not available for analysis."
        }
    
    def _analyze_bhakoot(self, k1, k2, bhakoot_score: Optional[int]) -> Dict:
        """Analyze Bhakoot dosha with fallback calculation."""
        if bhakoot_score is None:
            try:
                # Use the actual rashi data from kundalis
                rashi1 = getattr(k1, 'rashi', None)
                rashi2 = getattr(k2, 'rashi', None)
                bhakoot_score = self._calculate_bhakoot(rashi1, rashi2)
            except Exception as e:
                return {
                    'present': False,
                    'cancelled': False,
                    'severity': None,
                    'reasons': [f'Bhakoot calculation failed: {str(e)}'],
                    'mitigations': [],
                    'user_message': "⚠️ Could not calculate Bhakoot compatibility due to technical error."
                }
        
        return self.bhakoot_analyzer.analyze(bhakoot_score, k1, k2) if bhakoot_score is not None else {
            'present': False,
            'cancelled': False,
            'severity': None,
            'reasons': ['Bhakoot score unavailable'],
            'mitigations': [],
            'user_message': "⚠️ Bhakoot score not available for analysis."
        }
    
    def _calculate_nadi(self, nakshatra1: str, nakshatra2: str) -> int:
        """Calculate Nadi score between two nakshatras."""
        if not nakshatra1 or not nakshatra2:
            return 0
            
        # Use the same nadi mapping as in calculate_nadi function
        nakshatra_nadi = {
            'Ashwini': 'Aadi', 'Ardra': 'Aadi', 'Punarvasu': 'Aadi', 
            'Uttara Phalguni': 'Aadi', 'Hasta': 'Aadi', 'Jyeshtha': 'Aadi',
            'Mula': 'Aadi', 'Shatabhisha': 'Aadi', 'Purva Bhadrapada': 'Aadi',
            
            'Bharani': 'Madhya', 'Mrigashira': 'Madhya', 'Pushya': 'Madhya',
            'Purva Phalguni': 'Madhya', 'Chitra': 'Madhya', 'Anuradha': 'Madhya',
            'Purva Ashadha': 'Madhya', 'Dhanishta': 'Madhya', 'Uttara Bhadrapada': 'Madhya',
            
            'Krittika': 'Antya', 'Rohini': 'Antya', 'Ashlesha': 'Antya',
            'Magha': 'Antya', 'Swati': 'Antya', 'Vishakha': 'Antya',
            'Uttara Ashadha': 'Antya', 'Shravana': 'Antya', 'Revati': 'Antya'
        }
        
        nadi1 = nakshatra_nadi.get(nakshatra1, '')
        nadi2 = nakshatra_nadi.get(nakshatra2, '')
        
        return 8 if nadi1 != nadi2 else 0
    
    def _calculate_bhakoot(self, rashi1: str, rashi2: str) -> int:
        """Calculate Bhakoot score between two rashis."""
        if not rashi1 or not rashi2:
            return 0
            
        rashi_order = ['Mesh', 'Vrishabh', 'Mithun', 'Kark', 'Simha', 'Kanya', 
                       'Tula', 'Vrishchik', 'Dhanu', 'Makar', 'Kumbh', 'Meen']
        
        try:
            boy_idx = rashi_order.index(rashi1)
            girl_idx = rashi_order.index(rashi2)
            
            # Count distance from boy's rashi (1st house) to girl's rashi
            distance = (girl_idx - boy_idx) % 12
            if distance == 0:
                distance = 12
            
            return 7 if distance in BHAKOOT_GOOD_DISTANCES else 0
        except ValueError:
            return 0
    
    def _generate_summary(self, report: Dict) -> List[str]:
        """Generate summary of all doshas found."""
        summary = []
        
        mangal = report['mangal']
        
        # Only add to summary if dosha is present AND not cancelled
        if (mangal['partner1_manglik'] or mangal['partner2_manglik']) and not mangal['cancelled']:
            if mangal['partner1_manglik']:
                summary.append('Partner1 Manglik')
            if mangal['partner2_manglik']:
                summary.append('Partner2 Manglik')
                
        if report['nadi']['present'] and not report['nadi']['cancelled']:
            summary.append('Nadi Dosha present')
        if report['bhakoot']['present'] and not report['bhakoot']['cancelled']:
            summary.append('Bhakoot Dosha present')
        for key in ('rajju', 'vedha', 'gana', 'yoni'):
            r = report.get(key) or {}
            if r.get('present') and not r.get('cancelled'):
                summary.append(f"{r.get('title', key.title() + ' Dosha')} present")
        for who, label in (('partner1', 'Boy'), ('partner2', 'Girl')):
            for d in report.get('individual', {}).get(who, {}).values():
                if d['present'] and not d['cancelled']:
                    summary.append(f"{label}: {d['title']}")

        return summary
    
    def _generate_overall_message(self, report: Dict) -> str:
        """Generate an overall compatibility message."""
        dosha_count = sum(
            bool(report.get(k, {}).get('present') and not report.get(k, {}).get('cancelled'))
            for k in ('nadi', 'bhakoot', 'rajju', 'vedha', 'gana')
        )
        
        mangal_issue = (report['mangal']['partner1_manglik'] or report['mangal']['partner2_manglik']) and not report['mangal']['cancelled']
        
        if dosha_count == 0 and not mangal_issue:
            return "🎉 Excellent Compatibility! No major doshas found. This indicates a very favorable match for marriage."
        elif dosha_count <= 1 and not mangal_issue:
            return "✅ Good Compatibility! Minor doshas present but overall favorable. Consider simple remedies if needed."
        elif dosha_count <= 2 or mangal_issue:
            return "⚠️ Moderate Compatibility. Some doshas present. Recommended to consult with an astrologer for detailed analysis and remedies."
        else:
            return "❌ Challenging Compatibility. Multiple doshas present. Strongly recommend detailed astrological consultation before proceeding."