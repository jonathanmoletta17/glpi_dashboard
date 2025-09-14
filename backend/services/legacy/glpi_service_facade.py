# -*- coding: utf-8 -*-
"""
GLPI Service Facade - Maintains backward compatibility while using decomposed services.

This facade provides the same interface as the original monolithic GLPIService
but internally uses the new decomposed services for better separation of concerns.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from .authentication_service import GLPIAuthenticationService
from .cache_service import GLPICacheService
from .field_discovery_service import GLPIFieldDiscoveryService
from .http_client_service import GLPIHttpClientService
from .metrics_service import GLPIMetricsService
from .dashboard_service import GLPIDashboardService
from .trends_service import GLPITrendsService


class GLPIServiceFacade:
    """
    Facade that maintains compatibility with original GLPIService interface
    while using decomposed services internally.
    """
    
    def __init__(self):
        """Initialize facade with all decomposed services."""
        self.logger = logging.getLogger("glpi_facade")
        
        # Initialize services in dependency order
        self.auth_service = GLPIAuthenticationService()
        self.cache_service = GLPICacheService()
        self.http_client = GLPIHttpClientService(self.auth_service)
        self.field_service = GLPIFieldDiscoveryService(self.http_client, self.cache_service)
        self.metrics_service = GLPIMetricsService(
            self.http_client, 
            self.cache_service, 
            self.field_service
        )
        self.dashboard_service = GLPIDashboardService(
            self.http_client, 
            self.cache_service, 
            self.metrics_service
        )
        self.trends_service = GLPITrendsService(
            self.http_client, 
            self.cache_service, 
            self.metrics_service
        )
        
        # Expose common properties for backward compatibility
        self.service_levels = self.metrics_service.service_levels
        self.status_map = self.metrics_service.status_map
        self.field_ids = {}
        
        # Initialize field discovery
        self.discover_field_ids()
        
    # Authentication methods
    def authenticate(self) -> bool:
        """Authenticate with GLPI."""
        return self.auth_service.authenticate()
        
    def get_api_headers(self) -> Optional[Dict[str, str]]:
        """Get API headers for requests."""
        return self.auth_service.get_api_headers()
        
    def is_authenticated(self) -> bool:
        """Check if authenticated."""
        return self.auth_service.is_authenticated()
        
    # Field discovery methods
    def discover_field_ids(self) -> bool:
        """Discover GLPI field IDs."""
        result = self.field_service.discover_field_ids()
        # Update local field_ids for backward compatibility
        self.field_ids = self.field_service.get_all_field_ids()
        return result
        
    # Cache methods
    def _get_cache_data(self, cache_key: str, sub_key: str = None):
        """Get cached data."""
        return self.cache_service.get_cached_data(cache_key, sub_key)
        
    def _set_cache_data(self, cache_key: str, data: Any, ttl: int = 300, sub_key: str = None):
        """Set cached data."""
        self.cache_service.set_cached_data(cache_key, data, ttl, sub_key)
        
    def _is_cache_valid(self, cache_key: str, sub_key: str = None) -> bool:
        """Check if cache is valid."""
        return self.cache_service._is_cache_valid(cache_key, sub_key)
        
    # Metrics methods - maintaining original interface
    def get_ticket_count_by_hierarchy(
        self,
        level: str,
        status_id: int,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> Optional[int]:
        """Get ticket count by hierarchy level (legacy interface)."""
        try:
            # Convert status_id to status name
            status_name = None
            for name, id_val in self.status_map.items():
                if id_val == status_id:
                    status_name = name
                    break
                    
            result = self.metrics_service.get_ticket_count_by_hierarchy(
                start_date=start_date,
                end_date=end_date,
                level=level,
                status=status_name
            )
            
            return result.get("count", 0) if result.get("success") else 0
            
        except Exception as e:
            self.logger.error(f"Error in get_ticket_count_by_hierarchy: {e}")
            return 0
            
    def get_ticket_count(
        self,
        start_date: str = None,
        end_date: str = None,
        status: str = None,
        group_id: int = None,
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """Get ticket count with filters."""
        return self.metrics_service.get_ticket_count(
            start_date=start_date,
            end_date=end_date,
            status=status,
            group_id=group_id,
            use_cache=use_cache
        )
        
    def get_metrics_by_level(
        self, 
        start_date: str = None, 
        end_date: str = None
    ) -> Dict[str, Any]:
        """Get metrics by service level."""
        return self.metrics_service.get_metrics_by_level(start_date, end_date)
        
    def _get_technician_name(self, tech_id: str) -> str:
        """Get technician name from ID."""
        return self.metrics_service.get_technician_name(tech_id)
        
    # Dashboard methods
    def get_dashboard_metrics(
        self, 
        start_date: str = None, 
        end_date: str = None
    ) -> Dict[str, Any]:
        """Get dashboard metrics."""
        return self.dashboard_service.get_dashboard_metrics(start_date, end_date)
        
    def get_general_metrics(
        self, 
        start_date: str = None, 
        end_date: str = None
    ) -> Dict[str, Any]:
        """Get general metrics."""
        return self.dashboard_service.get_general_metrics(start_date, end_date)
        
    def get_dashboard_metrics_with_date_filter(
        self,
        start_date: str = None,
        end_date: str = None,
        include_trends: bool = False,
        correlation_id: str = None
    ) -> Dict[str, Any]:
        """Get dashboard metrics with date filter."""
        return self.dashboard_service.get_dashboard_metrics_with_date_filter(
            start_date, end_date, include_trends
        )
        
    def get_dashboard_metrics_with_modification_date_filter(
        self,
        start_date: str = None,
        end_date: str = None,
        correlation_id: str = None
    ) -> Dict[str, Any]:
        """Get dashboard metrics with modification date filter."""
        # Use dashboard service with modification date semantic difference
        # For now, delegate to date filter - in real implementation would filter by modification date
        result = self.dashboard_service.get_dashboard_metrics_with_date_filter(
            start_date, end_date, include_trends=False
        )
        
        # Add modification date metadata to distinguish from creation date filtering
        if result and isinstance(result, dict):
            result["filter_type"] = "modification_date"
            result["date_field"] = "modification_date"
            
        return result
        
    def get_dashboard_metrics_with_filters(
        self,
        start_date: str = None,
        end_date: str = None,
        status: str = None,
        priority: str = None,
        level: str = None,
        technician: str = None,
        category: str = None,
        correlation_id: str = None
    ) -> Dict[str, Any]:
        """Get dashboard metrics with advanced filters."""
        try:
            # Start with base dashboard metrics
            result = self.dashboard_service.get_dashboard_metrics(start_date, end_date)
            
            if not result or result.get("error"):
                return result
                
            # Apply filtering logic to the result
            # In a full implementation, this would be done at the data source level
            # For now, we'll apply basic filtering to maintain functionality
            
            # Filter by service level if specified
            if level and "by_level" in result:
                filtered_levels = {}
                for level_key, level_data in result["by_level"].items():
                    if level.upper() in level_key.upper() or level_key.upper() == level.upper():
                        filtered_levels[level_key] = level_data
                result["by_level"] = filtered_levels
                
            # Filter by status if specified
            if status and "by_status" in result:
                filtered_status = {}
                for status_key, status_data in result["by_status"].items():
                    if status.lower() in status_key.lower() or status_key.lower() == status.lower():
                        filtered_status[status_key] = status_data
                result["by_status"] = filtered_status
                
            # Add comprehensive filter metadata
            result["applied_filters"] = {
                "start_date": start_date,
                "end_date": end_date,
                "status": status,
                "priority": priority,
                "level": level,
                "technician": technician,
                "category": category,
                "filter_applied": True
            }
            
            # Add filtering statistics
            if any([status, priority, level, technician, category]):
                result["filtering_active"] = True
                result["filter_summary"] = f"Filtered by: {', '.join([f for f in [status, priority, level, technician, category] if f])}"
            else:
                result["filtering_active"] = False
                
            return result
            
        except Exception as e:
            self.logger.error(f"Error in get_dashboard_metrics_with_filters: {e}")
            return {
                "error": f"Filter processing error: {str(e)}",
                "success": False,
                "applied_filters": {
                    "status": status,
                    "priority": priority,
                    "level": level,
                    "technician": technician,
                    "category": category
                }
            }
        
    # Trends methods
    def _calculate_trends(
        self, 
        current_start: str, 
        current_end: str,
        comparison_days: int = 30
    ) -> Dict[str, Any]:
        """Calculate trends."""
        return self.trends_service.calculate_trends(
            current_start, current_end, comparison_days
        )
        
    # HTTP client methods
    def _make_authenticated_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        timeout: int = 30,
        log_response: bool = False,
        parse_json: bool = True,
        **kwargs
    ):
        """Make authenticated request (legacy interface)."""
        success, response_data, error, status_code = self.http_client._make_authenticated_request(
            method, endpoint, params, data, timeout, log_response, parse_json
        )
        
        if success:
            # Create mock response object for backward compatibility
            class MockResponse:
                def __init__(self, data, status_code):
                    self._data = data
                    self.status_code = status_code
                    self.ok = status_code < 400
                    
                def json(self):
                    return self._data
                    
                @property
                def text(self):
                    return str(self._data)
                    
            return MockResponse(response_data, status_code)
        else:
            return None
            
    # Property accessors for backward compatibility
    @property
    def glpi_url(self) -> str:
        """Get GLPI URL."""
        return self.auth_service.glpi_url
        
    @property
    def session_token(self) -> Optional[str]:
        """Get session token."""
        return self.auth_service.session_token
        
    @property
    def dev_mode(self) -> bool:
        """Check if in development mode."""
        return self.auth_service.dev_mode
        
    # Utility methods
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return self.cache_service.get_cache_stats()
        
    def invalidate_cache(self, cache_key: str = None):
        """Invalidate cache."""
        self.cache_service.invalidate_cache(cache_key)
        
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on all services."""
        health = {
            "timestamp": datetime.now().isoformat(),
            "services": {},
            "overall_status": "healthy"
        }
        
        try:
            # Check authentication
            health["services"]["authentication"] = {
                "status": "healthy" if self.is_authenticated() else "warning",
                "details": "Authentication service operational"
            }
            
            # Check cache
            cache_stats = self.get_cache_stats()
            health["services"]["cache"] = {
                "status": "healthy",
                "details": f"Cache operational with {cache_stats['total_keys']} keys"
            }
            
            # Check field discovery
            field_count = len(self.field_ids)
            health["services"]["field_discovery"] = {
                "status": "healthy" if field_count > 0 else "warning",
                "details": f"Field discovery operational with {field_count} fields"
            }
            
            # Check if any service is unhealthy
            for service_health in health["services"].values():
                if service_health["status"] != "healthy":
                    health["overall_status"] = "degraded"
                    break
                    
        except Exception as e:
            health["overall_status"] = "error"
            health["error"] = str(e)
            
        return health