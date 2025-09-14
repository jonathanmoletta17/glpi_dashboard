# -*- coding: utf-8 -*-
"""
GLPI Trends Service - Handles trend analysis and historical comparisons.

Extracted from monolithic GLPIService for better separation of concerns.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from utils.date_validator import DateValidator
from .http_client_service import GLPIHttpClientService
from .cache_service import GLPICacheService
from .metrics_service import GLPIMetricsService


class GLPITrendsService:
    """Handles trend analysis and historical data comparisons."""
    
    def __init__(
        self, 
        http_client: GLPIHttpClientService, 
        cache_service: GLPICacheService,
        metrics_service: GLPIMetricsService
    ):
        """Initialize trends service."""
        self.http_client = http_client
        self.cache_service = cache_service
        self.metrics_service = metrics_service
        self.logger = logging.getLogger("glpi_trends")
        
    def calculate_trends(
        self, 
        current_start: str, 
        current_end: str,
        comparison_days: int = 30
    ) -> Dict[str, Any]:
        """Calculate trends comparing current period with previous period."""
        try:
            # Validate dates
            if not DateValidator.is_valid_date(current_start):
                return {"error": "Invalid current_start date"}
            if not DateValidator.is_valid_date(current_end):
                return {"error": "Invalid current_end date"}
                
            # Check cache first
            cache_key = f"trends_{current_start}_{current_end}_{comparison_days}"
            cached_result = self.cache_service.get_cached_data("dashboard_metrics", cache_key)
            if cached_result:
                return cached_result
                
            # Calculate previous period dates
            current_start_dt = datetime.strptime(current_start, '%Y-%m-%d')
            current_end_dt = datetime.strptime(current_end, '%Y-%m-%d')
            
            period_length = (current_end_dt - current_start_dt).days
            
            previous_end_dt = current_start_dt - timedelta(days=1)
            previous_start_dt = previous_end_dt - timedelta(days=period_length)
            
            previous_start = previous_start_dt.strftime('%Y-%m-%d')
            previous_end = previous_end_dt.strftime('%Y-%m-%d')
            
            self.logger.info(f"Calculating trends: Current({current_start} to {current_end}) vs Previous({previous_start} to {previous_end})")
            
            # Get current period metrics
            current_metrics = self.metrics_service.get_metrics_by_level(current_start, current_end)
            previous_metrics = self.metrics_service.get_metrics_by_level(previous_start, previous_end)
            
            if current_metrics.get("error") or previous_metrics.get("error"):
                return {"error": "Failed to get metrics for trend calculation"}
                
            # Calculate overall trends
            current_totals = current_metrics.get("totals", {})
            previous_totals = previous_metrics.get("totals", {})
            
            trends = {
                "current_period": {
                    "start_date": current_start,
                    "end_date": current_end,
                    "totals": current_totals
                },
                "previous_period": {
                    "start_date": previous_start,
                    "end_date": previous_end,
                    "totals": previous_totals
                },
                "changes": {
                    "total_tickets": self._calculate_percentage_change(
                        current_totals.get("total", 0),
                        previous_totals.get("total", 0)
                    ),
                    "resolved_tickets": self._calculate_percentage_change(
                        current_totals.get("resolved", 0),
                        previous_totals.get("resolved", 0)
                    ),
                    "pending_tickets": self._calculate_percentage_change(
                        current_totals.get("pending", 0),
                        previous_totals.get("pending", 0)
                    )
                },
                "by_level": {}
            }
            
            # Calculate trends by service level
            current_levels = current_metrics.get("levels", {})
            previous_levels = previous_metrics.get("levels", {})
            
            for level in self.metrics_service.service_levels.keys():
                current_level_data = current_levels.get(level, {})
                previous_level_data = previous_levels.get(level, {})
                
                trends["by_level"][level] = {
                    "total_change": self._calculate_percentage_change(
                        current_level_data.get("total", 0),
                        previous_level_data.get("total", 0)
                    ),
                    "resolved_change": self._calculate_percentage_change(
                        current_level_data.get("resolved", 0),
                        previous_level_data.get("resolved", 0)
                    ),
                    "pending_change": self._calculate_percentage_change(
                        current_level_data.get("pending", 0),
                        previous_level_data.get("pending", 0)
                    )
                }
                
            # Cache results
            self.cache_service.set_cached_data("dashboard_metrics", trends, ttl=300, sub_key=cache_key)
            
            return trends
            
        except Exception as e:
            self.logger.error(f"Error calculating trends: {e}")
            return {"error": str(e)}
            
    def _calculate_percentage_change(self, current: int, previous: int) -> Dict[str, Any]:
        """Calculate percentage change between two values."""
        try:
            if previous == 0:
                if current == 0:
                    return {
                        "absolute": 0,
                        "percentage": 0.0,
                        "direction": "stable",
                        "formatted": "0%"
                    }
                else:
                    return {
                        "absolute": current,
                        "percentage": 100.0,
                        "direction": "up",
                        "formatted": "+100%"
                    }
                    
            absolute_change = current - previous
            percentage_change = (absolute_change / previous) * 100
            
            if percentage_change > 0:
                direction = "up"
                formatted = f"+{percentage_change:.1f}%"
            elif percentage_change < 0:
                direction = "down"
                formatted = f"{percentage_change:.1f}%"
            else:
                direction = "stable"
                formatted = "0%"
                
            return {
                "absolute": absolute_change,
                "percentage": round(percentage_change, 1),
                "direction": direction,
                "formatted": formatted
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating percentage change: {e}")
            return {
                "absolute": 0,
                "percentage": 0.0,
                "direction": "unknown",
                "formatted": "N/A"
            }
            
    def get_historical_data(
        self, 
        start_date: str, 
        end_date: str, 
        interval_days: int = 7
    ) -> Dict[str, Any]:
        """Get historical data broken down by intervals."""
        try:
            # Validate inputs
            if not DateValidator.is_valid_date(start_date):
                return {"error": "Invalid start_date"}
            if not DateValidator.is_valid_date(end_date):
                return {"error": "Invalid end_date"}
                
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            
            if start_dt >= end_dt:
                return {"error": "start_date must be before end_date"}
                
            # Check cache
            cache_key = f"historical_{start_date}_{end_date}_{interval_days}"
            cached_result = self.cache_service.get_cached_data("dashboard_metrics", cache_key)
            if cached_result:
                return cached_result
                
            historical_data = {
                "start_date": start_date,
                "end_date": end_date,
                "interval_days": interval_days,
                "data_points": [],
                "summary": {
                    "total_intervals": 0,
                    "avg_tickets_per_interval": 0.0
                }
            }
            
            # Generate data points for each interval
            current_start = start_dt
            total_tickets = 0
            
            while current_start < end_dt:
                current_end = min(current_start + timedelta(days=interval_days), end_dt)
                
                interval_start_str = current_start.strftime('%Y-%m-%d')
                interval_end_str = current_end.strftime('%Y-%m-%d')
                
                # Get metrics for this interval
                interval_metrics = self.metrics_service.get_metrics_by_level(
                    interval_start_str, 
                    interval_end_str
                )
                
                if not interval_metrics.get("error"):
                    interval_totals = interval_metrics.get("totals", {})
                    interval_total = interval_totals.get("total", 0)
                    total_tickets += interval_total
                    
                    historical_data["data_points"].append({
                        "start_date": interval_start_str,
                        "end_date": interval_end_str,
                        "metrics": interval_totals,
                        "levels": interval_metrics.get("levels", {})
                    })
                    
                current_start = current_end
                
            # Calculate summary
            historical_data["summary"]["total_intervals"] = len(historical_data["data_points"])
            if historical_data["summary"]["total_intervals"] > 0:
                historical_data["summary"]["avg_tickets_per_interval"] = (
                    total_tickets / historical_data["summary"]["total_intervals"]
                )
                
            # Cache results
            self.cache_service.set_cached_data(
                "dashboard_metrics", 
                historical_data, 
                ttl=600, 
                sub_key=cache_key
            )
            
            return historical_data
            
        except Exception as e:
            self.logger.error(f"Error getting historical data: {e}")
            return {"error": str(e)}