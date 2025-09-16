"""Aplicação FastAPI responsável por expor REST e GraphQL."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import generate_latest
from starlette.responses import PlainTextResponse

from glpi_dashboard_api.config.settings import load_api_settings
from glpi_dashboard_api.interfaces.graphql.schema import create_graphql_router
from glpi_dashboard_api.interfaces.rest import sla, system, technicians, tickets
from glpi_dashboard_shared.logging.logger import configure_logging
from glpi_dashboard_shared.monitoring.metrics import LatencyMiddleware

_LOG = configure_logging('api.main')
settings = load_api_settings()


def create_app() -> FastAPI:
    docs_url = '/docs' if settings.enable_docs else None
    openapi_url = '/openapi.json' if settings.enable_docs else None

    app = FastAPI(title='GLPI Dashboard API', docs_url=docs_url, openapi_url=openapi_url, version='0.1.0')
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=['*'],
        allow_headers=['*'],
        allow_credentials=True,
    )
    app.middleware('http')(LatencyMiddleware(lambda: datetime.now(tz=timezone.utc)))

    app.include_router(tickets.router)
    app.include_router(technicians.router)
    app.include_router(sla.router)
    app.include_router(system.router)

    graphql_router = create_graphql_router()
    app.include_router(graphql_router, prefix='/graphql')

    @app.get('/metrics', include_in_schema=False)
    async def metrics() -> PlainTextResponse:  # pragma: no cover - endpoint simples
        return PlainTextResponse(generate_latest(), media_type='text/plain; version=0.0.4')

    return app


def run() -> None:
    import uvicorn

    app = create_app()
    _LOG.info('Starting API', extra={'host': settings.host, 'port': settings.port})
    uvicorn.run(app, host=settings.host, port=settings.port)


app = create_app()
