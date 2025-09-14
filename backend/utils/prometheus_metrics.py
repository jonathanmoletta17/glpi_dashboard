"""Módulo de métricas Prometheus para observabilidade.

Este módulo implementa instrumentação com métricas Prometheus para monitoramento
de performance, latência e saúde do sistema.
"""

import logging
import time
from contextlib import contextmanager
from functools import wraps
from typing import Any, Dict, Optional, Union

try:
    from prometheus_client import (
        CONTENT_TYPE_LATEST,
        CollectorRegistry,
        Counter,
        Gauge,
        Histogram,
        Info,
        Summary,
        generate_latest,
        push_to_gateway,
    )

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    CONTENT_TYPE_LATEST = "text/plain"

    def generate_latest(registry: Any) -> Union[str, bytes]:  # type: ignore
        return ""

    def push_to_gateway(gateway: str, job: str, registry: Any, **kwargs: Any) -> None:  # type: ignore
        pass

    # Mock classes para quando prometheus_client não está disponível
    class CollectorRegistry:  # type: ignore
        def __init__(self) -> None:
            pass

    class Counter:  # type: ignore
        def labels(self, **kwargs: Any) -> Any:
            return self

        def inc(self, amount: float = 1) -> None:
            pass

    class Histogram:  # type: ignore
        def labels(self, **kwargs: Any) -> Any:
            return self

        def observe(self, amount: float) -> None:
            pass

    class Gauge:  # type: ignore
        def labels(self, **kwargs: Any) -> Any:
            return self

        def set(self, value: float) -> None:
            pass

        def inc(self, amount: float = 1) -> None:
            pass

        def dec(self, amount: float = 1) -> None:
            pass

    class Summary:  # type: ignore
        def labels(self, **kwargs: Any) -> Any:
            return self

        def observe(self, amount: float) -> None:
            pass

    class Info:  # type: ignore
        def labels(self, **kwargs: Any) -> Any:
            return self

        def info(self, data: Dict[str, Any]) -> None:
            pass

    logging.warning("prometheus_client não disponível. Métricas Prometheus desabilitadas.")

from config.settings import active_config

logger = logging.getLogger(__name__)


class PrometheusMetrics:
    """Gerenciador de métricas Prometheus para o GLPI Dashboard."""

    def __init__(self, registry: Optional[CollectorRegistry] = None):
        self.enabled = PROMETHEUS_AVAILABLE
        self.registry = registry or CollectorRegistry()
        self.config = active_config()

        if not self.enabled:
            logger.warning("Métricas Prometheus desabilitadas - prometheus_client não disponível")
            self._init_mock_metrics()
        else:
            self._init_metrics()
            logger.info("Métricas Prometheus inicializadas")

    def _init_metrics(self) -> None:
        """Inicializa todas as métricas Prometheus."""
        if not self.enabled:
            self._init_mock_metrics()
            return

        # Métricas de API
        self.api_requests_total = Counter(
            "glpi_api_requests_total",
            "Total de requisições à API",
            ["method", "endpoint", "status_code"],
            registry=self.registry,
        )

        self.api_request_duration = Histogram(
            "glpi_api_request_duration_seconds",
            "Duração das requisições à API em segundos",
            ["method", "endpoint"],
            buckets=[0.1, 0.3, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
            registry=self.registry,
        )

        # Métricas de GLPI
        self.glpi_requests_total = Counter(
            "glpi_external_requests_total",
            "Total de requisições ao GLPI externo",
            ["endpoint", "status_code"],
            registry=self.registry,
        )

        self.glpi_request_duration = Histogram(
            "glpi_external_request_duration_seconds",
            "Duração das requisições ao GLPI em segundos",
            ["endpoint"],
            buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0],
            registry=self.registry,
        )

        # Métricas de métricas (meta-métricas)
        self.metrics_processing_duration = Histogram(
            "glpi_metrics_processing_duration_seconds",
            "Tempo de processamento das métricas",
            ["query_type"],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0],
            registry=self.registry,
        )

        self.metrics_cache_hits = Counter(
            "glpi_metrics_cache_hits_total",
            "Total de cache hits nas métricas",
            ["query_type"],
            registry=self.registry,
        )

        self.metrics_cache_misses = Counter(
            "glpi_metrics_cache_misses_total",
            "Total de cache misses nas métricas",
            ["query_type"],
            registry=self.registry,
        )

        # Métricas de sistema
        self.active_connections = Gauge(
            "glpi_active_connections",
            "Número de conexões ativas",
            registry=self.registry,
        )

        self.tickets_total = Gauge(
            "glpi_tickets_total",
            "Total de tickets por status",
            ["status", "level"],
            registry=self.registry,
        )

        self.technicians_total = Gauge(
            "glpi_technicians_total",
            "Total de técnicos por nível",
            ["level"],
            registry=self.registry,
        )

        # Métricas de erro
        self.errors_total = Counter(
            "glpi_errors_total",
            "Total de erros por tipo",
            ["error_type", "component"],
            registry=self.registry,
        )

        # Métricas de alertas
        self.alerts_total = Counter(
            "glpi_alerts_total",
            "Total de alertas gerados",
            ["alert_type", "severity"],
            registry=self.registry,
        )

        # Informações do sistema
        self.system_info = Info("glpi_system_info", "Informações do sistema", registry=self.registry)

        # Definir informações do sistema
        self.system_info.info(
            {
                "version": getattr(self.config, "VERSION", "1.0.0"),
                "environment": getattr(self.config, "ENVIRONMENT", "development"),
                "python_version": getattr(self.config, "PYTHON_VERSION", "3.9+"),
            }
        )

    def _init_mock_metrics(self) -> None:
        """Inicializa métricas mock quando Prometheus não está disponível."""

        # Criar métricas mock usando as classes mock definidas no bloco except
        class MockMetric:
            """Mock para métricas quando Prometheus não está disponível."""

            def labels(self, **kwargs: Any) -> "MockMetric":
                return self

            def inc(self, amount: float = 1) -> None:
                pass

            def set(self, value: float) -> None:
                pass

            def dec(self, amount: float = 1) -> None:
                pass

            def observe(self, amount: float) -> None:
                pass

            def info(self, data: Dict[str, Any]) -> None:
                pass

        # Substituir métricas existentes por mocks
        mock_metric = MockMetric()
        self.api_requests_total = mock_metric  # type: ignore
        self.api_request_duration = mock_metric  # type: ignore
        self.glpi_requests_total = mock_metric  # type: ignore
        self.glpi_request_duration = mock_metric  # type: ignore
        self.metrics_processing_duration = mock_metric  # type: ignore
        self.metrics_cache_hits = mock_metric  # type: ignore
        self.metrics_cache_misses = mock_metric  # type: ignore
        self.active_connections = mock_metric  # type: ignore
        self.tickets_total = mock_metric  # type: ignore
        self.technicians_total = mock_metric  # type: ignore
        self.errors_total = mock_metric  # type: ignore
        self.alerts_total = mock_metric  # type: ignore
        self.system_info = mock_metric  # type: ignore

    def record_api_request(self, method: str, endpoint: str, status_code: int, duration: float) -> None:
        """Registra uma requisição à API."""
        if not self.enabled:
            return

        self.api_requests_total.labels(method=method, endpoint=endpoint, status_code=str(status_code)).inc()

        self.api_request_duration.labels(method=method, endpoint=endpoint).observe(duration)

    def record_glpi_request(self, endpoint: str, status_code: int, duration: float) -> None:
        """Registra uma requisição ao GLPI externo."""
        if not self.enabled:
            return

        self.glpi_requests_total.labels(endpoint=endpoint, status_code=str(status_code)).inc()

        self.glpi_request_duration.labels(endpoint=endpoint).observe(duration)

    def record_metrics_processing(self, query_type: str, duration: float) -> None:
        """Registra processamento de métricas."""
        if not self.enabled:
            return

        self.metrics_processing_duration.labels(query_type=query_type).observe(duration)

    def record_cache_hit(self, query_type: str) -> None:
        """Registra um cache hit."""
        if not self.enabled:
            return

        self.metrics_cache_hits.labels(query_type=query_type).inc()

    def record_cache_miss(self, query_type: str) -> None:
        """Registra um cache miss."""
        if not self.enabled:
            return

        self.metrics_cache_misses.labels(query_type=query_type).inc()

    def update_tickets_metrics(self, tickets_by_status: Dict[str, Dict[str, int]]) -> None:
        """Atualiza métricas de tickets."""
        if not self.enabled:
            return

        for level, statuses in tickets_by_status.items():
            for status, count in statuses.items():
                self.tickets_total.labels(status=status, level=level).set(count)

    def update_technicians_metrics(self, technicians_by_level: Dict[str, int]) -> None:
        """Atualiza métricas de técnicos."""
        if not self.enabled:
            return

        for level, count in technicians_by_level.items():
            self.technicians_total.labels(level=level).set(count)

    def record_error(self, error_type: str, component: str) -> None:
        """Registra um erro."""
        if not self.enabled:
            return

        self.errors_total.labels(error_type=error_type, component=component).inc()

    def record_alert(self, alert_type: str, severity: str) -> None:
        """Registra um alerta."""
        if not self.enabled:
            return

        self.alerts_total.labels(alert_type=alert_type, severity=severity).inc()

    def set_active_connections(self, count: int) -> None:
        """Define o número de conexões ativas."""
        if not self.enabled:
            return

        self.active_connections.set(count)

    @contextmanager
    def time_operation(self, operation_name: str, labels: Optional[Dict[str, str]] = None) -> Any:
        """Context manager para medir duração de operações."""
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            if self.enabled and hasattr(self, f"{operation_name}_duration"):
                metric = getattr(self, f"{operation_name}_duration")
                if labels:
                    metric.labels(**labels).observe(duration)
                else:
                    metric.observe(duration)

    def get_metrics_text(self) -> str:
        """Retorna métricas em formato texto Prometheus."""
        if not self.enabled:
            return "# Prometheus metrics disabled\n"

        return generate_latest(self.registry).decode("utf-8")

    def push_to_gateway(self, gateway_url: str, job_name: str = "glpi_dashboard") -> None:
        """Envia métricas para Prometheus Gateway."""
        if not self.enabled:
            logger.warning("Tentativa de push para gateway com Prometheus desabilitado")
            return

        try:
            push_to_gateway(gateway_url, job=job_name, registry=self.registry)
            logger.info(f"Métricas enviadas para gateway: {gateway_url}")
        except Exception as e:
            logger.error(f"Erro ao enviar métricas para gateway: {e}")
            self.record_error("push_gateway_error", "prometheus")


# Instância global
prometheus_metrics = PrometheusMetrics()


# Decoradores para instrumentação automática
def monitor_api_endpoint(endpoint_name: str) -> Any:
    """Decorador para monitorar endpoints da API."""

    def decorator(func: Any) -> Any:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            method = getattr(kwargs.get("request"), "method", "GET")
            status_code = 200

            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status_code = getattr(e, "status_code", 500)
                prometheus_metrics.record_error("api_error", endpoint_name)
                raise
            finally:
                duration = time.time() - start_time
                prometheus_metrics.record_api_request(
                    method=method,
                    endpoint=endpoint_name,
                    status_code=status_code,
                    duration=duration,
                )

                # Alerta se resposta for muito lenta (>300ms)
                if duration > 0.3:
                    prometheus_metrics.record_alert("slow_response", "warning")
                    logger.warning(
                        f"Resposta lenta detectada: {endpoint_name} - {duration:.3f}s",
                        extra={"duration": duration, "endpoint": endpoint_name},
                    )

        return wrapper

    return decorator


def monitor_glpi_request(endpoint_name: str) -> Any:
    """Decorador para monitorar requisições ao GLPI."""

    def decorator(func: Any) -> Any:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            status_code = 200

            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status_code = getattr(e, "status_code", 500)
                prometheus_metrics.record_error("glpi_error", endpoint_name)
                raise
            finally:
                duration = time.time() - start_time
                prometheus_metrics.record_glpi_request(endpoint=endpoint_name, status_code=status_code, duration=duration)

        return wrapper

    return decorator


def monitor_metrics_query(query_type: str) -> Any:
    """Decorador para monitorar queries de métricas."""

    def decorator(func: Any) -> Any:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()

            try:
                result = func(*args, **kwargs)

                # Verificar se resultado tem dados zerados (possível problema)
                if hasattr(result, "total") and result.total == 0:
                    prometheus_metrics.record_alert("zero_metrics", "warning")
                    logger.warning(
                        f"Métricas zeradas detectadas: {query_type}",
                        extra={"query_type": query_type, "result": str(result)},
                    )

                return result
            except Exception as e:
                prometheus_metrics.record_error("metrics_query_error", query_type)
                raise
            finally:
                duration = time.time() - start_time
                prometheus_metrics.record_metrics_processing(query_type, duration)

        return wrapper

    return decorator
