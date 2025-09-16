"""Entidades de SLA e alertas."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from glpi_dashboard_core_domain.tickets.value_objects import TicketId


@dataclass(slots=True)
class SlaBreach:
    ticket_id: TicketId
    technician: Optional[str]
    queue: Optional[str]
    breached_at: datetime
    delay_minutes: int
    severity: str
