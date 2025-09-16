"""Agregadores de produtividade de técnicos."""
from __future__ import annotations

from collections import defaultdict
from statistics import mean
from typing import Dict, Iterable, List

from glpi_dashboard_core_domain.technicians.entities import TechnicianPerformance
from glpi_dashboard_core_domain.tickets.entities import Ticket


def build_ranking(tickets: Iterable[Ticket]) -> List[TechnicianPerformance]:
    counters: Dict[int, TechnicianPerformance] = {}
    resolution_by_tech: Dict[int, List[int]] = defaultdict(list)

    for ticket in tickets:
        if ticket.technician_id is None:
            continue
        if ticket.technician_id not in counters:
            counters[ticket.technician_id] = TechnicianPerformance(
                technician_id=ticket.technician_id,
                name=ticket.technician or f'Técnico {ticket.technician_id}',
                tickets_handled=0,
                tickets_closed=0,
                sla_breaches=0,
                average_resolution_minutes=None,
            )
        current = counters[ticket.technician_id]
        counters[ticket.technician_id] = TechnicianPerformance(
            technician_id=current.technician_id,
            name=current.name,
            tickets_handled=current.tickets_handled + 1,
            tickets_closed=current.tickets_closed + (0 if ticket.closed_at is None else 1),
            sla_breaches=current.sla_breaches + (1 if ticket.sla_breached() else 0),
            average_resolution_minutes=current.average_resolution_minutes,
        )
        resolution = ticket.resolution_minutes()
        if resolution is not None:
            resolution_by_tech[ticket.technician_id].append(resolution)

    ranking: List[TechnicianPerformance] = []
    for technician_id, perf in counters.items():
        times = resolution_by_tech.get(technician_id, [])
        average = mean(times) if times else None
        ranking.append(
            TechnicianPerformance(
                technician_id=perf.technician_id,
                name=perf.name,
                tickets_handled=perf.tickets_handled,
                tickets_closed=perf.tickets_closed,
                sla_breaches=perf.sla_breaches,
                average_resolution_minutes=average,
            )
        )

    return sorted(ranking, key=lambda perf: (perf.efficiency_score(), perf.tickets_closed), reverse=True)
