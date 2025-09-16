"""Configuração centralizada de logging estruturado.

O logger segue as recomendações de observabilidade do Doc 05, publicando
mensagens em JSON com `trace_id` e `span_id` para permitir correlação ponta a
ponta entre ingestão, API e frontend.
"""
from __future__ import annotations

import json
import logging
import sys
from contextvars import ContextVar
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict

from glpi_dashboard_shared.config.settings import settings

_trace_id: ContextVar[str | None] = ContextVar('trace_id', default=None)
_span_id: ContextVar[str | None] = ContextVar('span_id', default=None)


@dataclass(slots=True)
class LogRecord:
    """Estrutura de log serializada como JSON."""

    level: str
    message: str
    timestamp: str
    service: str
    trace_id: str | None
    span_id: str | None
    extra: Dict[str, Any]

    def to_json(self) -> str:
        return json.dumps({
            'level': self.level,
            'message': self.message,
            'timestamp': self.timestamp,
            'service': self.service,
            'trace_id': self.trace_id,
            'span_id': self.span_id,
            **self.extra,
        }, ensure_ascii=False)


def configure_logging(service_name: str) -> logging.Logger:
    """Inicializa logging estruturado para o serviço informado."""

    logger = logging.getLogger(service_name)
    if logger.handlers:
        return logger

    logger.setLevel(settings.log_level)
    handler = logging.StreamHandler(sys.stdout)

    def emit(record: logging.LogRecord) -> None:
        payload = LogRecord(
            level=record.levelname,
            message=record.getMessage(),
            timestamp=datetime.utcnow().isoformat(timespec='milliseconds') + 'Z',
            service=service_name,
            trace_id=_trace_id.get(),
            span_id=_span_id.get(),
            extra=getattr(record, 'extra', {}),
        )
        handler.stream.write(payload.to_json() + '\n')

    handler.emit = emit  # type: ignore[assignment]
    logger.addHandler(handler)
    logger.propagate = False
    return logger


def set_trace_context(trace_id: str | None, span_id: str | None) -> None:
    """Atualiza o contexto de trace usado pelos logs."""

    _trace_id.set(trace_id)
    _span_id.set(span_id)


def clear_trace_context() -> None:
    """Limpa o contexto de trace (usar ao finalizar uma requisição)."""

    _trace_id.set(None)
    _span_id.set(None)
