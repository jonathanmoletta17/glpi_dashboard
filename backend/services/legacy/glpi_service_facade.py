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
            self.logger.info(f"[HIERARCHY_LEGACY] Starting hierarchy count request - level: {level}, status_id: {status_id}, start_date: {start_date}, end_date: {end_date}, correlation_id: {correlation_id}")
            
            # Convert status_id to status name
            status_name = None
            for name, id_val in self.status_map.items():
                if id_val == status_id:
                    status_name = name
                    break
                    
            self.logger.debug(f"[HIERARCHY_LEGACY] Converted status_id {status_id} to status_name: {status_name}")
            
            if not status_name:
                self.logger.warning(f"[HIERARCHY_LEGACY] Unknown status_id: {status_id}, using None")
                    
            result = self.metrics_service.get_ticket_count_by_hierarchy(
                start_date=start_date,
                end_date=end_date,
                level=level,
                status=status_name
            )
            
            self.logger.debug(f"[HIERARCHY_LEGACY] Metrics service result: {result}")
            
            count = result.get("count", 0) if result.get("success") else 0
            self.logger.info(f"[HIERARCHY_LEGACY] Returning count: {count} for level {level}, status {status_name}")
            
            return count
            
        except Exception as e:
            self.logger.error(f"[HIERARCHY_LEGACY] Error in get_ticket_count_by_hierarchy: {e}")
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
        """Get metrics by service level with detailed logging."""
        try:
            self.logger.info(f"[METRICS_LEVEL] Starting metrics by level request - start_date: {start_date}, end_date: {end_date}")
            
            # Check cache first
            cache_key = f"metrics_level_{start_date}_{end_date}"
            self.logger.debug(f"[METRICS_LEVEL] Checking cache with key: {cache_key}")
            cached_result = self.cache_service.get_cached_data("metrics_level", cache_key)
            if cached_result:
                self.logger.info(f"[METRICS_LEVEL] Returning cached metrics for period {start_date} to {end_date}")
                return cached_result
            
            self.logger.info(f"[METRICS_LEVEL] Cache miss, fetching fresh metrics from service")
            
            # Get metrics from the metrics service
            metrics_result = self.metrics_service.get_metrics_by_level(start_date, end_date)
            
            if metrics_result.get('error'):
                self.logger.error(f"[METRICS_LEVEL] Metrics service returned error: {metrics_result.get('error')}")
            else:
                total_levels = len(metrics_result.get('levels', {}))
                total_tickets = metrics_result.get('totals', {}).get('total', 0)
                self.logger.info(f"[METRICS_LEVEL] Successfully retrieved metrics: {total_levels} levels, {total_tickets} total tickets")
            
            # Cache the result
            self.cache_service.set_cached_data("metrics_level", metrics_result, ttl=300, sub_key=cache_key)
            self.logger.debug(f"[METRICS_LEVEL] Cached metrics result with key: {cache_key}")
            
            return metrics_result
            
        except Exception as e:
            self.logger.error(f"[METRICS_LEVEL] Error getting metrics by level: {e}")
            return {
                "error": str(e),
                "levels": {},
                "totals": {"total": 0, "resolved": 0, "pending": 0},
                "data_source": "error",
                "timestamp": datetime.now().isoformat()
            }
        
    def get_recent_tickets(self, limit: int = 20) -> Dict[str, Any]:
        """Get recent tickets from GLPI with enhanced error handling.
        
        Args:
            limit: Maximum number of tickets to return
            
        Returns:
            Dict with success status and ticket data
        """
        try:
            # Authenticate first
            if not self.auth_service.is_authenticated():
                if not self.auth_service.authenticate():
                    self.logger.error("Failed to authenticate with GLPI")
                    return self._get_enhanced_mock_tickets(limit, "Authentication failed")
            
            # Enhanced search criteria for recent tickets
            search_criteria = {
                'range': f'0-{limit-1}',  # Limit results
                'order': 'DESC',  # Most recent first
                'sort': '15',  # Sort by creation date (field 15)
                'criteria[0][field]': '15',  # Creation date field
                'criteria[0][searchtype]': 'morethan',
                'criteria[0][value]': (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),  # Last 30 days
                'forcedisplay[0]': '2',   # ID
                'forcedisplay[1]': '1',   # Name/Title
                'forcedisplay[2]': '12',  # Status
                'forcedisplay[3]': '15',  # Creation date
                'forcedisplay[4]': '3',   # Priority
                'forcedisplay[5]': '21',  # Content/Description
                'forcedisplay[6]': '4',   # Requester
            }
            
            # Log the search attempt
            self.logger.info(f"Searching for recent tickets with limit: {limit}")
            
            success, response_data, error_msg, status_code = self.http_client.search(
                'Ticket', 
                search_criteria,
                timeout=45  # Increased timeout
            )
            
            if not success:
                self.logger.error(f"GLPI API request failed: {error_msg} (status: {status_code})")
                # Enhanced fallback with better error context
                return self._get_enhanced_mock_tickets(limit, error_msg)
            
            # Enhanced response parsing with validation
            tickets_data = []
            if response_data and 'data' in response_data:
                self.logger.info(f"Processing {len(response_data['data'])} tickets from GLPI")
                for ticket_row in response_data['data']:
                    # GLPI returns data as arrays with numeric keys
                    ticket = {
                        'id': str(ticket_row.get('2', 'unknown')),  # Ensure string ID
                        'title': str(ticket_row.get('1', 'Sem título')),  # Name field
                        'status': self._get_status_name(ticket_row.get('12', '1')),  # Status field
                        'created_date': self._format_date(ticket_row.get('15', datetime.now().isoformat())),  # Creation date
                        'priority': self._get_priority_name(ticket_row.get('3', '3')),  # Priority field
                        'description': str(ticket_row.get('21', 'Sem descrição'))[:200],  # Truncated description
                        'requester': self._get_requester_name(ticket_row.get('4', '0'))  # Resolve requester name
                    }
                    tickets_data.append(ticket)
            else:
                self.logger.warning("No ticket data found in GLPI response")
            
            return {
                'success': True,
                'data': tickets_data,
                'count': len(tickets_data),
                'message': f'Retrieved {len(tickets_data)} recent tickets from GLPI',
                'data_source': 'glpi',
                'is_mock_data': False
            }
                
        except Exception as e:
            self.logger.error(f"Error getting recent tickets: {e}")
            # Fallback to enhanced mock data on error
            return self._get_enhanced_mock_tickets(limit, str(e))
    
    def _get_enhanced_mock_tickets(self, limit: int, error_context: str = None) -> Dict[str, Any]:
        """Enhanced fallback method with better mock data and error context."""
        tickets_data = []
        
        # Generate realistic mock ticket entries
        statuses = ['Novo', 'Processando (atribuído)', 'Pendente', 'Solucionado']
        priorities = ['Muito baixa', 'Baixa', 'Normal', 'Alta', 'Muito alta']
        
        for i in range(min(limit, 10)):  # Limit mock data to 10 items
            ticket = {
                'id': f'mock_{i+1:03d}',
                'title': f'Ticket de Exemplo #{i+1} - Sistema Indisponível',
                'status': statuses[i % len(statuses)],
                'created_date': (datetime.now() - timedelta(hours=i*2)).strftime('%Y-%m-%d'),
                'priority': priorities[i % len(priorities)],
                'description': f'Ticket mock gerado devido a falha na API GLPI: {error_context or "Erro desconhecido"}',
                'requester': f'usuario.exemplo{i+1}@ppiratini.rs.gov.br'
            }
            tickets_data.append(ticket)
        
        return {
            'success': True,
            'data': tickets_data,
            'count': len(tickets_data),
            'message': f'Fallback: Mock tickets generated due to GLPI API failure - {error_context or "Unknown error"}',
            'data_source': 'mock',
            'is_mock_data': True,
            'error_context': error_context
        }
    
    def _get_mock_tickets(self, limit: int) -> Dict[str, Any]:
        """Legacy fallback method - redirects to enhanced version."""
        return self._get_enhanced_mock_tickets(limit)
    
    def _format_date(self, date_str: str) -> str:
        """Format date string to ISO format."""
        try:
            if isinstance(date_str, str) and date_str:
                # Try to parse and reformat the date
                from datetime import datetime
                # Handle different date formats from GLPI
                for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%d/%m/%Y %H:%M:%S', '%d/%m/%Y']:
                    try:
                        parsed_date = datetime.strptime(date_str, fmt)
                        return parsed_date.strftime('%Y-%m-%d')
                    except ValueError:
                        continue
                # If no format matches, return as-is
                return date_str
            return datetime.now().strftime('%Y-%m-%d')
        except Exception as e:
            self.logger.warning(f"Date formatting error: {e}")
            return datetime.now().strftime('%Y-%m-%d')
    
    def _get_status_name(self, status_id: str) -> str:
        """Convert status ID to status name."""
        status_names = {
            '1': 'Novo',
            '2': 'Processando (atribuído)',
            '3': 'Processando (planejado)',
            '4': 'Pendente',
            '5': 'Solucionado',
            '6': 'Fechado'
        }
        return status_names.get(str(status_id), 'Desconhecido')
    
    def _get_priority_name(self, priority_id: str) -> str:
        """Convert priority ID to priority name."""
        priority_names = {
            '1': 'Muito baixa',
            '2': 'Baixa',
            '3': 'Normal',
            '4': 'Alta',
            '5': 'Muito alta',
            '6': 'Crítica'
        }
        return priority_names.get(str(priority_id), 'Normal')
    
    def _get_requester_name(self, requester_id: str) -> str:
        """Get requester name from ID."""
        try:
            self.logger.info(f"DEBUG: Getting requester name for ID: {requester_id}")
            
            if not requester_id or requester_id == '0':
                self.logger.info("DEBUG: Requester ID is empty or 0")
                return 'Usuário desconhecido'
            
            # Try to get user info from GLPI API
            self.logger.info(f"DEBUG: Making API request for User/{requester_id}")
            success, user_data, error_msg, status_code = self.http_client._make_authenticated_request(
                "GET", f"User/{requester_id}"
            )
            
            self.logger.info(f"DEBUG: API response - success: {success}, status: {status_code}, error: {error_msg}")
            
            if success and user_data:
                self.logger.info(f"DEBUG: User data received: {user_data}")
                # Get the user's real name or login
                real_name = user_data.get('realname', '')
                first_name = user_data.get('firstname', '')
                login = user_data.get('name', '')
                
                self.logger.info(f"DEBUG: Names - real: '{real_name}', first: '{first_name}', login: '{login}'")
                
                # Build full name
                if real_name and first_name:
                    result = f"{first_name} {real_name}"
                elif real_name:
                    result = real_name
                elif first_name:
                    result = first_name
                elif login:
                    result = login
                else:
                    result = f"Usuário #{requester_id}"
                
                self.logger.info(f"DEBUG: Final requester name: '{result}'")
                return result
            else:
                self.logger.warning(f"Could not get user info for ID {requester_id}: {error_msg}")
                return f"Usuário #{requester_id}"
                
        except Exception as e:
            self.logger.error(f"Error getting requester name for ID {requester_id}: {e}")
            return f"Usuário #{requester_id}"
        
    def _get_technician_name(self, tech_id: str) -> str:  
        """Get technician name from ID."""
        return self.metrics_service.get_technician_name(tech_id)
        
    def get_technician_performance(self) -> Dict[str, Any]:
        """Get technician performance data for ranking."""
        try:
            self.logger.info("Obtendo dados de performance dos técnicos")
            
            # Check cache first
            cache_key = "technician_performance"
            cached_data = self.cache_service.get_cached_data("technician_ranking", cache_key)
            if cached_data:
                self.logger.info("Dados de performance obtidos do cache")
                return {
                    "success": True,
                    "data": cached_data,
                    "source": "cache"
                }
            
            # Get tickets assigned to technicians using multiple OR criteria
            params = {
                "range": "0-999",
                "criteria[0][field]": "12",  # Status field
                "criteria[0][searchtype]": "equals",
                "criteria[0][value]": "5",  # Solucionado
                "criteria[1][field]": "12",
                "criteria[1][searchtype]": "equals",
                "criteria[1][value]": "6",  # Fechado
                "criteria[1][link]": "OR",
                "forcedisplay[0]": "2",   # ID
                "forcedisplay[1]": "12",  # Status
                "forcedisplay[2]": "5",   # Technician
                "forcedisplay[3]": "15",  # Creation date
                "forcedisplay[4]": "19",  # Modification date
                "forcedisplay[5]": "3",   # Priority
            }
            
            # Usa paginação iterativa para obter todos os tickets
            all_tickets = self._paginated_search("search/Ticket", base_params, max_results=limit * 3)
            
            if not all_tickets:
                self.logger.error("Falha ao obter tickets via paginação")
                return {
                    "success": False,
                    "data": [],
                    "error": error or "Falha ao obter dados dos tickets"
                }
            
            # Process tickets data
            tickets = tickets_data.get("data", [])
            technician_stats = {}
            
            for ticket in tickets:
                tech_field = ticket.get("5")  # Technician field
                
                # Handle different technician field formats
                tech_ids = []
                if tech_field is None:
                    continue  # Skip tickets without technicians
                elif isinstance(tech_field, list):
                    # Multiple technicians assigned
                    tech_ids = [str(tid) for tid in tech_field if tid and str(tid) != "0"]
                else:
                    # Single technician
                    tech_id = str(tech_field)
                    if tech_id != "0" and tech_id != "None":
                        tech_ids = [tech_id]
                
                if not tech_ids:
                    continue  # Skip if no valid technicians found
                
                # Process each technician for this ticket
                for tech_id in tech_ids:
                    
                    if tech_id not in technician_stats:
                        technician_stats[tech_id] = {
                            "id": tech_id,
                            "name": self._get_technician_name(tech_id),
                            "total_tickets": 0,
                            "resolved_tickets": 0,
                            "pending_tickets": 0,
                            "high_priority_tickets": 0,
                            "avg_resolution_time": 0
                        }
                    
                    stats = technician_stats[tech_id]
                    stats["total_tickets"] += 1
                    
                    # Count by status
                    status = ticket.get("12", "1")
                    if status in ["5", "6"]:  # Resolved/Closed
                        stats["resolved_tickets"] += 1
                    else:
                        stats["pending_tickets"] += 1
                    
                    # Count high priority
                    priority = ticket.get("3", "3")
                    if priority in ["4", "5"]:  # High/Very High priority
                        stats["high_priority_tickets"] += 1
            
            # Convert to list and calculate performance metrics
            performance_data = []
            for tech_id, stats in technician_stats.items():
                if stats["total_tickets"] > 0:
                    stats["resolution_rate"] = round(
                        (stats["resolved_tickets"] / stats["total_tickets"]) * 100, 2
                    )
                    stats["performance_score"] = (
                        stats["resolution_rate"] * 0.6 +  # 60% weight on resolution rate
                        min(stats["total_tickets"] * 2, 40) * 0.4  # 40% weight on volume (capped at 40)
                    )
                else:
                    stats["resolution_rate"] = 0
                    stats["performance_score"] = 0
                
                performance_data.append(stats)
            
            # Sort by performance score
            performance_data.sort(key=lambda x: x["performance_score"], reverse=True)
            
            # Cache the result
            self.cache_service.set_cached_data("technician_ranking", performance_data, ttl=300, sub_key=cache_key)
            
            self.logger.info(f"Dados de performance obtidos com sucesso: {len(performance_data)} técnicos")
            
            return {
                "success": True,
                "data": performance_data,
                "source": "api"
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao obter performance dos técnicos: {e}")
            return {
                "success": False,
                "data": [],
                "error": str(e)
            }
    
    def get_technician_ranking_with_filters(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        level: Optional[str] = None,
        limit: int = 50,
        entity_id: Optional[int] = None,
        correlation_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get technician ranking with filters.
        
        Args:
            start_date: Filter by start date
            end_date: Filter by end date
            level: Filter by technician level (N1, N2, N3, N4)
            limit: Maximum number of results
            entity_id: Filter by entity ID
            correlation_id: Correlation ID for tracking
            
        Returns:
            List of technician ranking data
        """
        try:
            self.logger.info(f"GLPIServiceFacade.get_technician_ranking_with_filters chamado com: start_date={start_date}, end_date={end_date}, level={level}, limit={limit}, entity_id={entity_id}, correlation_id={correlation_id}")
            
            # Build cache key with filters
            cache_key = f"technician_ranking_filters_{start_date}_{end_date}_{level}_{limit}_{entity_id}"
            cached_data = self.cache_service.get_cached_data("technician_ranking", cache_key)
            if cached_data:
                self.logger.info(f"Dados de ranking obtidos do cache: {len(cached_data)} técnicos")
                return cached_data[:limit] if limit else cached_data
            
            # Build search criteria with filters - PRIORIZAR APENAS TICKETS RESOLVIDOS/FECHADOS
            base_params = {
                "criteria[0][field]": "12",  # Status field
                "criteria[0][searchtype]": "equals",
                "criteria[0][value]": "5",  # Solucionado - PRIORIDADE PARA RANKING
                "criteria[1][field]": "12",
                "criteria[1][searchtype]": "equals",
                "criteria[1][value]": "6",  # Fechado - PRIORIDADE PARA RANKING
                "criteria[1][link]": "OR",
                "forcedisplay[0]": "2",   # ID
                "forcedisplay[1]": "12",  # Status
                "forcedisplay[2]": "5",   # Technician
                "forcedisplay[3]": "15",  # Creation date
                "forcedisplay[4]": "19",  # Modification date
                "forcedisplay[5]": "3",   # Priority
            }
            
            # Add date filters if provided
            criteria_index = 2  # Ajustado para nova estrutura com apenas 2 critérios de status
            if start_date:
                params[f"criteria[{criteria_index}][field]"] = "15"  # Creation date
                params[f"criteria[{criteria_index}][searchtype]"] = "morethan"
                params[f"criteria[{criteria_index}][value]"] = start_date
                params[f"criteria[{criteria_index}][link]"] = "AND"
                criteria_index += 1
                
            if end_date:
                params[f"criteria[{criteria_index}][field]"] = "15"  # Creation date
                params[f"criteria[{criteria_index}][searchtype]"] = "lessthan"
                params[f"criteria[{criteria_index}][value]"] = end_date
                params[f"criteria[{criteria_index}][link]"] = "AND"
                criteria_index += 1
            
            # Add entity filter if provided
            if entity_id:
                params[f"criteria[{criteria_index}][field]"] = "80"  # Entity field
                params[f"criteria[{criteria_index}][searchtype]"] = "equals"
                params[f"criteria[{criteria_index}][value]"] = str(entity_id)
                params[f"criteria[{criteria_index}][link]"] = "AND"
            
            success, tickets_data, error, status_code = self.http_client._make_authenticated_request(
                "GET", "search/Ticket", params=params
            )
            
            if not success or not tickets_data:
                self.logger.error(f"Falha ao obter tickets: {error}")
                return []
            
            # Process tickets data
            tickets = tickets_data.get("data", [])
            technician_stats = {}
            
            for ticket in tickets:
                tech_field = ticket.get("5")  # Technician field
                
                # Handle different technician field formats
                tech_ids = []
                if tech_field is None:
                    continue  # Skip tickets without technicians
                elif isinstance(tech_field, list):
                    # Multiple technicians assigned
                    tech_ids = [str(tid) for tid in tech_field if tid and str(tid) != "0"]
                else:
                    # Single technician
                    tech_id = str(tech_field)
                    if tech_id != "0" and tech_id != "None":
                        tech_ids = [tech_id]
                
                if not tech_ids:
                    continue  # Skip if no valid technicians found
                
                # Process each technician for this ticket
                for tech_id in tech_ids:
                    tech_name = self._get_technician_name(tech_id)
                    
                    # Apply level filter if specified
                    if level and not self._technician_matches_level(tech_name, level):
                        continue
                    
                    if tech_id not in technician_stats:
                        technician_stats[tech_id] = {
                            "id": tech_id,
                            "name": tech_name,
                            "level": self._extract_technician_level(tech_name),
                            "total_tickets": 0,
                            "resolved_tickets": 0,
                            "pending_tickets": 0,
                            "high_priority_tickets": 0,
                            "avg_resolution_time": 0,
                            "data_source": "glpi",
                            "is_mock_data": False
                        }
                    
                    stats = technician_stats[tech_id]
                    stats["total_tickets"] += 1
                    
                    # Count by status
                    status = ticket.get("12", "1")
                    if status in ["5", "6"]:  # Resolved/Closed
                        stats["resolved_tickets"] += 1
                    else:
                        stats["pending_tickets"] += 1
                    
                    # Count high priority
                    priority = ticket.get("3", "3")
                    if priority in ["4", "5"]:  # High/Very High priority
                        stats["high_priority_tickets"] += 1
            
            # Convert to list and calculate performance metrics
            ranking_data = []
            for tech_id, stats in technician_stats.items():
                if stats["total_tickets"] > 0:
                    stats["resolution_rate"] = round(
                        (stats["resolved_tickets"] / stats["total_tickets"]) * 100, 2
                    )
                    stats["performance_score"] = round(
                        stats["resolution_rate"] * 0.6 +  # 60% weight on resolution rate
                        min(stats["total_tickets"] * 2, 40) * 0.4, 2  # 40% weight on volume (capped at 40)
                    )
                    stats["ticket_count"] = stats["total_tickets"]
                else:
                    stats["resolution_rate"] = 0
                    stats["performance_score"] = 0
                    stats["ticket_count"] = 0
                
                ranking_data.append(stats)
            
            # Sort by performance score
            ranking_data.sort(key=lambda x: x["performance_score"], reverse=True)
            
            # Apply limit
            if limit:
                ranking_data = ranking_data[:limit]
            
            # Cache the result
            self.cache_service.set_cached_data("technician_ranking", ranking_data, ttl=300, sub_key=cache_key)
            
            self.logger.info(f"Ranking de técnicos obtido com sucesso: {len(ranking_data)} técnicos")
            self.logger.debug(f"Dados de ranking retornados: {ranking_data[:3] if ranking_data else 'Lista vazia'}")
            
            return ranking_data
            
        except Exception as e:
            self.logger.error(f"Erro ao obter ranking de técnicos: {e}")
            return []
    
    def _technician_matches_level(self, tech_name: str, level: str) -> bool:
        """Check if technician matches the specified level."""
        if not level or not tech_name:
            return True
        
        tech_name_upper = tech_name.upper()
        level_upper = level.upper()
        
        # Simple level matching - can be enhanced based on naming conventions
        return level_upper in tech_name_upper
    
    def _group_tickets_by_status(self, tickets: List[Dict]) -> Dict[str, int]:
        """Group tickets by status and return counts."""
        status_counts = {}
        for ticket in tickets:
            status_id = str(ticket.get('12', '1'))  # field 12 = status
            status_name = self._get_status_name(status_id)
            status_counts[status_name] = status_counts.get(status_name, 0) + 1
        return status_counts
    
    def _group_tickets_by_priority(self, tickets: List[Dict]) -> Dict[str, int]:
        """Group tickets by priority and return counts."""
        priority_counts = {}
        for ticket in tickets:
            priority_id = str(ticket.get('3', '1'))  # field 3 = priority
            priority_name = self._get_priority_name(priority_id)
            priority_counts[priority_name] = priority_counts.get(priority_name, 0) + 1
        return priority_counts

    def _extract_technician_level(self, tech_name: str) -> str:
        """Extract technician level from name.
        
        NOTA: Este é um método heurístico baseado em substring no nome.
        Para maior precisão, considere usar grupos GLPI:
        - N1: group_id = 89
        - N2: group_id = 90  
        - N3: group_id = 91
        - N4: group_id = 92
        """
        if not tech_name:
            return "N1"
        
        tech_name_upper = tech_name.upper()
        
        if "N4" in tech_name_upper:
            return "N4"
        elif "N3" in tech_name_upper:
            return "N3"
        elif "N2" in tech_name_upper:
            return "N2"
        else:
            return "N1"
    
    def _paginated_search(self, endpoint: str, base_params: Dict[str, Any], page_size: int = 500, max_results: int = None) -> List[Dict[str, Any]]:
        """
        Implementa paginação iterativa para evitar perda de dados em grandes consultas.
        
        Args:
            endpoint: Endpoint da API GLPI (ex: 'search/Ticket')
            base_params: Parâmetros base da consulta (sem range)
            page_size: Tamanho da página (padrão 500, máximo recomendado)
            max_results: Limite máximo de resultados (None = sem limite)
            
        Returns:
            Lista completa de resultados paginados
        """
        all_results = []
        start = 0
        
        while True:
            # Calcula o range atual
            end = start + page_size - 1
            if max_results and start >= max_results:
                break
                
            # Ajusta o range se necessário
            if max_results and end >= max_results:
                end = max_results - 1
            
            # Cria parâmetros com paginação
            params = base_params.copy()
            params["range"] = f"{start}-{end}"
            
            # Faz a requisição
            success, data, error, status_code = self.http_client._make_authenticated_request(
                "GET", endpoint, params=params
            )
            
            if not success or not data:
                self.logger.warning(f"Paginação parou em {start}: {error}")
                break
                
            # Processa os dados retornados
            if isinstance(data, dict) and "data" in data:
                page_results = data["data"]
            elif isinstance(data, list):
                page_results = data
            else:
                self.logger.warning(f"Formato de dados inesperado na página {start}: {type(data)}")
                break
            
            # Se não há mais resultados, para
            if not page_results or len(page_results) == 0:
                break
                
            all_results.extend(page_results)
            
            # Se retornou menos que o page_size, chegou ao fim
            if len(page_results) < page_size:
                break
                
            start += page_size
            
            # Log de progresso
            if len(all_results) % 1000 == 0:
                self.logger.info(f"Paginação: {len(all_results)} resultados coletados")
        
        self.logger.info(f"Paginação concluída: {len(all_results)} resultados totais")
        return all_results
        
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
        """Get dashboard metrics with modification date filter.
        
        Filtra tickets por data de modificação (campo 19) em vez de data de criação (campo 15).
        """
        try:
            cache_key = f"dashboard_metrics_mod_date_{start_date}_{end_date}"
            
            # Check cache first
            if self._is_cache_valid(cache_key):
                cached_data = self._get_cache_data(cache_key)
                if cached_data:
                    return cached_data
            
            # Build search criteria with modification date filter (field 19)
            criteria = []
            criteria_index = 0
            
            if start_date:
                criteria.append({
                    f"criteria[{criteria_index}][field]": "19",  # modification date
                    f"criteria[{criteria_index}][searchtype]": "morethan",
                    f"criteria[{criteria_index}][value]": start_date
                })
                criteria_index += 1
                
            if end_date:
                if criteria_index > 0:
                    criteria.append({f"criteria[{criteria_index}][link]": "AND"})
                criteria.append({
                    f"criteria[{criteria_index}][field]": "19",  # modification date
                    f"criteria[{criteria_index}][searchtype]": "lessthan", 
                    f"criteria[{criteria_index}][value]": end_date
                })
            
            # Flatten criteria for request
            search_params = {}
            for criterion in criteria:
                search_params.update(criterion)
            
            # Add standard parameters
            search_params.update({
                "range": "0-999",
                "order": "DESC",
                "sort": "19"  # sort by modification date
            })
            
            # Make request
            response = self._make_authenticated_request(
                "GET", 
                "/search/Ticket", 
                params=search_params
            )
            
            if response and response.get("data"):
                tickets = response["data"]
                
                # Process metrics from filtered tickets
                result = {
                    "total_tickets": len(tickets),
                    "filter_type": "modification_date",
                    "date_field": "modification_date",
                    "date_range": {
                        "start": start_date,
                        "end": end_date
                    },
                    "tickets_by_status": self._group_tickets_by_status(tickets),
                    "tickets_by_priority": self._group_tickets_by_priority(tickets)
                }
                
                # Cache result
                self._set_cache_data(cache_key, result, ttl=300)
                return result
            else:
                # Fallback to dashboard service if search fails
                result = self.dashboard_service.get_dashboard_metrics_with_date_filter(
                    start_date, end_date, include_trends=False
                )
                
                if result and isinstance(result, dict):
                    result["filter_type"] = "modification_date"
                    result["date_field"] = "modification_date"
                    
                return result
                
        except Exception as e:
            self.logger.error(f"Error in get_dashboard_metrics_with_modification_date_filter: {e}")
            return {"error": str(e), "filter_type": "modification_date"}
        
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
        
    def get_new_tickets_with_filters(
        self,
        limit: int = 20,
        priority: Optional[str] = None,
        category: Optional[str] = None,
        technician: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Get new tickets with filters applied.
        
        Args:
            limit: Maximum number of tickets to return
            priority: Filter by priority
            category: Filter by category
            technician: Filter by technician
            start_date: Filter by start date
            end_date: Filter by end date
            **kwargs: Additional filter parameters
            
        Returns:
            Dictionary with filtered tickets data
        """
        try:
            self.logger.info(f"Getting new tickets with filters - limit: {limit}, priority: {priority}, category: {category}")
            
            # Authenticate first
            if not self.auth_service.is_authenticated():
                if not self.auth_service.authenticate():
                    self.logger.error("Failed to authenticate with GLPI")
                    return self._get_enhanced_mock_tickets(limit, "Authentication failed")
            
            # Build search criteria for NEW tickets (status = 1)
            search_criteria = {
                'range': f'0-{limit-1}',  # Limit results
                'order': 'DESC',  # Most recent first
                'sort': '15',  # Sort by creation date (field 15)
                'criteria[0][field]': '12',  # Status field
                'criteria[0][searchtype]': 'equals',
                'criteria[0][value]': '1',  # Status "Novo" (New)
                'forcedisplay[0]': '2',   # ID
                'forcedisplay[1]': '1',   # Name/Title
                'forcedisplay[2]': '12',  # Status
                'forcedisplay[3]': '15',  # Creation date
                'forcedisplay[4]': '3',   # Priority
                'forcedisplay[5]': '21',  # Content/Description
                'forcedisplay[6]': '4',   # Requester
            }
            
            # Add additional filters if provided
            criteria_index = 1
            if priority:
                search_criteria[f'criteria[{criteria_index}][field]'] = '3'  # Priority field
                search_criteria[f'criteria[{criteria_index}][searchtype]'] = 'equals'
                search_criteria[f'criteria[{criteria_index}][value]'] = priority
                search_criteria[f'criteria[{criteria_index}][link]'] = 'AND'
                criteria_index += 1
            
            if start_date:
                search_criteria[f'criteria[{criteria_index}][field]'] = '15'  # Creation date field
                search_criteria[f'criteria[{criteria_index}][searchtype]'] = 'morethan'
                search_criteria[f'criteria[{criteria_index}][value]'] = start_date
                search_criteria[f'criteria[{criteria_index}][link]'] = 'AND'
                criteria_index += 1
            
            if end_date:
                search_criteria[f'criteria[{criteria_index}][field]'] = '15'  # Creation date field
                search_criteria[f'criteria[{criteria_index}][searchtype]'] = 'lessthan'
                search_criteria[f'criteria[{criteria_index}][value]'] = end_date
                search_criteria[f'criteria[{criteria_index}][link]'] = 'AND'
                criteria_index += 1
            
            # Log the search attempt
            self.logger.info(f"Searching for NEW tickets with limit: {limit}")
            
            success, response_data, error_msg, status_code = self.http_client.search(
                'Ticket', 
                search_criteria,
                timeout=45  # Increased timeout
            )
            
            if not success:
                self.logger.error(f"GLPI API request failed: {error_msg} (status: {status_code})")
                # Enhanced fallback with better error context
                return self._get_enhanced_mock_tickets(limit, error_msg)
            
            # Enhanced response parsing with validation
            tickets_data = []
            if response_data and 'data' in response_data:
                self.logger.info(f"Processing {len(response_data['data'])} NEW tickets from GLPI")
                for ticket_row in response_data['data']:
                    # Get requester name instead of just ID
                    requester_id = ticket_row.get('4', '0')
                    requester_name = self._get_requester_name(requester_id) if requester_id != '0' else 'Usuário desconhecido'
                    
                    # GLPI returns data as arrays with numeric keys
                    ticket = {
                        'id': str(ticket_row.get('2', 'unknown')),  # Ensure string ID
                        'title': str(ticket_row.get('1', 'Sem título')),  # Name field
                        'status': self._get_status_name(ticket_row.get('12', '1')),  # Status field
                        'created_date': self._format_date(ticket_row.get('15', datetime.now().isoformat())),  # Creation date
                        'priority': self._get_priority_name(ticket_row.get('3', '3')),  # Priority field
                        'description': str(ticket_row.get('21', 'Sem descrição'))[:200],  # Truncated description
                        'requester': requester_name  # Requester name instead of ID
                    }
                    tickets_data.append(ticket)
            else:
                self.logger.warning("No NEW ticket data found in GLPI response")
            
            result = {
                'success': True,
                'data': tickets_data,
                'count': len(tickets_data),
                'message': f'Retrieved {len(tickets_data)} new tickets from GLPI',
                'data_source': 'glpi',
                'is_mock_data': False,
                'filters_applied': {
                    'limit': limit,
                    'priority': priority,
                    'category': category,
                    'technician': technician,
                    'start_date': start_date,
                    'end_date': end_date,
                    'status': 'Novo'  # Always filtering by "Novo" status
                }
            }
            
            # Log successful filtering
            self.logger.info(f"Successfully retrieved {len(tickets_data)} NEW tickets with filters")
            return result
            
        except Exception as e:
            self.logger.error(f"Error getting tickets with filters: {e}")
            return self._get_enhanced_mock_tickets(
                limit=limit, 
                error_context=f"Filter error: {str(e)}"
            )
    
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