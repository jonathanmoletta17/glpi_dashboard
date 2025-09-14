# -*- coding: utf-8 -*-
"""
GLPI HTTP Client Service - Handles HTTP requests to GLPI API.

Extracted from monolithic GLPIService for better separation of concerns.
"""
import logging
import time
from typing import Any, Dict, List, Optional, Tuple

import requests

from utils.prometheus_metrics import monitor_glpi_request
from utils.structured_logging import log_glpi_request
from .authentication_service import GLPIAuthenticationService


class GLPIHttpClientService:
    """Handles HTTP communication with GLPI API."""
    
    def __init__(self, auth_service: GLPIAuthenticationService):
        """Initialize HTTP client service."""
        self.auth_service = auth_service
        self.logger = logging.getLogger("glpi_http")
        self.max_retries = 3
        self.retry_delay_base = 2
        
    def _make_authenticated_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        timeout: int = 30,
        log_response: bool = False,
        parse_json: bool = True,
    ) -> Tuple[bool, Optional[Dict], Optional[str], int]:
        """Make authenticated request to GLPI API with retry logic."""
        
        headers = self.auth_service.get_api_headers()
        if not headers:
            return False, None, "Authentication failed", 401
            
        url = f"{self.auth_service.glpi_url}/apirest.php/{endpoint.lstrip('/')}"
        
        # Prepare request arguments
        request_args = {
            "headers": headers,
            "timeout": timeout,
        }
        
        if params:
            request_args["params"] = params
        if data:
            request_args["json"] = data
            
        for attempt in range(self.max_retries):
            try:
                start_time = time.time()
                
                # Log request if structured logger available
                if self.auth_service.structured_logger:
                    log_glpi_request(
                        self.auth_service.structured_logger,
                        method,
                        url,
                        list(headers.keys())
                    )
                
                # Monitor with Prometheus if available
                try:
                    with monitor_glpi_request(endpoint, method):
                        response = requests.request(method, url, **request_args)
                except NameError:
                    # Fallback if Prometheus not available
                    response = requests.request(method, url, **request_args)
                
                response_time = time.time() - start_time
                
                # Handle authentication expiry
                if response.status_code == 401:
                    self.logger.warning("Session expired, re-authenticating...")
                    if self.auth_service.authenticate():
                        headers = self.auth_service.get_api_headers()
                        if headers:
                            request_args["headers"] = headers
                            continue
                    return False, None, "Re-authentication failed", 401
                
                # Log response details if requested
                if log_response:
                    self.logger.info(
                        f"{method} {endpoint} -> {response.status_code} "
                        f"({response_time:.2f}s)"
                    )
                
                # Handle successful responses
                if response.status_code in [200, 201]:
                    if parse_json:
                        try:
                            response_data = response.json()
                            return True, response_data, None, response.status_code
                        except ValueError as e:
                            return False, None, f"JSON parse error: {e}", response.status_code
                    else:
                        return True, {"text": response.text}, None, response.status_code
                
                # Handle client errors (don't retry)
                elif 400 <= response.status_code < 500:
                    error_msg = f"Client error {response.status_code}: {response.text}"
                    return False, None, error_msg, response.status_code
                
                # Handle server errors (retry)
                elif response.status_code >= 500:
                    if attempt < self.max_retries - 1:
                        delay = self.retry_delay_base ** attempt
                        self.logger.warning(
                            f"Server error {response.status_code}, retrying in {delay}s..."
                        )
                        time.sleep(delay)
                        continue
                    else:
                        error_msg = f"Server error {response.status_code}: {response.text}"
                        return False, None, error_msg, response.status_code
                
                # Handle unexpected status codes
                else:
                    error_msg = f"Unexpected status {response.status_code}: {response.text}"
                    return False, None, error_msg, response.status_code
                    
            except requests.exceptions.Timeout:
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay_base ** attempt
                    self.logger.warning(f"Request timeout, retrying in {delay}s...")
                    time.sleep(delay)
                    continue
                else:
                    return False, None, "Request timeout", 408
                    
            except requests.exceptions.ConnectionError as e:
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay_base ** attempt
                    self.logger.warning(f"Connection error, retrying in {delay}s: {e}")
                    time.sleep(delay)
                    continue
                else:
                    return False, None, f"Connection error: {e}", 503
                    
            except requests.exceptions.RequestException as e:
                return False, None, f"Request error: {e}", 500
                
            except Exception as e:
                self.logger.error(f"Unexpected error in request: {e}")
                return False, None, f"Unexpected error: {e}", 500
                
        return False, None, "Max retries exceeded", 500
        
    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None, **kwargs) -> Tuple[bool, Optional[Dict], Optional[str], int]:
        """Make GET request to GLPI API."""
        return self._make_authenticated_request("GET", endpoint, params=params, **kwargs)
        
    def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None, **kwargs) -> Tuple[bool, Optional[Dict], Optional[str], int]:
        """Make POST request to GLPI API."""
        return self._make_authenticated_request("POST", endpoint, data=data, **kwargs)
        
    def put(self, endpoint: str, data: Optional[Dict[str, Any]] = None, **kwargs) -> Tuple[bool, Optional[Dict], Optional[str], int]:
        """Make PUT request to GLPI API."""
        return self._make_authenticated_request("PUT", endpoint, data=data, **kwargs)
        
    def delete(self, endpoint: str, **kwargs) -> Tuple[bool, Optional[Dict], Optional[str], int]:
        """Make DELETE request to GLPI API."""
        return self._make_authenticated_request("DELETE", endpoint, **kwargs)
        
    def search(self, itemtype: str, criteria: Optional[Dict[str, Any]] = None, **kwargs) -> Tuple[bool, Optional[Dict], Optional[str], int]:
        """Search GLPI items using the search API."""
        endpoint = f"search/{itemtype}"
        params = {}
        
        if criteria:
            # Convert criteria to GLPI search format
            for key, value in criteria.items():
                params[key] = value
                
        return self.get(endpoint, params=params, **kwargs)
        
    def get_item(self, itemtype: str, item_id: int, **kwargs) -> Tuple[bool, Optional[Dict], Optional[str], int]:
        """Get specific item from GLPI."""
        endpoint = f"{itemtype}/{item_id}"
        return self.get(endpoint, **kwargs)
        
    def get_items(self, itemtype: str, ids: List[int], **kwargs) -> Tuple[bool, Optional[Dict], Optional[str], int]:
        """Get multiple items from GLPI."""
        endpoint = f"{itemtype}"
        params = {"ids": ids}
        return self.get(endpoint, params=params, **kwargs)