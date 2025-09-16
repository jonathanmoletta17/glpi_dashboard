"""
Unit tests for aggregator functions.

These tests verify that the ticket and technician aggregators compute
statistics correctly given a controlled set of input tickets.
"""

from datetime import datetime, timedelta

from glpi_dashboard_refactor.glpi_dashboard.packages.core_domain.tickets.models import Ticket
from glpi_dashboard_refactor.glpi_dashboard.packages.core_domain.common.enums import TicketStatus, TicketPriority
from glpi_dashboard_refactor.glpi_dashboard.packages.data_pipeline.aggregators.tickets_aggregator import (
    aggregate_ticket_metrics,
)
from glpi_dashboard_refactor.glpi_dashboard.packages.data_pipeline.aggregators.technician_aggregator import (
    aggregate_technician_performance,
)


def _sample_ticket(
    id: int,
    status: TicketStatus,
    technician_id: int | None = None,
    creation_offset_hours: int = 0,
    resolution_duration_hours: int = 0,
) -> Ticket:
    """Helper to create a sample ticket."""
    created_at = datetime(2024, 1, 1) + timedelta(hours=creation_offset_hours)
    updated_at = created_at + timedelta(hours=resolution_duration_hours)
    return Ticket(
        id=id,
        title=f"Ticket {id}",
        description="",
        status=status,
        priority=TicketPriority.MEDIUM,
        created_at=created_at,
        updated_at=updated_at,
        due_date=None,
        technician_id=technician_id,
    )


def test_aggregate_ticket_metrics_counts() -> None:
    tickets = [
        _sample_ticket(1, TicketStatus.NEW),
        _sample_ticket(2, TicketStatus.IN_PROGRESS),
        _sample_ticket(3, TicketStatus.RESOLVED, resolution_duration_hours=5),
        _sample_ticket(4, TicketStatus.CLOSED, resolution_duration_hours=2),
        _sample_ticket(5, TicketStatus.PENDING),
    ]
    metrics = aggregate_ticket_metrics(tickets)
    assert metrics.total_count == 5
    assert metrics.new_count == 1
    assert metrics.in_progress_count == 1
    assert metrics.resolved_count == 1
    assert metrics.closed_count == 1
    assert metrics.pending_count == 1
    # average resolution time should be (5 + 2) / 2 = 3.5
    assert metrics.average_resolution_time_hours == 3.5


def test_aggregate_technician_performance() -> None:
    tickets = [
        _sample_ticket(1, TicketStatus.RESOLVED, technician_id=1, resolution_duration_hours=4),
        _sample_ticket(2, TicketStatus.CLOSED, technician_id=1, resolution_duration_hours=2),
        _sample_ticket(3, TicketStatus.NEW, technician_id=2),
        _sample_ticket(4, TicketStatus.RESOLVED, technician_id=2, resolution_duration_hours=1),
    ]
    perf = aggregate_technician_performance(tickets)
    # Technician 1 has two tickets, both resolved
    tech1 = perf[1]
    assert tech1.ticket_count == 2
    assert tech1.resolved_ticket_count == 2
    assert tech1.average_resolution_time_hours == 3.0  # (4 + 2) / 2
    # Technician 2 has two tickets, one resolved
    tech2 = perf[2]
    assert tech2.ticket_count == 2
    assert tech2.resolved_ticket_count == 1
    assert tech2.average_resolution_time_hours == 1.0