import math
import re

SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", 
         "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]

def degrees_to_decimal(degrees, minutes=0, seconds=0):
    return degrees + minutes/60.0 + seconds/3600.0

def decimal_to_degrees(decimal_degrees):
    degrees = int(decimal_degrees)
    minutes_decimal = (decimal_degrees - degrees) * 60
    
    minutes = int(minutes_decimal)
    seconds = round((minutes_decimal - minutes) * 60)
    return degrees, minutes, seconds

def parse_jh_position(jh_string):
    """Parse JH position string like '18Ar29' or '6Cp58' into components"""
    match = re.match(r'(\d{1,2})([A-Za-z]{2})(\d{2})', jh_string)
    if match:
        deg_str = match.group(1)
        sign_str = match.group(2)
        min_str = match.group(3)
        return int(deg_str), sign_str, int(min_str)
    else:
        raise ValueError(f"Could not parse JH position: {jh_string}")

def get_jh_divisional_position(d1_sign_index, d1_longitude_decimal, divisional_factor, planet_name=None, rahu_d1_data=None):
    """
    Calculate divisional chart position with JH-compatible algorithms
    """
    division_size = 30.0 / divisional_factor
    division_index = int(d1_longitude_decimal // division_size)
    degree_in_division = d1_longitude_decimal % division_size
    
    # Calculate divisional degree
    divisional_longitude_decimal = (degree_in_division * divisional_factor) % 30
    
    # Handle Ketu (always opposite to Rahu in divisional charts)
    if planet_name == "Ketu" and rahu_d1_data:
        rahu_d1_sign, rahu_d1_degree = rahu_d1_data
        rahu_div_sign, rahu_div_long = get_jh_divisional_position(rahu_d1_sign, rahu_d1_degree, divisional_factor, "Rahu")
        ketu_div_sign = (rahu_div_sign + 6) % 12
        return ketu_div_sign, rahu_div_long
    
    # JH SEQUENCES FOR ALL DIVISIONS
    if divisional_factor == 1:  # D1 - Rasi
        divisional_sign_index = d1_sign_index
        
    elif divisional_factor == 2:  # D2 - Hora
        # Degree inside the sign
        degree_in_sign = d1_longitude_decimal % 30
        half_index = 0 if degree_in_sign < 15 else 1  # first half or second half

        hora_mapping = {
            0: [0, 1],    # Aries
            1: [3, 2],    # Taurus
            2: [4, 5],    # Gemini
            3: [7, 6],    # Cancer
            4: [8, 9],   # Leo
            5: [11, 10],   # Virgo
            6: [0, 1],    # Libra
            7: [3, 2],    # Scorpio - need to verify
            8: [4, 5],    # Sagittarius
            9: [7, 6],    # Capricorn
            10:[8, 9],    # Aquarius
            11:[11,10]    # Pisces
        }

        divisional_sign_index = hora_mapping[d1_sign_index][half_index]
        divisional_longitude_decimal = (d1_longitude_decimal % 15) * 2

        
    elif divisional_factor == 3:  # D3 - Drekkana
        # Degree inside the sign (0–30°)
        degree_in_sign = d1_longitude_decimal % 30
        drekkana_index = int(degree_in_sign // 10)  # 0–2

        drekkana_index_mapping = {
            0: [0, 4, 8],   
            1: [1,5,9], 
            2: [2,6,10],
            3: [3,7,11],
            4: [4,8,0],
            5: [5,9,1],
            6: [6,10,2],
            7: [7,11,3],
            8: [8,0,4],
            9: [9,1,5],
            10:[10,2,6],
            11:[11,3,7]
        }

        divisional_sign_index = drekkana_index_mapping[d1_sign_index][drekkana_index]
        divisional_longitude_decimal = (d1_longitude_decimal % 10) * 3


    elif divisional_factor == 4:  # D4 - Chaturthamsha
        # Degree inside the sign (0–30°)
        degree_in_sign = d1_longitude_decimal % 30
        quarter_index = int(degree_in_sign // 7.5)  # 0–3 (each part = 7°30′)

        d4_mapping = {
            0:  [0, 3, 6, 9],     # Aries
            1:  [1, 4, 7, 10],    # Taurus
            2:  [2, 5, 8, 11],    # Gemini
            3:  [3, 6, 9, 0],     # Cancer
            4:  [4, 7, 10, 1],    # Leo
            5:  [5, 8, 11, 2],    # Virgo
            6:  [6, 9, 0, 3],     # Libra
            7:  [7, 10, 1, 4],    # Scorpio
            8:  [8, 11, 2, 5],    # Sagittarius
            9:  [9, 0, 3, 6],     # Capricorn
            10: [10, 1, 4, 7],    # Aquarius
            11: [11, 2, 5, 8]     # Pisces
        }

        divisional_sign_index = d4_mapping[d1_sign_index][quarter_index]

        
    elif divisional_factor == 5:  # D5 - Panchamsa
        panchamsa_sequence = {
            0: [0, 10, 8, 2, 6], 1: [1, 5, 11, 9, 7],
            2: [0, 10, 8, 2, 6], 3: [1, 5, 11, 9, 7],
            4: [0, 10, 8, 2, 6], 5: [1, 5, 11, 9, 7],
            6: [0, 10, 8, 2, 6], 7: [1, 5, 11, 9, 7],
            8: [0, 10, 8, 2, 6], 9: [1, 5, 11, 9, 7],
            10: [0, 10, 8, 2, 6], 11: [1, 5, 11, 9, 7],
        }
        divisional_sign_index = panchamsa_sequence[d1_sign_index][division_index]
        
    elif divisional_factor == 6:  # D6 - Shashthamsa
        shashthamsa_sequence = {
            0: [0, 1 , 2, 3, 4 , 5], 1: [6, 7, 8, 9, 10, 11],
            2: [0, 1 , 2, 3, 4 , 5], 3: [6, 7, 8, 9, 10, 11],
            4: [0, 1 , 2, 3, 4 , 5], 5: [6, 7, 8, 9, 10, 11],
            6: [0, 1 , 2, 3, 4 , 5], 7: [6, 7, 8, 9, 10, 11],
            8: [0, 1 , 2, 3, 4 , 5], 9: [6, 7, 8, 9, 10, 11],
            10: [0, 1 , 2, 3, 4 , 5], 11: [6, 7, 8, 9, 10, 11],
        }
        divisional_sign_index = shashthamsa_sequence[d1_sign_index][division_index]
        
    elif divisional_factor == 7:  # D7 - Saptamsa
        saptamsa_sequence = {
            0: [0, 1, 2, 3, 4, 5, 6], 1: [7, 8, 9, 10, 11, 0, 1],
            2: [2, 3, 4, 5, 6, 7, 8], 3: [9, 10, 11, 0, 1, 2, 3],
            4: [4, 5, 6, 7, 8, 9, 10], 5: [11, 0, 1, 2, 3, 4, 5],
            6: [6, 7, 8, 9, 10, 11, 0], 7: [1, 2, 3, 4, 5, 6, 7],
            8: [8, 9, 10, 11, 0, 1, 2], 9: [3, 4, 5, 6, 7, 8, 9],
            10: [10, 11, 0, 1, 2, 3, 4], 11: [5, 6, 7, 8, 9, 10, 11],
        }
        divisional_sign_index = saptamsa_sequence[d1_sign_index][division_index]
        
    elif divisional_factor == 8:  # D8 - Ashtamsa
        ashtamsa_sequence = {
            0: [0, 1, 2, 3, 4, 5, 6, 7], 1: [8, 9, 10, 11, 0, 1, 2, 3],
            2: [4, 5, 6, 7, 8, 9, 10, 11], 3: [0, 1, 2, 3, 4, 5, 6, 7],
            4: [8, 9, 10, 11, 0, 1, 2, 3], 5: [4, 5, 6, 7, 8, 9, 10, 11],
            6: [0, 1, 2, 3, 4, 5, 6, 7], 7: [8, 9, 10, 11, 0, 1, 2, 3],
            8: [4, 5, 6, 7, 8, 9, 10, 11], 9: [0, 1, 2, 3, 4, 5, 6, 7],
            10: [8, 9, 10, 11, 0, 1, 2, 3], 11: [4, 5, 6, 7, 8, 9, 10, 11],
        }
        divisional_sign_index = ashtamsa_sequence[d1_sign_index][division_index]
        
    elif divisional_factor == 9:  # D9 - Navamsa (robust)
        # Convert D1 sign + degree_in_sign into absolute longitude
        d1_abs_long = d1_sign_index * 30.0 + d1_longitude_decimal

        # D9 absolute longitude
        d9_abs_long = (d1_abs_long * 9) % 360.0

        # Convert back to sign + degree_in_sign
        divisional_sign_index = int(d9_abs_long // 30.0)
        divisional_degree_in_sign = d9_abs_long % 30.0

        # Round to minutes
        deg = int(math.floor(divisional_degree_in_sign))
        mins = int(round((divisional_degree_in_sign - deg) * 60))
        if mins == 60:
            deg += 1
            mins = 0
        if deg == 30:
            deg = 0
            divisional_sign_index = (divisional_sign_index + 1) % 12

        divisional_longitude_decimal = deg + mins / 60.0

    elif divisional_factor == 10:  # D10 - Dasamsa
        rudramsa_sequence = {
            0: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
            1: [9, 10, 11, 0, 1, 2, 3, 4, 5, 6],
            2: [2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
            3: [11, 0, 1, 2, 3, 4, 5, 6, 7, 8],
            4: [4, 5, 6, 7, 8, 9, 10, 11, 0, 1],
            5: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            6: [6, 7, 8, 9, 10, 11, 0, 1, 2, 3],
            7: [3, 4, 5, 6, 7, 8, 9, 10, 11, 0],
            8: [8, 9, 10, 11, 0, 1, 2, 3, 4, 5],
            9: [5, 6, 7, 8, 9, 10, 11, 0, 1, 2],
            10: [10, 11, 0, 1, 2, 3, 4, 5, 6, 7],
            11: [7, 8, 9, 10, 11, 0, 1, 2, 3, 4],
        }
        divisional_sign_index = rudramsa_sequence[d1_sign_index][division_index]

    elif divisional_factor == 11:  # D11 - Rudramsa
        rudramsa_sequence = {
            0: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            1: [11, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
            2: [10, 11, 0, 1, 2, 3, 4, 5, 6, 7, 8],
            3: [9, 10, 11, 0, 1, 2, 3, 4, 5, 6, 7],
            4: [8, 9, 10, 11, 0, 1, 2, 3, 4, 5, 6],
            5: [7, 8, 9, 10, 11, 0, 1, 2, 3, 4, 5],
            6: [6, 7, 8, 9, 10, 11, 0, 1, 2, 3, 4],
            7: [5, 6, 7, 8, 9, 10, 11, 0, 1, 2, 3],
            8: [4, 5, 6, 7, 8, 9, 10, 11, 0, 1, 2],
            9: [3, 4, 5, 6, 7, 8, 9, 10, 11, 0, 1],
            10: [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 0],
            11: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
        }
        divisional_sign_index = rudramsa_sequence[d1_sign_index][division_index]
        
    elif divisional_factor == 12:  # D12 - Dwadasamsa
        divisional_sign_index = (d1_sign_index + division_index) % 12
        
    elif divisional_factor == 16:  # D16
        divisional_sign_index = (d1_sign_index * 16 + division_index) % 12
        
    elif divisional_factor == 20:  # D20
        divisional_sign_index = (d1_sign_index * 20 + division_index) % 12
        
    elif divisional_factor == 24:  # D24
        divisional_sign_index = (d1_sign_index*24 + division_index) % 12
        
    elif divisional_factor == 27:  # D27
        divisional_sign_index = (d1_sign_index * 27 + division_index) % 12
        
    elif divisional_factor == 30:  # D30
        # Define the two patterns
        odd_sign_pattern = [1, 1, 1, 1, 1, 5, 5, 5, 5, 5, 5, 5, 11, 11, 11, 11, 11, 11, 11, 11, 3, 3, 3, 3, 3, 7, 7, 7, 7, 7]
        even_sign_pattern = [0, 0, 0, 0, 0, 10, 10, 10, 10, 10, 8, 8, 8, 8, 8, 8, 8, 8, 2, 2, 2, 2, 2, 2, 2, 6, 6, 6, 6, 6]
        
        if d1_sign_index % 2 == 1:  # Odd signs
            divisional_sign_index = odd_sign_pattern[division_index]
        else:  # Even signs
            divisional_sign_index = even_sign_pattern[division_index]
            
    elif divisional_factor == 40:  # D40
        divisional_sign_index = (d1_sign_index * 40 + division_index) % 12
        
    elif divisional_factor == 45:  # D45
        divisional_sign_index = (d1_sign_index * 45 + division_index) % 12
        
    elif divisional_factor == 60:  # D60
        divisional_sign_index = (d1_sign_index * 60 + division_index) % 12
        
    elif divisional_factor == 81:  # D81
        divisional_sign_index = (d1_sign_index * 81 + division_index) % 12
        
    elif divisional_factor == 108:  # D108
        divisional_sign_index = (d1_sign_index + 9) % 12
        
    elif divisional_factor == 144:  # D144
        jhora_d144_sequence = {
            # Aries:    0°,    2.5°,  5°,    7.5°,  10°,   12.5°, 15°,   17.5°, 20°,   22.5°, 25°,   27.5°
            0: [0,      6,      1,     7,     2,     8,     0,     8,     3,     9,     4,     10],    # Aries
            1: [6,      0,      7,     1,     8,     2,     9,     3,     10,    4,     11,    3],     # Taurus  
            2: [1,      7,      2,     8,     3,     9,     4,     6,     0,     10,    5,     11],    # Gemini
            3: [2,      2,      3,     9,     4,     10,    5,     11,    6,     11,    0,     7],     # Cancer
            4: [3,      9,      4,     9,     10,    4,     11,    5,     0,     6,     1,     1],     # Leo
            5: [9,      3,      10,    4,     11,    5,     0,     3,     6,     1,     7,     4],     # Virgo
            6: [4,      10,     5,     9,     11,    5,     0,     6,     1,     11,    7,     2],     # Libra
            7: [5,      11,     6,     9,     0,     6,     6,     1,     7,     4,     8,     1],     # Scorpio
            8: [6,      0,      7,     1,     8,     2,     9,     9,     3,     10,    4,     11],    # Sagittarius
            9: [6,      2,      7,     1,     8,     2,     9,     3,     10,    0,     4,     5],     # Capricorn
            10: [7,      1,      8,     2,     9,     6,     3,     10,    4,     11,    5,     0],    # Aquarius
            11: [8,      2,      9,     3,     10,    7,     4,     11,    5,     0,     6,     1]     # Pisces
        }
        
        segment = int(d1_longitude_decimal // 2.5)
        divisional_sign_index = jhora_d144_sequence[d1_sign_index][segment]
        
        # Calculate divisional longitude
        remainder_degrees = d1_longitude_decimal % 2.5
        divisional_longitude_decimal = remainder_degrees * 12

    else:
        divisional_sign_index = (d1_sign_index * divisional_factor + division_index) % 12
    
    return divisional_sign_index, divisional_longitude_decimal

def calculate_divisional_ascendant(d1_asc_sign, d1_asc_deg, d1_asc_min, divisional_factor):
    """
    Calculate divisional chart ascendant
    Same logic as planetary positions but for ascendant
    """
    d1_asc_decimal = degrees_to_decimal(d1_asc_deg, d1_asc_min)
    div_asc_sign, div_asc_long = get_jh_divisional_position(d1_asc_sign, d1_asc_decimal, divisional_factor)
    div_asc_deg, div_asc_min, _ = decimal_to_degrees(div_asc_long)
    return SIGNS[div_asc_sign], div_asc_deg, div_asc_min

def find_house_position(planet_sign, planet_deg, planet_min, ascendant_sign, ascendant_deg, ascendant_min):
    """
    Find which house a planet is in based on ascendant
    Returns house number (1-12)
    """
    # Convert to decimal for precise calculation
    planet_decimal = degrees_to_decimal(planet_deg, planet_min) + (planet_sign * 30)
    ascendant_decimal = degrees_to_decimal(ascendant_deg, ascendant_min) + (ascendant_sign * 30)
    
    # Calculate house difference
    difference = (planet_decimal - ascendant_decimal) % 360
    house_number = int(difference // 30) + 1
    
    return house_number

def calculate_all_divisionals_with_houses(planet_data, d1_asc_data, rahu_d1_data=None):
    """
    Calculate all divisional charts for a planet WITH HOUSE POSITIONS
    Returns: dictionary with divisional positions and houses
    """
    d1_sign, d1_deg, d1_min, planet_name = planet_data
    d1_asc_sign, d1_asc_deg, d1_asc_min = d1_asc_data
    
    d1_decimal = degrees_to_decimal(d1_deg, d1_min)
    
    divisions = [
        ("D1", 1), ("D9", 9), ("D10", 10), ("D2", 2), ("D3", 3), ("D4", 4),
        ("D7", 7), ("D12", 12), ("D16", 16), ("D20", 20), ("D24", 24),
        ("D27", 27), ("D30", 30), ("D40", 40), ("D45", 45), ("D60", 60),
        ("D5", 5), ("D6", 6), ("D8", 8), ("D11", 11), ("D81", 81),
        ("D108", 108), ("D144", 144)
    ]
    
    results = {}
    house_results = {}
    
    for div_name, div_factor in divisions:
        if div_name == "D1":
            sign, deg, min_val = SIGNS[d1_sign], d1_deg, d1_min
            div_asc_sign, div_asc_deg, div_asc_min = SIGNS[d1_asc_sign], d1_asc_deg, d1_asc_min
        else:
            # Calculate planet position
            sign_idx, div_long = get_jh_divisional_position(d1_sign, d1_decimal, div_factor, planet_name, rahu_d1_data)
            sign = SIGNS[sign_idx]
            deg, min_val, _ = decimal_to_degrees(div_long)
            
            # Calculate divisional ascendant
            div_asc_sign, div_asc_deg, div_asc_min = calculate_divisional_ascendant(d1_asc_sign, d1_asc_deg, d1_asc_min, div_factor)
        
        # Calculate house position
        house_number = find_house_position(
            SIGNS.index(sign), deg, min_val,
            SIGNS.index(div_asc_sign), div_asc_deg, div_asc_min
        )
        
        results[div_name] = f"{deg:02d}{sign[:3]}{min_val:02d}"
        house_results[div_name] = f"H{house_number}"
    
    return results, house_results

def generate_complete_divisional_table_with_houses():
    """
    Generate complete divisional table for all planets WITH HOUSE POSITIONS
    """
    # D1 Ascendant data
    d1_asc_data = (9, 3, 27)  # Aries 24°14'
    
    # Planet D1 positions
    planets_d1 = [
        # (sign_index, degrees, minutes, planet_name)
        (9, 3, 27, "Asc"),    # Aries 24°14'
        (4, 8, 40, "Sun"),    # Taurus 22°16'
        (1, 28, 19, "Moon"),     # Libra 4°01'
        (5, 9, 54, "Mars"),     # Leo 0°03'
        (5, 0, 51, "Mercury"), # Gemini 1°40'
        (8, 18, 52, "Jupiter"),  # Gemini 5°08'
        (4, 29, 44, "Venus"),   # Aries 6°32'
        (4, 16, 45, "Saturn"), # Pisces 6°39'
        (9, 23, 48, "Rahu"),  # Aquarius 29°38'
        (3, 23, 48, "Ketu"),   # Leo 29°38'
    ]
    
    
    rahu_d1_data = (8, degrees_to_decimal(19, 50))
    
    divisions_order = ["D1", "D9", "D10", "D2", "D3", "D4", "D7", "D12", "D16", 
                     "D20", "D24", "D27", "D30", "D40", "D45", "D60", "D5", 
                     "D6", "D8", "D11", "D81", "D108", "D144"]
    
    # Calculate all divisional charts with houses
    all_results = {}
    all_houses = {}
    
    for planet_data in planets_d1:
        planet_name = planet_data[3]
        if planet_name == "Ketu":
            results, houses = calculate_all_divisionals_with_houses(planet_data, d1_asc_data, rahu_d1_data)
        else:
            results, houses = calculate_all_divisionals_with_houses(planet_data, d1_asc_data)
        all_results[planet_name] = results
        all_houses[planet_name] = houses
    
    # Generate table with positions and houses
    header = ["Body"] + divisions_order
    
    table_rows = []
    for planet_name in ["Asc", "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]:
        row = [planet_name]
        for division in divisions_order:
            position = all_results[planet_name][division]
            house = all_houses[planet_name][division]
            row.append(f"{position}({house})")
        table_rows.append(row)
    
    return header, table_rows

def print_table(header, rows):
    """Print the table in a formatted way"""
    col_widths = [len(str(col)) for col in header]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))
    
    # Print header
    header_line = " | ".join(f"{header[i]:<{col_widths[i]}}" for i in range(len(header)))
    separator = "-+-".join("-" * col_widths[i] for i in range(len(header)))
    
    print(header_line)
    print(separator)
    
    # Print rows
    for row in rows:
        row_line = " | ".join(f"{row[i]:<{col_widths[i]}}" for i in range(len(row)))
        print(row_line)

# MAIN EXECUTION
if __name__ == "__main__":
    print("COMPLETE DIVISIONAL CHART TABLE WITH HOUSE POSITIONS")
    print("=" * 150)
    
    header, table_rows = generate_complete_divisional_table_with_houses()
    print_table(header, table_rows)
    
    print("\n" + "=" * 150)
    print("FORMAT: SignDegMin(House) - e.g., 'Ar2414(H1)' = Aries 24°14' in 1st House")
    print("Sign abbreviations: Ar=Aries, Ta=Taurus, Ge=Gemini, Cn=Cancer, Le=Leo, Vi=Virgo")
    print("                   Li=Libra, Sc=Scorpio, Sg=Sagittarius, Cp=Capricorn, Aq=Aquarius, Pi=Pisces")