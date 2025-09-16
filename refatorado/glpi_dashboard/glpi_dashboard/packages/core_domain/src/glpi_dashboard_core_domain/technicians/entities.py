"""Entidades e DTOs relacionados a técnicos."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(slots=True)
class TechnicianPerformance:
    """Dados agregados de produtividade utilizados no ranking."""

    technician_id: int
    name: str
    tickets_handled: int
    tickets_closed: int
    sla_breaches: int
    average_resolution_minutes: Optional[float]

    def efficiency_score(self) -> float:
        if self.tickets_handled == 0:
            return 0.0
        closed_ratio = self.tickets_closed / self.tickets_handled
        penalty = 1 + (self.sla_breaches * 0.1)
        return round(closed_ratio / penalty, 3)


@dataclass(slots=True)
class TechnicianAssignment:
    technician_id: int
    name: str
    assigned_at: datetime
