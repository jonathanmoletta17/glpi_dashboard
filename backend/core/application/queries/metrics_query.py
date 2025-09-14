# -*- coding: utf-8 -*-
"""
Metrics Query - Consultas autocontidas para métricas do GLPI.

Este módulo implementa o padrão Query Object para isolar a lógica de consulta
de métricas, fornecendo uma interface limpa e testável para obtenção de dados.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

from ..dto.metrics_dto import (
    MetricsFilterDTO,
    create_empty_dashboard_metrics,
    create_error_response,
    create_success_response,
)

# Import consolidated models from schemas (API boundary types)
from schemas.dashboard import (
    DashboardMetrics,
    TechnicianRanking,
    NewTicket,
    LevelMetrics,
    ApiResponse,
    ApiError,
    TicketStatus,
    TechnicianLevel,
)

logger = logging.getLogger(__name__)


class QueryExecutionError(Exception):
    """Exceção para erros de execução de query."""

    pass


class DataValidationError(Exception):
    """Exceção para erros de validação de dados."""

    pass


@dataclass
class QueryContext:
    """Contexto de execução de uma query."""

    correlation_id: Optional[str] = None
    user_id: Optional[int] = None
    start_time: Optional[datetime] = None
    timeout_seconds: int = 30
    cache_enabled: bool = True
    cache_ttl_seconds: int = 300

    def __post_init__(self):
        if self.start_time is None:
            self.start_time = datetime.now()


class MetricsDataSource(ABC):
    """Interface abstrata para fonte de dados de métricas."""

    @abstractmethod
    async def get_ticket_count_by_hierarchy(
        self,
        filters: Optional[MetricsFilterDTO] = None,
        context: Optional[QueryContext] = None,
    ) -> Dict[str, Any]:
        """Obtém contagem de tickets por hierarquia."""
        pass

    @abstractmethod
    async def get_technician_metrics(
        self,
        technician_id: Optional[int] = None,
        filters: Optional[MetricsFilterDTO] = None,
        context: Optional[QueryContext] = None,
    ) -> List[Dict[str, Any]]:
        """Obtém métricas de técnicos."""
        pass

    @abstractmethod
    async def get_ticket_metrics(
        self,
        filters: Optional[MetricsFilterDTO] = None,
        context: Optional[QueryContext] = None,
    ) -> Dict[str, Any]:
        """Obtém métricas de tickets."""
        pass

    @abstractmethod
    async def get_technician_hierarchy(self, context: Optional[QueryContext] = None) -> Dict[int, str]:
        """Obtém mapeamento de técnico para nível hierárquico."""
        pass

    @abstractmethod
    async def get_new_tickets(
        self,
        filters: Optional[MetricsFilterDTO] = None,
        context: Optional[QueryContext] = None,
    ) -> List[Dict[str, Any]]:
        """Obtém tickets novos/recentes."""
        pass

    @abstractmethod
    async def get_system_status(self, context: Optional[QueryContext] = None) -> Dict[str, Any]:
        """Obtém status do sistema GLPI."""
        pass

    @abstractmethod
    async def discover_field_ids(self, context: Optional[QueryContext] = None) -> Dict[str, int]:
        """Descobre IDs dos campos GLPI."""
        pass


class BaseMetricsQuery(ABC):
    """Classe base para queries de métricas."""

    def __init__(self, data_source: MetricsDataSource):
        self.data_source = data_source
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def _log_query_start(self, query_name: str, context: QueryContext) -> None:
        """Log do início da execução da query."""
        self.logger.info(
            f"Starting query: {query_name}",
            extra={
                "correlation_id": context.correlation_id,
                "query_name": query_name,
                "user_id": context.user_id,
                "start_time": context.start_time.isoformat() if context.start_time else None,
            },
        )

    def _log_query_end(
        self,
        query_name: str,
        context: QueryContext,
        success: bool = True,
        error: Optional[str] = None,
    ) -> None:
        """Log do fim da execução da query."""
        execution_time = None
        if context.start_time:
            execution_time = (datetime.now() - context.start_time).total_seconds() * 1000

        log_data = {
            "correlation_id": context.correlation_id,
            "query_name": query_name,
            "success": success,
            "execution_time_ms": execution_time,
        }

        if error:
            log_data["error"] = error

        if success:
            self.logger.info(f"Query completed: {query_name}", extra=log_data)
        else:
            self.logger.error(f"Query failed: {query_name}", extra=log_data)

    def _validate_filters(self, filters: Optional[MetricsFilterDTO]) -> None:
        """Valida filtros de entrada."""
        if filters is None:
            return

        # Validação de datas
        if filters.start_date and filters.end_date:
            if filters.start_date >= filters.end_date:
                raise DataValidationError("start_date deve ser anterior a end_date")

        # Validação de período máximo (1 ano)
        if filters.start_date and filters.end_date:
            max_period = timedelta(days=365)
            if (filters.end_date - filters.start_date) > max_period:
                raise DataValidationError("Período máximo permitido é de 1 ano")

        # Validação de limite
        if filters.limit and filters.limit > 10000:
            raise DataValidationError("Limite máximo permitido é 10000")

    @abstractmethod
    async def execute(
        self,
        filters: Optional[MetricsFilterDTO] = None,
        context: Optional[QueryContext] = None,
    ) -> ApiResponse:
        """Executa a query e retorna o resultado."""
        pass


class GeneralMetricsQuery(BaseMetricsQuery):
    """Query para métricas gerais do dashboard."""

    async def execute(
        self,
        filters: Optional[MetricsFilterDTO] = None,
        context: Optional[QueryContext] = None,
    ) -> ApiResponse:
        """Executa query para métricas gerais."""
        if context is None:
            context = QueryContext()

        query_name = "general_metrics"
        self._log_query_start(query_name, context)

        try:
            # Validar filtros
            self._validate_filters(filters)

            # Obter dados básicos
            ticket_data = await self.data_source.get_ticket_count_by_hierarchy(filters=filters, context=context)

            technician_hierarchy = await self.data_source.get_technician_hierarchy(context=context)

            # Processar dados
            metrics_dto = await self._process_general_metrics(ticket_data, technician_hierarchy, filters)

            self._log_query_end(query_name, context, success=True)

            response = create_success_response(
                data=metrics_dto,
                correlation_id=context.correlation_id,
                message="Métricas gerais obtidas com sucesso",
            )
            response.set_execution_time(context.start_time)

            return response

        except Exception as e:
            error_msg = f"Erro ao obter métricas gerais: {str(e)}"
            self._log_query_end(query_name, context, success=False, error=error_msg)

            return create_error_response(error_message=error_msg, correlation_id=context.correlation_id)

    async def _process_general_metrics(
        self,
        ticket_data: Dict[str, Any],
        technician_hierarchy: Dict[int, str],
        filters: Optional[MetricsFilterDTO],
    ) -> DashboardMetrics:
        """Processa dados brutos em DTO de métricas."""

        # Inicializar DTO vazio
        metrics = create_empty_dashboard_metrics()

        # Processar dados por nível
        level_data = ticket_data.get("levels", {})

        total_tickets = 0
        total_technicians = len(technician_hierarchy)

        for level_name, level_info in level_data.items():
            if level_name not in ["N1", "N2", "N3", "N4"]:
                continue

            # Contar técnicos por nível
            technicians_in_level = sum(1 for tech_level in technician_hierarchy.values() if tech_level == level_name)

            # Criar métricas de tickets para o nível
            level_metrics = LevelMetrics(
                total=level_info.get("total", 0),
                novos=level_info.get("new", 0),
                pendentes=level_info.get("pending", 0),
                progresso=level_info.get("in_progress", 0),
                resolvidos=level_info.get("resolved", 0),
            )

            # Atribuir às métricas por nível
            if level_name == "N1":
                metrics.niveis.n1 = level_metrics
            elif level_name == "N2":
                metrics.niveis.n2 = level_metrics
            elif level_name == "N3":
                metrics.niveis.n3 = level_metrics
            elif level_name == "N4":
                metrics.niveis.n4 = level_metrics

            total_tickets += level_metrics.total

        # Atualizar totais gerais
        metrics.total = total_tickets
        metrics.novos = sum(level.novos for level in metrics.niveis.values())
        metrics.pendentes = sum(level.pendentes for level in metrics.niveis.values())
        metrics.progresso = sum(level.progresso for level in metrics.niveis.values())
        metrics.resolvidos = sum(level.resolvidos for level in metrics.niveis.values())

        # Definir período se filtros foram aplicados
        if filters:
            metrics.period_start = filters.start_date
            metrics.period_end = filters.end_date

        return metrics


class TechnicianRankingQuery(BaseMetricsQuery):
    """Query para ranking de técnicos."""

    async def execute(
        self,
        filters: Optional[MetricsFilterDTO] = None,
        context: Optional[QueryContext] = None,
    ) -> ApiResponse:
        """Executa query para ranking de técnicos."""
        if context is None:
            context = QueryContext()

        query_name = "technician_ranking"
        self._log_query_start(query_name, context)

        try:
            # Validar filtros
            self._validate_filters(filters)

            # Obter dados de técnicos
            technician_data = await self.data_source.get_technician_metrics(filters=filters, context=context)

            technician_hierarchy = await self.data_source.get_technician_hierarchy(context=context)

            # Processar ranking
            ranking = await self._process_technician_ranking(technician_data, technician_hierarchy, filters)

            self._log_query_end(query_name, context, success=True)

            response = create_success_response(
                data=ranking,
                correlation_id=context.correlation_id,
                message="Ranking de técnicos obtido com sucesso",
            )
            response.set_execution_time(context.start_time)

            return response

        except Exception as e:
            error_msg = f"Erro ao obter ranking de técnicos: {str(e)}"
            self._log_query_end(query_name, context, success=False, error=error_msg)

            return create_error_response(error_message=error_msg, correlation_id=context.correlation_id)

    async def _process_technician_ranking(
        self,
        technician_data: List[Dict[str, Any]],
        technician_hierarchy: Dict[int, str],
        filters: Optional[MetricsFilterDTO],
    ) -> List[TechnicianRanking]:
        """Processa dados de técnicos em ranking."""

        ranking = []

        for idx, tech_data in enumerate(technician_data, 1):
            tech_id = tech_data.get("id")
            # Ensure tech_id is int or use default
            tech_id_int = tech_id if isinstance(tech_id, int) else 0
            tech_level = technician_hierarchy.get(tech_id_int, TechnicianLevel.UNKNOWN.value)

            # Calcular score de eficiência (baseado em tickets resolvidos vs total)
            total_tickets = tech_data.get("total", 0)
            resolvidos = tech_data.get("resolved", 0)
            efficiency_score = None
            if total_tickets > 0:
                efficiency_score = (resolvidos / total_tickets) * 100

            # Criar DTO do técnico usando TechnicianRanking
            technician_dto = TechnicianRanking(
                id=tech_id or 0,
                name=tech_data.get("name", "Desconhecido"),
                ticket_count=total_tickets,
                level=tech_level if tech_level in [l.value for l in TechnicianLevel] else TechnicianLevel.UNKNOWN.value,
                performance_score=efficiency_score,
            )

            ranking.append(technician_dto)

        # Ordenar por total de tickets (descendente)
        ranking.sort(key=lambda x: x.ticket_count, reverse=True)

        # Aplicar limite se especificado
        if filters and filters.limit:
            ranking = ranking[: filters.limit]

        return ranking


class NewTicketsQuery(BaseMetricsQuery):
    """Query para tickets novos/recentes."""

    async def execute(
        self,
        filters: Optional[MetricsFilterDTO] = None,
        context: Optional[QueryContext] = None,
    ) -> ApiResponse:
        """Executa query para tickets novos."""
        if context is None:
            context = QueryContext()

        query_name = "new_tickets"
        self._log_query_start(query_name, context)

        try:
            # Validar filtros
            self._validate_filters(filters)

            # Definir filtros padrão se não especificados
            if filters is None:
                filters = MetricsFilterDTO(
                    start_date=datetime.now() - timedelta(days=7),
                    end_date=datetime.now(),
                    limit=50,
                    status=None,
                    level=None,
                    service_level=None,
                    use_modification_date=False,
                    technician_id=None,
                    category_id=None,
                    priority=None,
                    offset=0,
                )

            # Obter tickets novos
            tickets_data = await self.data_source.get_new_tickets(filters=filters, context=context)

            self._log_query_end(query_name, context, success=True)

            response = create_success_response(
                data=tickets_data,
                correlation_id=context.correlation_id,
                message="Tickets novos obtidos com sucesso",
            )
            response.set_execution_time(context.start_time)

            return response

        except Exception as e:
            error_msg = f"Erro ao obter tickets novos: {str(e)}"
            self._log_query_end(query_name, context, success=False, error=error_msg)

            return create_error_response(error_message=error_msg, correlation_id=context.correlation_id)


class SystemStatusQuery(BaseMetricsQuery):
    """Query para status do sistema GLPI."""

    async def execute(
        self,
        filters: Optional[MetricsFilterDTO] = None,
        context: Optional[QueryContext] = None,
    ) -> ApiResponse:
        """Executa query para status do sistema."""
        if context is None:
            context = QueryContext()

        query_name = "system_status"
        self._log_query_start(query_name, context)

        try:
            # Obter status do sistema
            status_data = await self.data_source.get_system_status(context=context)

            self._log_query_end(query_name, context, success=True)

            response = create_success_response(
                data=status_data,
                correlation_id=context.correlation_id,
                message="Status do sistema obtido com sucesso",
            )
            response.set_execution_time(context.start_time)

            return response

        except Exception as e:
            error_msg = f"Erro ao obter status do sistema: {str(e)}"
            self._log_query_end(query_name, context, success=False, error=error_msg)

            return create_error_response(error_message=error_msg, correlation_id=context.correlation_id)


class FieldDiscoveryQuery(BaseMetricsQuery):
    """Query para descoberta de IDs dos campos GLPI."""

    async def execute(
        self,
        filters: Optional[MetricsFilterDTO] = None,
        context: Optional[QueryContext] = None,
    ) -> ApiResponse:
        """Executa query para descobrir IDs dos campos."""
        if context is None:
            context = QueryContext()

        query_name = "field_discovery"
        self._log_query_start(query_name, context)

        try:
            # Descobrir IDs dos campos
            field_ids = await self.data_source.discover_field_ids(context=context)

            self._log_query_end(query_name, context, success=True)

            response = create_success_response(
                data=field_ids,
                correlation_id=context.correlation_id,
                message="IDs dos campos descobertos com sucesso",
            )
            response.set_execution_time(context.start_time)

            return response

        except Exception as e:
            error_msg = f"Erro ao descobrir IDs dos campos: {str(e)}"
            self._log_query_end(query_name, context, success=False, error=error_msg)

            return create_error_response(error_message=error_msg, correlation_id=context.correlation_id)


class DashboardMetricsQuery(BaseMetricsQuery):
    """Query para métricas completas do dashboard."""

    def __init__(self, data_source: MetricsDataSource):
        super().__init__(data_source)
        self.general_query = GeneralMetricsQuery(data_source)
        self.ranking_query = TechnicianRankingQuery(data_source)

    async def execute(
        self,
        filters: Optional[MetricsFilterDTO] = None,
        context: Optional[QueryContext] = None,
    ) -> ApiResponse:
        """Executa query para métricas completas do dashboard."""
        if context is None:
            context = QueryContext()

        query_name = "dashboard_metrics"
        self._log_query_start(query_name, context)

        try:
            # Validar filtros
            self._validate_filters(filters)

            # Executar queries em paralelo (simulado)
            general_response = await self.general_query.execute(filters, context)
            ranking_response = await self.ranking_query.execute(filters, context)

            # Verificar se ambas foram bem-sucedidas
            if not general_response.success:
                return general_response

            if not ranking_response.success:
                return ranking_response

            # Obter tickets recentes
            recent_tickets = await self._get_recent_tickets(filters, context)

            # Return the dashboard metrics directly
            # Combine the data from both queries into a DashboardMetrics object
            if isinstance(general_response.data, DashboardMetrics):
                dashboard_dto = general_response.data
            else:
                from ..dto.metrics_dto import create_empty_dashboard_metrics

                dashboard_dto = create_empty_dashboard_metrics()

            self._log_query_end(query_name, context, success=True)

            response = create_success_response(
                data=dashboard_dto,
                correlation_id=context.correlation_id,
                message="Métricas do dashboard obtidas com sucesso",
            )
            response.set_execution_time(context.start_time)

            return response

        except Exception as e:
            error_msg = f"Erro ao obter métricas do dashboard: {str(e)}"
            self._log_query_end(query_name, context, success=False, error=error_msg)

            return create_error_response(error_message=error_msg, correlation_id=context.correlation_id)

    async def _get_recent_tickets(self, filters: Optional[MetricsFilterDTO], context: QueryContext) -> List[Dict[str, Any]]:
        """Obtém tickets recentes."""
        try:
            # Criar filtro para tickets recentes (últimos 7 dias)
            recent_filter = MetricsFilterDTO(
                start_date=datetime.now() - timedelta(days=7),
                end_date=datetime.now(),
                status=None,
                level=None,
                service_level=None,
                use_modification_date=False,
                technician_id=None,
                category_id=None,
                priority=None,
                limit=20,
                offset=0,
            )

            # Se já há filtros, combinar com os existentes
            if filters:
                if filters.start_date and recent_filter.start_date and filters.start_date > recent_filter.start_date:
                    recent_filter.start_date = filters.start_date
                if filters.end_date and recent_filter.end_date and filters.end_date < recent_filter.end_date:
                    recent_filter.end_date = filters.end_date

            ticket_data = await self.data_source.get_ticket_metrics(filters=recent_filter, context=context)

            return ticket_data.get("recent_tickets", [])

        except Exception as e:
            self.logger.warning(
                f"Erro ao obter tickets recentes: {str(e)}",
                extra={"correlation_id": context.correlation_id},
            )
            return []


class MetricsQueryFactory:
    """Factory para criação de queries de métricas."""

    def __init__(self, data_source: MetricsDataSource):
        self.data_source = data_source

    def create_general_metrics_query(self) -> GeneralMetricsQuery:
        """Cria query para métricas gerais."""
        return GeneralMetricsQuery(self.data_source)

    def create_technician_ranking_query(self) -> TechnicianRankingQuery:
        """Cria query para ranking de técnicos."""
        return TechnicianRankingQuery(self.data_source)

    def create_dashboard_metrics_query(self) -> DashboardMetricsQuery:
        """Cria query para métricas do dashboard."""
        return DashboardMetricsQuery(self.data_source)

    def create_new_tickets_query(self) -> NewTicketsQuery:
        """Cria query para tickets novos."""
        return NewTicketsQuery(self.data_source)

    def create_system_status_query(self) -> SystemStatusQuery:
        """Cria query para status do sistema."""
        return SystemStatusQuery(self.data_source)

    def create_field_discovery_query(self) -> FieldDiscoveryQuery:
        """Cria query para descoberta de campos."""
        return FieldDiscoveryQuery(self.data_source)

    def create_query_by_type(self, query_type: str) -> BaseMetricsQuery:
        """Cria query baseada no tipo."""
        query_map = {
            "general": self.create_general_metrics_query,
            "ranking": self.create_technician_ranking_query,
            "dashboard": self.create_dashboard_metrics_query,
            "new_tickets": self.create_new_tickets_query,
            "system_status": self.create_system_status_query,
            "field_discovery": self.create_field_discovery_query,
        }

        if query_type not in query_map:
            raise ValueError(f"Tipo de query inválido: {query_type}")

        return query_map[query_type]()


# Utilitários para testes e desenvolvimento


class MockMetricsDataSource(MetricsDataSource):
    """Implementação mock para testes."""

    async def get_ticket_count_by_hierarchy(
        self,
        filters: Optional[MetricsFilterDTO] = None,
        context: Optional[QueryContext] = None,
    ) -> Dict[str, Any]:
        """Mock de dados de tickets por hierarquia."""
        return {
            "levels": {
                "N1": {
                    "total": 150,
                    "new": 20,
                    "pending": 30,
                    "in_progress": 50,
                    "resolved": 40,
                    "closed": 10,
                    "cancelled": 0,
                    "avg_resolution_time": 2.5,
                },
                "N2": {
                    "total": 100,
                    "new": 15,
                    "pending": 20,
                    "in_progress": 35,
                    "resolved": 25,
                    "closed": 5,
                    "cancelled": 0,
                    "avg_resolution_time": 4.2,
                },
                "N3": {
                    "total": 75,
                    "new": 10,
                    "pending": 15,
                    "in_progress": 25,
                    "resolved": 20,
                    "closed": 5,
                    "cancelled": 0,
                    "avg_resolution_time": 6.8,
                },
                "N4": {
                    "total": 50,
                    "new": 5,
                    "pending": 10,
                    "in_progress": 15,
                    "resolved": 15,
                    "closed": 5,
                    "cancelled": 0,
                    "avg_resolution_time": 12.5,
                },
            }
        }

    async def get_technician_metrics(
        self,
        technician_id: Optional[int] = None,
        filters: Optional[MetricsFilterDTO] = None,
        context: Optional[QueryContext] = None,
    ) -> List[Dict[str, Any]]:
        """Mock de dados de técnicos."""
        return [
            {
                "id": 1,
                "name": "João Silva",
                "total": 45,
                "new": 5,
                "pending": 8,
                "in_progress": 12,
                "resolved": 15,
                "closed": 5,
                "cancelled": 0,
                "avg_resolution_time": 2.1,
                "last_activity": datetime.now() - timedelta(hours=2),
            },
            {
                "id": 2,
                "name": "Maria Santos",
                "total": 38,
                "new": 4,
                "pending": 6,
                "in_progress": 10,
                "resolved": 13,
                "closed": 5,
                "cancelled": 0,
                "avg_resolution_time": 2.8,
                "last_activity": datetime.now() - timedelta(hours=1),
            },
        ]

    async def get_ticket_metrics(
        self,
        filters: Optional[MetricsFilterDTO] = None,
        context: Optional[QueryContext] = None,
    ) -> Dict[str, Any]:
        """Mock de métricas de tickets."""
        return {
            "recent_tickets": [
                {
                    "id": 1001,
                    "title": "Problema de rede",
                    "status": "in_progress",
                    "created_at": datetime.now() - timedelta(hours=3),
                    "technician_id": 1,
                },
                {
                    "id": 1002,
                    "title": "Instalação de software",
                    "status": "resolved",
                    "created_at": datetime.now() - timedelta(hours=5),
                    "technician_id": 2,
                },
            ]
        }

    async def get_technician_hierarchy(self, context: Optional[QueryContext] = None) -> Dict[int, str]:
        """Mock de hierarquia de técnicos."""
        return {1: "N1", 2: "N1", 3: "N2", 4: "N2", 5: "N3", 6: "N4"}

    async def get_new_tickets(
        self,
        filters: Optional[MetricsFilterDTO] = None,
        context: Optional[QueryContext] = None,
    ) -> List[Dict[str, Any]]:
        """Mock de tickets novos."""
        return [
            {
                "id": 1001,
                "title": "Problema de conexão de rede",
                "description": "Usuário relatou intermitência na conexão",
                "status": "new",
                "priority": "medium",
                "category": "Network",
                "technician_id": None,
                "created_at": datetime.now() - timedelta(hours=2),
                "updated_at": datetime.now() - timedelta(hours=2),
                "requester": "João Silva",
                "location": "Sala 201",
            },
            {
                "id": 1002,
                "title": "Solicitação de instalação de software",
                "description": "Instalação do Office 365",
                "status": "assigned",
                "priority": "low",
                "category": "Software",
                "technician_id": 1,
                "created_at": datetime.now() - timedelta(hours=4),
                "updated_at": datetime.now() - timedelta(hours=1),
                "requester": "Maria Santos",
                "location": "Sala 105",
            },
            {
                "id": 1003,
                "title": "Computador não liga",
                "description": "Equipamento apresentou falha crítica",
                "status": "new",
                "priority": "high",
                "category": "Hardware",
                "technician_id": None,
                "created_at": datetime.now() - timedelta(minutes=30),
                "updated_at": datetime.now() - timedelta(minutes=30),
                "requester": "Carlos Lima",
                "location": "Sala 302",
            },
        ]

    async def get_system_status(self, context: Optional[QueryContext] = None) -> Dict[str, Any]:
        """Mock de status do sistema."""
        return {
            "glpi_version": "10.0.8",
            "api_version": "1.0",
            "database_status": "connected",
            "api_status": "healthy",
            "last_check": datetime.now().isoformat(),
            "response_time_ms": 45.2,
            "active_sessions": 8,
            "total_tickets": 375,
            "total_users": 142,
            "total_technicians": 12,
            "uptime_hours": 72.5,
            "memory_usage_mb": 256,
            "disk_usage_percent": 68.3,
            "services": {
                "web_server": "running",
                "database": "running",
                "cron_jobs": "running",
                "email_notifications": "running",
            },
            "health_score": 95.8,
        }

    async def discover_field_ids(self, context: Optional[QueryContext] = None) -> Dict[str, int]:
        """Mock de descoberta de IDs dos campos."""
        return {
            "group_id": 71,  # Campo para grupo responsável
            "status_id": 12,  # Campo para status do ticket
            "priority_id": 3,  # Campo para prioridade
            "category_id": 5,  # Campo para categoria
            "technician_id": 4,  # Campo para técnico responsável
            "requester_id": 22,  # Campo para solicitante
            "location_id": 83,  # Campo para localização
            "created_date": 15,  # Campo para data de criação
            "updated_date": 19,  # Campo para data de atualização
            "resolution_date": 61,  # Campo para data de resolução
            "title": 1,  # Campo para título
            "description": 21,  # Campo para descrição
            "solution": 24,  # Campo para solução
        }


# Exemplo de uso
async def example_usage():
    """Exemplo de como usar as queries."""

    # Criar data source (mock para exemplo)
    data_source = MockMetricsDataSource()

    # Criar factory
    factory = MetricsQueryFactory(data_source)

    # Criar contexto
    context = QueryContext(correlation_id="example-123", user_id=1)

    # Executar query de métricas gerais
    general_query = factory.create_general_metrics_query()
    general_result = await general_query.execute(context=context)

    if general_result.success:
        print(f"Métricas gerais: {general_result.data.total} tickets")

    # Executar query de ranking
    ranking_query = factory.create_technician_ranking_query()
    ranking_result = await ranking_query.execute(context=context)

    if ranking_result.success:
        print(f"Top técnico: {ranking_result.data[0].name}")

    # Executar query completa do dashboard
    dashboard_query = factory.create_dashboard_metrics_query()
    dashboard_result = await dashboard_query.execute(context=context)

    if dashboard_result.success:
        print(f"Dashboard: {len(dashboard_result.data.technicians)} técnicos")


if __name__ == "__main__":
    import asyncio

    asyncio.run(example_usage())
