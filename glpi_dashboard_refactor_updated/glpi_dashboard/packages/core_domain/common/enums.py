"""
common/enums.py
This module defines common enumerations used across the GLPI dashboard domain models.

These enums represent standardised values for ticket status, priority and alert levels.
Keeping these definitions in a central location makes it easy to maintain
consistency across domain entities, mappers and API contracts.
"""

from enum import Enum


class TicketStatus(str, Enum):
    """Enumeration of possible ticket statuses.

    The values should mirror those returned by the GLPI API. Adjust as needed
    to reflect your organisation's workflow.
    """

    NEW = "new"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"
    PENDING = "pending"


class TicketPriority(str, Enum):
    """Enumeration of possible ticket priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class AlertLevel(str, Enum):
    """Enumeration of alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"