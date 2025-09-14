# -*- coding: utf-8 -*-
"""
GLPI External Integration Module.

Este módulo contém adaptadores e integrações com a API externa do GLPI.
"""

from .metrics_adapter import (
    GLPIAPIClient,
    GLPIAPIError,
    GLPIAuthenticationError,
    GLPIConfig,
    GLPIConnectionError,
    GLPIMetricsAdapter,
    GLPISessionManager,
    create_glpi_metrics_adapter,
)

__all__ = [
    # Adapter principal
    "GLPIMetricsAdapter",
    # Configuração
    "GLPIConfig",
    # Componentes internos
    "GLPISessionManager",
    "GLPIAPIClient",
    # Exceções
    "GLPIConnectionError",
    "GLPIAuthenticationError",
    "GLPIAPIError",
    # Factory
    "create_glpi_metrics_adapter",
]
