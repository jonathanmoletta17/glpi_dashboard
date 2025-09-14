# -*- coding: utf-8 -*-
"""
Data Transfer Objects (DTOs) para a aplicação.

Este módulo centraliza todos os DTOs utilizados na aplicação,
fornecendo estruturas de dados padronizadas e validadas.
"""

from .metrics_dto import (
    MetricsFilterDTO,
    create_empty_dashboard_metrics,
    create_error_response,
    create_success_response,
)

# Import consolidated models from schemas (single source of truth)
from schemas.dashboard import (
    DashboardMetrics,
    TechnicianRanking,
    NewTicket,
    LevelMetrics,
    ApiResponse,
    ApiError,
    TicketStatus,
    TechnicianLevel,
)

__all__ = [
    # Enums from schemas (consolidated)
    "TicketStatus",
    "TechnicianLevel",
    # Consolidated schemas (API boundary models)
    "DashboardMetrics",
    "TechnicianRanking",
    "NewTicket",
    "LevelMetrics",
    "ApiResponse",
    "ApiError",
    # Internal DTOs (unique types)
    "MetricsFilterDTO",
    # Factory functions
    "create_empty_dashboard_metrics",
    "create_error_response",
    "create_success_response",
    # Backward compatibility aliases
    "MetricsDTO",  # -> DashboardMetrics
    "TechnicianMetricsDTO",  # -> TechnicianRanking
    "MetricsResponseDTO",  # -> ApiResponse
]

# Backward compatibility aliases
MetricsDTO = DashboardMetrics
TechnicianMetricsDTO = TechnicianRanking
MetricsResponseDTO = ApiResponse
LevelMetricsDTO = LevelMetrics
TicketMetricsDTO = LevelMetrics
DashboardMetricsDTO = DashboardMetrics
