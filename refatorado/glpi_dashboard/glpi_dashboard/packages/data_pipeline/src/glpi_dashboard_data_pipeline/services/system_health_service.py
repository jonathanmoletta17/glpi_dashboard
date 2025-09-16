"""Casos de uso de saúde do sistema."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from glpi_dashboard_data_pipeline.repositories.ticket_repository import TicketRepository
from glpi_dashboard_shared.monitoring.metrics import observe_ingestion_lag


@dataclass(frozen=True)
class SystemHealth:
    ingestion_lag_seconds: Optional[float]
    tickets_snapshot_at: Optional[datetime]


class SystemHealthService:
    def __init__(self, repository: TicketRepository | None = None):
        self._repository = repository or TicketRepository()

    def health(self) -> SystemHealth:
        last_fetched = self._repository.last_fetched_at()
        if last_fetched is None:
            observe_ingestion_lag(None)
            return SystemHealth(ingestion_lag_seconds=None, tickets_snapshot_at=None)
        now = datetime.now(tz=timezone.utc)
        lag_seconds = (now - last_fetched).total_seconds()
        observe_ingestion_lag(last_fetched)
        return SystemHealth(ingestion_lag_seconds=lag_seconds, tickets_snapshot_at=last_fetched)
