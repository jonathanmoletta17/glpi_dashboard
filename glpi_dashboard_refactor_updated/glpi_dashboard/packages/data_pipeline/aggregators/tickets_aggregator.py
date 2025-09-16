"""
Aggregators for ticket metrics.

This module defines functions to compute aggregated statistics over a list
of ticket domain objects. These functions are used by services to prepare
data for the API and dashboard layers.
"""

from datetime import datetime
from typing import Iterable

from ...core_domain.tickets.models import Ticket, TicketMetrics
from ...core_domain.common.enums import TicketStatus


def aggregate_ticket_metrics(tickets: Iterable[Ticket]) -> TicketMetrics:
    """Compute summary statistics across a collection of tickets.

    Args:
        tickets: An iterable of Ticket instances.

    Returns:
        TicketMetrics: aggregated metrics summarising the collection.
    """
    total = 0
    counts = {
        TicketStatus.NEW: 0,
        TicketStatus.IN_PROGRESS: 0,
        TicketStatus.RESOLVED: 0,
        TicketStatus.CLOSED: 0,
        TicketStatus.PENDING: 0,
    }
    resolution_durations = []  # durations in hours for resolved/closed tickets

    for ticket in tickets:
        total += 1
        counts[ticket.status] = counts.get(ticket.status, 0) + 1
        if ticket.status in (TicketStatus.RESOLVED, TicketStatus.CLOSED):
            # Compute resolution time in hours
            duration = (ticket.updated_at - ticket.created_at).total_seconds() / 3600.0
            resolution_durations.append(duration)

    avg_resolution = (
        sum(resolution_durations) / len(resolution_durations)
        if resolution_durations
        else None
    )

    return TicketMetrics(
        total_count=total,
        new_count=counts[TicketStatus.NEW],
        in_progress_count=counts[TicketStatus.IN_PROGRESS],
        resolved_count=counts[TicketStatus.RESOLVED],
        closed_count=counts[TicketStatus.CLOSED],
        pending_count=counts[TicketStatus.PENDING],
        average_resolution_time_hours=avg_resolution,
    )