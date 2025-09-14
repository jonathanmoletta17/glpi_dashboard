# -*- coding: utf-8 -*-
"""
Metrics Facade

Orchestrates all metrics operations using Clean Architecture patterns.
Provides sync wrappers for Flask while using async core internally.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from ...application.contracts.metrics_contracts import UnifiedGLPIServiceContract
from ...application.dto.metrics_dto import MetricsFilterDTO
from ...application.queries.metrics_query import MetricsQueryFactory, QueryContext, MetricsDataSource
from ...infrastructure.cache.unified_cache import unified_cache
from ...infrastructure.external.glpi.metrics_adapter import GLPIMetricsAdapter, GLPIConfig
from config.settings import active_config, Config
from utils.mock_data_generator import (
    get_mock_dashboard_metrics,
    get_mock_technician_ranking,
    get_mock_new_tickets,
    get_mock_system_status,
)

# Import schema models
from schemas.dashboard import DashboardMetrics, TechnicianRanking, NewTicket, ApiResponse, TicketStatus, TechnicianLevel


class MetricsFacade(UnifiedGLPIServiceContract):
    """
    Facade that orchestrates metrics operations using Clean Architecture.

    Provides the same interface as legacy GLPIService while using
    async adapters and queries internally.
    """

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # Load configuration
        config = active_config()
        self.use_mock_data = config.USE_MOCK_DATA

        # Create GLPI adapter and query factory
        self.glpi_config = GLPIConfig(
            base_url=config.GLPI_URL,
            app_token=config.GLPI_APP_TOKEN,
            user_token=config.GLPI_USER_TOKEN,
            timeout=getattr(config, "API_TIMEOUT", 30),
        )

        # Import GLPIMetricsAdapter directly instead of using factory
        from ...infrastructure.external.glpi.metrics_adapter import GLPIMetricsAdapter

        self.glpi_adapter = GLPIMetricsAdapter(self.glpi_config)

        self.query_factory = MetricsQueryFactory(self.glpi_adapter)

        # Cache namespaces
        self.METRICS_CACHE_NS = "metrics"
        self.TECHNICIANS_CACHE_NS = "technicians"
        self.TICKETS_CACHE_NS = "tickets"
        self.SYSTEM_CACHE_NS = "system"

    def _run_async(self, coro):
        """Run async coroutine in sync context."""
        try:
            # Try to get existing event loop
            loop = asyncio.get_running_loop()
            # If we're already in an async context, we need to run in a new thread
            import concurrent.futures
            import threading

            def run_in_new_loop():
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    return new_loop.run_until_complete(coro)
                finally:
                    new_loop.close()

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(run_in_new_loop)
                return future.result()

        except RuntimeError:
            # No event loop running, we can run directly
            return asyncio.run(coro)

    def _create_filters_dto(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        category: Optional[str] = None,
        technician: Optional[str] = None,
        entity_id: Optional[int] = None,
        level: Optional[str] = None,
        modification_date: bool = False,
    ) -> MetricsFilterDTO:
        """Create MetricsFilterDTO from parameters."""

        # Convert dates to datetime objects if provided
        start_datetime = None
        end_datetime = None

        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            except ValueError:
                self.logger.warning(f"Invalid start_date format: {start_date}")

        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            except ValueError:
                self.logger.warning(f"Invalid end_date format: {end_date}")

        # Convert string values to proper enum types
        status_enum = None
        if status:
            try:
                status_enum = TicketStatus(status.lower())
            except ValueError:
                self.logger.warning(f"Invalid status: {status}")

        level_enum = None
        if level:
            try:
                level_enum = TechnicianLevel(level.upper())
            except ValueError:
                self.logger.warning(f"Invalid level: {level}")

        # Convert priority string to int
        priority_int = None
        if priority and priority.isdigit():
            priority_int = int(priority)

        return MetricsFilterDTO(
            start_date=start_datetime,
            end_date=end_datetime,
            status=status_enum,
            priority=priority_int,
            category_id=int(category) if category and category.isdigit() else None,
            technician_id=int(technician) if technician and technician.isdigit() else None,
            level=level_enum,
            service_level=None,
            use_modification_date=modification_date,
            limit=None,
            offset=0,
        )

    # Metrics Service Methods

    def get_dashboard_metrics(self, correlation_id: Optional[str] = None) -> DashboardMetrics:
        """
        Obtém métricas do dashboard com fallback explícito para dados mock.
        
        Melhorias implementadas:
        - Tratamento de erros mais específico
        - Fallback explícito para dados mock
        - Logs mais detalhados
        - Sistema de retry básico
        """
        # Verificar se deve usar dados mock diretamente
        if self.use_mock_data:
            self.logger.info("Usando dados mock (configuração USE_MOCK_DATA=true)")
            return get_mock_dashboard_metrics()
        
        # Verificar cache primeiro
        cache_key = f"dashboard_metrics_{correlation_id or 'default'}"
        cached_result = unified_cache.get(self.METRICS_CACHE_NS, cache_key)
        if cached_result:
            self.logger.info("Retornando métricas do cache")
            return cached_result

        async def _get_metrics():
            query = self.query_factory.create_dashboard_metrics_query()
            context = QueryContext(correlation_id=correlation_id)
            return await query.execute(context=context)

        # Tentar obter dados do GLPI com tratamento de erro melhorado
        max_retries = 2
        for attempt in range(max_retries + 1):
            try:
                api_response = self._run_async(_get_metrics())

                # Verificar se a resposta é válida
                if hasattr(api_response, "data") and api_response.data:
                    result = api_response.data
                    # Cache do resultado
                    unified_cache.set(self.METRICS_CACHE_NS, cache_key, result, ttl_seconds=180)
                    self.logger.info("Métricas obtidas do GLPI com sucesso")
                    return result
                else:
                    self.logger.warning("Resposta GLPI vazia ou inválida")
                    break  # Não retry para resposta vazia

            except Exception as e:
                error_msg = str(e).lower()
                
                # Identificar tipo de erro
                if any(auth_error in error_msg for auth_error in [
                    'session_token_missing', 'unauthorized', 'authentication', 'token'
                ]):
                    self.logger.error(f"Erro de autenticação GLPI (tentativa {attempt + 1}): {e}")
                    if attempt == 0:
                        self.logger.warning("Verifique as credenciais GLPI (GLPI_APP_TOKEN, GLPI_USER_TOKEN)")
                    
                elif any(conn_error in error_msg for conn_error in [
                    'connection', 'timeout', 'network', 'unreachable'
                ]):
                    self.logger.error(f"Erro de conexão GLPI (tentativa {attempt + 1}): {e}")
                    if attempt == 0:
                        self.logger.warning("Verifique a conectividade com o servidor GLPI")
                    
                else:
                    self.logger.error(f"Erro desconhecido GLPI (tentativa {attempt + 1}): {e}")
                
                # Se é a última tentativa, fazer fallback
                if attempt == max_retries:
                    self.logger.error(f"Todas as {max_retries + 1} tentativas falharam, fazendo fallback para dados mock")
                    return get_mock_dashboard_metrics()
                
                # Aguardar antes da próxima tentativa
                import time
                time.sleep(1 * (attempt + 1))  # Backoff simples
        
        # Fallback final para dados mock
        self.logger.warning("Fazendo fallback para dados mock devido a falhas no GLPI")
        return get_mock_dashboard_metrics()

    def get_dashboard_metrics_with_date_filter(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> DashboardMetrics:
        """Get dashboard metrics with date filter."""
        cache_key = {
            "method": "dashboard_metrics_date_filter",
            "start_date": start_date,
            "end_date": end_date,
            "correlation_id": correlation_id,
        }

        cached_result = unified_cache.get(self.METRICS_CACHE_NS, cache_key)
        if cached_result:
            return cached_result

        async def _get_metrics():
            filters = self._create_filters_dto(start_date=start_date, end_date=end_date)
            query = self.query_factory.create_dashboard_metrics_query()
            context = QueryContext(correlation_id=correlation_id)
            return await query.execute(filters=filters, context=context)

        try:
            api_response = self._run_async(_get_metrics())

            # Extract DashboardMetrics from ApiResponse
            if hasattr(api_response, "data") and api_response.data:
                result = api_response.data
                unified_cache.set(self.METRICS_CACHE_NS, cache_key, result, ttl_seconds=180)
                return result
            else:
                from ..dto.metrics_dto import create_empty_dashboard_metrics

                return create_empty_dashboard_metrics()

        except Exception as e:
            self.logger.error(f"Error getting dashboard metrics with date filter: {e}")
            from ..dto.metrics_dto import create_empty_dashboard_metrics

            return create_empty_dashboard_metrics()

    def get_dashboard_metrics_with_modification_date_filter(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> DashboardMetrics:
        """Get dashboard metrics with modification date filter."""
        cache_key = {
            "method": "dashboard_metrics_mod_date_filter",
            "start_date": start_date,
            "end_date": end_date,
            "correlation_id": correlation_id,
        }

        cached_result = unified_cache.get(self.METRICS_CACHE_NS, cache_key)
        if cached_result:
            return cached_result

        async def _get_metrics():
            filters = self._create_filters_dto(start_date=start_date, end_date=end_date, modification_date=True)
            query = self.query_factory.create_dashboard_metrics_query()
            context = QueryContext(correlation_id=correlation_id)
            return await query.execute(filters=filters, context=context)

        try:
            api_response = self._run_async(_get_metrics())

            # Extract DashboardMetrics from ApiResponse
            if hasattr(api_response, "data") and api_response.data:
                result = api_response.data
                unified_cache.set(self.METRICS_CACHE_NS, cache_key, result, ttl_seconds=180)
                return result
            else:
                from ..dto.metrics_dto import create_empty_dashboard_metrics

                return create_empty_dashboard_metrics()

        except Exception as e:
            self.logger.error(f"Error getting dashboard metrics with modification date filter: {e}")
            from ..dto.metrics_dto import create_empty_dashboard_metrics

            return create_empty_dashboard_metrics()

    def get_dashboard_metrics_with_filters(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        category: Optional[str] = None,
        technician: Optional[str] = None,
        entity_id: Optional[int] = None,
        correlation_id: Optional[str] = None,
    ) -> DashboardMetrics:
        """Get dashboard metrics with multiple filters."""
        cache_key = {
            "method": "dashboard_metrics_filters",
            "start_date": start_date,
            "end_date": end_date,
            "status": status,
            "priority": priority,
            "category": category,
            "technician": technician,
            "entity_id": entity_id,
            "correlation_id": correlation_id,
        }

        cached_result = unified_cache.get(self.METRICS_CACHE_NS, cache_key)
        if cached_result:
            return cached_result

        async def _get_metrics():
            filters = self._create_filters_dto(
                start_date=start_date,
                end_date=end_date,
                status=status,
                priority=priority,
                category=category,
                technician=technician,
                entity_id=entity_id,
            )
            query = self.query_factory.create_dashboard_metrics_query()
            context = QueryContext(correlation_id=correlation_id)
            return await query.execute(filters=filters, context=context)

        try:
            api_response = self._run_async(_get_metrics())

            # Extract DashboardMetrics from ApiResponse
            if hasattr(api_response, "data") and api_response.data:
                result = api_response.data
                unified_cache.set(self.METRICS_CACHE_NS, cache_key, result, ttl_seconds=180)
                return result
            else:
                from ..dto.metrics_dto import create_empty_dashboard_metrics

                return create_empty_dashboard_metrics()

        except Exception as e:
            self.logger.error(f"Error getting dashboard metrics with filters: {e}")
            from ..dto.metrics_dto import create_empty_dashboard_metrics

            return create_empty_dashboard_metrics()

    # Technician Service Methods

    def get_all_technician_ids_and_names(self, entity_id: Optional[int] = None) -> Tuple[List[int], List[str]]:
        """Get all technician IDs and names."""
        if self.use_mock_data:
            # Return mock data for testing
            ranking = get_mock_technician_ranking()
            ids = [1, 2]  # Mock IDs
            names = ["Tech 1", "Tech 2"]  # Mock names
            return ids, names
            
        cache_key = {"method": "all_technicians", "entity_id": entity_id}

        cached_result = unified_cache.get(self.TECHNICIANS_CACHE_NS, cache_key)
        if cached_result:
            return cached_result

        async def _get_technicians():
            # Use the technician hierarchy to get all technicians
            hierarchy = await self.glpi_adapter.get_technician_hierarchy()

            # Extract IDs and names from hierarchy
            ids = list(hierarchy.keys())
            names = list(hierarchy.values())

            return ids, names

        try:
            result = self._run_async(_get_technicians())
            unified_cache.set(self.TECHNICIANS_CACHE_NS, cache_key, result, ttl_seconds=600)
            return result

        except Exception as e:
            self.logger.error(f"Error getting technician IDs and names: {e}")
            return [], []

    def get_technician_ranking(self, limit: int = 50) -> List[TechnicianRanking]:
        """Get technician ranking."""
        if self.use_mock_data:
            self.logger.info("Using mock data for technician ranking")
            return get_mock_technician_ranking(limit=limit)

        cache_key = {"method": "technician_ranking", "limit": limit}

        cached_result = unified_cache.get(self.TECHNICIANS_CACHE_NS, cache_key)
        if cached_result:
            return cached_result

        async def _get_ranking():
            query = self.query_factory.create_technician_ranking_query()
            context = QueryContext(correlation_id=None)
            return await query.execute(context=context)

        try:
            api_response = self._run_async(_get_ranking())

            # Extract List[TechnicianRanking] from ApiResponse
            if hasattr(api_response, "data") and api_response.data:
                result = api_response.data
                unified_cache.set(self.TECHNICIANS_CACHE_NS, cache_key, result, ttl_seconds=300)
                return result
            else:
                return []

        except Exception as e:
            self.logger.error(f"Error getting technician ranking: {e}")
            return []

    def get_technician_ranking_with_filters(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        level: Optional[str] = None,
        limit: int = 50,
        entity_id: Optional[int] = None,
        correlation_id: Optional[str] = None,
    ) -> List[TechnicianRanking]:
        """Get technician ranking with filters."""
        cache_key = {
            "method": "technician_ranking_filters",
            "start_date": start_date,
            "end_date": end_date,
            "level": level,
            "limit": limit,
            "entity_id": entity_id,
            "correlation_id": correlation_id,
        }

        cached_result = unified_cache.get(self.TECHNICIANS_CACHE_NS, cache_key)
        if cached_result:
            return cached_result

        async def _get_ranking():
            filters = self._create_filters_dto(start_date=start_date, end_date=end_date, level=level, entity_id=entity_id)
            query = self.query_factory.create_technician_ranking_query()
            context = QueryContext(correlation_id=correlation_id)
            return await query.execute(filters=filters, context=context)

        try:
            api_response = self._run_async(_get_ranking())

            # Extract List[TechnicianRanking] from ApiResponse
            if hasattr(api_response, "data") and api_response.data:
                result = api_response.data
                unified_cache.set(self.TECHNICIANS_CACHE_NS, cache_key, result, ttl_seconds=300)
                return result
            else:
                return []

        except Exception as e:
            self.logger.error(f"Error getting technician ranking with filters: {e}")
            return []

    # Ticket Service Methods (Simplified implementations)

    def get_new_tickets(self, limit: int = 20) -> List[NewTicket]:
        """Get new tickets."""
        if self.use_mock_data:
            return get_mock_new_tickets(limit=limit)
        # For now, return basic structure - can be expanded later
        return []

    def get_new_tickets_with_filters(
        self,
        limit: int = 20,
        priority: Optional[str] = None,
        category: Optional[str] = None,
        technician: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[NewTicket]:
        """Get new tickets with filters."""
        # For now, return basic structure - can be expanded later
        return []

    # System Service Methods (Simplified implementations)

    def get_system_status(self) -> ApiResponse:
        """Get system status."""
        if self.use_mock_data:
            return get_mock_system_status()
            
        cache_key = {"method": "system_status"}

        cached_result = unified_cache.get(self.SYSTEM_CACHE_NS, cache_key)
        if cached_result:
            return cached_result

        # For now, return basic structure - can be expanded later
        from ..dto.metrics_dto import create_success_response

        status_data = {"status": "online", "message": "Sistema operacional"}
        result = create_success_response(status_data, message="Sistema operacional")
        unified_cache.set(self.SYSTEM_CACHE_NS, cache_key, result, ttl_seconds=60)
        return result

    def authenticate_with_retry(self) -> bool:
        """Authenticate with retry."""
        # This would use the session manager from GLPI adapter
        return True


# Global facade instance
metrics_facade = MetricsFacade()
