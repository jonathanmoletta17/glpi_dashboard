"""Configurações específicas do worker."""
from __future__ import annotations

from dataclasses import dataclass

from glpi_dashboard_shared.config.settings import Settings, settings


@dataclass(frozen=True)
class WorkerConfig:
    base_url: str
    use_fixture: bool


def load_worker_config(*, settings_override: Settings | None = None, use_fixture: bool = False) -> WorkerConfig:
    opts = settings_override or settings
    return WorkerConfig(base_url=opts.glpi_base_url, use_fixture=use_fixture or opts.environment == 'local')
