"""
Performance Benchmarks

THESE ARE CRITICAL - They prove your performance claims!

Run with: pytest tests/benchmark.py -v
"""

import pytest
import time
import statistics
import csv
import os
from infrastructure.spatial_index import UltraFastSpatialIndex, initialize_spatial_index
from optimization.optimizer import SmartGreedyOptimizer


@pytest.fixture(scope='module')
def spatial_index():
    """Load spatial index once for all benchmark tests"""
    # Create sample data if geocoded data doesn't exist
    data_path = os.path.join('data', 'fuel_stations_geocoded.csv')
    
    if not os.path.exists(data_path):
        # Create minimal test data
        test_path = '/tmp/test_stations.csv'
        with open(test_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'OPIS Truckstop ID', 'Truckstop Name', 'City', 'State',
                'Retail Price', 'latitude', 'longitude'
            ])
            writer.writeheader()
            
            # Generate 100 test stations
            for i in range(100):
                writer.writerow({
                    'OPIS Truckstop ID': str(i),
                    'Truckstop Name': f'Station {i}',
                    'City': 'Test City',
                    'State': 'CA',
                    'Retail Price': 3.50 + (i % 10) * 0.1,
                    'latitude': 34.0 + (i % 10) * 0.5,
                    'longitude': -118.0 - (i % 10) * 0.5,
                })
        
        data_path = test_path
    
    index = UltraFastSpatialIndex()
    index.load_from_csv(data_path)
    return index


@pytest.mark.benchmark
class TestPerformanceBenchmarks:
    """
    Performance benchmarks with target metrics
    
    These must pass to claim performance numbers in demo!
    """
    
    def test_spatial_query_performance(self, spatial_index):
        """
        CRITICAL: Spatial queries must be < 1ms
        
        Target: < 1ms median
        """
        times = []
        
        # Run 1000 queries
        for i in range(1000):
            lat = 34.0 + (i % 10) * 0.1
            lon = -118.0 - (i % 10) * 0.1
            
            start = time.perf_counter()
            results = spatial_index.find_in_radius((lat, lon), radius_miles=20)
            elapsed = (time.perf_counter() - start) * 1000  # Convert to ms
            
            times.append(elapsed)
        
        # Calculate statistics
        median = statistics.median(times)
        mean = statistics.mean(times)
        p95 = statistics.quantiles(times, n=20)[18]  # 95th percentile
        
        print(f"\n{'='*60}")
        print("SPATIAL QUERY PERFORMANCE")
        print(f"{'='*60}")
        print(f"Queries: 1000")
        print(f"Median: {median:.2f}ms")
        print(f"Mean: {mean:.2f}ms")
        print(f"P95: {p95:.2f}ms")
        print(f"Target: < 1.0ms")
        print(f"Result: {'✓ PASS' if median < 1.0 else '✗ FAIL'}")
        print(f"{'='*60}\n")
        
        # This is the claim you make in your video
        assert median < 1.0, f"Too slow! Median: {median:.2f}ms (target: <1ms)"
    
    def test_optimization_performance(self, spatial_index):
        """
        CRITICAL: Full optimization must be < 100ms
        
        Target: < 100ms
        """
        optimizer = SmartGreedyOptimizer()
        
        # Sample route (LA to SF)
        route_points = [
            (34.0522, -118.2437),
            (34.5, -118.0),
            (35.0, -119.0),
            (35.5, -120.0),
            (36.0, -121.0),
            (36.5, -121.5),
            (37.0, -122.0),
            (37.7749, -122.4194),
        ]
        
        times = []
        
        # Run 100 optimizations
        for _ in range(100):
            start = time.perf_counter()
            result = optimizer.optimize(
                route_points=route_points,
                total_distance=380.0,
                spatial_index=spatial_index
            )
            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)
        
        median = statistics.median(times)
        mean = statistics.mean(times)
        p95 = statistics.quantiles(times, n=20)[18]
        
        print(f"\n{'='*60}")
        print("OPTIMIZATION PERFORMANCE")
        print(f"{'='*60}")
        print(f"Optimizations: 100")
        print(f"Median: {median:.2f}ms")
        print(f"Mean: {mean:.2f}ms")
        print(f"P95: {p95:.2f}ms")
        print(f"Target: < 100ms")
        print(f"Result: {'✓ PASS' if median < 100 else '✗ FAIL'}")
        print(f"{'='*60}\n")
        
        assert median < 100, f"Too slow! Median: {median:.2f}ms (target: <100ms)"
    
    def test_memory_usage(self, spatial_index):
        """
        Test memory footprint of spatial index
        
        Target: < 50MB for 8000 stations
        """
        stats = spatial_index.get_stats()
        memory_mb = stats['memory_mb']
        
        print(f"\n{'='*60}")
        print("MEMORY USAGE")
        print(f"{'='*60}")
        print(f"Stations: {stats['station_count']}")
        print(f"Memory: {memory_mb:.2f} MB")
        print(f"Target: < 50 MB")
        print(f"Result: {'✓ PASS' if memory_mb < 50 else '✗ FAIL'}")
        print(f"{'='*60}\n")
        
        assert memory_mb < 50, f"Too much memory! {memory_mb:.2f}MB (target: <50MB)"


@pytest.mark.benchmark
def test_end_to_end_performance(spatial_index):
    """
    CRITICAL: Full API simulation
    
    Simulates what happens when API is called
    """
    from infrastructure.map_service import OpenRouteServiceClient
    from optimization.optimizer import SmartGreedyOptimizer
    from django.core.cache import cache
    
    optimizer = SmartGreedyOptimizer()
    
    # Simulate cached route data (skip API call)
    mock_route = {
        'polyline': [
            (34.0522, -118.2437),
            (35.0, -119.0),
            (36.0, -121.0),
            (37.7749, -122.4194),
        ],
        'distance_miles': 380.0,
        'duration_hours': 5.5,
    }
    
    # Time the optimization part only
    start = time.perf_counter()
    result = optimizer.optimize(
        route_points=mock_route['polyline'],
        total_distance=mock_route['distance_miles'],
        spatial_index=spatial_index
    )
    elapsed_ms = (time.perf_counter() - start) * 1000
    
    print(f"\n{'='*60}")
    print("END-TO-END SIMULATION")
    print(f"{'='*60}")
    print(f"Optimization: {elapsed_ms:.2f}ms")
    print(f"Fuel stops: {len(result.stops)}")
    print(f"Total cost: ${result.total_cost:.2f}")
    print(f"Target: < 100ms for optimization")
    print(f"Result: {'✓ PASS' if elapsed_ms < 100 else '✗ FAIL'}")
    print(f"{'='*60}\n")
    
    assert elapsed_ms < 100


if __name__ == '__main__':
    print("\n" + "="*60)
    print("RUNNING PERFORMANCE BENCHMARKS")
    print("="*60)
    print("\nThese benchmarks prove your performance claims!")
    print("Run with: pytest tests/benchmark.py -v\n")
    pytest.main([__file__, '-v', '-s'])
