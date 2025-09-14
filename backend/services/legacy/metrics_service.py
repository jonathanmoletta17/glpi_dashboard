# -*- coding: utf-8 -*-
"""
GLPI Metrics Service - Handles ticket metrics and aggregations.

Extracted from monolithic GLPIService for better separation of concerns.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any

from utils.date_validator import DateValidator
from .http_client_service import GLPIHttpClientService
from .cache_service import GLPICacheService
from .field_discovery_service import GLPIFieldDiscoveryService


class GLPIMetricsService:
    """Handles GLPI ticket metrics and aggregations."""
    
    def __init__(
        self, 
        http_client: GLPIHttpClientService, 
        cache_service: GLPICacheService,
        field_service: GLPIFieldDiscoveryService
    ):
        """Initialize metrics service."""
        self.http_client = http_client
        self.cache_service = cache_service
        self.field_service = field_service
        self.logger = logging.getLogger("glpi_metrics")
        
        # Service level mappings
        self.service_levels = {
            "N1": 89,  # CC-SE-SUBADM-DTIC > N1
            "N2": 90,  # CC-SE-SUBADM-DTIC > N2
            "N3": 91,  # CC-SE-SUBADM-DTIC > N3
            "N4": 92,  # CC-SE-SUBADM-DTIC > N4
        }
        
        # Status mappings
        self.status_map = {
            "Novo": 1,
            "Processando (atribuído)": 2,
            "Processando (planejado)": 3,
            "Pendente": 4,
            "Solucionado": 5,
            "Fechado": 6,
        }
        
    def get_ticket_count_by_hierarchy(
        self,
        start_date: str = None,
        end_date: str = None,
        level: str = None,
        status: str = None,
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """Get ticket count by service hierarchy level."""
        try:
            # Validate dates
            if start_date:
                if not DateValidator.is_valid_date(start_date):
                    return {"error": "Invalid start_date format", "count": 0}
            else:
                start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
                
            if end_date:
                if not DateValidator.is_valid_date(end_date):
                    return {"error": "Invalid end_date format", "count": 0}
            else:
                end_date = datetime.now().strftime('%Y-%m-%d')
                
            # Check cache if enabled
            cache_key = f"ticket_count_{level}_{status}_{start_date}_{end_date}"
            if use_cache:
                cached_result = self.cache_service.get_cached_data("ticket_metrics", cache_key)
                if cached_result:
                    self.logger.debug(f"Returning cached ticket count for {cache_key}")
                    return cached_result
                    
            # Get field IDs
            group_field_id = self.field_service.get_field_id("groups_id_tech") or "8"
            status_field_id = self.field_service.get_field_id("status") or "12"
            date_field_id = self.field_service.get_field_id("date") or "15"
            
            # Build search criteria
            criteria = []
            metacriteria = []
            
            # Date range criteria
            criteria.extend([
                {
                    "link": "AND",
                    "field": date_field_id,
                    "searchtype": "morethan",
                    "value": f"{start_date} 00:00:00"
                },
                {
                    "link": "AND", 
                    "field": date_field_id,
                    "searchtype": "lessthan",
                    "value": f"{end_date} 23:59:59"
                }
            ])
            
            # Level/group criteria
            if level and level in self.service_levels:
                criteria.append({
                    "link": "AND",
                    "field": group_field_id,
                    "searchtype": "equals",
                    "value": str(self.service_levels[level])
                })
                
            # Status criteria  
            if status and status in self.status_map:
                criteria.append({
                    "link": "AND",
                    "field": status_field_id,
                    "searchtype": "equals", 
                    "value": str(self.status_map[status])
                })
                
            # Prepare search parameters
            search_params = {
                "criteria": criteria,
                "range": "0-1",  # Just get count
                "only_id": "true"
            }
            
            if metacriteria:
                search_params["metacriteria"] = metacriteria
                
            # Execute search
            success, data, error, status_code = self.http_client.search("Ticket", search_params)
            
            if not success:
                self.logger.error(f"Failed to get ticket count: {error}")
                return {"error": error, "count": 0}
                
            # Extract count from response
            total_count = 0
            if isinstance(data, dict):
                total_count = data.get("totalcount", 0)
                
            result = {
                "count": total_count,
                "level": level,
                "status": status,
                "start_date": start_date,
                "end_date": end_date,
                "success": True
            }
            
            # Cache result
            if use_cache:
                self.cache_service.set_cached_data("ticket_metrics", result, ttl=300, sub_key=cache_key)
                
            return result
            
        except Exception as e:
            self.logger.error(f"Error getting ticket count by hierarchy: {e}")
            return {"error": str(e), "count": 0}
            
    def get_ticket_count(
        self,
        start_date: str = None,
        end_date: str = None,
        status: str = None,
        group_id: int = None,
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """Get general ticket count with filters."""
        try:
            # Validate dates
            if start_date and not DateValidator.is_valid_date(start_date):
                return {"error": "Invalid start_date format", "count": 0}
            if end_date and not DateValidator.is_valid_date(end_date):
                return {"error": "Invalid end_date format", "count": 0}
                
            # Set defaults
            if not start_date:
                start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            if not end_date:
                end_date = datetime.now().strftime('%Y-%m-%d')
                
            # Check cache
            cache_key = f"general_count_{status}_{group_id}_{start_date}_{end_date}"
            if use_cache:
                cached_result = self.cache_service.get_cached_data("ticket_metrics", cache_key)
                if cached_result:
                    return cached_result
                    
            # Build search criteria
            criteria = []
            
            # Date field
            date_field_id = self.field_service.get_field_id("date") or "15"
            criteria.extend([
                {
                    "link": "AND",
                    "field": date_field_id,
                    "searchtype": "morethan",
                    "value": f"{start_date} 00:00:00"
                },
                {
                    "link": "AND",
                    "field": date_field_id, 
                    "searchtype": "lessthan",
                    "value": f"{end_date} 23:59:59"
                }
            ])
            
            # Status filter
            if status:
                status_field_id = self.field_service.get_field_id("status") or "12"
                if status in self.status_map:
                    criteria.append({
                        "link": "AND",
                        "field": status_field_id,
                        "searchtype": "equals",
                        "value": str(self.status_map[status])
                    })
                    
            # Group filter
            if group_id:
                group_field_id = self.field_service.get_field_id("groups_id_tech") or "8"
                criteria.append({
                    "link": "AND", 
                    "field": group_field_id,
                    "searchtype": "equals",
                    "value": str(group_id)
                })
                
            # Execute search
            search_params = {
                "criteria": criteria,
                "range": "0-1",
                "only_id": "true"
            }
            
            success, data, error, status_code = self.http_client.search("Ticket", search_params)
            
            if not success:
                self.logger.error(f"Failed to get ticket count: {error}")
                return {"error": error, "count": 0}
                
            # Extract count
            total_count = 0
            if isinstance(data, dict):
                total_count = data.get("totalcount", 0)
                
            result = {
                "count": total_count,
                "status": status,
                "group_id": group_id,
                "start_date": start_date,
                "end_date": end_date,
                "success": True
            }
            
            # Cache result
            if use_cache:
                self.cache_service.set_cached_data("ticket_metrics", result, ttl=300, sub_key=cache_key)
                
            return result
            
        except Exception as e:
            self.logger.error(f"Error getting ticket count: {e}")
            return {"error": str(e), "count": 0}
            
    def get_metrics_by_level(self, start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        """Get metrics aggregated by service level."""
        try:
            # Set date defaults
            if not start_date:
                start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            if not end_date:
                end_date = datetime.now().strftime('%Y-%m-%d')
                
            # Check cache
            cache_key = f"metrics_by_level_{start_date}_{end_date}"
            cached_result = self.cache_service.get_cached_data("ticket_metrics", cache_key)
            if cached_result:
                return cached_result
                
            result = {
                "start_date": start_date,
                "end_date": end_date,
                "levels": {},
                "totals": {"total": 0, "resolved": 0, "pending": 0}
            }
            
            # Get metrics for each service level
            for level_name, group_id in self.service_levels.items():
                level_metrics = {
                    "total": 0,
                    "resolved": 0, 
                    "pending": 0,
                    "group_id": group_id
                }
                
                # Total tickets for this level
                total_result = self.get_ticket_count(
                    start_date=start_date,
                    end_date=end_date,
                    group_id=group_id,
                    use_cache=True
                )
                if total_result.get("success"):
                    level_metrics["total"] = total_result.get("count", 0)
                    
                # Resolved tickets (status 5 or 6)
                for status in ["Solucionado", "Fechado"]:
                    resolved_result = self.get_ticket_count(
                        start_date=start_date,
                        end_date=end_date,
                        group_id=group_id,
                        status=status,
                        use_cache=True
                    )
                    if resolved_result.get("success"):
                        level_metrics["resolved"] += resolved_result.get("count", 0)
                        
                # Pending tickets (status 1-4)
                for status in ["Novo", "Processando (atribuído)", "Processando (planejado)", "Pendente"]:
                    pending_result = self.get_ticket_count(
                        start_date=start_date,
                        end_date=end_date,
                        group_id=group_id,
                        status=status,
                        use_cache=True
                    )
                    if pending_result.get("success"):
                        level_metrics["pending"] += pending_result.get("count", 0)
                        
                result["levels"][level_name] = level_metrics
                
                # Add to totals
                result["totals"]["total"] += level_metrics["total"]
                result["totals"]["resolved"] += level_metrics["resolved"]
                result["totals"]["pending"] += level_metrics["pending"]
                
            # Cache result
            self.cache_service.set_cached_data("ticket_metrics", result, ttl=300, sub_key=cache_key)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error getting metrics by level: {e}")
            return {"error": str(e), "levels": {}, "totals": {}}
            
    def get_technician_name(self, tech_id: str) -> str:
        """Get technician name from ID."""
        try:
            if not tech_id or tech_id == "0":
                return "Não atribuído"
                
            # Check cache first
            cache_key = f"tech_name_{tech_id}"
            cached_name = self.cache_service.get_cached_data("active_technicians", cache_key)
            if cached_name:
                return cached_name
                
            # Get from API
            success, data, error, status_code = self.http_client.get_item("User", int(tech_id))
            
            if success and isinstance(data, dict):
                # Extract name from response
                name = data.get("name", f"Técnico {tech_id}")
                if "firstname" in data and "realname" in data:
                    firstname = data.get("firstname", "").strip()
                    realname = data.get("realname", "").strip()
                    if firstname and realname:
                        name = f"{firstname} {realname}"
                        
                # Cache the name
                self.cache_service.set_cached_data("active_technicians", name, ttl=600, sub_key=cache_key)
                return name
            else:
                self.logger.warning(f"Failed to get technician name for ID {tech_id}: {error}")
                return f"Técnico {tech_id}"
                
        except Exception as e:
            self.logger.error(f"Error getting technician name for {tech_id}: {e}")
            return f"Técnico {tech_id}"