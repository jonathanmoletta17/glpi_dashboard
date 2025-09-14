# -*- coding: utf-8 -*-
"""
GLPI Field Discovery Service - Handles discovery and mapping of GLPI field IDs.

Extracted from monolithic GLPIService for better separation of concerns.
"""
import logging
from typing import Dict, Optional

from .http_client_service import GLPIHttpClientService
from .cache_service import GLPICacheService


class GLPIFieldDiscoveryService:
    """Handles discovery and mapping of GLPI field IDs."""
    
    def __init__(self, http_client: GLPIHttpClientService, cache_service: GLPICacheService):
        """Initialize field discovery service."""
        self.http_client = http_client
        self.cache_service = cache_service
        self.logger = logging.getLogger("glpi_fields")
        self.field_ids = {}
        
    def discover_field_ids(self) -> bool:
        """Discover and map GLPI field IDs for tickets."""
        try:
            # Check cache first
            cached_fields = self.cache_service.get_cached_data("field_ids")
            if cached_fields:
                self.field_ids = cached_fields
                self.logger.info("Field IDs loaded from cache")
                return True
                
            self.logger.info("Discovering GLPI field IDs...")
            
            # Discover fields by analyzing ticket structure
            success, data, error, status_code = self.http_client.search(
                "Ticket",
                {
                    "range": "0-1",  # Get just one ticket to analyze structure
                    "forcedisplay[0]": 2,  # ID
                    "forcedisplay[1]": 1,  # Name/Title
                }
            )
            
            if not success:
                self.logger.error(f"Failed to discover fields: {error}")
                self._apply_fallback_field_ids()
                return False
                
            # Extract field mappings from response
            field_mappings = self._extract_field_mappings(data)
            
            if field_mappings:
                self.field_ids.update(field_mappings)
                
                # Cache the discovered fields
                self.cache_service.set_cached_data("field_ids", self.field_ids, ttl=1800)
                
                self.logger.info(f"Discovered {len(self.field_ids)} field mappings")
                return True
            else:
                self.logger.warning("No field mappings discovered, using fallback")
                self._apply_fallback_field_ids()
                return False
                
        except Exception as e:
            self.logger.error(f"Error in field discovery: {e}")
            self._apply_fallback_field_ids()
            return False
            
    def _extract_field_mappings(self, search_data: Dict) -> Dict[str, int]:
        """Extract field ID mappings from search response."""
        mappings = {}
        
        try:
            # Try to extract from search response structure
            if "data" in search_data:
                # Standard search response format
                for item in search_data["data"]:
                    if isinstance(item, dict):
                        for key, value in item.items():
                            if key.isdigit():
                                field_id = int(key)
                                # Map common field names
                                if field_id == 1:
                                    mappings["name"] = field_id
                                elif field_id == 2:
                                    mappings["id"] = field_id
                                elif field_id == 12:
                                    mappings["status"] = field_id
                                elif field_id == 4:
                                    mappings["users_id_requester"] = field_id
                                elif field_id == 5:
                                    mappings["users_id_tech"] = field_id
                                elif field_id == 8:
                                    mappings["groups_id_tech"] = field_id
                                elif field_id == 15:
                                    mappings["date"] = field_id
                                elif field_id == 18:
                                    mappings["closedate"] = field_id
                                elif field_id == 19:
                                    mappings["solvedate"] = field_id
                                    
            # Also try to get fields from listSearchOptions if available
            success, options_data, _, _ = self.http_client.get("listSearchOptions/Ticket")
            if success and isinstance(options_data, dict):
                for field_id, field_info in options_data.items():
                    if field_id.isdigit() and isinstance(field_info, dict):
                        field_name = field_info.get("field", "").lower()
                        table = field_info.get("table", "")
                        
                        # Map based on field name and table
                        if field_name == "name" and "glpi_tickets" in table:
                            mappings["name"] = int(field_id)
                        elif field_name == "status" and "glpi_tickets" in table:
                            mappings["status"] = int(field_id)
                        elif field_name == "date" and "glpi_tickets" in table:
                            mappings["date"] = int(field_id)
                        elif field_name == "closedate" and "glpi_tickets" in table:
                            mappings["closedate"] = int(field_id)
                        elif field_name == "solvedate" and "glpi_tickets" in table:
                            mappings["solvedate"] = int(field_id)
                            
        except Exception as e:
            self.logger.error(f"Error extracting field mappings: {e}")
            
        return mappings
        
    def _apply_fallback_field_ids(self):
        """Apply known fallback field IDs for common GLPI installations."""
        fallback_fields = {
            "id": 2,
            "name": 1,
            "status": 12,
            "users_id_requester": 4,
            "users_id_tech": 5,
            "groups_id_tech": 8,
            "date": 15,
            "closedate": 18,
            "solvedate": 19,
            "priority": 3,
            "urgency": 10,
            "impact": 11,
            "category": 7,
            "type": 14,
            "entities_id": 80,
            "locations_id": 83,
        }
        
        self.field_ids.update(fallback_fields)
        
        # Cache fallback fields with shorter TTL
        self.cache_service.set_cached_data("field_ids", self.field_ids, ttl=600)
        
        self.logger.info(f"Applied {len(fallback_fields)} fallback field mappings")
        
    def get_field_id(self, field_name: str) -> Optional[int]:
        """Get field ID for a field name."""
        if not self.field_ids:
            self.discover_field_ids()
            
        return self.field_ids.get(field_name)
        
    def get_all_field_ids(self) -> Dict[str, int]:
        """Get all discovered field IDs."""
        if not self.field_ids:
            self.discover_field_ids()
            
        return self.field_ids.copy()
        
    def invalidate_field_cache(self):
        """Invalidate cached field mappings."""
        self.cache_service.invalidate_cache("field_ids")
        self.field_ids.clear()
        self.logger.info("Field ID cache invalidated")
        
    def refresh_field_mappings(self) -> bool:
        """Force refresh of field mappings."""
        self.invalidate_field_cache()
        return self.discover_field_ids()