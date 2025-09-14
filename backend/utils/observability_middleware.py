"""Middleware de observabilidade para Flask.

Este módulo implementa middleware para instrumentação automática de rotas Flask
com métricas Prometheus, logs estruturados e alertas.
"""

import logging
import time
from functools import wraps
from typing import Any, Dict, Optional

from flask import Flask, g, jsonify, request
from werkzeug.exceptions import HTTPException

from .alerting_system import alert_manager, record_api_response_time
from .prometheus_metrics import prometheus_metrics
from .structured_logging import StructuredLogger, api_logger, correlation_id_var, log_api_request, SensitiveDataRedactor


class ObservabilityMiddleware:
    """Middleware de observabilidade para Flask."""

    def __init__(self, app: Optional[Flask] = None):
        self.app = app
        self.logger = StructuredLogger("observability.middleware")

        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask):
        """Inicializa o middleware com a aplicação Flask."""
        self.app = app

        # Registrar handlers de request
        app.before_request(self._before_request)
        app.after_request(self._after_request)
        app.teardown_appcontext(self._teardown_request)

        # Registrar handler de erro
        app.errorhandler(Exception)(self._handle_exception)

        # Adicionar rota de métricas
        app.add_url_rule("/metrics", "metrics", self._metrics_endpoint, methods=["GET"])
        app.add_url_rule("/health", "health", self._health_endpoint, methods=["GET"])
        app.add_url_rule("/alerts", "alerts", self._alerts_endpoint, methods=["GET"])

        self.logger.logger.info("Middleware de observabilidade inicializado")

    def _before_request(self):
        """Executado antes de cada request com filtragem de dados sensíveis."""
        # Gerar correlation ID
        correlation_id = self._get_or_generate_correlation_id()
        correlation_id_var.set(correlation_id)

        # Armazenar dados do request no contexto (com redação)
        g.start_time = time.time()
        g.correlation_id = correlation_id

        # Filtrar headers sensíveis
        filtered_headers = self._filter_request_headers()

        # Filtrar query parameters sensíveis
        filtered_query_params = self._filter_query_parameters()

        # Filtrar dados do corpo da requisição se aplicável
        filtered_form_data = self._filter_request_body()

        g.request_data = {
            "method": request.method,
            "endpoint": request.endpoint or "unknown",
            "path": SensitiveDataRedactor.redact_url(request.path),
            "remote_addr": request.remote_addr,
            "user_agent": request.headers.get("User-Agent", "unknown"),
            "headers": filtered_headers,
            "query_params": filtered_query_params,
            "form_data": filtered_form_data,
            "content_type": request.content_type,
            "content_length": request.content_length,
        }

        # Log início do request (dados já filtrados)
        api_logger.log_operation_start(
            "api_request",
            correlation_id=correlation_id,
            method=request.method,
            endpoint=request.endpoint,
            path=SensitiveDataRedactor.redact_url(request.path),
            remote_addr=request.remote_addr,
            headers_count=len(filtered_headers),
            has_query_params=len(filtered_query_params) > 0,
            has_form_data=len(filtered_form_data) > 0,
        )

    def _after_request(self, response):
        """Executado após cada request com filtragem de dados sensíveis."""
        if not hasattr(g, "start_time"):
            return response

        # Calcular duração
        duration = time.time() - g.start_time

        # Obter dados do request
        request_data = getattr(g, "request_data", {})
        correlation_id = getattr(g, "correlation_id", "unknown")

        # Filtrar headers de resposta sensíveis
        filtered_response_headers = self._filter_response_headers(response.headers)

        # Filtrar dados de resposta se necessário
        filtered_response_data = self._filter_response_data(response)

        # Registrar métricas
        prometheus_metrics.record_api_request(
            method=request_data.get("method", "unknown"),
            endpoint=request_data.get("endpoint", "unknown"),
            status_code=response.status_code,
            duration=duration,
        )

        # Registrar no sistema de alertas
        record_api_response_time(duration, endpoint=request_data.get("endpoint", "unknown"))

        # Log estruturado com dados filtrados
        log_api_request(
            method=request_data.get("method", "unknown"),
            endpoint=request_data.get("endpoint", "unknown"),
            status_code=response.status_code,
            duration=duration,
            correlation_id=correlation_id,
            remote_addr=request_data.get("remote_addr"),
            user_agent=request_data.get("user_agent"),
            request_headers_filtered=len(request_data.get("headers", {})),
            response_headers_filtered=len(filtered_response_headers),
            response_content_type=response.content_type,
        )

        # Log fim do request com dados filtrados
        api_logger.log_operation_end(
            "api_request",
            success=200 <= response.status_code < 400,
            status_code=response.status_code,
            duration=duration,
            response_size=len(response.get_data()),
            response_headers_count=len(filtered_response_headers),
            response_content_type=response.content_type,
            request_summary={
                "headers_count": len(request_data.get("headers", {})),
                "query_params_count": len(request_data.get("query_params", {})),
                "has_form_data": len(request_data.get("form_data", {})) > 0,
            },
        )

        # Adicionar headers de observabilidade (não sensíveis)
        response.headers["X-Correlation-ID"] = correlation_id
        response.headers["X-Response-Time"] = f"{duration:.3f}s"
        
        # Adicionar headers de segurança
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"

        return response

    def _teardown_request(self, exception=None):
        """Executado no teardown do request."""
        # Limpar contexto
        correlation_id_var.set(None)

    def _handle_exception(self, error):
        """Handler global de exceções."""
        correlation_id = getattr(g, "correlation_id", "unknown")
        request_data = getattr(g, "request_data", {})

        # Determinar status code
        if isinstance(error, HTTPException):
            status_code = error.code
            error_type = "http_error"
        else:
            status_code = 500
            error_type = "internal_error"

        # Registrar erro nas métricas
        prometheus_metrics.record_error(error_type, request_data.get("endpoint", "unknown"))

        # Log estruturado do erro com redação
        api_logger.log_error_with_context(
            error_type,
            f"Erro na API: {SensitiveDataRedactor.redact_exception_message(str(error))}",
            exception=error,
            correlation_id=correlation_id,
            endpoint=request_data.get("endpoint"),
            method=request_data.get("method"),
            status_code=status_code,
            request_path=SensitiveDataRedactor.redact_url(request_data.get("path", "")),
            headers_count=len(request_data.get("headers", {})),
        )

        # Retornar resposta de erro estruturada (com redação)
        error_response = {
            "error": {
                "type": error_type,
                "message": SensitiveDataRedactor.redact_exception_message(str(error)),
                "correlation_id": correlation_id,
                "timestamp": time.time(),
            }
        }

        return jsonify(error_response), status_code

    def _get_or_generate_correlation_id(self) -> str:
        """Obtém correlation ID do header ou gera um novo."""
        # Tentar obter do header
        correlation_id = request.headers.get("X-Correlation-ID")

        if not correlation_id:
            # Gerar novo
            correlation_id = api_logger.generate_correlation_id()

        return correlation_id

    def _filter_request_headers(self) -> Dict[str, str]:
        """Filtra headers sensíveis da requisição."""
        if not hasattr(request, "headers"):
            return {}

        headers_dict = dict(request.headers)
        return SensitiveDataRedactor.redact_http_headers(headers_dict)

    def _filter_query_parameters(self) -> Dict[str, Any]:
        """Filtra parâmetros de query sensíveis."""
        if not hasattr(request, "args"):
            return {}

        query_params = dict(request.args)
        return SensitiveDataRedactor.redact_query_params(query_params)

    def _filter_request_body(self) -> Dict[str, Any]:
        """Filtra dados do corpo da requisição sensíveis."""
        filtered_data = {}

        try:
            # Verificar form data
            if hasattr(request, "form") and request.form:
                form_data = dict(request.form)
                filtered_data["form"] = SensitiveDataRedactor.redact_data(form_data)

            # Verificar JSON data
            if hasattr(request, "json") and request.json:
                json_data = request.json
                filtered_data["json"] = SensitiveDataRedactor.redact_data(json_data)

            # Verificar files
            if hasattr(request, "files") and request.files:
                files_info = {
                    name: {"filename": file.filename, "content_type": file.content_type}
                    for name, file in request.files.items()
                }
                filtered_data["files"] = files_info

        except Exception as e:
            # Em caso de erro, registrar sem expor dados sensíveis
            filtered_data = {"error": f"Failed to parse request body: {type(e).__name__}"}

        return filtered_data

    def _filter_response_headers(self, headers) -> Dict[str, str]:
        """Filtra headers sensíveis da resposta."""
        if not headers:
            return {}

        headers_dict = dict(headers)
        return SensitiveDataRedactor.redact_http_headers(headers_dict)

    def _filter_response_data(self, response) -> Dict[str, Any]:
        """Filtra dados sensíveis da resposta."""
        filtered_data = {
            "content_type": response.content_type,
            "content_length": len(response.get_data()) if response.get_data() else 0,
            "status_code": response.status_code,
        }

        # Não logar o conteúdo da resposta por padrão para evitar vazamentos
        # Se necessário para debugging, pode ser habilitado com configuração específica
        try:
            if response.content_type and "application/json" in response.content_type:
                # Para responses JSON pequenas, podemos logar um resumo filtrado
                data = response.get_json()
                if data and len(str(data)) < 1000:  # Limit size
                    filtered_data["json_summary"] = {
                        "keys": list(data.keys()) if isinstance(data, dict) else "non_dict",
                        "size": len(str(data)),
                    }
        except Exception:
            # Falhar silenciosamente para não afetar a resposta
            pass

        return filtered_data

    def _metrics_endpoint(self):
        """Endpoint para métricas Prometheus."""
        try:
            metrics_text = prometheus_metrics.get_metrics_text()
            return metrics_text, 200, {"Content-Type": "text/plain; charset=utf-8"}
        except Exception as e:
            self.logger.log_error_with_context(
                "metrics_endpoint_error",
                f"Erro ao gerar métricas: {str(e)}",
                exception=e,
            )
            return "Error generating metrics", 500

    def _health_endpoint(self):
        """Endpoint de health check."""
        try:
            # Verificar saúde básica do sistema
            health_data = {
                "status": "healthy",
                "timestamp": time.time(),
                "version": "1.0.0",
                "checks": {
                    "prometheus_metrics": prometheus_metrics.enabled,
                    "alert_manager": len(alert_manager.rules) > 0,
                    "active_alerts": len(alert_manager.get_active_alerts()),
                },
            }

            # Verificar se há alertas críticos
            critical_alerts = [alert for alert in alert_manager.get_active_alerts() if alert.severity.value == "critical"]

            if critical_alerts:
                health_data["status"] = "degraded"
                health_data["critical_alerts"] = len(critical_alerts)

            status_code = 200 if health_data["status"] == "healthy" else 503

            return jsonify(health_data), status_code

        except Exception as e:
            self.logger.log_error_with_context("health_endpoint_error", f"Erro no health check: {str(e)}", exception=e)
            return (
                jsonify({"status": "unhealthy", "error": str(e), "timestamp": time.time()}),
                500,
            )

    def _alerts_endpoint(self):
        """Endpoint para consultar alertas."""
        try:
            # Obter parâmetros de query
            status_filter = request.args.get("status", "active")
            limit = int(request.args.get("limit", 50))

            if status_filter == "active":
                alerts = alert_manager.get_active_alerts()
            elif status_filter == "history":
                alerts = alert_manager.get_alert_history(limit)
            else:
                alerts = alert_manager.get_active_alerts()

            # Converter para dicionários
            alerts_data = [alert.to_dict() for alert in alerts]

            # Estrutura esperada pelos testes
            active_alerts = alert_manager.get_active_alerts()
            alert_history = alert_manager.get_alert_history(limit)

            response_data = {
                "active_alerts": [alert.to_dict() for alert in active_alerts],
                "alert_history": [alert.to_dict() for alert in alert_history],
                "summary": alert_manager.get_alert_summary(),
                "timestamp": time.time(),
            }

            return jsonify(response_data), 200

        except Exception as e:
            self.logger.log_error_with_context(
                "alerts_endpoint_error",
                f"Erro ao consultar alertas: {str(e)}",
                exception=e,
            )
            return jsonify({"error": str(e), "timestamp": time.time()}), 500


# Decorador para instrumentação manual de funções
def with_observability_instrumentation(operation_name: str, component: str = "api"):
    """Decorador para instrumentação manual com observabilidade completa."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = StructuredLogger(f"observability.{component}")
            correlation_id = correlation_id_var.get() or logger.generate_correlation_id()

            # Configurar contexto
            correlation_id_var.set(correlation_id)

            start_time = time.time()

            # Log início
            logger.log_operation_start(
                operation_name,
                correlation_id=correlation_id,
                component=component,
                function=func.__name__,
            )

            try:
                result = func(*args, **kwargs)

                duration = time.time() - start_time

                # Log sucesso
                logger.log_operation_end(
                    operation_name,
                    success=True,
                    duration=duration,
                    result_type=type(result).__name__,
                )

                # Registrar métrica de performance
                logger.log_performance_metric(
                    f"{operation_name}_duration",
                    duration,
                    "seconds",
                    component=component,
                )

                return result

            except Exception as e:
                duration = time.time() - start_time

                # Log erro
                logger.log_operation_end(operation_name, success=False, duration=duration, error=str(e))

                logger.log_error_with_context(
                    f"{operation_name}_error",
                    f"Erro na operação {operation_name}: {str(e)}",
                    exception=e,
                    component=component,
                    function=func.__name__,
                )

                # Registrar erro nas métricas
                prometheus_metrics.record_error(f"{operation_name}_error", component)

                raise

        return wrapper

    return decorator


# Função para configurar observabilidade em uma aplicação Flask
def setup_observability(app: Flask, config: Optional[Dict[str, Any]] = None) -> ObservabilityMiddleware:
    """Configura observabilidade completa em uma aplicação Flask."""
    config = config or {}

    # Configurar logging
    if config.get("structured_logging", True):
        # Configurar handler JSON para o logger root da aplicação
        from .structured_logging import JSONFormatter

        handler = logging.StreamHandler()
        handler.setFormatter(JSONFormatter())

        app.logger.handlers.clear()
        app.logger.addHandler(handler)
        app.logger.setLevel(logging.INFO)

    # Inicializar middleware
    middleware = ObservabilityMiddleware(app)

    # Configurar Prometheus Gateway se especificado
    gateway_url = config.get("prometheus_gateway_url")
    if gateway_url:
        import atexit

        def push_metrics_on_exit():
            try:
                prometheus_metrics.push_to_gateway(gateway_url)
            except Exception as e:
                app.logger.error(f"Erro ao enviar métricas no shutdown: {e}")

        atexit.register(push_metrics_on_exit)

    app.logger.info("Observabilidade configurada com sucesso")

    return middleware


# Instância global para uso direto
observability_middleware = ObservabilityMiddleware()
