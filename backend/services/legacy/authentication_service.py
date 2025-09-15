# -*- coding: utf-8 -*-
"""
GLPI Authentication Service - Handles session management and authentication.

Extracted from monolithic GLPIService for better separation of concerns.
"""
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Optional

import requests

from config.settings import active_config
from utils.structured_logger import create_glpi_logger
from utils.structured_logging import log_glpi_request


class GLPIAuthenticationService:
    """Handles GLPI authentication and session management."""
    
    def __init__(self):
        """Initialize authentication service."""
        config_obj = active_config()
        
        # Configuration setup
        self.dev_mode = getattr(config_obj, "DEBUG", False)
        raw_url = getattr(config_obj, "GLPI_URL", "http://localhost:9999")
        self.glpi_url = self._normalize_glpi_url(raw_url)
        self.app_token = getattr(config_obj, "GLPI_APP_TOKEN", None)
        self.user_token = getattr(config_obj, "GLPI_USER_TOKEN", None)
        
        # Logger setup
        self.logger = logging.getLogger("glpi_auth")
        try:
            self.structured_logger = create_glpi_logger(getattr(config_obj, "LOG_LEVEL", "INFO"))
        except Exception as e:
            self.structured_logger = None
            logging.warning(f"Failed to create structured_logger: {e}")
        
        # Session management
        self.session_token = None
        self.token_created_at = None
        self.token_expires_at = None
        self.session_timeout = 3600  # 1 hour
        self.max_retries = 3
        self.retry_delay_base = 2
        
    def _normalize_glpi_url(self, url: str) -> str:
        """Normalize GLPI URL ensuring it ends with /apirest.php."""
        if not url or not isinstance(url, str):
            return url
            
        url = url.rstrip('/')
        
        # Ensure URL ends with /apirest.php
        if not url.endswith('/apirest.php'):
            if url.endswith('/apirest'):
                url += '.php'
            else:
                url += '/apirest.php'
        
        return url
        
    def _is_token_expired(self) -> bool:
        """Check if current session token is expired."""
        if not self.session_token or not self.token_created_at:
            return True
            
        if self.token_expires_at:
            return datetime.now() >= self.token_expires_at
            
        elapsed = (datetime.now() - self.token_created_at).total_seconds()
        return elapsed >= self.session_timeout
        
    def _ensure_authenticated(self) -> bool:
        """Ensure we have a valid authenticated session."""
        if self.dev_mode and (not self.app_token or not self.user_token):
            self.logger.warning("Development mode - GLPI not configured")
            return False
            
        if not self._is_token_expired():
            return True
            
        return self.authenticate()
        
    def authenticate(self) -> bool:
        """Authenticate with GLPI and store session token with retry logic and detailed logging."""
        self.logger.info(f"[AUTH] Starting authentication process - URL: {self.glpi_url}")
        
        for attempt in range(self.max_retries):
            try:
                self.logger.info(f"[AUTH] Authentication attempt {attempt + 1}/{self.max_retries}")
                
                # Log current session state
                self.logger.debug(f"[AUTH] Current session token: {'***' if self.session_token else 'None'}")
                self.logger.debug(f"[AUTH] Current authenticated state: {not self._is_token_expired()}")
                
                success = self._perform_authentication()
                if success:
                    self.logger.info(f"[AUTH] Authentication successful on attempt {attempt + 1}")
                    self.logger.debug(f"[AUTH] New session token obtained: {'***' if self.session_token else 'None'}")
                    return True
                else:
                    self.logger.warning(f"[AUTH] Authentication failed on attempt {attempt + 1} - no exception thrown")
                    
            except requests.exceptions.ConnectionError as e:
                self.logger.error(f"[AUTH] Connection error on attempt {attempt + 1}: {e}")
            except requests.exceptions.Timeout as e:
                self.logger.error(f"[AUTH] Timeout error on attempt {attempt + 1}: {e}")
            except requests.exceptions.HTTPError as e:
                self.logger.error(f"[AUTH] HTTP error on attempt {attempt + 1}: {e}")
            except Exception as e:
                self.logger.error(f"[AUTH] Unexpected error on attempt {attempt + 1}: {e}")
                
            if attempt < self.max_retries - 1:
                delay = self.retry_delay_base ** attempt
                self.logger.info(f"[AUTH] Waiting {delay} seconds before retry...")
                time.sleep(delay)
        
        self.logger.error(f"[AUTH] All {self.max_retries} authentication attempts failed")
        self.session_token = None
        self.token_created_at = None
        self.token_expires_at = None
        return False
        
    def _authenticate_with_retry(self) -> bool:
        """Authenticate with exponential backoff retry."""
        for attempt in range(self.max_retries):
            try:
                if self._perform_authentication():
                    return True
                    
            except Exception as e:
                self.logger.error(f"Authentication attempt {attempt + 1} failed: {e}")
                
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay_base ** attempt
                    self.logger.info(f"Retrying authentication in {delay} seconds...")
                    time.sleep(delay)
                    
        self.logger.error("All authentication attempts failed")
        return False
        
    def _perform_authentication(self) -> bool:
        """Perform the actual authentication request."""
        # Construct the proper API URL
        url = f"{self.glpi_url}/initSession"
        headers = {
            "Content-Type": "application/json",
            "App-Token": self.app_token,
            "Authorization": f"user_token {self.user_token}",
        }
        
        try:
            start_time = time.time()
            
            response = requests.post(url, headers=headers, timeout=30)
            response_time = time.time() - start_time
            
            if self.structured_logger:
                log_glpi_request(
                    url,
                    response.status_code,
                    response_time
                )
            
            if response.status_code == 200:
                data = response.json()
                self.session_token = data.get("session_token")
                self.token_created_at = datetime.now()
                self.token_expires_at = None  # GLPI manages expiration
                
                self.logger.info(f"Authentication successful in {response_time:.2f}s")
                return True
            else:
                self.logger.error(f"Authentication failed: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Authentication request failed: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected authentication error: {e}")
            return False
            
    def get_api_headers(self) -> Optional[Dict[str, str]]:
        """Get headers for authenticated API requests."""
        if not self._ensure_authenticated():
            return None
            
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "App-Token": self.app_token,
            "Session-Token": self.session_token,
        }
        
    def is_authenticated(self) -> bool:
        """Check if currently authenticated."""
        return not self._is_token_expired()
        
    def logout(self) -> bool:
        """Logout and invalidate session."""
        if not self.session_token:
            return True
            
        try:
            # Remove /apirest.php if already present in glpi_url to avoid duplication
            base_url = self.glpi_url.rstrip('/apirest.php')
            url = f"{base_url}/apirest.php/killSession"
            headers = self.get_api_headers()
            
            if headers:
                response = requests.delete(url, headers=headers, timeout=30)
                
            # Always reset local session state
            self.session_token = None
            self.token_created_at = None
            self.token_expires_at = None
            
            self.logger.info("Session logged out successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Logout error: {e}")
            # Reset session state even on error
            self.session_token = None
            self.token_created_at = None
            self.token_expires_at = None
            return False