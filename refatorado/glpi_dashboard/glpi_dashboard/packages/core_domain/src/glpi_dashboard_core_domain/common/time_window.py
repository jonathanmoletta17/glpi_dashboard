"""Representação explícita de janelas temporais."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass(frozen=True)
class TimeWindow:
    start: datetime
    end: datetime

    def contains(self, instant: datetime) -> bool:
        return self.start <= instant <= self.end

    @classmethod
    def last_hours(cls, hours: int, *, reference: datetime) -> 'TimeWindow':
        return cls(start=reference - timedelta(hours=hours), end=reference)

    @classmethod
    def last_days(cls, days: int, *, reference: datetime) -> 'TimeWindow':
        return cls(start=reference - timedelta(days=days), end=reference)
