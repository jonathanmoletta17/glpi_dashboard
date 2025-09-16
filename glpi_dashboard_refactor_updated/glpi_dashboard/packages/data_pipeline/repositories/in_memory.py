"""
In-memory repositories for domain entities.

These classes provide a simple storage mechanism for tickets and technicians
without relying on an external database. They are intended for development,
testing and demonstration purposes. In a production setting, replace
these with repositories backed by a persistent datastore.
"""

from typing import Dict, Iterable, List, Optional

from ...core_domain.tickets.models import Ticket
from ...core_domain.technicians.models import Technician


class TicketRepository:
    """Stores tickets in memory."""

    def __init__(self) -> None:
        self._tickets: Dict[int, Ticket] = {}

    def add(self, ticket: Ticket) -> None:
        self._tickets[ticket.id] = ticket

    def add_many(self, tickets: Iterable[Ticket]) -> None:
        for t in tickets:
            self.add(t)

    def list_all(self) -> List[Ticket]:
        return list(self._tickets.values())

    def get(self, ticket_id: int) -> Optional[Ticket]:
        return self._tickets.get(ticket_id)


class TechnicianRepository:
    """Stores technicians in memory."""

    def __init__(self) -> None:
        self._techs: Dict[int, Technician] = {}

    def add(self, technician: Technician) -> None:
        self._techs[technician.id] = technician

    def add_many(self, technicians: Iterable[Technician]) -> None:
        for t in technicians:
            self.add(t)

    def list_all(self) -> List[Technician]:
        return list(self._techs.values())

    def get(self, technician_id: int) -> Optional[Technician]:
        return self._techs.get(technician_id)