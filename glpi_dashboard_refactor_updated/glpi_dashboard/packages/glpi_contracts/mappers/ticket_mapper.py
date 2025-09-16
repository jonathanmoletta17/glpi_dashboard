"""
Mapper functions to convert raw GLPI ticket data into domain models.

GLPI API responses return dictionaries with keys like "id", "name", "status",
"priority", "date_creation" and "date_mod". This mapper translates those
responses into Ticket domain objects. Adjust field names as necessary to match
your GLPI version.
"""

from datetime import datetime
from typing import Any, Dict

from ...core_domain.tickets.models import Ticket
from ...core_domain.common.enums import TicketPriority, TicketStatus


def parse_datetime(dt_str: str) -> datetime:
    """Parse a GLPI date string into a datetime object.

    GLPI dates are typically in the format "YYYY-MM-DD HH:MM:SS". If parsing
    fails, a ValueError will be raised.
    """
    return datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")


def glpi_ticket_to_domain(data: Dict[str, Any]) -> Ticket:
    """Convert a raw GLPI ticket JSON object into a Ticket domain instance.

    Args:
        data: Dictionary representing a ticket from the GLPI API.

    Returns:
        Ticket: domain entity.

    Raises:
        KeyError if required fields are missing.
    """
    return Ticket(
        id=int(data["id"]),
        title=data.get("name", ""),
        description=data.get("content", ""),
        status=TicketStatus(data.get("status", "new")),
        priority=TicketPriority(data.get("priority", "medium")),
        created_at=parse_datetime(data.get("date_creation", data.get("date", "1970-01-01 00:00:00"))),
        updated_at=parse_datetime(data.get("date_mod", data.get("date_creation", "1970-01-01 00:00:00"))),
        due_date=parse_datetime(data["due_date"]) if data.get("due_date") else None,
        technician_id=int(data["technician_id"]) if data.get("technician_id") else None,
    )