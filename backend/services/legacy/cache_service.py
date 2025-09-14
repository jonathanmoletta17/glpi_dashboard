# -*- coding: utf-8 -*-
"""
GLPI Cache Service - Handles caching logic for GLPI data.

Extracted from monolithic GLPIService for better separation of concerns.
"""
import time
from typing import Any, Dict, Optional


class GLPICacheService:
    """Handles caching for GLPI service data."""
    
    def __init__(self):
        """Initialize cache service."""
        self._cache = {
            "technician_ranking": {
                "data": None,
                "timestamp": None, 
                "ttl": 300,  # 5 minutes
            },
            "active_technicians": {
                "data": None,
                "timestamp": None,
                "ttl": 600,  # 10 minutes
            },
            "field_ids": {
                "data": None,
                "timestamp": None,
                "ttl": 1800,  # 30 minutes
            },
            "dashboard_metrics": {
                "data": None,
                "timestamp": None,
                "ttl": 180,  # 3 minutes
            },
            "ticket_metrics": {
                "data": None,
                "timestamp": None,
                "ttl": 300,  # 5 minutes
            },
            "general_metrics": {
                "data": None,
                "timestamp": None,
                "ttl": 240,  # 4 minutes
            },
        }
        
    def _is_cache_valid(self, cache_key: str, sub_key: str = None) -> bool:
        """Check if cache entry is valid and not expired."""
        try:
            if cache_key not in self._cache:
                return False
                
            cache_entry = self._cache[cache_key]
            
            if sub_key:
                if not isinstance(cache_entry.get("data"), dict):
                    return False
                if sub_key not in cache_entry["data"]:
                    return False
                sub_entry = cache_entry["data"][sub_key]
                if not isinstance(sub_entry, dict):
                    return False
                timestamp = sub_entry.get("timestamp")
                ttl = sub_entry.get("ttl", cache_entry.get("ttl", 300))
            else:
                timestamp = cache_entry.get("timestamp")
                ttl = cache_entry.get("ttl", 300)
                
            if not timestamp:
                return False
                
            elapsed = time.time() - timestamp
            return elapsed < ttl
            
        except Exception:
            return False
            
    def _get_cache_data(self, cache_key: str, sub_key: str = None):
        """Get data from cache if valid."""
        try:
            if not self._is_cache_valid(cache_key, sub_key):
                return None
                
            cache_entry = self._cache[cache_key]
            
            if sub_key:
                if isinstance(cache_entry.get("data"), dict) and sub_key in cache_entry["data"]:
                    sub_entry = cache_entry["data"][sub_key]
                    if isinstance(sub_entry, dict):
                        return sub_entry.get("data")
                return None
            else:
                return cache_entry.get("data")
                
        except Exception:
            return None
            
    def _set_cache_data(self, cache_key: str, data: Any, ttl: int = 300, sub_key: str = None):
        """Set data in cache with TTL."""
        try:
            current_time = time.time()
            
            if cache_key not in self._cache:
                self._cache[cache_key] = {
                    "data": None,
                    "timestamp": None,
                    "ttl": ttl,
                }
                
            if sub_key:
                if not isinstance(self._cache[cache_key]["data"], dict):
                    self._cache[cache_key]["data"] = {}
                    
                self._cache[cache_key]["data"][sub_key] = {
                    "data": data,
                    "timestamp": current_time,
                    "ttl": ttl,
                }
            else:
                self._cache[cache_key]["data"] = data
                self._cache[cache_key]["timestamp"] = current_time
                if ttl != 300:  # Only update TTL if different from default
                    self._cache[cache_key]["ttl"] = ttl
                    
        except Exception as e:
            # Log cache errors but don't fail the operation
            pass
            
    def get_cached_data(self, cache_key: str, sub_key: str = None):
        """Public method to get cached data."""
        return self._get_cache_data(cache_key, sub_key)
        
    def set_cached_data(self, cache_key: str, data: Any, ttl: int = 300, sub_key: str = None):
        """Public method to set cached data."""
        self._set_cache_data(cache_key, data, ttl, sub_key)
        
    def invalidate_cache(self, cache_key: str = None, sub_key: str = None):
        """Invalidate specific cache entry or all cache."""
        try:
            if cache_key is None:
                # Clear all cache
                for key in self._cache:
                    self._cache[key]["data"] = None
                    self._cache[key]["timestamp"] = None
            elif cache_key in self._cache:
                if sub_key and isinstance(self._cache[cache_key]["data"], dict):
                    # Clear specific sub-key
                    if sub_key in self._cache[cache_key]["data"]:
                        del self._cache[cache_key]["data"][sub_key]
                else:
                    # Clear entire cache key
                    self._cache[cache_key]["data"] = None
                    self._cache[cache_key]["timestamp"] = None
                    
        except Exception:
            pass
            
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics for monitoring."""
        stats = {
            "total_keys": len(self._cache),
            "valid_entries": 0,
            "expired_entries": 0,
            "cache_details": {}
        }
        
        current_time = time.time()
        
        for key, entry in self._cache.items():
            timestamp = entry.get("timestamp")
            ttl = entry.get("ttl", 300)
            has_data = entry.get("data") is not None
            
            if timestamp and has_data:
                elapsed = current_time - timestamp
                is_valid = elapsed < ttl
                
                if is_valid:
                    stats["valid_entries"] += 1
                else:
                    stats["expired_entries"] += 1
                    
                stats["cache_details"][key] = {
                    "has_data": has_data,
                    "is_valid": is_valid,
                    "elapsed_seconds": elapsed if timestamp else None,
                    "ttl_seconds": ttl,
                }
            else:
                stats["cache_details"][key] = {
                    "has_data": has_data,
                    "is_valid": False,
                    "elapsed_seconds": None,
                    "ttl_seconds": ttl,
                }
                
        return stats