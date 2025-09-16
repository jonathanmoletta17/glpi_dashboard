"""
Aggregators for technician performance metrics.

This module computes performance statistics for each technician based on
their assigned tickets.
"""

from collections import defaultdict
from datetime import datetime
from typing import Dict, Iterable, List

from ...core_domain.tickets.models import Ticket
from ...core_domain.technicians.models import TechnicianPerformance
from ...core_domain.common.enums import TicketStatus


def aggregate_technician_performance(
    tickets: Iterable[Ticket],
) -> Dict[int, TechnicianPerformance]:
    """Aggregate performance metrics for technicians.

    Groups tickets by technician_id and computes performance metrics.

    Args:
        tickets: Iterable of Ticket instances.

    Returns:
        dict mapping technician_id to TechnicianPerformance.
    """
    grouped: Dict[int, List[Ticket]] = defaultdict(list)
    for ticket in tickets:
        if ticket.technician_id is None:
            continue
        grouped[ticket.technician_id].append(ticket)

    results: Dict[int, TechnicianPerformance] = {}
    for tech_id, tech_tickets in grouped.items():
        total_tickets = len(tech_tickets)
        resolved_tickets = 0
        resolution_durations = []
        for t in tech_tickets:
            if t.status in (TicketStatus.RESOLVED, TicketStatus.CLOSED):
                resolved_tickets += 1
                resolution_durations.append(
                    (t.updated_at - t.created_at).total_seconds() / 3600.0
                )

        avg_resolution = (
            sum(resolution_durations) / len(resolution_durations)
            if resolution_durations
            else None
        )
        # Placeholder for satisfaction; in a real system this might come
        # from survey responses or separate scoring system.
        satisfaction = None
        results[tech_id] = TechnicianPerformance(
            technician_id=tech_id,
            ticket_count=total_tickets,
            resolved_ticket_count=resolved_tickets,
            average_resolution_time_hours=avg_resolution,
            satisfaction_score=satisfaction,
        )
    return results