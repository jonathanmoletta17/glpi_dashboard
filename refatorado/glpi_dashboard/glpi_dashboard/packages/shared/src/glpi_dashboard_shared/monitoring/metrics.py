"""Abstrações de métricas Prometheus usadas pelos serviços."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable, Optional

from prometheus_client import Counter, Gauge

from glpi_dashboard_shared.config.settings import settings

_ingestion_lag_gauge = Gauge(
    'glpi_ingestion_lag_seconds',
    'Atraso entre o último evento recebido do GLPI e o horário atual.',
)

_glpi_retry_counter = Counter(
    'glpi_client_retries_total',
    'Quantidade de retries realizados ao chamar a API do GLPI.',
)

_api_latency_gauge = Gauge(
    'glpi_api_latency_seconds',
    'Latência média das respostas REST calculada pelos handlers.',
)


def observe_ingestion_lag(last_event_at: Optional[datetime]) -> None:
    """Atualiza a métrica de lag considerando o timestamp do último evento."""

    if not settings.enable_metrics:
        return
    if last_event_at is None:
        _ingestion_lag_gauge.set(float('nan'))
        return
    now = datetime.now(tz=timezone.utc)
    delta = (now - last_event_at).total_seconds()
    _ingestion_lag_gauge.set(max(delta, 0.0))


def increment_retry() -> None:
    """Incrementa o contador de retries do cliente GLPI."""

    if settings.enable_metrics:
        _glpi_retry_counter.inc()


def observe_latency(latency_seconds: float) -> None:
    """Registra latência de requisições da API pública."""

    if settings.enable_metrics:
        _api_latency_gauge.set(latency_seconds)


class LatencyMiddleware:
    """Middleware simples para medir latência em FastAPI sem dependências extras."""

    def __init__(self, time_provider: Callable[[], datetime]):
        self._time_provider = time_provider

    async def __call__(self, request, call_next):  # type: ignore[no-untyped-def]
        start = self._time_provider()
        response = await call_next(request)
        duration = (self._time_provider() - start).total_seconds()
        observe_latency(duration)
        return response
