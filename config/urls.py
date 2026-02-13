"""
URL Configuration for fuel_route_optimizer
"""
from django.contrib import admin
from django.urls import path
from api.views import OptimizeRouteAPI, HealthCheckAPI

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/optimize', OptimizeRouteAPI.as_view(), name='optimize-route'),
    path('health', HealthCheckAPI.as_view(), name='health-check'),
]
