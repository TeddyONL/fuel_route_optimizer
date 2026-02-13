"""
Pytest configuration and fixtures
"""

import pytest
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()


@pytest.fixture
def sample_route_points():
    """Sample route polyline (LA to SF roughly)"""
    return [
        (34.0522, -118.2437),  # LA
        (34.5, -118.0),
        (35.0, -119.0),
        (35.5, -120.0),
        (36.0, -121.0),
        (36.5, -121.5),
        (37.0, -122.0),
        (37.7749, -122.4194),  # SF
    ]


@pytest.fixture
def sample_stations():
    """Sample fuel stations"""
    return [
        {
            'id': '1',
            'name': 'Station A',
            'city': 'Bakersfield',
            'state': 'CA',
            'lat': 35.3733,
            'lon': -119.0187,
            'price': 3.50,
        },
        {
            'id': '2',
            'name': 'Station B',
            'city': 'Paso Robles',
            'state': 'CA',
            'lat': 35.6269,
            'lon': -120.6907,
            'price': 3.30,
        },
        {
            'id': '3',
            'name': 'Station C',
            'city': 'San Luis Obispo',
            'state': 'CA',
            'lat': 35.2828,
            'lon': -120.6596,
            'price': 3.80,
        },
    ]
