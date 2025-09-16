"""Schemas expostos pela API pública."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class QueueBacklogModel(BaseModel):
    queue: str
    count: int


class AgingBucketModel(BaseModel):
    bucket: str
    count: int


class TicketsOverviewModel(BaseModel):
    total_backlog: int
    backlog_by_status: dict[str, int]
    backlog_by_priority: dict[str, int]
    backlog_by_queue: List[QueueBacklogModel]
    new_last_24h: int
    new_last_7d: int
    aging: List[AgingBucketModel]
    sla_breaches: int
    average_resolution_minutes: Optional[float]


class TicketTimelineEventModel(BaseModel):
    at: datetime
    description: str
    status: str


class TicketTimelineModel(BaseModel):
    events: List[TicketTimelineEventModel]


class TechnicianRankingEntryModel(BaseModel):
    technician_id: int
    name: str
    tickets_handled: int
    tickets_closed: int
    sla_breaches: int
    average_resolution_minutes: Optional[float]
    efficiency_score: float


class SlaBreachModel(BaseModel):
    ticket_id: int
    technician: Optional[str]
    queue: Optional[str]
    breached_at: datetime
    delay_minutes: int
    severity: str


class SlaSummaryModel(BaseModel):
    total_breaches: int
    breaches_by_queue: dict[str, int]
    recent_breaches: List[SlaBreachModel]


class SystemHealthModel(BaseModel):
    ingestion_lag_seconds: Optional[float]
    tickets_snapshot_at: Optional[datetime]
