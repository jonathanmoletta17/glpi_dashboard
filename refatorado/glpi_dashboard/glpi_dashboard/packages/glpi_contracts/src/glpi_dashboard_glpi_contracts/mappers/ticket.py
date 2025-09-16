"""Conversão GLPI → domínio."""
from __future__ import annotations

from glpi_dashboard_core_domain.tickets.entities import Ticket
from glpi_dashboard_core_domain.tickets.value_objects import QueueName, SlaStatus, TicketId, TicketPriority, TicketStatus
from glpi_dashboard_glpi_contracts.schemas.ticket import GLPITicket


def to_domain(ticket: GLPITicket) -> Ticket:
    queue = QueueName(ticket.group) if ticket.group else None
    sla = SlaStatus(due_at=ticket.due_at, breached=ticket.sla_overdue)
    return Ticket(
        ticket_id=TicketId(ticket.id),
        title=ticket.name,
        status=TicketStatus.from_glpi(ticket.status_name),
        priority=TicketPriority.from_glpi(ticket.priority_name),
        queue=queue,
        category=ticket.category,
        technician=ticket.technician,
        technician_id=ticket.technician_id,
        requester=ticket.requester,
        opened_at=ticket.created_at,
        updated_at=ticket.updated_at,
        closed_at=ticket.closed_at,
        sla=sla,
        time_to_resolve_minutes=ticket.time_to_resolve_minutes,
    )
