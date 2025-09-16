"""Worker responsável por obter tickets via polling da API GLPI."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Sequence

from glpi_dashboard_glpi_contracts.client.auth import GLPISession
from glpi_dashboard_glpi_contracts.client.criteria_builder import CriteriaBuilder, default_tickets_criteria
from glpi_dashboard_glpi_contracts.client.http import GLPIClient, load_fixture_tickets
from glpi_dashboard_glpi_contracts.mappers import ticket as ticket_mapper
from glpi_dashboard_shared.logging.logger import configure_logging

from glpi_dashboard_worker_ingestion.config import WorkerConfig
from glpi_dashboard_worker_ingestion.publishers.event_bus import SnapshotPublisher

_LOG = configure_logging('worker.polling')


class GlpiPollingWorker:
    def __init__(self, config: WorkerConfig, publisher: SnapshotPublisher | None = None):
        self._config = config
        self._publisher = publisher or SnapshotPublisher()

    async def poll(self, criteria: CriteriaBuilder | None = None) -> None:
        criteria = criteria or default_tickets_criteria()
        if self._config.use_fixture:
            glpi_tickets = load_fixture_tickets()
        else:
            session = GLPISession.from_settings()
            async with GLPIClient(base_url=self._config.base_url, session=session, use_fixture=False) as client:
                glpi_tickets = await client.list_tickets(criteria)
        domain_tickets = [ticket_mapper.to_domain(ticket) for ticket in glpi_tickets]
        self._publisher.publish(domain_tickets)
        _LOG.info('Polling run finished', extra={'tickets': len(domain_tickets)})


def build_worker(config: WorkerConfig) -> GlpiPollingWorker:
    return GlpiPollingWorker(config=config)
