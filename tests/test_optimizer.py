"""
Tests for route optimizer
"""

import pytest
from optimization.optimizer import SmartGreedyOptimizer
from infrastructure.spatial_index import UltraFastSpatialIndex


class TestOptimizer:
    """Test the optimization algorithm"""
    
    def test_optimizer_initialization(self):
        """Test optimizer can be created"""
        optimizer = SmartGreedyOptimizer(max_range=500, mpg=10.0)
        assert optimizer.max_range == 500
        assert optimizer.mpg == 10.0
    
    def test_short_route_no_stops(self, sample_route_points):
        """Test that short route needs no fuel stops"""
        optimizer = SmartGreedyOptimizer(max_range=500, mpg=10.0)
        
        # Create mock spatial index
        spatial_index = UltraFastSpatialIndex()
        
        # Short route (< 200 miles)
        short_route = sample_route_points[:3]
        
        result = optimizer.optimize(
            route_points=short_route,
            total_distance=150.0,
            spatial_index=spatial_index
        )
        
        # Should need no stops for 150 miles with 500 mile range
        assert len(result.stops) == 0
        assert result.total_cost == 0
    
    def test_distance_calculation(self):
        """Test haversine distance calculation"""
        optimizer = SmartGreedyOptimizer()
        
        # LA to SF is about 380 miles
        la = (34.0522, -118.2437)
        sf = (37.7749, -122.4194)
        
        distance = optimizer._distance(la, sf)
        
        # Should be approximately 340-360 miles (straight line)
        assert 300 < distance < 400
    
    def test_route_sampling(self):
        """Test that route sampling works correctly"""
        optimizer = SmartGreedyOptimizer()
        
        # Create a long route
        route = [(i, i) for i in range(100)]
        
        sampled = optimizer._sample_route(route, interval=10)
        
        # Should have fewer points than original
        assert len(sampled) < len(route)
        
        # Should include start and end
        assert sampled[0] == route[0]
        assert sampled[-1] == route[-1]
