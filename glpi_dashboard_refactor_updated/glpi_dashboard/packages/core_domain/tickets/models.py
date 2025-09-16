"""
Domain models for ticket management.

These classes represent the fundamental entities and value objects for the
ticket domain. They are kept pure (no external dependencies) so they can be
used by services, aggregators, mappers and API layers without bringing in
unnecessary runtime dependencies.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from ..common.enums import TicketPriority, TicketStatus


@dataclass
class Ticket:
    """Represents a single ticket in the GLPI system."""

    id: int
    title: str
    description: str
    status: TicketStatus
    priority: TicketPriority
    created_at: datetime
    updated_at: datetime
    due_date: Optional[datetime] = None
    technician_id: Optional[int] = None


@dataclass
class TicketMetrics:
    """Aggregated metrics over a collection of tickets.

    These metrics can be used to feed dashboards or summary reports.
    """

    total_count: int
    new_count: int
    in_progress_count: int
    resolved_count: int
    closed_count: int
    pending_count: int
    average_resolution_time_hours: Optional[float] = None