"""Container simples de dependências para a API."""
from __future__ import annotations

from functools import lru_cache

from glpi_dashboard_data_pipeline.repositories.ticket_repository import TicketRepository
from glpi_dashboard_data_pipeline.services.sla_service import SlaService
from glpi_dashboard_data_pipeline.services.system_health_service import SystemHealthService
from glpi_dashboard_data_pipeline.services.technician_service import TechnicianService
from glpi_dashboard_data_pipeline.services.ticket_service import TicketMetricsService


@lru_cache(maxsize=1)
def get_ticket_repository() -> TicketRepository:
    return TicketRepository()


def get_ticket_service() -> TicketMetricsService:
    return TicketMetricsService(repository=get_ticket_repository())


def get_technician_service() -> TechnicianService:
    return TechnicianService(repository=get_ticket_repository())


def get_sla_service() -> SlaService:
    return SlaService(repository=get_ticket_repository())


def get_system_health_service() -> SystemHealthService:
    return SystemHealthService(repository=get_ticket_repository())
