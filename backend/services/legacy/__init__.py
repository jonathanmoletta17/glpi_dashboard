# -*- coding: utf-8 -*-
"""
Legacy GLPI Services - Decomposed modules from monolithic GLPIService.

This package contains the decomposed modules that maintain backward compatibility
while providing better separation of concerns for the legacy GLPI integration.
"""

# Import main classes for backward compatibility
from .authentication_service import GLPIAuthenticationService
from .cache_service import GLPICacheService
from .field_discovery_service import GLPIFieldDiscoveryService
from .http_client_service import GLPIHttpClientService
from .metrics_service import GLPIMetricsService
from .dashboard_service import GLPIDashboardService
from .trends_service import GLPITrendsService
from .glpi_service_facade import GLPIServiceFacade

__all__ = [
    "GLPIAuthenticationService",
    "GLPICacheService", 
    "GLPIFieldDiscoveryService",
    "GLPIHttpClientService",
    "GLPIMetricsService",
    "GLPIDashboardService",
    "GLPITrendsService",
    "GLPIServiceFacade",
]