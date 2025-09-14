from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

from pydantic import BaseModel, Field, root_validator, validator
from pydantic.types import NonNegativeInt, PositiveInt


class TicketStatus(str, Enum):
    """Enum para status de tickets."""

    NOVO = "novo"
    PENDENTE = "pendente"
    PROGRESSO = "progresso"
    RESOLVIDO = "resolvido"
    FECHADO = "fechado"
    CANCELADO = "cancelado"


class TechnicianLevel(str, Enum):
    """Enum para níveis de técnicos."""

    N1 = "N1"
    N2 = "N2"
    N3 = "N3"
    N4 = "N4"
    UNKNOWN = "UNKNOWN"


class LevelMetrics(BaseModel):
    """Métricas de um nível específico (N1, N2, N3, N4)"""

    novos: NonNegativeInt = Field(0, description="Número de tickets novos")
    pendentes: NonNegativeInt = Field(0, description="Número de tickets pendentes")
    progresso: NonNegativeInt = Field(0, description="Número de tickets em progresso")
    resolvidos: NonNegativeInt = Field(0, description="Número de tickets resolvidos")
    total: NonNegativeInt = Field(0, description="Total de tickets no nível")

    @root_validator(skip_on_failure=True)
    def calculate_total(cls, values):
        """Calcula o total baseado nos status individuais."""
        total_calculated = (
            values.get("novos", 0) + values.get("pendentes", 0) + values.get("progresso", 0) + values.get("resolvidos", 0)
        )
        # Se total não foi fornecido, calcula automaticamente
        if values.get("total", 0) == 0:
            values["total"] = total_calculated
        return values


class NiveisMetrics(BaseModel):
    """Métricas de todos os níveis"""

    n1: LevelMetrics
    n2: LevelMetrics
    n3: LevelMetrics
    n4: LevelMetrics

    def __setitem__(self, key: str, value: LevelMetrics):
        """Allow setting level metrics using bracket notation."""
        if hasattr(self, key):
            setattr(self, key, value)
        else:
            raise KeyError(f"Invalid level key: {key}")

    def values(self):
        """Return all level metrics values."""
        return [self.n1, self.n2, self.n3, self.n4]


class TendenciasMetrics(BaseModel):
    """Tendências das métricas"""

    novos: str = "0"
    pendentes: str = "0"
    progresso: str = "0"
    resolvidos: str = "0"


class FiltersApplied(BaseModel):
    """Filtros aplicados na consulta"""

    start_date: Optional[str] = None
    end_date: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    level: Optional[str] = None
    technician: Optional[str] = None
    category: Optional[str] = None


class DashboardMetrics(BaseModel):
    """Schema unificado para métricas do dashboard"""

    novos: int = Field(ge=0, description="Total de tickets novos")
    pendentes: int = Field(ge=0, description="Total de tickets pendentes")
    progresso: int = Field(ge=0, description="Total de tickets em progresso")
    resolvidos: int = Field(ge=0, description="Total de tickets resolvidos")
    total: int = Field(ge=0, description="Total geral de tickets")
    niveis: NiveisMetrics
    tendencias: TendenciasMetrics
    filters_applied: Optional[FiltersApplied] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None


class TechnicianRanking(BaseModel):
    """Ranking de técnico"""

    id: int
    name: str
    ticket_count: int = Field(ge=0)
    level: str
    performance_score: Optional[float] = None


class NewTicket(BaseModel):
    """Ticket novo"""

    id: str
    title: str
    description: str
    date: str
    requester: str
    priority: str
    status: str = "Novo"
    filters_applied: Optional[FiltersApplied] = None


class ApiResponse(BaseModel):
    """Schema padrão para respostas da API"""

    success: bool = True
    data: Any
    message: Optional[str] = None
    errors: Optional[List[str]] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    execution_time_ms: Optional[float] = None

    def set_execution_time(self, start_time: Optional[datetime] = None):
        """Calculate and set execution time from start time."""
        if start_time:
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            self.execution_time_ms = execution_time


class ApiError(ApiResponse):
    """Schema para erros da API"""

    success: bool = False
    data: None = None
    message: Optional[str] = None
    errors: Optional[List[str]] = None
    error_code: Optional[str] = None

    def __init__(self, message: str, errors: Optional[List[str]] = None, **kwargs):
        if errors is None:
            errors = [message]
        super().__init__(success=False, data=None, message=message, errors=errors, **kwargs)
