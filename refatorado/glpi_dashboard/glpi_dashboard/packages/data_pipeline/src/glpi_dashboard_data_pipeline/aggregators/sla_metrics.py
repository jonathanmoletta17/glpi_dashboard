"""Agregadores de SLA e alertas."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, List

from glpi_dashboard_core_domain.alerts.entities import SlaBreach
from glpi_dashboard_core_domain.tickets.entities import Ticket


@dataclass(frozen=True)
class SlaSummary:
    total_breaches: int
    breaches_by_queue: dict[str, int]
    recent_breaches: List[SlaBreach]


def collect_breaches(tickets: Iterable[Ticket], *, reference: datetime) -> SlaSummary:
    breaches: List[SlaBreach] = []
    breaches_by_queue: dict[str, int] = {}

    for ticket in tickets:
        if not ticket.sla_breached():
            continue
        queue = str(ticket.queue) if ticket.queue else 'Sem fila'
        breaches_by_queue[queue] = breaches_by_queue.get(queue, 0) + 1
        breached_at = ticket.closed_at or reference
        delay_minutes = ticket.resolution_minutes() or int((reference - ticket.opened_at).total_seconds() // 60)
        severity = 'high' if delay_minutes > 240 else 'medium'
        breaches.append(
            SlaBreach(
                ticket_id=ticket.ticket_id,
                technician=ticket.technician,
                queue=ticket.queue.value if ticket.queue else None,
                breached_at=breached_at,
                delay_minutes=delay_minutes,
                severity=severity,
            )
        )

    breaches.sort(key=lambda breach: breach.delay_minutes, reverse=True)
    recent = sorted(breaches, key=lambda breach: breach.breached_at, reverse=True)[:10]
    return SlaSummary(total_breaches=len(breaches), breaches_by_queue=breaches_by_queue, recent_breaches=recent)
