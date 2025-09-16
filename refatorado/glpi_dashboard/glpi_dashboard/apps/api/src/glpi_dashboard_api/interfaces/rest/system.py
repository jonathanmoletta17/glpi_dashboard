"""Endpoints REST de saúde do sistema."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from glpi_dashboard_api.dependencies.services import get_system_health_service
from glpi_dashboard_api.schemas import SystemHealthModel
from glpi_dashboard_data_pipeline.services.system_health_service import SystemHealthService

router = APIRouter(prefix='/v1/system', tags=['system'])


@router.get('/health', response_model=SystemHealthModel)
async def get_health(service: SystemHealthService = Depends(get_system_health_service)) -> SystemHealthModel:
    health = service.health()
    return SystemHealthModel(
        ingestion_lag_seconds=health.ingestion_lag_seconds,
        tickets_snapshot_at=health.tickets_snapshot_at,
    )
