"""Cliente HTTP assíncrono responsável por conversar com o GLPI."""
from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import List

import httpx
from pydantic import ValidationError

from glpi_dashboard_shared.logging.logger import configure_logging
from glpi_dashboard_shared.monitoring.metrics import increment_retry
from glpi_dashboard_glpi_contracts.client.auth import GLPISession
from glpi_dashboard_glpi_contracts.client.criteria_builder import CriteriaBuilder
from glpi_dashboard_glpi_contracts.schemas.ticket import GLPITicket

_LOG = configure_logging('glpi_contracts.client')
_FIXTURE_PATH = Path(__file__).resolve().parent.parent / 'fixtures' / 'tickets_sample.json'


class GLPIClient:
    """Cliente com _retry_ exponencial e suporte a fixtures locais."""

    def __init__(self, *, base_url: str, session: GLPISession, use_fixture: bool = False):
        self._base_url = base_url.rstrip('/')
        self._session = session
        self._use_fixture = use_fixture
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> 'GLPIClient':
        self._client = httpx.AsyncClient(base_url=self._base_url, headers=self._session.as_headers(), timeout=30.0)
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # type: ignore[no-untyped-def]
        if self._client:
            await self._client.aclose()

    async def list_tickets(self, criteria: CriteriaBuilder) -> List[GLPITicket]:
        """Retorna tickets respeitando o criteria informado."""

        if self._use_fixture:
            return self._load_fixture()
        assert self._client, 'Use GLPIClient como contexto async'
        payload = criteria.build()
        retries = 3
        for attempt in range(1, retries + 1):
            try:
                response = await self._client.get('/ticket', params={'criteria': payload})
                response.raise_for_status()
                data = response.json()
                return [GLPITicket.model_validate(item) for item in data]
            except (httpx.HTTPError, ValidationError) as error:  # pragma: no cover - caminhos de erro
                if attempt >= retries:
                    _LOG.error('GLPI request failed', extra={'payload': payload, 'error': str(error)})
                    raise
                await asyncio.sleep(2 ** attempt)
                increment_retry()
        raise RuntimeError('unreachable retry loop')

    def _load_fixture(self) -> List[GLPITicket]:
        with _FIXTURE_PATH.open('r', encoding='utf-8') as handle:
            data = json.load(handle)
        return [GLPITicket.model_validate(item) for item in data]


def load_fixture_tickets() -> List[GLPITicket]:
    """Função utilitária usada em testes sem instanciar o cliente."""

    with _FIXTURE_PATH.open('r', encoding='utf-8') as handle:
        data = json.load(handle)
    return [GLPITicket.model_validate(item) for item in data]
