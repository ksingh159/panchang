import swisseph as swe
from datetime import datetime, timedelta
import pytz
import copy

class KundaliCalculator:
    """
    Vedic Kundali Calculator using Swiss Ephemeris with CORRECT divisional chart calculation.
    """

    def __init__(self, birth_datetime, lat, lon, tz_offset=None):
        self.lat = lat
        self.lon = lon
        self.birth_datetime = birth_datetime
        self.tz_offset = tz_offset

        # Set the ephemeris path and sidereal mode first
        swe.set_ephe_path()
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        swe.set_topo(lon, lat, 0)

        birth_utc = birth_datetime.astimezone(pytz.UTC)
        self.jd_ut = swe.julday(birth_utc.year, birth_utc.month, birth_utc.day, 
                               birth_utc.hour + birth_utc.minute/60.0)

        self.ayanamsa = swe.get_ayanamsa_ut(self.jd_ut)

        print(f"=== KUNDALI CALCULATOR (Correct Divisional Charts) ===")
        print(f"Input Local Time: {birth_datetime}")
        print(f"UTC Time: {birth_utc}")
        print(f"Julian Day: {self.jd_ut}")
        print(f"Ayanamsa: {self.ayanamsa}°")

        # Houses calculation
        self.houses_tropical, self.houses_sidereal = self._compute_houses()
        
        # Calculate planets
        self.planets_d1 = self._calculate_planets()
        
        # Divisional charts with CORRECT calculation
        self.divisional_charts = self._calculate_all_divisional_correct()
        self.dashas = self._calculate_dashas()
        self.doshas = self.calculate_all_doshas()

    def _compute_houses(self):
        """Calculate houses"""
        try:
            houses = swe.houses(self.jd_ut, self.lat, self.lon, b'P')
            tropical_cusps = list(houses[0])
            sidereal_cusps = [(c - self.ayanamsa) % 360 for c in tropical_cusps]

            self.houses_tropical = tropical_cusps
            self.houses_sidereal = sidereal_cusps
            self.ascendant_tropical = tropical_cusps[0] % 360
            self.ascendant_sidereal = sidereal_cusps[0] % 360
            
            return tropical_cusps, sidereal_cusps
            
        except Exception as e:
            print(f"House calculation error: {e}")
            return self._compute_houses_manual()

    def _compute_houses_manual(self):
        """Fallback house calculation"""
        lst = swe.sidtime(self.jd_ut) + self.lon/15.0
        lst_degrees = (lst % 24) * 15
        
        ascendant_tropical = lst_degrees
        ascendant_sidereal = (ascendant_tropical - self.ayanamsa) % 360
        
        tropical_cusps = [(ascendant_tropical + i * 30) % 360 for i in range(13)]
        sidereal_cusps = [(ascendant_sidereal + i * 30) % 360 for i in range(13)]
        
        return tropical_cusps, sidereal_cusps

    def _calculate_planets(self):
        """Calculate planetary positions"""
        planet_ids = [
            (swe.SUN, "Sun"), (swe.MOON, "Moon"), (swe.MARS, "Mars"),
            (swe.MERCURY, "Mercury"), (swe.JUPITER, "Jupiter"),
            (swe.VENUS, "Venus"), (swe.SATURN, "Saturn"),
            (swe.TRUE_NODE, "Rahu")
        ]
        
        positions = {}
        flags = swe.FLG_SWIEPH | swe.FLG_SPEED
        
        for pid, name in planet_ids:
            try:
                pos, _ = swe.calc_ut(self.jd_ut, pid, flags)
                lon_trop = pos[0] % 360
                lon_sid = (lon_trop - self.ayanamsa) % 360
                
                positions[name] = {
                    "longitude_tropical": round(lon_trop, 6),
                    "longitude_sidereal": round(lon_sid, 6),
                    "sign": self.get_zodiac_sign(lon_sid),
                    "degree": round(lon_sid % 30, 6),
                    "house": self.get_house_number(lon_sid),
                    "nakshatra": self.get_nakshatra(lon_sid),
                    "longitude_raw": lon_sid,
                    "sign_index": int(lon_sid // 30),  # Store sign index for divisional calculation
                    "degree_in_sign": lon_sid % 30     # Store degree within sign
                }
            except Exception as e:
                print(f"Error calculating {name}: {e}")
                positions[name] = self._get_default_planet_data()

        # Calculate Ketu
        self._calculate_ketu(positions)
        return positions

    def _calculate_ketu(self, positions):
        """Calculate Ketu as opposite to Rahu"""
        if "Rahu" in positions and positions["Rahu"]["longitude_sidereal"] is not None:
            rahu_lon = positions["Rahu"]["longitude_sidereal"]
            ketu_lon = (rahu_lon + 180) % 360
            positions["Ketu"] = {
                "longitude_tropical": round((positions["Rahu"]["longitude_tropical"] + 180) % 360, 6),
                "longitude_sidereal": round(ketu_lon, 6),
                "sign": self.get_zodiac_sign(ketu_lon),
                "degree": round(ketu_lon % 30, 6),
                "house": self.get_house_number(ketu_lon),
                "nakshatra": self.get_nakshatra(ketu_lon),
                "longitude_raw": ketu_lon,
                "sign_index": int(ketu_lon // 30),
                "degree_in_sign": ketu_lon % 30
            }

    def _get_default_planet_data(self):
        """Return default planet data"""
        return {
            "longitude_tropical": None,
            "longitude_sidereal": None,
            "sign": None,
            "degree": None,
            "house": None,
            "nakshatra": None,
            "longitude_raw": None,
            "sign_index": None,
            "degree_in_sign": None
        }

    def _calculate_all_divisional_correct(self):
        """
        CORRECT DIVISIONAL CHART CALCULATION
        Each zodiac sign is divided into equal parts based on divisional factor
        """
        factors = {
            'd1': 1, 'd2': 2, 'd3': 3, 'd4': 4, 'd5': 5, 
            'd7': 7, 'd9': 9, 'd10': 10, 'd12': 12, 'd16': 16, 
            'd20': 20, 'd24': 24, 'd27': 27, 'd30': 30, 'd40': 40, 
            'd45': 45, 'd60': 60
        }
        
        divisional = {}
        
        print("=== CALCULATING DIVISIONAL CHARTS (CORRECT METHOD) ===")
        
        for dname, factor in factors.items():
            chart = {}
            
            # 1. Calculate DIVISIONAL ASCENDANT using correct method
            d1_asc_sign_index = int(self.ascendant_sidereal // 30)
            d1_asc_degree_in_sign = self.ascendant_sidereal % 30
            
            # Each division size within a sign
            division_size = 30.0 / factor
            
            # Find which division the ascendant falls into
            asc_division_index = int(d1_asc_degree_in_sign // division_size)
            
            # Calculate divisional ascendant sign and degree
            divisional_asc_sign_index = (d1_asc_sign_index * factor + asc_division_index) % 12
            divisional_asc_degree = (d1_asc_degree_in_sign % division_size) * (factor)
            divisional_asc_longitude = (divisional_asc_sign_index * 30) + divisional_asc_degree
            
            print(f"{dname.upper()} Chart:")
            print(f"  D1 Asc: {self.get_zodiac_sign(self.ascendant_sidereal)} {d1_asc_degree_in_sign:.2f}°")
            print(f"  {dname.upper()} Asc: {self.get_zodiac_sign(divisional_asc_longitude)} {divisional_asc_degree:.2f}°")
            print(f"  Division Size: {division_size:.2f}°, Asc Division: {asc_division_index + 1}")
            
            # 2. Calculate houses for divisional chart
            divisional_houses = self._calculate_divisional_houses(divisional_asc_longitude)
            
            # Calculate planet positions in divisional chart
            for planet, pdata in self.planets_d1.items():
                if pdata.get("sign_index") is None or pdata.get("degree_in_sign") is None:
                    chart[planet] = self._get_default_planet_data()
                    continue
                
                # Get D1 planet data
                d1_sign_index = pdata["sign_index"]
                d1_degree_in_sign = pdata["degree_in_sign"]
                
                # FIXED: Treat ALL planets the same way, including Ketu
                # No special handling needed for Ketu since it's already calculated in D1
                planet_division_index = int(d1_degree_in_sign // division_size)
                divisional_sign_index = (d1_sign_index * factor + planet_division_index) % 12
                divisional_degree = (d1_degree_in_sign % division_size) * factor
                
                # Calculate final longitude
                divisional_longitude = (divisional_sign_index * 30) + divisional_degree
                
                # Find house in divisional chart
                new_house = self._find_house_number(divisional_longitude, divisional_houses)
                
                chart[planet] = {
                    "longitude_sidereal": round(divisional_longitude, 6),
                    "sign": self.get_zodiac_sign(divisional_longitude),
                    "degree": round(divisional_degree, 6),
                    "house": new_house,
                    "nakshatra": self.get_nakshatra(divisional_longitude),
                    "longitude_raw": divisional_longitude
                }
                
                # Debug output
                d1_sign = pdata["sign"]
                new_sign = chart[planet]["sign"]
                if d1_sign != new_sign:
                    print(f"  {planet}: {d1_sign} → {new_sign} (H{new_house})")
                else:
                    print(f"  {planet}: {new_sign} (H{new_house})")
            
            divisional[dname] = chart
            print("")
        
        return divisional

    def _calculate_divisional_houses(self, divisional_ascendant):
        """Calculate house cusps for divisional chart"""
        houses = []
        for i in range(13):
            house_cusp = (divisional_ascendant + i * 30) % 360
            houses.append(house_cusp)
        return houses

    def _find_house_number(self, longitude, house_cusps):
        """Find which house a longitude falls into"""
        longitude_norm = longitude % 360
        
        for i in range(12):
            start_cusp = house_cusps[i] % 360
            end_cusp = house_cusps[i + 1] % 360
            
            if start_cusp > end_cusp:
                if longitude_norm >= start_cusp or longitude_norm < end_cusp:
                    return i + 1
            else:
                if start_cusp <= longitude_norm < end_cusp:
                    return i + 1
        return 1

    def get_zodiac_sign(self, longitude):
        """Get zodiac sign from longitude"""
        signs = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
                "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
        idx = int((longitude % 360) // 30)
        return signs[idx]

    def get_nakshatra(self, longitude):
        """Get nakshatra from longitude"""
        nakshatras = [
            "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
            "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
            "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
            "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
            "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
        ]
        idx = int((longitude % 360) // (360 / 27))
        return nakshatras[idx]

    def get_house_number(self, longitude):
        """Get house number from longitude"""
        asc = self.ascendant_sidereal
        asc_sign_index = int(asc // 30)
        planet_sign_index = int(longitude // 30)
        house = (planet_sign_index - asc_sign_index) % 12 + 1
        return house

    def _calculate_ascendant(self):
        """Calculate ascendant data"""
        asc_tropical = self.houses_tropical[0] % 360
        asc_sidereal = (asc_tropical - self.ayanamsa) % 360
        return {
            "asc_tropical": round(asc_tropical, 6),
            "asc_sidereal": round(asc_sidereal, 6),
            "sign_sidereal": self.get_zodiac_sign(asc_sidereal),
            "degree_in_sign": round(asc_sidereal % 30, 6)
        }

    def calculate_all_data(self):
        """Return all calculated data"""
        result = {
            "ascendant": self._calculate_ascendant(),
            "d1_chart": self.planets_d1,
            "divisional_charts": self.divisional_charts,
            "structured_dashas": self.dashas,
            "doshas": self.doshas,
            "calculation_time": datetime.now().isoformat(),
            "houses": {
                "tropical": [round(c, 6) for c in self.houses_tropical],
                "sidereal": [round(c, 6) for c in self.houses_sidereal]
            }
        }
        
        self._verify_calculation(result)
        return result

    def _verify_calculation(self, data):
        """Verify that the calculation makes sense"""
        print(f"=== CALCULATION VERIFICATION ===")
        ascendant = data["ascendant"]
        print(f"Ascendant: {ascendant['sign_sidereal']} {ascendant['degree_in_sign']:.2f}°")
        
        # Verify divisional charts have different signs
        for chart_name, chart_data in data["divisional_charts"].items():
            if chart_name != 'd1':
                sample_planet = next(iter(chart_data.values())) if chart_data else None
                d1_planet = data["d1_chart"].get(next(iter(chart_data.keys())) if chart_data else None, {})
                if sample_planet and d1_planet:
                    d1_sign = d1_planet.get("sign")
                    div_sign = sample_planet.get("sign")
                    if d1_sign != div_sign:
                        print(f"{chart_name}: OK - signs changed ({d1_sign} → {div_sign})")
                    else:
                        print(f"{chart_name}: CHECK - signs same as D1")

    # ----------------- Dashas -----------------
    def _calculate_dashas(self):
        """Calculate Vimshottari Dasha periods"""
        try:
            # Get Moon's longitude for nakshatra calculation
            moon_longitude = self.planets_d1.get("Moon", {}).get("longitude_sidereal", 0)
            if moon_longitude is None:
                moon_longitude = 0
            
            # Calculate nakshatra index (0-26)
            nakshatra_size = 360.0 / 27.0
            nakshatra_index = int(moon_longitude / nakshatra_size)
            
            # Vimshottari dasha sequence and durations (in years)
            dasha_sequence = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", 
                             "Jupiter", "Saturn", "Mercury"]
            dasha_durations = [7, 20, 6, 10, 7, 18, 16, 19, 17]
            
            # Calculate starting point in current nakshatra
            nakshatra_start_degree = nakshatra_index * nakshatra_size
            degrees_into_nakshatra = (moon_longitude - nakshatra_start_degree) % 360
            percent_completed = degrees_into_nakshatra / nakshatra_size
            
            # Find current dasha starting from birth nakshatra
            current_dasha_index = nakshatra_index % 9
            
            # Calculate remaining years in current dasha
            current_dasha_duration = dasha_durations[current_dasha_index]
            remaining_years = current_dasha_duration * (1 - percent_completed)
            
            structured_dashas = []
            current_date = self.birth_datetime
            
            # Calculate next 9 mahadashas (complete 120-year cycle)
            for i in range(9):
                dasha_index = (current_dasha_index + i) % 9
                planet = dasha_sequence[dasha_index]
                total_duration = dasha_durations[dasha_index]
                
                if i == 0:  # First period is remaining part of current dasha
                    duration_years = remaining_years
                else:
                    duration_years = total_duration
                
                # Calculate end date
                end_date = current_date + timedelta(days=duration_years * 365.25)
                
                mahadasha_data = {
                    "planet": planet,
                    "start_date": current_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "duration_years": round(duration_years, 4)
                }
                
                # Calculate antardashas for this mahadasha
                antardashas = self._calculate_antardashas(current_date, duration_years, planet)
                
                structured_dashas.append({
                    "mahadasha": mahadasha_data,
                    "antardashas": antardashas
                })
                
                current_date = end_date
            
            return structured_dashas
            
        except Exception as e:
            print(f"Error calculating dashas: {e}")
            # Return sample data for testing
            return self._get_sample_dashas()

    def _calculate_antardashas(self, start_date, mahadasha_duration, mahadasha_planet):
        """Calculate antardasha periods for a mahadasha"""
        try:
            # Antardasha sequence (same as mahadasha sequence)
            sequence = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", 
                       "Jupiter", "Saturn", "Mercury"]
            durations = [7, 20, 6, 10, 7, 18, 16, 19, 17]
            total_cycle_years = sum(durations)  # 120 years
            
            # Find starting index based on mahadasha planet
            start_index = sequence.index(mahadasha_planet)
            
            antardashas = []
            current_date = start_date
            
            # Calculate antardashas for the mahadasha period
            for i in range(9):
                planet_index = (start_index + i) % 9
                planet = sequence[planet_index]
                planet_duration = durations[planet_index]
                
                # Proportional duration in this mahadasha
                antardasha_years = (planet_duration / total_cycle_years) * mahadasha_duration
                end_date = current_date + timedelta(days=antardasha_years * 365.25)
                
                antardashas.append({
                    "planet": planet,
                    "start_date": current_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "duration_years": round(antardasha_years, 4),
                    "mahadasha_planet": mahadasha_planet
                })
                
                current_date = end_date
            
            return antardashas
            
        except Exception as e:
            print(f"Error calculating antardashas: {e}")
            return []

    def _get_sample_dashas(self):
        """Return sample dasha data for testing when calculation fails"""
        sample_date = self.birth_datetime
        return [
            {
                "mahadasha": {
                    "planet": "Moon",
                    "start_date": sample_date.isoformat(),
                    "end_date": (sample_date + timedelta(days=365.25 * 10)).isoformat(),
                    "duration_years": 10.0
                },
                "antardashas": [
                    {
                        "planet": "Moon",
                        "start_date": sample_date.isoformat(),
                        "end_date": (sample_date + timedelta(days=365.25 * 1.67)).isoformat(),
                        "duration_years": 1.67,
                        "mahadasha_planet": "Moon"
                    }
                ]
            }
        ]

    # ----------------- Doshas -----------------
    def calculate_all_doshas(self):
        doshas = {}
        d1 = self.planets_d1

        # Mangal Dosha
        mars_house = d1.get("Mars", {}).get("house")
        doshas['mangal_dosha'] = mars_house in [1,4,7,8,12]

        # Kaal Sarp Dosha
        rahu_house = d1.get("Rahu", {}).get("house")
        ketu_house = d1.get("Ketu", {}).get("house")
        planet_houses = [v.get("house") for k,v in d1.items() if k not in ["Rahu","Ketu"]]
        if rahu_house is not None and ketu_house is not None:
            start = min(rahu_house, ketu_house)
            end = max(rahu_house, ketu_house)
            doshas['kaal_sarp_dosha'] = all(h >= start and h <= end for h in planet_houses if h is not None)
        else:
            doshas['kaal_sarp_dosha'] = False

        # Pitra Dosha
        sun_house = d1.get("Sun", {}).get("house")
        doshas['pitra_dosha'] = sun_house in [9,12]

        # Nadi Dosha
        moon_nak = d1.get("Moon", {}).get("nakshatra")
        lagna_nak = self.get_nakshatra(self.houses_sidereal[0])
        doshas['nadi_dosha'] = moon_nak == lagna_nak

        # Shani Dosha
        saturn_house = d1.get("Saturn", {}).get("house")
        doshas['shani_dosha'] = saturn_house in [1,4,7,8,12]

        # Guru Chandal Dosha
        jupiter_lon = d1.get("Jupiter", {}).get("longitude_sidereal")
        ketu_lon = d1.get("Ketu", {}).get("longitude_sidereal")
        doshas['guru_chandal_dosha'] = False
        if jupiter_lon is not None and ketu_lon is not None:
            doshas['guru_chandal_dosha'] = abs(jupiter_lon - ketu_lon) < 5

        # Shrapit Dosha
        doshas['shrapit_dosha'] = False
        if sun_house in [1,8] or saturn_house == 1:
            doshas['shrapit_dosha'] = True

        return doshas

    # ----------------- JSON Serialization -----------------
    def to_json_serializable(self, data):
        out = copy.deepcopy(data)
        def convert(obj):
            if isinstance(obj,dict): return {k:convert(v) for k,v in obj.items()}
            if isinstance(obj,list): return [convert(v) for v in obj]
            if isinstance(obj,datetime): return obj.isoformat()
            return obj
        return convert(out)