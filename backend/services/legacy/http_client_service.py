# -*- coding: utf-8 -*-
"""
GLPI HTTP Client Service - Handles HTTP requests to GLPI API.

Extracted from monolithic GLPIService for better separation of concerns.
"""
import logging
import random
import time
from typing import Any, Dict, List, Optional, Tuple, Union

import requests

from utils.prometheus_metrics import monitor_glpi_request
from utils.structured_logging import log_glpi_request
from .authentication_service import GLPIAuthenticationService


class GLPIHttpClientService:
    """Handles HTTP communication with GLPI API with enhanced robustness and performance."""
    
    def __init__(self, auth_service: GLPIAuthenticationService):
        """Initialize HTTP client service with session reuse and enhanced retry logic."""
        self.auth_service = auth_service
        self.logger = logging.getLogger("glpi.http")  # Padronized logger name
        self.max_retries = 3
        self.retry_delay_base = 2
        
        # Session reuse for better performance (keep-alive)
        self.session = requests.Session()
        
        # Track re-authentication attempts to prevent loops
        self._reauth_attempts = 0
        self._max_reauth_attempts = 2
        
    def _sleep_with_jitter(self, attempt: int) -> None:
        """Sleep with exponential backoff and jitter to reduce thundering herd."""
        base_delay = self.retry_delay_base ** attempt
        jitter = random.uniform(0, 0.5)  # Add up to 500ms jitter
        total_delay = base_delay + jitter
        self.logger.debug(f"Sleeping {total_delay:.2f}s (base: {base_delay}s, jitter: {jitter:.2f}s)")
        time.sleep(total_delay)
        
    def _sanitize_params_for_logging(self, params: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Sanitize parameters for logging, masking sensitive data."""
        if not params:
            return {}
            
        sanitized = {}
        sensitive_keys = {'token', 'password', 'secret', 'key', 'auth', 'session'}
        
        for key, value in params.items():
            key_lower = key.lower()
            if any(sensitive in key_lower for sensitive in sensitive_keys):
                sanitized[key] = '***'
            elif isinstance(value, str) and len(value) > 100:
                sanitized[key] = f"{value[:50]}...({len(value)} chars)"
            else:
                sanitized[key] = value
                
        return sanitized
        
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
            
        url = f"{self.auth_service.glpi_url}/{endpoint.lstrip('/')}"
        
        # Log the constructed URL for debugging with sanitized params
        sanitized_params = self._sanitize_params_for_logging(params)
        self.logger.debug(f"Making {method} request to: {url}")
        if sanitized_params:
            self.logger.debug(f"Request params: {sanitized_params}")
        
        # Prepare request arguments
        request_args = {
            "headers": headers,
            "timeout": timeout,
        }
        
        if params:
            request_args["params"] = params
        if data:
            request_args["json"] = data
            
        # Reset re-auth attempts for new request
        self._reauth_attempts = 0
        
        for attempt in range(self.max_retries):
            try:
                start_time = time.time()
                
                # Make the request using session for connection reuse
                response = self.session.request(method, url, **request_args)
                
                response_time = time.time() - start_time
                
                # Log request if structured logger available
                if self.auth_service.structured_logger:
                    log_glpi_request(
                        url,
                        response.status_code,
                        response_time
                    )
                
                # Integrate observability metrics
                try:
                    monitor_glpi_request(
                        method=method,
                        endpoint=endpoint,
                        status=response.status_code,
                        duration_seconds=response_time
                    )
                except Exception as e:
                    self.logger.debug(f"Failed to record metrics: {e}")
                
                # Handle authentication expiry (401) and forbidden (403 - some GLPIs return this for invalid session)
                if response.status_code in (401, 403):
                    if self._reauth_attempts < self._max_reauth_attempts:
                        self._reauth_attempts += 1
                        self.logger.warning(f"Session invalid (HTTP {response.status_code}), re-authenticating (attempt {self._reauth_attempts}/{self._max_reauth_attempts})...")
                        if self.auth_service.authenticate():
                            headers = self.auth_service.get_api_headers()
                            if headers:
                                request_args["headers"] = headers
                                continue
                        self.logger.error("Re-authentication failed")
                    return False, None, f"Authentication failed after {self._reauth_attempts} attempts", response.status_code
                
                # Handle rate limiting (429)
                if response.status_code == 429:
                    if attempt < self.max_retries - 1:
                        retry_after = response.headers.get("Retry-After")
                        if retry_after and retry_after.isdigit():
                            delay = float(retry_after)
                            self.logger.warning(f"Rate limited (429), respecting Retry-After: {delay}s")
                        else:
                            delay = self.retry_delay_base ** attempt
                            self.logger.warning(f"Rate limited (429), using exponential backoff: {delay}s")
                        time.sleep(delay)
                        continue
                    return False, None, "Rate limited (429) - max retries exceeded", 429
                
                # Log response details if requested
                if log_response:
                    self.logger.info(
                        f"{method} {endpoint} -> {response.status_code} "
                        f"({response_time:.2f}s)"
                    )
                
                # Handle successful responses
                if response.status_code in [200, 201, 206]:
                    if parse_json:
                        try:
                            response_data = response.json()
                            return True, response_data, None, response.status_code
                        except ValueError as e:
                            # Fallback for non-JSON responses when JSON was expected
                            content_type = response.headers.get("content-type", "").lower()
                            if content_type.startswith(("text/", "application/xml", "text/html")):
                                self.logger.debug(f"JSON parse failed, returning text content (Content-Type: {content_type})")
                                return True, {"text": response.text, "content_type": content_type}, None, response.status_code
                            # Log the raw response content for debugging
                            self.logger.error(
                                f"JSON parse error for {method} {endpoint}: {e}. "
                                f"Status: {response.status_code}, "
                                f"Content-Type: {response.headers.get('content-type', 'unknown')}, "
                                f"Content-Length: {len(response.text)}, "
                                f"Raw response: '{response.text[:200]}'"
                            )
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
                        self.logger.warning(
                            f"Server error {response.status_code}, retrying (attempt {attempt + 1}/{self.max_retries})"
                        )
                        self._sleep_with_jitter(attempt)
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
                    self.logger.warning(f"Request timeout, retrying (attempt {attempt + 1}/{self.max_retries})")
                    self._sleep_with_jitter(attempt)
                    continue
                else:
                    return False, None, "Request timeout", 408
                    
            except requests.exceptions.ConnectionError as e:
                if attempt < self.max_retries - 1:
                    self.logger.warning(f"Connection error, retrying (attempt {attempt + 1}/{self.max_retries}): {e}")
                    self._sleep_with_jitter(attempt)
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