# -*- coding: utf-8 -*-
"""
GLPI Dashboard Service - Handles dashboard metrics and general statistics.

Extracted from monolithic GLPIService for better separation of concerns.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from utils.date_validator import DateValidator
from .http_client_service import GLPIHttpClientService
from .cache_service import GLPICacheService
from .metrics_service import GLPIMetricsService


class GLPIDashboardService:
    """Handles dashboard metrics and general statistics."""
    
    def __init__(
        self, 
        http_client: GLPIHttpClientService, 
        cache_service: GLPICacheService,
        metrics_service: GLPIMetricsService
    ):
        """Initialize dashboard service."""
        self.http_client = http_client
        self.cache_service = cache_service
        self.metrics_service = metrics_service
        self.logger = logging.getLogger("glpi_dashboard")
        
    def get_dashboard_metrics(
        self, 
        start_date: str = None, 
        end_date: str = None
    ) -> Dict[str, Any]:
        """Get comprehensive dashboard metrics."""
        try:
            # Set date defaults
            if not start_date:
                start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            if not end_date:
                end_date = datetime.now().strftime('%Y-%m-%d')
                
            # Validate dates
            if not DateValidator.is_valid_date(start_date):
                return {"error": "Invalid start_date format"}
            if not DateValidator.is_valid_date(end_date):
                return {"error": "Invalid end_date format"}
                
            # Check cache first
            cache_key = f"dashboard_{start_date}_{end_date}"
            cached_result = self.cache_service.get_cached_data("dashboard_metrics", cache_key)
            if cached_result:
                self.logger.debug(f"Returning cached dashboard metrics for {cache_key}")
                return cached_result
                
            # Initialize result structure
            result = {
                "start_date": start_date,
                "end_date": end_date,
                "timestamp": datetime.now().isoformat(),
                "totals": {
                    "total_tickets": 0,
                    "resolved_tickets": 0,
                    "pending_tickets": 0,
                    "new_tickets": 0
                },
                "by_level": {},
                "by_status": {},
                "performance": {
                    "resolution_rate": 0.0,
                    "avg_resolution_time": 0.0
                },
                "success": True
            }
            
            # Get metrics by service level
            level_metrics = self.metrics_service.get_metrics_by_level(start_date, end_date)
            if level_metrics and not level_metrics.get("error"):
                result["by_level"] = level_metrics.get("levels", {})
                result["totals"] = level_metrics.get("totals", result["totals"])
                
            # Get status breakdown
            status_breakdown = self._get_status_breakdown(start_date, end_date)
            result["by_status"] = status_breakdown
            
            # Calculate performance metrics
            if result["totals"]["total_tickets"] > 0:
                result["performance"]["resolution_rate"] = (
                    result["totals"]["resolved_tickets"] / result["totals"]["total_tickets"]
                ) * 100
                
            # Get average resolution time
            result["performance"]["avg_resolution_time"] = self._calculate_avg_resolution_time(
                start_date, end_date
            )
            
            # Cache the result
            self.cache_service.set_cached_data("dashboard_metrics", result, ttl=180, sub_key=cache_key)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error getting dashboard metrics: {e}")
            return {"error": str(e), "success": False}
            
    def _get_status_breakdown(self, start_date: str, end_date: str) -> Dict[str, int]:
        """Get breakdown of tickets by status."""
        status_breakdown = {}
        
        try:
            # Get count for each status
            for status_name, status_id in self.metrics_service.status_map.items():
                result = self.metrics_service.get_ticket_count(
                    start_date=start_date,
                    end_date=end_date,
                    status=status_name,
                    use_cache=True
                )
                
                if result.get("success"):
                    status_breakdown[status_name] = result.get("count", 0)
                else:
                    status_breakdown[status_name] = 0
                    
        except Exception as e:
            self.logger.error(f"Error getting status breakdown: {e}")
            
        return status_breakdown
        
    def _calculate_avg_resolution_time(self, start_date: str, end_date: str) -> float:
        """Calculate average resolution time in hours."""
        try:
            # This would require more complex queries to get resolution times
            # For now, return a placeholder value
            # In a real implementation, this would:
            # 1. Get tickets with both creation and resolution dates
            # 2. Calculate time difference for each ticket
            # 3. Return average
            
            return 0.0
            
        except Exception as e:
            self.logger.error(f"Error calculating average resolution time: {e}")
            return 0.0
            
    def get_general_metrics(self, start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        """Get general system metrics."""
        try:
            # Set defaults
            if not start_date:
                start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            if not end_date:
                end_date = datetime.now().strftime('%Y-%m-%d')
                
            # Check cache
            cache_key = f"general_{start_date}_{end_date}"
            cached_result = self.cache_service.get_cached_data("general_metrics", cache_key)
            if cached_result:
                return cached_result
                
            result = {
                "start_date": start_date,
                "end_date": end_date,
                "metrics": {
                    "total_tickets": 0,
                    "active_technicians": 0,
                    "avg_tickets_per_tech": 0.0,
                    "workload_distribution": {}
                },
                "success": True
            }
            
            # Get total tickets
            total_result = self.metrics_service.get_ticket_count(
                start_date=start_date,
                end_date=end_date,
                use_cache=True
            )
            
            if total_result.get("success"):
                result["metrics"]["total_tickets"] = total_result.get("count", 0)
                
            # Get active technicians count
            # This would require a more complex query to get unique technicians
            # For now, estimate based on service levels
            result["metrics"]["active_technicians"] = len(self.metrics_service.service_levels) * 5  # Estimate
            
            if result["metrics"]["active_technicians"] > 0:
                result["metrics"]["avg_tickets_per_tech"] = (
                    result["metrics"]["total_tickets"] / result["metrics"]["active_technicians"]
                )
                
            # Cache result
            self.cache_service.set_cached_data("general_metrics", result, ttl=240, sub_key=cache_key)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error getting general metrics: {e}")
            return {"error": str(e), "success": False}
            
    def get_dashboard_metrics_with_date_filter(
        self,
        start_date: str = None,
        end_date: str = None,
        include_trends: bool = False
    ) -> Dict[str, Any]:
        """Get dashboard metrics with optional trend analysis."""
        try:
            # Get base dashboard metrics
            metrics = self.get_dashboard_metrics(start_date, end_date)
            
            if not metrics.get("success"):
                return metrics
                
            # Add trends if requested
            if include_trends:
                from .trends_service import GLPITrendsService
                trends_service = GLPITrendsService(
                    self.http_client, 
                    self.cache_service, 
                    self.metrics_service
                )
                
                trends = trends_service.calculate_trends(start_date, end_date)
                metrics["trends"] = trends
                
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error getting dashboard metrics with filter: {e}")
            return {"error": str(e), "success": False}