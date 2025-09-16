"""Agregadores responsáveis por produzir métricas de tickets."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from statistics import mean
from typing import Iterable, List, Optional, Sequence

from glpi_dashboard_core_domain.tickets.entities import Ticket
from glpi_dashboard_core_domain.tickets.value_objects import TicketPriority, TicketStatus


@dataclass(frozen=True)
class QueueBacklog:
    queue: str
    count: int


@dataclass(frozen=True)
class AgingBucket:
    bucket: str
    count: int


@dataclass(frozen=True)
class TicketsOverview:
    total_backlog: int
    backlog_by_status: dict[str, int]
    backlog_by_priority: dict[str, int]
    backlog_by_queue: List[QueueBacklog]
    new_last_24h: int
    new_last_7d: int
    aging: List[AgingBucket]
    sla_breaches: int
    average_resolution_minutes: Optional[float]


@dataclass(frozen=True)
class TicketTimelineEvent:
    at: datetime
    description: str
    status: str


def calculate_overview(tickets: Sequence[Ticket], *, reference: datetime) -> TicketsOverview:
    backlog_tickets = [ticket for ticket in tickets if ticket.is_open()]
    total_backlog = len(backlog_tickets)
    backlog_by_status: dict[str, int] = {}
    backlog_by_priority: dict[str, int] = {}
    queue_counter: dict[str, int] = {}
    resolution_times: List[int] = []
    sla_breaches = 0

    for ticket in tickets:
        status_key = ticket.status.value
        backlog_by_status[status_key] = backlog_by_status.get(status_key, 0) + (1 if ticket.is_open() else 0)
        priority_key = ticket.priority.value
        backlog_by_priority[priority_key] = backlog_by_priority.get(priority_key, 0) + (1 if ticket.is_open() else 0)
        queue = str(ticket.queue) if ticket.queue else 'Sem fila'
        if ticket.is_open():
            queue_counter[queue] = queue_counter.get(queue, 0) + 1
        if ticket.sla_breached():
            sla_breaches += 1
        resolution = ticket.resolution_minutes()
        if resolution is not None:
            resolution_times.append(resolution)

    new_last_24h = _count_created_within(tickets, timedelta(hours=24), reference)
    new_last_7d = _count_created_within(tickets, timedelta(days=7), reference)
    aging = _build_aging(backlog_tickets, reference)

    average_resolution = mean(resolution_times) if resolution_times else None

    queue_backlog = [QueueBacklog(queue=queue, count=count) for queue, count in sorted(queue_counter.items(), key=lambda item: item[1], reverse=True)]

    return TicketsOverview(
        total_backlog=total_backlog,
        backlog_by_status=backlog_by_status,
        backlog_by_priority=backlog_by_priority,
        backlog_by_queue=queue_backlog,
        new_last_24h=new_last_24h,
        new_last_7d=new_last_7d,
        aging=aging,
        sla_breaches=sla_breaches,
        average_resolution_minutes=average_resolution,
    )


def _count_created_within(tickets: Iterable[Ticket], delta: timedelta, reference: datetime) -> int:
    lower_bound = reference - delta
    return sum(1 for ticket in tickets if ticket.opened_at >= lower_bound)


def _build_aging(backlog_tickets: Sequence[Ticket], reference: datetime) -> List[AgingBucket]:
    buckets = {
        '<4h': 0,
        '4-24h': 0,
        '1-3d': 0,
        '>3d': 0,
    }
    for ticket in backlog_tickets:
        hours = ticket.backlog_age_hours(reference)
        if hours < 4:
            buckets['<4h'] += 1
        elif hours < 24:
            buckets['4-24h'] += 1
        elif hours <= 72:
            buckets['1-3d'] += 1
        else:
            buckets['>3d'] += 1
    return [AgingBucket(bucket=key, count=value) for key, value in buckets.items()]


def build_timeline(ticket: Ticket) -> List[TicketTimelineEvent]:
    events: List[TicketTimelineEvent] = [
        TicketTimelineEvent(at=ticket.opened_at, description='Ticket criado', status='created')
    ]
    if ticket.closed_at:
        events.append(TicketTimelineEvent(at=ticket.closed_at, description='Ticket fechado', status='closed'))
    events.append(TicketTimelineEvent(at=ticket.updated_at, description='Última atualização', status=ticket.status.value))
    return sorted(events, key=lambda event: event.at)
