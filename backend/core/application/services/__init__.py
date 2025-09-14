# -*- coding: utf-8 -*-
"""
Application Services - Camada de serviços da aplicação.

Este módulo contém os serviços de aplicação que orquestram
a lógica de negócio e coordenam entre diferentes camadas.
"""

from .metrics_facade import MetricsFacade

__all__ = [
    "MetricsFacade",
]
