"""Entidades de ticket seguindo Clean Architecture."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from glpi_dashboard_core_domain.tickets.value_objects import (
    QueueName,
    SlaStatus,
    TicketId,
    TicketPriority,
    TicketStatus,
)


@dataclass(slots=True)
class Ticket:
    """Entidade raiz representando um ticket do GLPI."""

    ticket_id: TicketId
    title: str
    status: TicketStatus
    priority: TicketPriority
    queue: Optional[QueueName]
    category: Optional[str]
    technician: Optional[str]
    technician_id: Optional[int]
    requester: Optional[str]
    opened_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime]
    sla: SlaStatus
    time_to_resolve_minutes: Optional[int]

    def is_open(self) -> bool:
        return self.status not in {TicketStatus.SOLVED, TicketStatus.CLOSED}

    def backlog_age_hours(self, reference: datetime) -> float:
        delta = reference - self.opened_at
        return delta.total_seconds() / 3600

    def resolution_minutes(self) -> Optional[int]:
        if self.time_to_resolve_minutes is not None:
            return self.time_to_resolve_minutes
        if self.closed_at is None:
            return None
        return int((self.closed_at - self.opened_at).total_seconds() // 60)

    def sla_breached(self) -> bool:
        return self.sla.breached
