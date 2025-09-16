"""Endpoints REST relacionados a tickets."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from glpi_dashboard_api.schemas import (
    AgingBucketModel,
    QueueBacklogModel,
    TicketTimelineEventModel,
    TicketTimelineModel,
    TicketsOverviewModel,
)
from glpi_dashboard_data_pipeline.aggregators.ticket_metrics import TicketsOverview
from glpi_dashboard_data_pipeline.services.ticket_service import TicketMetricsService

from glpi_dashboard_api.dependencies.services import get_ticket_service

router = APIRouter(prefix='/v1/tickets', tags=['tickets'])


def _serialize_overview(overview: TicketsOverview) -> TicketsOverviewModel:
    return TicketsOverviewModel(
        total_backlog=overview.total_backlog,
        backlog_by_status=overview.backlog_by_status,
        backlog_by_priority=overview.backlog_by_priority,
        backlog_by_queue=[QueueBacklogModel(queue=item.queue, count=item.count) for item in overview.backlog_by_queue],
        new_last_24h=overview.new_last_24h,
        new_last_7d=overview.new_last_7d,
        aging=[AgingBucketModel(bucket=item.bucket, count=item.count) for item in overview.aging],
        sla_breaches=overview.sla_breaches,
        average_resolution_minutes=overview.average_resolution_minutes,
    )


@router.get('/overview', response_model=TicketsOverviewModel)
async def get_overview(service: TicketMetricsService = Depends(get_ticket_service)) -> TicketsOverviewModel:
    overview = service.overview()
    return _serialize_overview(overview)


@router.get('/{ticket_id}/timeline', response_model=TicketTimelineModel)
async def get_timeline(ticket_id: int, service: TicketMetricsService = Depends(get_ticket_service)) -> TicketTimelineModel:
    try:
        events = service.timeline(ticket_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return TicketTimelineModel(events=[TicketTimelineEventModel(at=event.at, description=event.description, status=event.status) for event in events])
