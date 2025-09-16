"""Value Objects relacionados a tickets do Service Desk."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class TicketStatus(str, Enum):
    NEW = 'new'
    IN_PROGRESS = 'in_progress'
    PENDING = 'pending'
    SOLVED = 'solved'
    CLOSED = 'closed'

    @classmethod
    def from_glpi(cls, status_name: str) -> 'TicketStatus':
        normalized = status_name.strip().lower()
        mapping = {
            'new': cls.NEW,
            'processing (assigned)': cls.IN_PROGRESS,
            'processing (planned)': cls.IN_PROGRESS,
            'pending': cls.PENDING,
            'solved': cls.SOLVED,
            'closed': cls.CLOSED,
        }
        return mapping.get(normalized, cls.IN_PROGRESS)


class TicketPriority(str, Enum):
    VERY_LOW = 'very_low'
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    VERY_HIGH = 'very_high'

    @classmethod
    def from_glpi(cls, priority_name: str) -> 'TicketPriority':
        normalized = priority_name.strip().lower()
        mapping = {
            'very low': cls.VERY_LOW,
            'low': cls.LOW,
            'medium': cls.MEDIUM,
            'high': cls.HIGH,
            'very high': cls.VERY_HIGH,
        }
        return mapping.get(normalized, cls.MEDIUM)


@dataclass(frozen=True)
class TicketId:
    value: int

    def __post_init__(self) -> None:
        if self.value <= 0:
            raise ValueError('TicketId deve ser positivo')

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class QueueName:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError('Fila não pode ser vazia')

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class SlaStatus:
    due_at: Optional[datetime]
    breached: bool

    def remaining_seconds(self, *, reference: datetime) -> Optional[float]:
        if self.due_at is None:
            return None
        return (self.due_at - reference).total_seconds()
