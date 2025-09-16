"""Ponto de entrada do worker de ingestão."""
from __future__ import annotations

import argparse
import asyncio

from glpi_dashboard_worker_ingestion.config import load_worker_config
from glpi_dashboard_worker_ingestion.consumers.glpi_polling import build_worker


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Executa uma rodada de ingestão GLPI.')
    parser.add_argument('--use-fixture', action='store_true', help='Utiliza dados locais ao invés da API real.')
    return parser.parse_args()


def run() -> None:
    args = parse_args()
    config = load_worker_config(use_fixture=args.use_fixture)
    worker = build_worker(config)
    asyncio.run(worker.poll())


if __name__ == '__main__':  # pragma: no cover - entrypoint manual
    run()
