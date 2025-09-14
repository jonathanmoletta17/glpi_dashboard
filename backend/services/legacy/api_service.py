import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests

from config.settings import active_config
from services.legacy.glpi_service_facade import GLPIServiceFacade
from utils.response_formatter import ResponseFormatter


class APIService:
    """Service to handle external API communications"""

    def __init__(self):
        config_obj = active_config()
        self.base_url = config_obj.BACKEND_API_URL
        self.api_key = config_obj.API_KEY
        self.timeout = config_obj.API_TIMEOUT
        self.logger = logging.getLogger("services")

        # Initialize GLPI service using decomposed facade
        self.glpi_service = GLPIServiceFacade()

        # Default headers for API requests
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "TechDept-Dashboard/1.0",
        }

        if self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}"

    def _make_request(self, endpoint: str, method: str = "GET", data: Dict = None) -> Dict:
        """Make HTTP request to external API"""
        url = f"{self.base_url}{endpoint}"

        try:
            if method == "GET":
                response = requests.get(url, headers=self.headers, timeout=self.timeout)
            elif method == "POST":
                response = requests.post(url, json=data, headers=self.headers, timeout=self.timeout)

            response.raise_for_status()
            return response.json()

        except requests.exceptions.Timeout:
            self.logger.error(f"Timeout error for {url}")
            raise Exception("Timeout na conexão com a API")
        except requests.exceptions.ConnectionError:
            self.logger.error(f"Connection error for {url}")
            raise Exception("Erro de conexão com a API")
        except requests.exceptions.HTTPError as e:
            self.logger.error(f"HTTP error {e.response.status_code} for {url}")
            raise Exception(f"Erro HTTP {e.response.status_code}")
        except Exception as e:
            self.logger.error(f"Unexpected error for {url}: {str(e)}")
            raise Exception("Erro inesperado na API")

    def get_metrics(self) -> Dict:
        """Get dashboard metrics from external API"""
        try:
            return self._make_request("/api/metrics")
        except Exception as e:
            # Return empty state with error indication
            logging.warning(f"Could not fetch metrics: {str(e)}")
            return {
                "error": True,
                "message": str(e),
                "data": {
                    "cpu_usage": {"value": 0, "status": "error"},
                    "memory_usage": {"value": 0, "status": "error"},
                    "disk_usage": {"value": 0, "status": "error"},
                    "network_status": {"status": "error"},
                    "active_users": {"count": 0, "status": "error"},
                    "system_uptime": {"value": 0, "status": "error"},
                },
            }

    def get_system_status(self) -> Dict:
        """Get current system status"""
        try:
            return self._make_request("/api/system/status")
        except Exception as e:
            logging.warning(f"Could not fetch system status: {str(e)}")
            return {
                "error": True,
                "message": str(e),
                "status": "offline",
                "last_update": datetime.now().isoformat(),
            }

    def search(self, query: str) -> List[Dict]:
        """Search functionality"""
        try:
            return self._make_request(f"/api/search?q={query}")
        except Exception as e:
            logging.warning(f"Search failed: {str(e)}")
            return {"error": True, "message": str(e), "results": []}

    def get_chart_data(self, chart_type: str) -> Dict:
        """Get data for specific chart types"""
        try:
            return self._make_request(f"/api/charts/{chart_type}")
        except Exception as e:
            logging.warning(f"Could not fetch chart data for {chart_type}: {str(e)}")
            return {
                "error": True,
                "message": str(e),
                "data": {"labels": [], "datasets": []},
            }

    def get_alerts(self) -> List[Dict]:
        """Get system alerts"""
        try:
            return self._make_request("/api/alerts")
        except Exception as e:
            logging.warning(f"Could not fetch alerts: {str(e)}")
            return {"error": True, "message": str(e), "alerts": []}

    def get_dashboard_metrics(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> Dict:
        """Get dashboard metrics from GLPI service"""
        try:
            if start_date and end_date:
                level_metrics = self.glpi_service.get_metrics_by_level(start_date, end_date, correlation_id=correlation_id)
                general_metrics = self.glpi_service.get_general_metrics(start_date, end_date, correlation_id=correlation_id)
            else:
                level_metrics = self.glpi_service.get_metrics_by_level(correlation_id=correlation_id)
                general_metrics = self.glpi_service.get_general_metrics(correlation_id=correlation_id)

            return {"level_metrics": level_metrics, "general_metrics": general_metrics}
        except Exception as e:
            self.logger.error(f"Error getting dashboard metrics: {str(e)}")
            return None

    def format_response(self, data: Any) -> Dict:
        """Format successful response"""
        return ResponseFormatter.success(data)

    def format_error_response(self, message: str) -> Dict:
        """Format error response"""
        return ResponseFormatter.error(message)

    def validate_date_format(self, date_str: str) -> bool:
        """Validate date format (YYYY-MM-DD)"""
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except ValueError:
            return False

    def validate_date_range(self, start_date: str, end_date: str) -> bool:
        """Validate date range (start_date <= end_date)"""
        try:
            if not self.validate_date_format(start_date) or not self.validate_date_format(end_date):
                return False

            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
            return start <= end
        except ValueError:
            return False

    def get_trends_data(self, start_date: str, end_date: str) -> List[Dict]:
        """Get trends data from GLPI service"""
        try:
            return self.glpi_service.get_historical_metrics(start_date, end_date)
        except Exception as e:
            self.logger.error(f"Error getting trends data: {str(e)}")
            return []

    def get_performance_metrics(self) -> Dict:
        """Get performance metrics"""
        import time

        try:
            response_time = self._calculate_response_time()
            return {"response_time": response_time, "timestamp": time.time()}
        except Exception as e:
            self.logger.error(f"Error getting performance metrics: {str(e)}")
            return {"response_time": 0, "timestamp": time.time()}

    def _calculate_response_time(self) -> float:
        """Calculate response time for performance metrics"""
        import time

        start_time = time.time()
        # Simulate some processing
        time.sleep(0.001)
        return (time.time() - start_time) * 1000  # Return in milliseconds
