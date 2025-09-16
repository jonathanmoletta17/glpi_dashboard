"""Endpoints REST de técnicos."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from glpi_dashboard_api.dependencies.services import get_technician_service
from glpi_dashboard_api.schemas import TechnicianRankingEntryModel
from glpi_dashboard_data_pipeline.services.technician_service import TechnicianService

router = APIRouter(prefix='/v1/technicians', tags=['technicians'])


@router.get('/ranking', response_model=list[TechnicianRankingEntryModel])
async def get_ranking(service: TechnicianService = Depends(get_technician_service)) -> list[TechnicianRankingEntryModel]:
    ranking = service.ranking()
    return [
        TechnicianRankingEntryModel(
            technician_id=item.technician_id,
            name=item.name,
            tickets_handled=item.tickets_handled,
            tickets_closed=item.tickets_closed,
            sla_breaches=item.sla_breaches,
            average_resolution_minutes=item.average_resolution_minutes,
            efficiency_score=item.efficiency_score(),
        )
        for item in ranking
    ]
