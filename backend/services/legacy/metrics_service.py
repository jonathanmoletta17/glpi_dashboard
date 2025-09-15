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
        """Get general ticket count with filters and enhanced validation."""
        try:
            self.logger.debug(f"Getting ticket count with filters - status: {status}, group_id: {group_id}, start_date: {start_date}, end_date: {end_date}")
            
            # Validate dates
            if start_date and not DateValidator.is_valid_date(start_date):
                self.logger.error(f"Invalid start_date format: {start_date}")
                return {
                    "error": "Invalid start_date format", 
                    "count": 0,
                    "success": False,
                    "filters": {"status": status, "group_id": group_id, "start_date": start_date, "end_date": end_date},
                    "timestamp": datetime.now().isoformat()
                }
            if end_date and not DateValidator.is_valid_date(end_date):
                self.logger.error(f"Invalid end_date format: {end_date}")
                return {
                    "error": "Invalid end_date format", 
                    "count": 0,
                    "success": False,
                    "filters": {"status": status, "group_id": group_id, "start_date": start_date, "end_date": end_date},
                    "timestamp": datetime.now().isoformat()
                }
                
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
                    self.logger.debug(f"Returning cached result for {cache_key}")
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
                else:
                    self.logger.warning(f"Unknown status: {status}. Available: {list(self.status_map.keys())}")
                    
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
                "only_id": "true",
                "forcedisplay": ["2"]  # Minimal fields for performance
            }
            
            self.logger.debug(f"Executing search with params: {search_params}")
            
            success, data, error, status_code = self.http_client.search("Ticket", search_params)
            
            self.logger.debug(f"Search result - Success: {success}, Status: {status_code}, Error: {error}")
            
            if not success:
                self.logger.error(f"Failed to get ticket count: {error}")
                return {
                    "error": error or "Unknown GLPI error", 
                    "count": 0,
                    "success": False,
                    "filters": {"status": status, "group_id": group_id, "start_date": start_date, "end_date": end_date},
                    "data_source": "glpi",
                    "timestamp": datetime.now().isoformat()
                }
                
            # Extract count with validation
            total_count = 0
            if isinstance(data, dict):
                total_count = data.get("totalcount", 0)
                # Ensure count is a valid integer
                try:
                    total_count = int(total_count) if total_count is not None else 0
                except (ValueError, TypeError):
                    self.logger.warning(f"Invalid totalcount value: {total_count}, defaulting to 0")
                    total_count = 0
            else:
                self.logger.warning(f"Unexpected data type: {type(data)}, value: {data}")
                
            result = {
                "count": total_count,
                "status": status,
                "group_id": group_id,
                "start_date": start_date,
                "end_date": end_date,
                "success": True,
                "filters": {
                    "status": status,
                    "group_id": group_id,
                    "start_date": start_date,
                    "end_date": end_date
                },
                "data_source": "glpi",
                "timestamp": datetime.now().isoformat()
            }
            
            self.logger.info(f"Successfully retrieved {total_count} tickets with filters")
            
            # Cache result
            if use_cache:
                self.cache_service.set_cached_data("ticket_metrics", result, ttl=300, sub_key=cache_key)
                
            return result
            
        except Exception as e:
            self.logger.error(f"Error getting ticket count: {e}")
            return {
                "error": str(e), 
                "count": 0,
                "success": False,
                "filters": {"status": status, "group_id": group_id, "start_date": start_date, "end_date": end_date},
                "data_source": "error",
                "timestamp": datetime.now().isoformat()
            }
            
    def _get_level_metrics(self, level_id: str, start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        """Get metrics for a specific service level with enhanced error handling."""
        try:
            self.logger.debug(f"Getting metrics for level {level_id} from {start_date} to {end_date}")
            
            # Build search criteria
            criteria = [
                {'field': 2, 'searchtype': 'equals', 'value': level_id}  # Group ID
            ]
            
            if start_date:
                criteria.append({
                    'field': 15,  # Date field
                    'searchtype': 'morethan',
                    'value': start_date
                })
            
            if end_date:
                criteria.append({
                    'field': 15,  # Date field
                    'searchtype': 'lessthan',
                    'value': end_date
                })
            
            # Get total tickets with timeout and retry
            total_response = self.http_client.search('Ticket', {
                'criteria': criteria,
                'range': '0-0',  # Just get count
                'forcedisplay': [2]  # Minimal fields for performance
            })
            
            if not total_response or not total_response.get('success'):
                error_msg = total_response.get('error', 'Unknown error') if total_response else 'No response'
                self.logger.error(f"Failed to get total tickets for level {level_id}: {error_msg}")
                return {
                    'total': 0,
                    'by_status': {},
                    'error': f"Failed to fetch data: {error_msg}",
                    'level_id': level_id
                }
            
            total_count = total_response.get('totalcount', 0)
            self.logger.debug(f"Level {level_id} has {total_count} total tickets")
            
            # Get tickets by status with better error handling
            status_counts = {}
            status_names = {
                '1': 'new',
                '2': 'assigned', 
                '3': 'planned',
                '4': 'waiting',
                '5': 'solved',
                '6': 'closed'
            }
            
            for status_id, status_name in status_names.items():
                try:
                    status_criteria = criteria + [
                        {'field': 12, 'searchtype': 'equals', 'value': status_id}
                    ]
                    
                    status_response = self.http_client.search('Ticket', {
                        'criteria': status_criteria,
                        'range': '0-0',
                        'forcedisplay': [2]
                    })
                    
                    if status_response and status_response.get('success'):
                        count = status_response.get('totalcount', 0)
                        status_counts[status_id] = count
                        self.logger.debug(f"Level {level_id} status {status_name}: {count} tickets")
                    else:
                        status_counts[status_id] = 0
                        self.logger.warning(f"Failed to get status {status_name} count for level {level_id}")
                        
                except Exception as status_error:
                    self.logger.error(f"Error getting status {status_name} for level {level_id}: {status_error}")
                    status_counts[status_id] = 0
            
            # Validate data consistency
            status_sum = sum(status_counts.values())
            if status_sum > total_count:
                self.logger.warning(f"Status sum ({status_sum}) exceeds total ({total_count}) for level {level_id}")
            
            result = {
                'total': total_count,
                'by_status': status_counts,
                'level_id': level_id,
                'data_quality': {
                    'status_sum': status_sum,
                    'total_count': total_count,
                    'consistency_check': status_sum <= total_count
                }
            }
            
            self.logger.debug(f"Successfully retrieved metrics for level {level_id}: {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error getting level metrics for {level_id}: {e}")
            return {
                'total': 0,
                'by_status': {},
                'error': str(e),
                'level_id': level_id
            }
            
    def get_metrics_by_level(self, start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        """Get metrics aggregated by service level with enhanced validation."""
        try:
            # Set date defaults
            if not start_date:
                start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            if not end_date:
                end_date = datetime.now().strftime('%Y-%m-%d')
                
            # Validate dates
            if start_date and not DateValidator.is_valid_date(start_date):
                self.logger.error(f"Invalid start_date format: {start_date}")
                return {"error": "Invalid start_date format", "levels": {}, "totals": {"total": 0, "resolved": 0, "pending": 0}}
            if end_date and not DateValidator.is_valid_date(end_date):
                self.logger.error(f"Invalid end_date format: {end_date}")
                return {"error": "Invalid end_date format", "levels": {}, "totals": {"total": 0, "resolved": 0, "pending": 0}}
                
            # Check cache
            cache_key = f"metrics_by_level_{start_date}_{end_date}"
            cached_result = self.cache_service.get_cached_data("ticket_metrics", cache_key)
            if cached_result:
                self.logger.info(f"Returning cached metrics for key: {cache_key}")
                return cached_result
                
            self.logger.info(f"Fetching metrics by level for period: {start_date} to {end_date}")
                
            result = {
                "start_date": start_date,
                "end_date": end_date,
                "levels": {},
                "totals": {"total": 0, "resolved": 0, "pending": 0},
                "data_source": "glpi",
                "is_mock_data": False,
                "timestamp": datetime.now().isoformat()
            }
            
            # Get metrics for each service level
            for level_name, group_id in self.service_levels.items():
                self.logger.debug(f"Processing level {level_name} (ID: {group_id})")
                
                level_metrics = {
                    "total": 0,
                    "resolved": 0, 
                    "pending": 0,
                    "group_id": group_id,
                    "by_status": {}
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
                else:
                    self.logger.warning(f"Failed to get total count for level {level_name}: {total_result.get('error')}")
                    
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
                        count = resolved_result.get("count", 0)
                        level_metrics["resolved"] += count
                        level_metrics["by_status"][status] = count
                    else:
                        level_metrics["by_status"][status] = 0
                        
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
                        count = pending_result.get("count", 0)
                        level_metrics["pending"] += count
                        level_metrics["by_status"][status] = count
                    else:
                        level_metrics["by_status"][status] = 0
                        
                result["levels"][level_name] = level_metrics
                
                # Add to totals
                result["totals"]["total"] += level_metrics["total"]
                result["totals"]["resolved"] += level_metrics["resolved"]
                result["totals"]["pending"] += level_metrics["pending"]
                
                self.logger.debug(f"Level {level_name}: {level_metrics['total']} total, {level_metrics['resolved']} resolved, {level_metrics['pending']} pending")
                
            # Cache result
            self.cache_service.set_cached_data("ticket_metrics", result, ttl=300, sub_key=cache_key)
            self.logger.info(f"Cached metrics result with {result['totals']['total']} total tickets")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error getting metrics by level: {e}")
            return {
                "error": str(e), 
                "levels": {}, 
                "totals": {"total": 0, "resolved": 0, "pending": 0},
                "start_date": start_date,
                "end_date": end_date,
                "data_source": "error",
                "is_mock_data": False,
                "timestamp": datetime.now().isoformat()
            }
            
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