"""Schema GraphQL seguindo contratos do Doc 03."""
from __future__ import annotations

import strawberry
from strawberry.fastapi import GraphQLRouter

from glpi_dashboard_api.dependencies.services import (
    get_sla_service,
    get_system_health_service,
    get_technician_service,
    get_ticket_service,
)
from glpi_dashboard_data_pipeline.services.sla_service import SlaService
from glpi_dashboard_data_pipeline.services.system_health_service import SystemHealthService
from glpi_dashboard_data_pipeline.services.technician_service import TechnicianService
from glpi_dashboard_data_pipeline.services.ticket_service import TicketMetricsService


@strawberry.type
class QueueBacklogType:
    queue: str
    count: int


@strawberry.type
class AgingBucketType:
    bucket: str
    count: int


@strawberry.type
class TicketsOverviewType:
    total_backlog: int
    backlog_by_status: strawberry.scalars.JSON
    backlog_by_priority: strawberry.scalars.JSON
    backlog_by_queue: list[QueueBacklogType]
    new_last_24h: int
    new_last_7d: int
    aging: list[AgingBucketType]
    sla_breaches: int
    average_resolution_minutes: float | None


@strawberry.type
class TechnicianRankingEntryType:
    technician_id: int
    name: str
    tickets_handled: int
    tickets_closed: int
    sla_breaches: int
    average_resolution_minutes: float | None
    efficiency_score: float


@strawberry.type
class SlaBreachType:
    ticket_id: int
    technician: str | None
    queue: str | None
    breached_at: str
    delay_minutes: int
    severity: str


@strawberry.type
class SlaSummaryType:
    total_breaches: int
    breaches_by_queue: strawberry.scalars.JSON
    recent_breaches: list[SlaBreachType]


@strawberry.type
class SystemHealthType:
    ingestion_lag_seconds: float | None
    tickets_snapshot_at: str | None


@strawberry.type
class Query:
    tickets_overview: TicketsOverviewType = strawberry.field(description='Resumo geral de tickets.')
    technician_ranking: list[TechnicianRankingEntryType] = strawberry.field(description='Ranking de técnicos.')
    sla_summary: SlaSummaryType = strawberry.field(description='Resumo de violações de SLA.')
    system_health: SystemHealthType = strawberry.field(description='Saúde da ingestão e dados.')

    @strawberry.field
    def tickets_overview(self, info) -> TicketsOverviewType:  # type: ignore[override]
        service: TicketMetricsService = get_ticket_service()
        overview = service.overview()
        return TicketsOverviewType(
            total_backlog=overview.total_backlog,
            backlog_by_status=overview.backlog_by_status,
            backlog_by_priority=overview.backlog_by_priority,
            backlog_by_queue=[QueueBacklogType(queue=item.queue, count=item.count) for item in overview.backlog_by_queue],
            new_last_24h=overview.new_last_24h,
            new_last_7d=overview.new_last_7d,
            aging=[AgingBucketType(bucket=item.bucket, count=item.count) for item in overview.aging],
            sla_breaches=overview.sla_breaches,
            average_resolution_minutes=overview.average_resolution_minutes,
        )

    @strawberry.field
    def technician_ranking(self, info) -> list[TechnicianRankingEntryType]:  # type: ignore[override]
        service: TechnicianService = get_technician_service()
        ranking = service.ranking()
        return [
            TechnicianRankingEntryType(
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

    @strawberry.field
    def sla_summary(self, info) -> SlaSummaryType:  # type: ignore[override]
        service: SlaService = get_sla_service()
        summary = service.summary()
        return SlaSummaryType(
            total_breaches=summary.total_breaches,
            breaches_by_queue=summary.breaches_by_queue,
            recent_breaches=[
                SlaBreachType(
                    ticket_id=item.ticket_id.value,
                    technician=item.technician,
                    queue=item.queue,
                    breached_at=item.breached_at.isoformat(),
                    delay_minutes=item.delay_minutes,
                    severity=item.severity,
                )
                for item in summary.recent_breaches
            ],
        )

    @strawberry.field
    def system_health(self, info) -> SystemHealthType:  # type: ignore[override]
        service: SystemHealthService = get_system_health_service()
        health = service.health()
        return SystemHealthType(
            ingestion_lag_seconds=health.ingestion_lag_seconds,
            tickets_snapshot_at=health.tickets_snapshot_at.isoformat() if health.tickets_snapshot_at else None,
        )


def create_graphql_router() -> GraphQLRouter:
    schema = strawberry.Schema(query=Query)
    return GraphQLRouter(schema, graphiql=True)
