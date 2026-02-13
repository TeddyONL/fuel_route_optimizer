from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.cache import cache
from django.conf import settings
import hashlib
import logging
import time

from optimization.optimizer import SmartGreedyOptimizer
from infrastructure.spatial_index import get_spatial_index
from infrastructure.map_service import OpenRouteServiceClient

logger = logging.getLogger('api')


class OptimizeRouteAPI(APIView):
    """
    POST /api/optimize
    
    Request:
    {
        "start": "Los Angeles, CA" or "34.0522,-118.2437",
        "end": "San Francisco, CA" or "37.7749,-122.4194",
        "max_range": 500 (optional),
        "mpg": 10.0 (optional)
    }
    
    Response:
    {
        "success": true,
        "cache_hit": false,
        "route": {...},
        "fuel": {...},
        "performance": {...}
    }
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.optimizer = SmartGreedyOptimizer()
        self.spatial_index = get_spatial_index()
        
        # Initialize map service if API key is configured
        if settings.ORS_API_KEY:
            self.map_service = OpenRouteServiceClient(settings.ORS_API_KEY)
        else:
            self.map_service = None
            logger.warning("ORS_API_KEY not configured!")
    
    def post(self, request):
        """Handle route optimization request"""
        request_start = time.perf_counter()
        
        # Validate input
        start = request.data.get('start')
        end = request.data.get('end')
        
        if not start or not end:
            return Response(
                {
                    'success': False,
                    'error': 'Both "start" and "end" are required'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Optional parameters
        max_range = request.data.get('max_range', 500)
        mpg = request.data.get('mpg', 10.0)
        
        # Update optimizer parameters if provided
        if max_range != 500 or mpg != 10.0:
            self.optimizer = SmartGreedyOptimizer(max_range=max_range, mpg=mpg)
        
        # Check cache
        cache_key = self._generate_cache_key(start, end, max_range, mpg)
        cached = cache.get(cache_key)
        
        if cached:
            logger.info(f"✓ Cache hit: {start} -> {end}")
            cached['cache_hit'] = True
            cached['performance']['total_response_ms'] = round(
                (time.perf_counter() - request_start) * 1000, 2
            )
            return Response(cached, status=status.HTTP_200_OK)
        
        # Validate map service
        if not self.map_service:
            return Response(
                {
                    'success': False,
                    'error': 'Map service not configured. Set ORS_API_KEY in .env'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Check spatial index
        stats = self.spatial_index.get_stats()
        if not stats['is_loaded'] or stats['station_count'] == 0:
            return Response(
                {
                    'success': False,
                    'error': 'Fuel station data not loaded. Run: python scripts/prepare_data.py'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        try:
            # Parse locations
            start_coords = self.map_service.parse_location(start)
            end_coords = self.map_service.parse_location(end)
            
            logger.info(f"Route request: {start} {start_coords} -> {end} {end_coords}")
            
            # Get route from map service
            route = self.map_service.get_route(start_coords, end_coords)
            
            logger.debug(
                f"Route: {route['distance_miles']:.1f} miles, "
                f"{len(route['polyline'])} points"
            )
            
            # Optimize fuel stops
            result = self.optimizer.optimize(
                route_points=route['polyline'],
                total_distance=route['distance_miles'],
                spatial_index=self.spatial_index
            )
            
            # Format response
            response_data = {
                'success': True,
                'cache_hit': False,
                'route': {
                    'start': start,
                    'end': end,
                    'distance_miles': result.total_distance,
                    'duration_hours': round(route['duration_hours'], 2),
                    'encoded_polyline': route['encoded_polyline']
                },
                'fuel': {
                    'total_cost': result.total_cost,
                    'total_gallons': result.total_gallons,
                    'cost_per_gallon_avg': round(
                        result.total_cost / result.total_gallons, 2
                    ) if result.total_gallons > 0 else 0,
                    'stops': [
                        {
                            'name': stop.name,
                            'location': {
                                'lat': stop.location[0],
                                'lon': stop.location[1]
                            },
                            'price_per_gallon': stop.price,
                            'gallons': stop.gallons,
                            'cost': stop.cost,
                            'miles_from_start': stop.miles_from_start
                        }
                        for stop in result.stops
                    ],
                    'num_stops': len(result.stops)
                },
                'performance': {
                    'optimization_ms': result.computation_ms,
                    'total_response_ms': round(
                        (time.perf_counter() - request_start) * 1000, 2
                    ),
                    'station_count': stats['station_count']
                },
                'map_url': self._generate_map_url(start, end, result.stops)
            }
            
            # Cache result
            cache.set(cache_key, response_data, timeout=3600)  # 1 hour
            
            logger.info(
                f"✓ Optimized: ${result.total_cost:.2f}, "
                f"{len(result.stops)} stops, "
                f"{response_data['performance']['total_response_ms']:.0f}ms"
            )
            
            return Response(response_data, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.exception("Route optimization failed")
            return Response(
                {
                    'success': False,
                    'error': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _generate_cache_key(self, start: str, end: str, max_range: int, mpg: float) -> str:
        """Generate cache key from request parameters"""
        key_str = f"route:{start}:{end}:{max_range}:{mpg}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _generate_map_url(self, start: str, end: str, stops: list) -> str:
        """Generate Google Maps URL with waypoints"""
        if not stops:
            return f"https://www.google.com{start}/{end}"
        
        waypoints = '|'.join(
            f"{stop.location[0]},{stop.location[1]}"
            for stop in stops
        )
        
        return (
            f"https://www.google.com?api=1"
            f"&origin={start}"
            f"&destination={end}"
            f"&waypoints={waypoints}"
        )


class HealthCheckAPI(APIView):
    """
    GET /health
    
    Check if service is healthy
    """
    
    def get(self, request):
        """Health check endpoint"""
        spatial_index = get_spatial_index()
        stats = spatial_index.get_stats()
        
        is_healthy = (
            stats['is_loaded'] and
            stats['station_count'] > 0 and
            settings.ORS_API_KEY
        )
        
        return Response(
            {
                'status': 'healthy' if is_healthy else 'unhealthy',
                'stats': stats,
                'map_service': 'configured' if settings.ORS_API_KEY else 'missing'
            },
            status=status.HTTP_200_OK if is_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
        )
