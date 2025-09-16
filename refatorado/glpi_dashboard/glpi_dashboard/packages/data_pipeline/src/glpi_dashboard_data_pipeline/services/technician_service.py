"""Casos de uso de ranking de técnicos."""
from __future__ import annotations

from typing import List

from glpi_dashboard_core_domain.technicians.entities import TechnicianPerformance
from glpi_dashboard_data_pipeline.aggregators.technician_metrics import build_ranking
from glpi_dashboard_data_pipeline.repositories.ticket_repository import TicketRepository


class TechnicianService:
    def __init__(self, repository: TicketRepository | None = None):
        self._repository = repository or TicketRepository()

    def ranking(self) -> List[TechnicianPerformance]:
        tickets = self._repository.load()
        return build_ranking(tickets)
