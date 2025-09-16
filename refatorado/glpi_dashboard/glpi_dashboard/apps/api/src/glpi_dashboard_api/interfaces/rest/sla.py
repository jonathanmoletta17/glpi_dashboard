"""Endpoints REST de SLA."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from glpi_dashboard_api.dependencies.services import get_sla_service
from glpi_dashboard_api.schemas import SlaBreachModel, SlaSummaryModel
from glpi_dashboard_data_pipeline.services.sla_service import SlaService

router = APIRouter(prefix='/v1/sla', tags=['sla'])


@router.get('/breaches', response_model=SlaSummaryModel)
async def get_sla_breaches(service: SlaService = Depends(get_sla_service)) -> SlaSummaryModel:
    summary = service.summary()
    return SlaSummaryModel(
        total_breaches=summary.total_breaches,
        breaches_by_queue=summary.breaches_by_queue,
        recent_breaches=[
            SlaBreachModel(
                ticket_id=item.ticket_id.value,
                technician=item.technician,
                queue=item.queue,
                breached_at=item.breached_at,
                delay_minutes=item.delay_minutes,
                severity=item.severity,
            )
            for item in summary.recent_breaches
        ],
    )
