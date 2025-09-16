"""Pydantic schema definitions for GLPI ticket DTOs.

These schemas reflect the structure of ticket data returned by the GLPI API.
Extend these models as necessary to include all relevant fields.
"""

from pydantic import BaseModel, Field
from typing import Optional


class TicketSummary(BaseModel):
    id: int
    title: str
    status: str
    queue: Optional[str] = None
    created_at: Optional[str] = Field(None, alias="date_creation")
    updated_at: Optional[str] = Field(None, alias="date_modification")


class TechnicianScorecard(BaseModel):
    technician_id: int
    technician_name: str
    handled: int
    sla_breaches: int
    productivity_score: float