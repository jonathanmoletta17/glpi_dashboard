# -*- coding: utf-8 -*-
"""
Internal Data Transfer Objects (DTOs) para métricas do GLPI Dashboard.

Este módulo define apenas DTOs únicos para uso interno que não duplicam
os modelos de API em schemas/dashboard.py. Para modelos de API, use schemas/.
"""

from datetime import datetime
from typing import Optional, Dict, Any, Union, List

from pydantic import BaseModel, Field, validator
from pydantic.types import NonNegativeInt, PositiveInt

# Import enums from schemas (single source of truth)
from schemas.dashboard import TicketStatus, TechnicianLevel, DashboardMetrics, TechnicianRanking, ApiResponse, ApiError


class MetricsFilterDTO(BaseModel):
    """DTO para filtros de métricas."""

    start_date: Optional[datetime] = Field(None, description="Data de início do filtro")
    end_date: Optional[datetime] = Field(None, description="Data de fim do filtro")
    status: Optional[TicketStatus] = Field(None, description="Status do ticket")
    level: Optional[TechnicianLevel] = Field(None, description="Nível do técnico")
    service_level: Optional[str] = Field(None, description="Nível de serviço")
    use_modification_date: bool = Field(False, description="Usar data de modificação ao invés de criação")
    technician_id: Optional[PositiveInt] = Field(None, description="ID do técnico")
    category_id: Optional[PositiveInt] = Field(None, description="ID da categoria")
    priority: Optional[int] = Field(None, ge=1, le=6, description="Prioridade do ticket (1-6)")
    limit: Optional[PositiveInt] = Field(None, description="Limite de resultados")
    offset: Optional[NonNegativeInt] = Field(0, description="Offset para paginação")

    @validator("end_date")
    def validate_end_date(cls, v, values):
        """Valida que end_date é posterior a start_date."""
        if v and "start_date" in values and values["start_date"]:
            if v <= values["start_date"]:
                raise ValueError("end_date deve ser posterior a start_date")
        return v

    class Config:
        use_enum_values = True
        json_encoders = {datetime: lambda v: v.isoformat() if v else None}


# Import additional models for type aliases
from schemas.dashboard import LevelMetrics

# Type aliases for backward compatibility
# These can be gradually removed as code is updated to use schemas directly
TicketMetricsDTO = LevelMetrics  # Use LevelMetrics from schemas instead
TechnicianMetricsDTO = TechnicianRanking  # Use TechnicianRanking from schemas instead
MetricsDTO = DashboardMetrics  # Use DashboardMetrics from schemas instead
MetricsResponseDTO = ApiResponse  # Use ApiResponse from schemas instead


# TicketMetricsDTO removed - use LevelMetrics from schemas/dashboard.py instead


# LevelMetricsDTO removed - use LevelMetrics from schemas/dashboard.py instead


# TechnicianMetricsDTO removed - use TechnicianRanking from schemas/dashboard.py instead


# MetricsDTO removed - use DashboardMetrics from schemas/dashboard.py instead


# DashboardMetricsDTO removed - use DashboardMetrics from schemas/dashboard.py instead


# MetricsResponseDTO removed - use ApiResponse/ApiError from schemas/dashboard.py instead


# Factory functions para criação de DTOs


# Factory functions for creating consolidated schema models

from schemas.dashboard import (
    DashboardMetrics,
    TendenciasMetrics,
    NiveisMetrics,
    LevelMetrics,
    FiltersApplied,
    ApiResponse,
    ApiError,
)


def create_empty_dashboard_metrics() -> DashboardMetrics:
    """Cria métricas de dashboard vazias com valores padrão."""
    return DashboardMetrics(
        novos=0,
        pendentes=0,
        progresso=0,
        resolvidos=0,
        total=0,
        niveis=NiveisMetrics(
            n1=LevelMetrics(novos=0, pendentes=0, progresso=0, resolvidos=0, total=0),
            n2=LevelMetrics(novos=0, pendentes=0, progresso=0, resolvidos=0, total=0),
            n3=LevelMetrics(novos=0, pendentes=0, progresso=0, resolvidos=0, total=0),
            n4=LevelMetrics(novos=0, pendentes=0, progresso=0, resolvidos=0, total=0),
        ),
        tendencias=TendenciasMetrics(),
    )


def create_error_response(error_message: str, correlation_id: Optional[str] = None) -> ApiError:
    """Cria uma resposta de erro padronizada."""
    return ApiError(message=error_message, errors=[error_message])


def create_success_response(
    data: Any,
    correlation_id: Optional[str] = None,
    message: Optional[str] = None,
) -> ApiResponse:
    """Cria uma resposta de sucesso padronizada."""
    return ApiResponse(data=data, message=message)
