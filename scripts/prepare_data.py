#!/usr/bin/env python
"""
Data Preparation Script

Geocodes fuel stations and prepares data for the spatial index.

For the demo, we'll use city/state centroids which are fast and good enough
for 500-mile range fuel stops.
"""

import csv
import sys
import os
from typing import Tuple, Dict
import time

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Simple US Cities Database (major cities)
# In production, use a complete database or geocoding API
US_CITIES = {
    ('Big Cabin', 'OK'): (36.5270, -95.2286),
    ('Tomah', 'WI'): (43.9847, -90.5040),
    ('Gila Bend', 'AZ'): (32.9479, -112.7163),
    ('Fort Smith', 'AR'): (35.3859, -94.3985),
    ('Columbia', 'NJ'): (40.9251, -75.0824),
    ('Mount Jackson', 'VA'): (38.7451, -78.6450),
    ('Jarrell', 'TX'): (30.8246, -97.6028),
    ('Shorter', 'AL'): (32.4157, -85.8947),
    ('Seymour', 'IN'): (38.9592, -85.8903),
    ('Council Bluffs', 'IA'): (41.2619, -95.8608),
    ('Sterling', 'ND'): (46.9761, -100.5090),
    ('Montrose', 'CO'): (38.4783, -107.8762),
    ('Laurel', 'DE'): (38.5565, -75.5713),
    ('New Castle', 'DE'): (39.6621, -75.5664),
    ('Ellenton', 'FL'): (27.5214, -82.5240),
    ('Dumont', 'CO'): (39.6286, -105.9117),
    ('Crawfordville', 'GA'): (33.5551, -82.8932),
    ('Bridgeport', 'MI'): (43.3608, -83.8791),
    ('Lupton', 'AZ'): (34.8000, -109.2500),
    ('Eloy', 'AZ'): (32.7559, -111.5548),
    ('Henderson', 'KY'): (37.8361, -87.5900),
    ('Effingham', 'IL'): (39.1200, -88.5434),
    ('Atkinson', 'IL'): (41.4200, -90.0179),
    ('Daleville', 'IN'): (40.1214, -85.5583),
    ('Fort Wayne', 'IN'): (41.0793, -85.1394),
    ('Gothenburg', 'NE'): (40.9272, -100.1604),
    ('Jacksonville', 'FL'): (30.3322, -81.6557),
    ('Denham Springs', 'LA'): (30.4880, -90.9540),
    ('Lake Station', 'IN'): (41.5753, -87.2464),
    ('Hebron', 'IN'): (41.3192, -87.2003),
    ('Nacogdoches', 'TX'): (31.6035, -94.6555),
    ('Moorcroft', 'WY'): (44.2633, -104.9522),
    ('Latimer', 'IA'): (42.7666, -93.3627),
    ('Clear Lake', 'IA'): (43.1380, -93.3796),
    ('Stuart', 'IA'): (41.5036, -94.3197),
    ('West Memphis', 'AR'): (35.1465, -90.1848),
    ('Atwood', 'CO'): (40.5194, -103.2963),
    ('Salina', 'KS'): (38.8403, -97.6114),
    ('Highland', 'IN'): (41.5536, -87.4519),
    ('Sardinia', 'OH'): (39.0014, -83.7988),
    ('Ocean Springs', 'MS'): (30.4113, -88.8278),
    ('Mount Vernon', 'KY'): (37.3526, -84.3402),
    ('Ocala', 'FL'): (29.1872, -82.1401),
    ('Port Allen', 'LA'): (30.4518, -91.2104),
    ('Lake Village', 'IN'): (40.9503, -87.4531),
    ('Duson', 'LA'): (30.2366, -92.1851),
    ('New Orleans', 'LA'): (29.9511, -90.0715),
    ('Hays', 'KS'): (38.8792, -99.3268),
    ('Grantsville', 'MD'): (39.7006, -79.1547),
    ('Great Falls', 'MT'): (47.5002, -111.3008),
    ('Bridgman', 'MI'): (41.9431, -86.5567),
    ('Dodge City', 'KS'): (37.7528, -100.0171),
    ('Monroe', 'MI'): (41.9164, -83.3977),
    ('Carlisle', 'IN'): (38.9667, -87.4000),
    ('Taylorsville', 'IN'): (39.2564, -85.9527),
    ('Lawrence', 'KS'): (38.9717, -95.2353),
    ('Cherryvale', 'KS'): (37.2697, -95.5522),
    ('Matfield Green', 'KS'): (38.1581, -96.5622),
    ('Springfield', 'MA'): (42.1015, -72.5898),
    ('Kansas City', 'KS'): (39.1142, -94.6275),
    ('Ogallala', 'NE'): (41.1281, -101.7188),
    ('Willard', 'UT'): (41.4094, -112.0361),
    ('Saint Johns', 'FL'): (30.0847, -81.5523),
    ('Portage', 'IN'): (41.5759, -87.1762),
    ('Binghamton', 'NY'): (42.0987, -75.9180),
    ('Gansevoort', 'NY'): (43.1942, -73.6418),
    ('Hammond', 'IN'): (41.5834, -87.5000),
    ('Yuma', 'AZ'): (32.6927, -114.6277),
    ('Sunbury', 'OH'): (40.2423, -82.8591),
    ('Seville', 'OH'): (41.0103, -81.8629),
    ('Perrysburg', 'OH'): (41.5570, -83.6271),
    ('Oklahoma City', 'OK'): (35.4676, -97.5164),
    ('Los Angeles', 'CA'): (34.0522, -118.2437),
    ('San Francisco', 'CA'): (37.7749, -122.4194),
    ('Chicago', 'IL'): (41.8781, -87.6298),
    ('Houston', 'TX'): (29.7604, -95.3698),
    ('Phoenix', 'AZ'): (33.4484, -112.0740),
    ('Philadelphia', 'PA'): (39.9526, -75.1652),
    ('San Antonio', 'TX'): (29.4241, -98.4936),
    ('San Diego', 'CA'): (32.7157, -117.1611),
    ('Dallas', 'TX'): (32.7767, -96.7970),
    ('San Jose', 'CA'): (37.3382, -121.8863),
}


def get_city_coords(city: str, state: str) -> Tuple[float, float]:
    """
    Get coordinates for city/state
    
    Uses simple lookup table for speed.
    In production, use a proper geocoding service.
    """
    key = (city.strip(), state.strip())
    
    if key in US_CITIES:
        return US_CITIES[key]
    
    # Try case-insensitive match
    for (c, s), coords in US_CITIES.items():
        if c.lower() == city.lower() and s.upper() == state.upper():
            return coords
    
    return None, None


def geocode_fuel_stations(input_csv: str, output_csv: str):
    """
    Add coordinates to fuel station CSV
    
    Args:
        input_csv: Path to original CSV (fuel-prices-for-be-assessment.csv)
        output_csv: Path to output CSV with coordinates
    """
    print("=" * 60)
    print("FUEL STATION GEOCODING")
    print("=" * 60)
    
    if not os.path.exists(input_csv):
        print(f"✗ Error: Input file not found: {input_csv}")
        print(f"\nPlease place fuel-prices-for-be-assessment.csv in the data/ directory")
        return False
    
    stations = []
    geocoded = 0
    failed = 0
    
    print(f"\nReading: {input_csv}")
    
    with open(input_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for i, row in enumerate(reader, 1):
            city = row.get('City', '').strip()
            state = row.get('State', '').strip()
            
            # Get coordinates
            lat, lon = get_city_coords(city, state)
            
            if lat and lon:
                row['latitude'] = lat
                row['longitude'] = lon
                stations.append(row)
                geocoded += 1
            else:
                failed += 1
            
            if i % 1000 == 0:
                print(f"  Processed {i} stations... (geocoded: {geocoded}, failed: {failed})")
    
    # Write output
    print(f"\nWriting: {output_csv}")
    
    if stations:
        fieldnames = list(stations[0].keys())
        
        with open(output_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(stations)
    
    print("\n" + "=" * 60)
    print("GEOCODING RESULTS")
    print("=" * 60)
    print(f"Total stations: {geocoded + failed}")
    print(f"Successfully geocoded: {geocoded}")
    print(f"Failed (no coordinates): {failed}")
    print(f"Success rate: {geocoded / (geocoded + failed) * 100:.1f}%")
    print("\n✓ Done! Data ready for use.")
    print(f"\nOutput saved to: {output_csv}")
    print("\nNext steps:")
    print("1. Start Redis: redis-server")
    print("2. Run server: python manage.py runserver")
    print("3. Test endpoint: curl -X POST http://localhost:8000/api/optimize \\")
    print('     -H "Content-Type: application/json" \\')
    print('     -d \'{"start": "Los Angeles, CA", "end": "San Francisco, CA"}\'')
    print("\n" + "=" * 60)
    
    return True


if __name__ == '__main__':
    # File paths
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
    input_file = os.path.join(data_dir, 'fuel-prices-for-be-assessment.csv')
    output_file = os.path.join(data_dir, 'fuel_stations_geocoded.csv')
    
    # Create data directory if it doesn't exist
    os.makedirs(data_dir, exist_ok=True)
    
    # Run geocoding
    success = geocode_fuel_stations(input_file, output_file)
    
    sys.exit(0 if success else 1)
