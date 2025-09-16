"""Repositório de tickets usando armazenamento em arquivo JSON."""
from __future__ import annotations

import json
from datetime import datetime
from typing import List, Optional, Sequence

from glpi_dashboard_core_domain.tickets.entities import Ticket
from glpi_dashboard_core_domain.tickets.value_objects import (
    QueueName,
    SlaStatus,
    TicketId,
    TicketPriority,
    TicketStatus,
)
from glpi_dashboard_shared.config.settings import Settings, settings


class TicketRepository:
    """Persiste snapshots de tickets processados pela ingestão."""

    def __init__(self, *, settings_override: Settings | None = None):
        self._settings = settings_override or settings
        directory = self._settings.resolved_data_directory()
        self._snapshot_path = directory / 'tickets_snapshot.json'
        self._metadata_path = directory / 'tickets_metadata.json'

    def save(self, tickets: Sequence[Ticket], *, fetched_at: datetime) -> None:
        payload = [
            {
                'id': ticket.ticket_id.value,
                'title': ticket.title,
                'status': ticket.status.value,
                'priority': ticket.priority.value,
                'queue': ticket.queue.value if ticket.queue else None,
                'category': ticket.category,
                'technician': ticket.technician,
                'technician_id': ticket.technician_id,
                'requester': ticket.requester,
                'opened_at': ticket.opened_at.isoformat(),
                'updated_at': ticket.updated_at.isoformat(),
                'closed_at': ticket.closed_at.isoformat() if ticket.closed_at else None,
                'sla': {
                    'due_at': ticket.sla.due_at.isoformat() if ticket.sla.due_at else None,
                    'breached': ticket.sla.breached,
                },
                'time_to_resolve_minutes': ticket.time_to_resolve_minutes,
            }
            for ticket in tickets
        ]
        with self._snapshot_path.open('w', encoding='utf-8') as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
        with self._metadata_path.open('w', encoding='utf-8') as handle:
            json.dump({'fetched_at': fetched_at.isoformat()}, handle)

    def load(self) -> List[Ticket]:
        if not self._snapshot_path.exists():
            return []
        with self._snapshot_path.open('r', encoding='utf-8') as handle:
            data = json.load(handle)
        tickets: List[Ticket] = []
        for entry in data:
            tickets.append(
                Ticket(
                    ticket_id=TicketId(entry['id']),
                    title=entry['title'],
                    status=TicketStatus(entry['status']),
                    priority=TicketPriority(entry['priority']),
                    queue=QueueName(entry['queue']) if entry.get('queue') else None,
                    category=entry.get('category'),
                    technician=entry.get('technician'),
                    technician_id=entry.get('technician_id'),
                    requester=entry.get('requester'),
                    opened_at=datetime.fromisoformat(entry['opened_at']),
                    updated_at=datetime.fromisoformat(entry['updated_at']),
                    closed_at=datetime.fromisoformat(entry['closed_at']) if entry.get('closed_at') else None,
                    sla=SlaStatus(
                        due_at=datetime.fromisoformat(entry['sla']['due_at']) if entry['sla'].get('due_at') else None,
                        breached=entry['sla']['breached'],
                    ),
                    time_to_resolve_minutes=entry.get('time_to_resolve_minutes'),
                )
            )
        return tickets

    def last_fetched_at(self) -> Optional[datetime]:
        if not self._metadata_path.exists():
            return None
        with self._metadata_path.open('r', encoding='utf-8') as handle:
            data = json.load(handle)
        fetched_at = data.get('fetched_at')
        return datetime.fromisoformat(fetched_at) if fetched_at else None
