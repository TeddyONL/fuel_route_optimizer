"""
OpenRouteService API Client - FIXED VERSION

Handles route calculation and geocoding with correct API endpoints
"""

import requests
import polyline
from typing import Dict, Tuple, List
import logging

logger = logging.getLogger(__name__)


class OpenRouteServiceClient:
    """
    Client for OpenRouteService API
    
    IMPORTANT: ORS API v2 geocoding uses different endpoint format
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.openrouteservice.org"
        self.session = requests.Session()
        # Authorization header format for ORS
        self.session.headers.update({
            'Authorization': api_key,
            'Content-Type': 'application/json'
        })
    
    def get_route(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float]
    ) -> Dict:
        """
        Get route between two points
        
        Args:
            start: (latitude, longitude)
            end: (latitude, longitude)
        
        Returns:
            Dict with polyline, distance, duration
        """
        url = f"{self.base_url}/v2/directions/driving-car"
        
        # ORS expects [lon, lat] not [lat, lon]!
        payload = {
            'coordinates': [
                [start[1], start[0]],  # [lon, lat]
                [end[1], end[0]]
            ],
            'instructions': False,
            'geometry': True
        }
        
        try:
            response = self.session.post(url, json=payload, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            route = data['routes'][0]
            
            # Decode polyline to list of coordinates
            encoded_polyline = route['geometry']
            coords = polyline.decode(encoded_polyline)
            
            return {
                'polyline': coords,
                'encoded_polyline': encoded_polyline,
                'distance_miles': route['summary']['distance'] / 1609.34,
                'duration_hours': route['summary']['duration'] / 3600
            }
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Route API error: {e}")
            raise Exception(f"Failed to get route: {str(e)}")
    
    def geocode(self, address: str) -> Tuple[float, float]:
        """
        Geocode address to coordinates using Pelias geocoding API
        
        ORS uses Pelias geocoding which has a different endpoint structure
        
        Args:
            address: Address string (e.g., "Los Angeles, CA")
        
        Returns:
            (latitude, longitude)
        """
        # Correct endpoint for ORS geocoding (Pelias-based)
        url = f"{self.base_url}/geocode/search"
        
        # Use query params, not path params
        params = {
            'api_key': self.api_key,
            'text': address,
            'boundary.country': 'US',  # Use 'US' not 'USA'
            'size': 1
        }
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            
            # Check response
            if response.status_code != 200:
                logger.error(f"Geocoding failed: {response.status_code} - {response.text}")
                # Try alternative: use coordinates directly from common cities
                return self._fallback_geocode(address)
            
            data = response.json()
            
            if data.get('features') and len(data['features']) > 0:
                coords = data['features'][0]['geometry']['coordinates']
                return (coords[1], coords[0])  # Return (lat, lon)
            else:
                logger.warning(f"No geocoding results for: {address}")
                return self._fallback_geocode(address)
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Geocoding error: {e}")
            return self._fallback_geocode(address)
    
    def _fallback_geocode(self, address: str) -> Tuple[float, float]:
        """
        Fallback geocoding using hardcoded major US cities
        
        This ensures the demo works even if geocoding API has issues
        """
        # Major US cities coordinates
        cities = {
            'los angeles': (34.0522, -118.2437),
            'san francisco': (37.7749, -122.4194),
            'new york': (40.7128, -74.0060),
            'chicago': (41.8781, -87.6298),
            'houston': (29.7604, -95.3698),
            'phoenix': (33.4484, -112.0740),
            'philadelphia': (39.9526, -75.1652),
            'san antonio': (29.4241, -98.4936),
            'san diego': (32.7157, -117.1611),
            'dallas': (32.7767, -96.7970),
            'seattle': (47.6062, -122.3321),
            'boston': (42.3601, -71.0589),
            'las vegas': (36.1699, -115.1398),
            'portland': (45.5152, -122.6784),
            'denver': (39.7392, -104.9903),
            'miami': (25.7617, -80.1918),
            'atlanta': (33.7490, -84.3880),
            'sacramento': (38.5816, -121.4944),
            'oakland': (37.8044, -122.2712),
            'bakersfield': (35.3733, -119.0187),
        }
        
        # Normalize address
        addr_lower = address.lower()
        
        # Try to match city name
        for city, coords in cities.items():
            if city in addr_lower:
                logger.info(f"Using fallback coordinates for {city}")
                return coords
        
        # If no match, raise error
        raise ValueError(f"Could not geocode address: {address}. Try using coordinates instead (lat,lon)")
    
    def parse_location(self, location: str) -> Tuple[float, float]:
        """
        Parse location string to coordinates
        
        Handles:
        - Coordinates: "34.0522,-118.2437"
        - Addresses: "Los Angeles, CA"
        
        Returns:
            (latitude, longitude)
        """
        # Check if it's already coordinates
        if ',' in location:
            try:
                parts = location.split(',')
                if len(parts) == 2:
                    lat, lon = float(parts[0].strip()), float(parts[1].strip())
                    if -90 <= lat <= 90 and -180 <= lon <= 180:
                        logger.info(f"Parsed coordinates: ({lat}, {lon})")
                        return (lat, lon)
            except ValueError:
                pass
        
        # Otherwise, geocode it
        return self.geocode(location)