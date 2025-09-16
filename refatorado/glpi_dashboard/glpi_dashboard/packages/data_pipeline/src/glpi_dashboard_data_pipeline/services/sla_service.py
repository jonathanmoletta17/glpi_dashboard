"""Casos de uso de SLA e alertas."""
from __future__ import annotations

from datetime import datetime, timezone

from glpi_dashboard_data_pipeline.aggregators.sla_metrics import SlaSummary, collect_breaches
from glpi_dashboard_data_pipeline.repositories.ticket_repository import TicketRepository


class SlaService:
    def __init__(self, repository: TicketRepository | None = None):
        self._repository = repository or TicketRepository()

    def summary(self) -> SlaSummary:
        tickets = self._repository.load()
        return collect_breaches(tickets, reference=datetime.now(tz=timezone.utc))
