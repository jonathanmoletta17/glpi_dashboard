"""Casos de uso relacionados a tickets."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable, List, Optional

from glpi_dashboard_core_domain.tickets.entities import Ticket
from glpi_dashboard_data_pipeline.aggregators.ticket_metrics import (
    TicketTimelineEvent,
    TicketsOverview,
    build_timeline,
    calculate_overview,
)
from glpi_dashboard_data_pipeline.repositories.ticket_repository import TicketRepository


class TicketMetricsService:
    """Fornece métricas agregadas a partir dos snapshots persistidos."""

    def __init__(self, repository: TicketRepository | None = None):
        self._repository = repository or TicketRepository()

    def overview(self, *, reference: Optional[datetime] = None) -> TicketsOverview:
        reference = reference or datetime.now(tz=timezone.utc)
        tickets = self._repository.load()
        return calculate_overview(tickets, reference=reference)

    def timeline(self, ticket_id: int) -> List[TicketTimelineEvent]:
        tickets = self._repository.load()
        for ticket in tickets:
            if ticket.ticket_id.value == ticket_id:
                return build_timeline(ticket)
        raise ValueError(f'Ticket {ticket_id} não encontrado')

    def tickets(self) -> Iterable[Ticket]:
        return self._repository.load()
