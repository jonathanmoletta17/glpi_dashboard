"""
REST endpoints for ticket metrics and technician performance.

These endpoints provide aggregated statistics for consumption by front-end
dashboards or other services. They rely on a shared in-memory repository.
"""

from typing import Dict

from fastapi import APIRouter, Depends

from ......packages.data_pipeline.aggregators.tickets_aggregator import aggregate_ticket_metrics
from ......packages.data_pipeline.aggregators.technician_aggregator import aggregate_technician_performance
from ......packages.data_pipeline.repositories.in_memory import TicketRepository


router = APIRouter(prefix="/tickets", tags=["tickets"])


def get_repository() -> TicketRepository:
    """Provide the ticket repository.

    In a more sophisticated application this could be dependency-injected
    using a proper container or factory.
    """
    from ..main import ticket_repository  # type: ignore
    return ticket_repository


@router.get("/metrics")
def ticket_metrics(repo: TicketRepository = Depends(get_repository)) -> Dict[str, object]:
    """Return aggregated ticket metrics."""
    metrics = aggregate_ticket_metrics(repo.list_all())
    return metrics.__dict__


@router.get("/technicians/performance")
def technician_performance(repo: TicketRepository = Depends(get_repository)) -> Dict[int, object]:
    """Return performance metrics for all technicians."""
    performance = aggregate_technician_performance(repo.list_all())
    # Convert dataclasses to plain dicts for JSON serialization
    return {tech_id: perf.__dict__ for tech_id, perf in performance.items()}