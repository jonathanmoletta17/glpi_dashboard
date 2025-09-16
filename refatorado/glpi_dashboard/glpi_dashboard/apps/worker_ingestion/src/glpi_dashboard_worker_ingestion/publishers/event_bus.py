"""Publicador de snapshots para o pipeline de métricas."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Sequence

from glpi_dashboard_core_domain.tickets.entities import Ticket
from glpi_dashboard_data_pipeline.repositories.ticket_repository import TicketRepository
from glpi_dashboard_shared.logging.logger import configure_logging

_LOG = configure_logging('worker.publisher')


class SnapshotPublisher:
    """Persiste tickets agregados e emite logs estruturados."""

    def __init__(self, repository: TicketRepository | None = None):
        self._repository = repository or TicketRepository()

    def publish(self, tickets: Sequence[Ticket]) -> None:
        fetched_at = datetime.now(tz=timezone.utc)
        self._repository.save(tickets, fetched_at=fetched_at)
        _LOG.info('Tickets snapshot persisted', extra={'count': len(tickets), 'fetched_at': fetched_at.isoformat()})
