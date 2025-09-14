# -*- coding: utf-8 -*-
"""
Queries para a aplicação.

Este módulo centraliza todas as queries utilizadas na aplicação,
fornecendo uma interface limpa para consultas de dados.
"""

from .metrics_query import (  # Classes base; Queries específicas; Factory; Mock para testes
    BaseMetricsQuery,
    DashboardMetricsQuery,
    DataValidationError,
    GeneralMetricsQuery,
    MetricsDataSource,
    MetricsQueryFactory,
    MockMetricsDataSource,
    QueryContext,
    QueryExecutionError,
    TechnicianRankingQuery,
)

__all__ = [
    # Classes base
    "BaseMetricsQuery",
    "MetricsDataSource",
    "QueryContext",
    "QueryExecutionError",
    "DataValidationError",
    # Queries específicas
    "GeneralMetricsQuery",
    "TechnicianRankingQuery",
    "DashboardMetricsQuery",
    # Factory
    "MetricsQueryFactory",
    # Mock para testes
    "MockMetricsDataSource",
]
