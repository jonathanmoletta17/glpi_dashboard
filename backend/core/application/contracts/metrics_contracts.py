# -*- coding: utf-8 -*-
"""
Contratos/Interfaces para Métricas

Define os contratos que as rotas esperam do sistema de métricas,
permitindo migração progressiva da arquitetura legada.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple

from schemas.dashboard import DashboardMetrics, TechnicianRanking, NewTicket, ApiResponse, ApiError


class MetricsServiceContract(ABC):
    """Contrato principal para serviços de métricas."""

    @abstractmethod
    def get_dashboard_metrics(self, correlation_id: Optional[str] = None) -> DashboardMetrics:
        """Obtém métricas gerais do dashboard."""
        pass

    @abstractmethod
    def get_dashboard_metrics_with_date_filter(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> DashboardMetrics:
        """Obtém métricas do dashboard com filtro de data."""
        pass

    @abstractmethod
    def get_dashboard_metrics_with_modification_date_filter(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> DashboardMetrics:
        """Obtém métricas do dashboard com filtro de data de modificação."""
        pass

    @abstractmethod
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
        """Obtém métricas do dashboard com múltiplos filtros."""
        pass


class TechnicianServiceContract(ABC):
    """Contrato para serviços de técnicos."""

    @abstractmethod
    def get_all_technician_ids_and_names(self, entity_id: Optional[int] = None) -> Tuple[List[int], List[str]]:
        """Obtém IDs e nomes de todos os técnicos."""
        pass

    @abstractmethod
    def get_technician_ranking(self, limit: int = 50) -> List[TechnicianRanking]:
        """Obtém ranking de técnicos."""
        pass

    @abstractmethod
    def get_technician_ranking_with_filters(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        level: Optional[str] = None,
        limit: int = 50,
        entity_id: Optional[int] = None,
        correlation_id: Optional[str] = None,
    ) -> List[TechnicianRanking]:
        """Obtém ranking de técnicos com filtros."""
        pass


class TicketServiceContract(ABC):
    """Contrato para serviços de tickets."""

    @abstractmethod
    def get_new_tickets(self, limit: int = 20) -> List[NewTicket]:
        """Obtém tickets novos."""
        pass

    @abstractmethod
    def get_new_tickets_with_filters(
        self,
        limit: int = 20,
        priority: Optional[str] = None,
        category: Optional[str] = None,
        technician: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[NewTicket]:
        """Obtém tickets novos com filtros."""
        pass


class SystemServiceContract(ABC):
    """Contrato para serviços de sistema."""

    @abstractmethod
    def get_system_status(self) -> ApiResponse:
        """Obtém status do sistema."""
        pass

    @abstractmethod
    def authenticate_with_retry(self) -> bool:
        """Autentica com retry automático."""
        pass


class UnifiedGLPIServiceContract(
    MetricsServiceContract, TechnicianServiceContract, TicketServiceContract, SystemServiceContract
):
    """Contrato unificado que combina todos os serviços GLPI."""

    pass
