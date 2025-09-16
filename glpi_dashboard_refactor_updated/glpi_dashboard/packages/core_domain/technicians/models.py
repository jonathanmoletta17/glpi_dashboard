"""
Domain models for technicians and their performance metrics.

Technicians are responsible for handling tickets in the GLPI system. The
`TechnicianPerformance` model aggregates statistics about their work.
"""

from dataclasses import dataclass
from typing import Optional

@dataclass
class Technician:
    """Represents a technician in the organisation."""

    id: int
    name: str
    team: Optional[str] = None


@dataclass
class TechnicianPerformance:
    """Aggregated performance metrics for a technician."""

    technician_id: int
    ticket_count: int
    resolved_ticket_count: int
    average_resolution_time_hours: Optional[float]
    satisfaction_score: Optional[float]