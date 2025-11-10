import swisseph as swe
from datetime import datetime, timedelta
import math
import pytz

class KundaliCalculator:
    def __init__(self, birth_datetime, lat, lon, tz_offset):
        self.birth_datetime = birth_datetime
        self.lat = lat
        self.lon = lon
        self.tz_offset = tz_offset
        self.julian_day = self.get_julian_day()
        
    def get_julian_day(self):
        dt = self.birth_datetime
        return swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute/60.0)
    
    def calculate_ascendant(self):
        """Calculate Lagna (Ascendant)"""
        jd = self.julian_day
        try:
            houses = swe.houses(jd, self.lat, self.lon, b'P')  # Placidus house system
            return houses[0][0]  # Ascendant longitude
        except:
            # Fallback calculation
            return (swe.sidtime(jd) * 15 + self.lon) % 360
    
    def calculate_planetary_positions(self):
        """Calculate positions of all planets"""
        planets = {
            swe.SUN: "Sun", 
            swe.MOON: "Moon", 
            swe.MARS: "Mars", 
            swe.MERCURY: "Mercury", 
            swe.JUPITER: "Jupiter", 
            swe.VENUS: "Venus", 
            swe.SATURN: "Saturn",
            swe.MEAN_NODE: "Rahu"
            # Ketu is opposite to Rahu
        }
        
        positions = {}
        ayanamsa = swe.get_ayanamsa_ut(self.julian_day)
        
        for planet_id, planet_name in planets.items():
            try:
                pos, flags = swe.calc_ut(self.julian_day, planet_id)
                longitude = (pos[0] - ayanamsa) % 360
                
                # Calculate Ketu (opposite of Rahu)
                if planet_name == "Rahu":
                    ketu_longitude = (longitude + 180) % 360
                    positions["Ketu"] = {
                        'longitude': ketu_longitude,
                        'sign': self.get_zodiac_sign(ketu_longitude),
                        'house': self.get_house_number(ketu_longitude),
                        'nakshatra': self.get_nakshatra(ketu_longitude),
                        'degree': round(ketu_longitude % 30, 2)
                    }
                
                positions[planet_name] = {
                    'longitude': longitude,
                    'sign': self.get_zodiac_sign(longitude),
                    'house': self.get_house_number(longitude),
                    'nakshatra': self.get_nakshatra(longitude),
                    'degree': round(longitude % 30, 2)
                }
            except Exception as e:
                print(f"Error calculating {planet_name}: {e}")
                positions[planet_name] = {
                    'longitude': 0,
                    'sign': 'Unknown',
                    'house': 0,
                    'nakshatra': 'Unknown',
                    'degree': 0
                }
        
        return positions
    
    def calculate_divisional_charts(self):
        """Calculate D1 to D12 charts dynamically (in memory)"""
        d1_positions = self.calculate_planetary_positions()
        
        divisional_factors = {
            'd1': 1,
            'd2': 2,
            'd3': 3,
            'd4': 4,
            'd5': 5,
            'd7': 7,
            'd9': 9,
            'd12': 12
        }
        
        divisional_charts = {}
        
        for chart_name, factor in divisional_factors.items():
            chart_positions = {}
            for planet, data in d1_positions.items():
                long_div = (data['longitude'] * factor) % 360
                chart_positions[planet] = {
                    'longitude': long_div,
                    'sign': self.get_zodiac_sign(long_div),
                    'house': self.get_house_number(long_div),
                    'nakshatra': self.get_nakshatra(long_div),
                    'degree': round(long_div % 30, 2)
                }
            divisional_charts[chart_name] = chart_positions
        
        return divisional_charts

    def get_zodiac_sign(self, longitude):
        signs = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
                "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
        index = int(longitude // 30) % 12
        return signs[index]
    
    def get_house_number(self, longitude):
        """Calculate which house the planet is in"""
        try:
            ascendant = self.calculate_ascendant()
            house_size = 30  # Each house is 30 degrees
            difference = (longitude - ascendant) % 360
            house_num = int(difference // house_size) + 1
            return min(max(house_num, 1), 12)  # Ensure between 1-12
        except:
            return 1  # Fallback to first house
    
    def get_nakshatra(self, longitude):
        nakshatras = ["Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
                     "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
                     "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
                     "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
                     "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"]
        nakshatra_size = 360 / 27
        index = int(longitude // nakshatra_size) % 27
        return nakshatras[index]
    
    def calculate_dasha_periods(self):
        """Calculate Vimshottari Dasha periods"""
        try:
            moon_longitude = self.calculate_planetary_positions()['Moon']['longitude']
            nakshatra_size = 360 / 27
            nakshatra_index = int(moon_longitude // nakshatra_size)
            
            # Dasha order and durations (in years)
            dasha_sequence = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", 
                             "Jupiter", "Saturn", "Mercury"]
            dasha_durations = [7, 20, 6, 10, 7, 18, 16, 19, 17]
            
            # Find current dasha starting point
            current_nakshatra_start = nakshatra_index * nakshatra_size
            degrees_into_nakshatra = (moon_longitude - current_nakshatra_start) % 360
            percent_complete = degrees_into_nakshatra / nakshatra_size
            
            # Calculate dashas
            dashas = []
            birth_date = self.birth_datetime
            
            # Start with current dasha
            current_dasha_index = nakshatra_index % 9
            remaining_years = dasha_durations[current_dasha_index] * (1 - percent_complete)
            
            start_date = birth_date
            for i in range(9):  # Calculate next 9 periods (120 years coverage)
                dasha_index = (current_dasha_index + i) % 9
                planet = dasha_sequence[dasha_index]
                total_duration = dasha_durations[dasha_index]
                
                if i == 0:  # First period is remaining part of current dasha
                    duration_years = remaining_years
                else:
                    duration_years = total_duration
                    
                end_date = start_date + timedelta(days=duration_years * 365.25)
                
                dashas.append({
                    'planet': planet,
                    'type': 'mahadasha',
                    'start_date': start_date,
                    'end_date': end_date,
                    'duration_years': round(duration_years, 2)
                })
                
                # Calculate sub-periods (Antardasha)
                sub_dashas = self.calculate_antardasha(start_date, planet, duration_years)
                dashas.extend(sub_dashas)
                
                start_date = end_date
            
            return dashas
        except Exception as e:
            print(f"Error calculating dasha periods: {e}")
            return []
    
    def calculate_antardasha(self, start_date, mahadasha_planet, duration_years):
        """Calculate Antardasha periods"""
        try:
            sub_sequence = ["Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", 
                           "Mercury", "Ketu", "Venus"]
            sub_durations = [6, 10, 7, 18, 16, 19, 17, 7, 20]  # Proportional years
            
            total_duration = sum(sub_durations)
            sub_dashas = []
            
            current_start = start_date
            for i, planet in enumerate(sub_sequence):
                sub_duration_years = (sub_durations[i] / total_duration) * duration_years
                end_date = current_start + timedelta(days=sub_duration_years * 365.25)
                
                sub_dashas.append({
                    'planet': planet,
                    'type': 'antardasha',
                    'mahadasha_planet': mahadasha_planet,
                    'start_date': current_start,
                    'end_date': end_date,
                    'duration_years': round(sub_duration_years, 2)
                })
                
                current_start = end_date
            
            return sub_dashas
        except Exception as e:
            print(f"Error calculating antardasha: {e}")
            return []

    # Helper functions
    def calculate_aspect(planet, current_data, birth_data):
        """Calculate planetary aspects"""
        try:
            current_house = current_data.get('house', 1)
            birth_house = birth_data.get('house', 1)
            
            aspect_diff = abs(current_house - birth_house)
            if aspect_diff == 0:
                return "Conjunction"
            elif aspect_diff in [3, 6, 9]:
                return "Strong Aspect"
            elif aspect_diff in [1, 2, 4, 5, 7, 8, 10, 11]:
                return "Weak Aspect"
            else:
                return "Neutral"
        except:
            return "Unknown"

    def get_influence_level(planet, current_data, birth_data):
        """Determine influence level of transit"""
        try:
            current_house = current_data.get('house', 1)
            birth_house = birth_data.get('house', 1)
            
            if current_house == birth_house:
                return "Strong Influence"
            elif abs(current_house - birth_house) in [1, 5, 9]:
                return "Moderate Influence"
            else:
                return "Mild Influence"
        except:
            return "Unknown"
    
    def calculate_all_data(self):
        """Main entrypoint to compute full Kundali"""
        jd_ut = self._get_julian_day()

        # Example: get ascendant
        ascendant = self._calculate_ascendant(jd_ut)

        # Example: get planet positions
        planets = self._calculate_planets(jd_ut)

        # Example: dashas
        dashas = self._calculate_dashas(jd_ut)

        return {
            "ascendant": ascendant,
            "d1_chart": planets,
            "structured_dashas": dashas,
            "calculation_time": self.birth_datetime.isoformat()
        }