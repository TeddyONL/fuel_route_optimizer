"""
OpenRouteService API Client

Handles route calculation and geocoding
"""

import requests
import polyline
from typing import Dict, Tuple, List
import logging

logger = logging.getLogger(__name__)


class OpenRouteServiceClient:
    """
    Client for OpenRouteService API
    
    Free tier limits:
    - 2000 requests/day
    - 40 requests/minute
    
    Get API key: https://openrouteservice.org/dev/#/signup
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.openrouteservice.org/v2"
        self.session = requests.Session()
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
            Dict with:
            - polyline: List of (lat, lon) tuples
            - encoded_polyline: String
            - distance_miles: Float
            - duration_hours: Float
        """
        url = f"{self.base_url}/directions/driving-car"
        
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
                'polyline': coords,  # List of (lat, lon) tuples
                'encoded_polyline': encoded_polyline,
                'distance_miles': route['summary']['distance'] / 1609.34,  # meters to miles
                'duration_hours': route['summary']['duration'] / 3600  # seconds to hours
            }
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Route API error: {e}")
            raise Exception(f"Failed to get route: {str(e)}")
    
    def geocode(self, address: str) -> Tuple[float, float]:
        """
        Geocode address to coordinates
        
        Args:
            address: Address string (e.g., "Los Angeles, CA")
        
        Returns:
            (latitude, longitude)
        """
        url = f"{self.base_url}/geocode/search"
        
        params = {
            'api_key': self.api_key,
            'text': address,
            'boundary.country': 'USA',
            'size': 1
        }
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data['features']:
                coords = data['features'][0]['geometry']['coordinates']
                return (coords[1], coords[0])  # Return (lat, lon)
            else:
                raise ValueError(f"Could not geocode address: {address}")
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Geocoding error: {e}")
            raise Exception(f"Failed to geocode address: {str(e)}")
    
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
                        return (lat, lon)
            except ValueError:
                pass
        
        # Otherwise, geocode it
        return self.geocode(location)
