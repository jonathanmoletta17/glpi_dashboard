"""Esquemas Pydantic que espelham respostas relevantes do GLPI."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class GLPITicket(BaseModel):
    """Schema simplificado baseado em `ticket` do GLPI."""

    id: int = Field(..., description='Identificador único do ticket no GLPI.')
    name: str = Field(..., description='Título do ticket.')
    status_code: int = Field(..., alias='status', description='Código numérico do status no GLPI.')
    status_name: str = Field(..., description='Representação textual do status.')
    priority_code: int = Field(..., alias='priority', description='Código numérico da prioridade.')
    priority_name: str = Field(..., description='Descrição da prioridade.')
    requester: Optional[str] = Field(None, description='Nome do solicitante.')
    technician: Optional[str] = Field(None, description='Técnico atualmente designado.')
    technician_id: Optional[int] = Field(None, description='ID do técnico designado.')
    group: Optional[str] = Field(None, description='Fila ou grupo responsável.')
    category: Optional[str] = Field(None, description='Categoria principal do ticket.')
    created_at: datetime = Field(..., alias='date', description='Data de abertura.')
    updated_at: datetime = Field(..., alias='date_mod', description='Última atualização.')
    closed_at: Optional[datetime] = Field(None, alias='close_date', description='Data de fechamento.')
    due_at: Optional[datetime] = Field(None, description='Prazo calculado de SLA.')
    sla_overdue: bool = Field(False, description='Indica se o SLA foi extrapolado.')
    time_to_resolve_minutes: Optional[int] = Field(
        None,
        description='Tempo total para resolver em minutos quando fechado.',
    )

    model_config = {
        'populate_by_name': True,
        'from_attributes': True,
    }
