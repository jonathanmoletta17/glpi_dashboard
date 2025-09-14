import logging
import time
import uuid
from datetime import datetime
from functools import wraps
from typing import Any, Dict, Callable, List


class ObservabilityLogger:
    """Utilitário para instrumentação de logs com correlationId e alertas"""

    def __init__(self, logger_name: str = "observability"):
        self.logger = logging.getLogger(logger_name)

    @staticmethod
    def generate_correlation_id() -> str:
        """Gera um correlationId único para rastreabilidade"""
        return str(uuid.uuid4())

    def log_pipeline_start(self, correlation_id: str, operation: str, **params: Any) -> None:
        """Log do início de uma operação do pipeline"""
        sanitized_params = self._sanitize_params(params)
        self.logger.info(
            f"[{correlation_id}] Pipeline iniciado - Operação: {operation}",
            extra={
                "correlation_id": correlation_id,
                "operation": operation,
                "params": sanitized_params,
                "log_timestamp": datetime.utcnow().isoformat(),
            },
        )

    def log_pipeline_step(self, correlation_id: str, step: str, data: Dict[str, Any]) -> None:
        """Log de uma etapa específica do pipeline"""
        sanitized_data = self._sanitize_params(data)
        self.logger.debug(
            f"[{correlation_id}] Etapa: {step}",
            extra={
                "correlation_id": correlation_id,
                "step": step,
                "data": sanitized_data,
                "log_timestamp": datetime.utcnow().isoformat(),
            },
        )

    def log_pipeline_end(self, correlation_id: str, operation: str, result_count: int, duration_ms: float) -> None:
        """Log do fim de uma operação do pipeline"""
        self.logger.info(
            f"[{correlation_id}] Pipeline concluído - Operação: {operation}, Resultados: {result_count}, Duração: {duration_ms:.2f}ms",
            extra={
                "correlation_id": correlation_id,
                "operation": operation,
                "result_count": result_count,
                "duration_ms": duration_ms,
                "log_timestamp": datetime.utcnow().isoformat(),
            },
        )

    def emit_warning(self, correlation_id: str, warning_type: str, message: str, **context: Any) -> None:
        """Emite um warning com contexto"""
        sanitized_context = self._sanitize_params(context)
        self.logger.warning(
            f"[{correlation_id}] ALERTA - {warning_type}: {message}",
            extra={
                "correlation_id": correlation_id,
                "warning_type": warning_type,
                "alert_message": message,
                "context": sanitized_context,
                "log_timestamp": datetime.utcnow().isoformat(),
            },
        )

    def check_technician_cardinality(self, correlation_id: str, technician_count: int, threshold: int = 18) -> None:
        """Verifica se a cardinalidade de técnicos excede o limite"""
        if technician_count > threshold:
            self.emit_warning(
                correlation_id,
                "HIGH_TECHNICIAN_CARDINALITY",
                f"Cardinalidade de técnicos ({technician_count}) excede o limite ({threshold})",
                technician_count=technician_count,
                threshold=threshold,
            )

    def check_technician_names(self, correlation_id: str, technicians: List[Any]) -> None:
        """Verifica nomes de técnicos suspeitos"""
        suspicious_names = []
        unresolved_ids = []

        for tech in technicians:
            # Handle both dict and Pydantic model formats
            if isinstance(tech, dict):
                # Dictionary format
                name = tech.get("name", "")
                tech_id = tech.get("id")
            else:
                # Pydantic model (TechnicianRanking)
                name = getattr(tech, "name", "")
                tech_id = getattr(tech, "id", None)

            # Verificar nomes contendo "TECNICO"
            if "TECNICO" in name.upper():
                suspicious_names.append({"id": tech_id, "name": name})

            # Verificar IDs sem nome resolvido
            if not name or name.strip() == "" or name.isdigit():
                unresolved_ids.append({"id": tech_id, "name": name})

        if suspicious_names:
            self.emit_warning(
                correlation_id,
                "SUSPICIOUS_TECHNICIAN_NAMES",
                f"Encontrados {len(suspicious_names)} técnicos com nomes suspeitos contendo 'TECNICO'",
                suspicious_names=suspicious_names,
            )

        if unresolved_ids:
            self.emit_warning(
                correlation_id,
                "UNRESOLVED_TECHNICIAN_IDS",
                f"Encontrados {len(unresolved_ids)} IDs de técnicos sem nome resolvido",
                unresolved_ids=unresolved_ids,
            )

    def check_zero_totals(self, correlation_id: str, technicians: List[Any], filters_applied: Dict[str, Any]) -> None:
        """Verifica se há totais zerados após filtros"""
        zero_total_count = 0
        for tech in technicians:
            # Handle both dict and Pydantic model formats
            if isinstance(tech, dict):
                # Dictionary format
                total = tech.get("total", 0)
            else:
                # Pydantic model (TechnicianRanking)
                total = getattr(tech, "total", 0)

            if total == 0:
                zero_total_count += 1

        if zero_total_count > 0:
            self.emit_warning(
                correlation_id,
                "ZERO_TOTALS_AFTER_FILTER",
                f"Encontrados {zero_total_count} técnicos com total zerado após aplicação de filtros",
                zero_total_count=zero_total_count,
                total_technicians=len(technicians),
                filters_applied=filters_applied,
            )

    def _sanitize_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Remove ou anonimiza dados sensíveis dos parâmetros"""
        sanitized = {}

        for key, value in params.items():
            # Anonimizar campos que podem conter PII
            if key.lower() in ["name", "email", "username", "user_name"]:
                if isinstance(value, str) and value:
                    # Manter apenas as primeiras 2 letras + ***
                    sanitized[key] = value[:2] + "***" if len(value) > 2 else "***"
                else:
                    sanitized[key] = value
            elif key.lower() in ["password", "token", "secret", "key"]:
                sanitized[key] = "[REDACTED]"
            else:
                sanitized[key] = value

        return sanitized


def with_observability(operation_name: str) -> Callable:
    """Decorator para instrumentar funções com observabilidade"""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            obs_logger = ObservabilityLogger()
            correlation_id = obs_logger.generate_correlation_id()
            start_time = time.time()

            # Log início da operação
            obs_logger.log_pipeline_start(correlation_id, operation_name, **kwargs)

            try:
                # Adicionar correlation_id aos kwargs se a função aceitar
                if "correlation_id" in func.__code__.co_varnames:
                    kwargs["correlation_id"] = correlation_id

                result = func(*args, **kwargs)

                # Log fim da operação
                duration_ms = (time.time() - start_time) * 1000
                result_count = len(result) if isinstance(result, (list, tuple)) else 1
                obs_logger.log_pipeline_end(correlation_id, operation_name, result_count, duration_ms)

                return result

            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                obs_logger.logger.error(
                    f"[{correlation_id}] Erro na operação {operation_name}: {str(e)}",
                    extra={
                        "correlation_id": correlation_id,
                        "operation": operation_name,
                        "error": str(e),
                        "duration_ms": duration_ms,
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                    exc_info=True,
                )
                raise

        return wrapper

    return decorator
