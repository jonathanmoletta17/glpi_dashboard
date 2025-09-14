# -*- coding: utf-8 -*-
"""
Módulo de logging estruturado para o GLPI Dashboard.
Implementa logging em formato JSON com timestamp, nível, nome do logger e mensagem.
"""

import json
import logging
import time
import traceback
from datetime import datetime, timezone
from functools import wraps
from typing import Any, Callable, Optional


class JSONFormatter(logging.Formatter):
    """
    Formatador personalizado para logs em formato JSON.
    """

    def __init__(self, include_extra_fields: bool = True):
        super().__init__()
        self.include_extra_fields = include_extra_fields

    def format(self, record: logging.LogRecord) -> str:
        """
        Formata o registro de log em JSON.

        Args:
            record: Registro de log do Python logging

        Returns:
            String JSON formatada
        """
        try:
            # Campos básicos obrigatórios
            log_entry = {
                "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
                "level": record.levelname or "UNKNOWN",
                "logger_name": record.name or "unknown",
                "message": self._safe_get_message(record),
            }

            # Adicionar informações de contexto se disponíveis
            if hasattr(record, "module") and record.module:
                log_entry["module"] = str(record.module)

            if hasattr(record, "funcName") and record.funcName:
                log_entry["function"] = str(record.funcName)

            if hasattr(record, "lineno") and record.lineno:
                log_entry["line_number"] = str(record.lineno)

            # Adicionar informações de exceção se houver
            if record.exc_info:
                try:
                    exception_info = {
                        "type": record.exc_info[0].__name__ if record.exc_info[0] else "Unknown",
                        "message": str(record.exc_info[1]) if record.exc_info[1] else "No message",
                        "traceback": traceback.format_exception(*record.exc_info),
                    }
                    log_entry["exception"] = json.dumps(exception_info)
                except Exception:
                    log_entry["exception"] = json.dumps({"error": "Failed to format exception info"})

            # Adicionar campos extras personalizados
            if self.include_extra_fields:
                extra_fields = {}
                excluded_keys = {
                    "name",
                    "msg",
                    "args",
                    "levelname",
                    "levelno",
                    "pathname",
                    "filename",
                    "module",
                    "lineno",
                    "funcName",
                    "created",
                    "msecs",
                    "relativeCreated",
                    "thread",
                    "threadName",
                    "processName",
                    "process",
                    "exc_info",
                    "exc_text",
                    "stack_info",
                    "getMessage",
                }

                for key, value in record.__dict__.items():
                    if key not in excluded_keys:
                        try:
                            # Tentar serializar o valor para JSON
                            json.dumps(value)
                            extra_fields[key] = value
                        except (TypeError, ValueError):
                            # Se não for serializável, converter para string
                            try:
                                extra_fields[key] = str(value)
                            except Exception:
                                extra_fields[key] = "<unserializable>"

                if extra_fields:
                    log_entry["extra"] = json.dumps(extra_fields)

            return json.dumps(log_entry, ensure_ascii=False, default=str)

        except Exception as e:
            # Fallback para formato básico em caso de erro
            fallback_entry = {
                "timestamp": datetime.now(tz=timezone.utc).isoformat(),
                "level": "ERROR",
                "logger_name": "JSONFormatter",
                "message": f"Failed to format log record: {str(e)}",
                "original_message": getattr(record, "msg", "Unknown") if hasattr(record, "msg") else "Unknown",
            }
            return json.dumps(fallback_entry, ensure_ascii=False, default=str)

    def _safe_get_message(self, record: logging.LogRecord) -> str:
        """
        Obtém a mensagem do log de forma segura.

        Args:
            record: Registro de log

        Returns:
            Mensagem formatada ou fallback
        """
        try:
            return record.getMessage()
        except Exception:
            try:
                return str(record.msg) if hasattr(record, "msg") else "No message"
            except Exception:
                return "Failed to get message"


class StructuredLogger:
    """
    Logger estruturado para o GLPI Dashboard.
    Fornece métodos convenientes para logging com contexto adicional.
    """

    def __init__(self, name: str, level: str = "INFO"):
        """
        Inicializa o logger estruturado.

        Args:
            name: Nome do logger
            level: Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        try:
            # Validar entrada
            if not name or not isinstance(name, str):
                name = "unknown_logger"

            if not level or not isinstance(level, str):
                level = "INFO"

            # Validar nível de log
            valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
            level_upper = level.upper()
            if level_upper not in valid_levels:
                level_upper = "INFO"

            self.logger = logging.getLogger(name)
            self.logger.setLevel(getattr(logging, level_upper))

        except Exception:
            # Fallback para configuração básica
            self.logger = logging.getLogger("fallback_logger")
            self.logger.setLevel(logging.INFO)

            # Evitar duplicação de handlers
            if not self.logger.handlers:
                try:
                    handler = logging.StreamHandler()
                    handler.setFormatter(JSONFormatter())
                    self.logger.addHandler(handler)
                except Exception:
                    # Fallback para handler básico
                    basic_handler = logging.StreamHandler()
                    basic_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
                    self.logger.addHandler(basic_handler)

            # Evitar propagação para o logger raiz
            self.logger.propagate = False

        except Exception:
            # Configuração de emergência
            self.logger = logging.getLogger("emergency_logger")
            self.logger.setLevel(logging.INFO)
            if not self.logger.handlers:
                emergency_handler = logging.StreamHandler()
                emergency_handler.setFormatter(logging.Formatter("%(asctime)s - EMERGENCY - %(message)s"))
                self.logger.addHandler(emergency_handler)
            self.logger.propagate = False

    def _log_with_context(self, level: str, message: str, **kwargs: Any) -> None:
        """
        Registra uma mensagem com contexto adicional.

        Args:
            level: Nível do log
            message: Mensagem do log
            **kwargs: Campos adicionais para o contexto
        """
        try:
            # Garantir que message seja string
            message = str(message) if message is not None else "No message"

            # Sanitizar kwargs
            safe_kwargs = {}
            for key, value in kwargs.items():
                try:
                    # Verificar se a chave é válida
                    if isinstance(key, str) and key.isidentifier():
                        safe_kwargs[key] = value
                except Exception:
                    pass

            extra = safe_kwargs.copy()
            log_method = getattr(self.logger, level.lower(), None)
            if log_method:
                log_method(message, extra=extra)
            else:
                self.logger.info(message, extra=extra)

        except Exception as e:
            # Fallback para log básico
            try:
                self.logger.error(f"Failed to log message: {str(e)}. Original message: {message}")
            except Exception:
                # Último recurso
                print(f"CRITICAL: Failed to log message: {message}")

    def debug(self, message: str, **kwargs: Any) -> None:
        """Registra mensagem de debug."""
        self._log_with_context("DEBUG", message, **kwargs)

    def info(self, message: str, **kwargs: Any) -> None:
        """Registra mensagem informativa."""
        self._log_with_context("INFO", message, **kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        """Registra mensagem de aviso."""
        self._log_with_context("WARNING", message, **kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        """Registra mensagem de erro."""
        self._log_with_context("ERROR", message, **kwargs)

    def critical(self, message: str, **kwargs: Any) -> None:
        """Registra mensagem crítica."""
        self._log_with_context("CRITICAL", message, **kwargs)


def log_api_call(logger: StructuredLogger) -> Callable:
    """
    Decorador para logar chamadas de API com parâmetros e tempo de execução.

    Args:
        logger: Instância do StructuredLogger
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                start_time = time.time()
                function_name = getattr(func, "__name__", "unknown_function")

                # Preparar parâmetros para log (remover dados sensíveis)
                safe_args = []
                try:
                    for arg in args[1:]:  # Pular self
                        if isinstance(arg, str) and len(arg) > 100:
                            safe_args.append(f"{arg[:100]}...")
                        else:
                            try:
                                # Tentar serializar para verificar se é seguro
                                json.dumps(arg, default=str)
                                safe_args.append(arg)
                            except Exception:
                                safe_args.append(str(arg)[:100] if str(arg) else "<empty>")
                except Exception:
                    safe_args = ["<failed_to_process_args>"]

                safe_kwargs = {}
                try:
                    sensitive_keys = {
                        "password",
                        "token",
                        "secret",
                        "key",
                        "auth",
                        "credential",
                    }
                    for key, value in kwargs.items():
                        try:
                            if any(sensitive in str(key).lower() for sensitive in sensitive_keys):
                                safe_kwargs[key] = "***REDACTED***"
                            elif isinstance(value, str) and len(value) > 100:
                                safe_kwargs[key] = f"{value[:100]}..."
                            else:
                                # Tentar serializar para verificar se é seguro
                                json.dumps(value, default=str)
                                safe_kwargs[key] = value
                        except Exception:
                            safe_kwargs[key] = str(value)[:100] if str(value) else "<empty>"
                except Exception:
                    safe_kwargs = {"error": "failed_to_process_kwargs"}

                try:
                    logger.info(
                        f"Iniciando chamada de API: {function_name}",
                        api_function=function_name,
                        parameters={"args": safe_args, "kwargs": safe_kwargs},
                        event_type="api_call_start",
                    )
                except Exception:
                    # Fallback para log básico se o log estruturado falhar
                    print(f"Starting API call: {function_name}")

                try:
                    result = func(*args, **kwargs)
                    execution_time = time.time() - start_time

                    try:
                        logger.info(
                            f"Chamada de API concluída: {function_name}",
                            api_function=function_name,
                            execution_time_seconds=round(execution_time, 4),
                            success=True,
                            event_type="api_call_success",
                        )
                    except Exception:
                        print(f"API call completed: {function_name} in {execution_time:.4f}s")

                    return result

                except Exception as e:
                    execution_time = time.time() - start_time

                    try:
                        logger.error(
                            f"Erro na chamada de API: {function_name}",
                            api_function=function_name,
                            execution_time_seconds=round(execution_time, 4),
                            error_type=type(e).__name__,
                            error_message=str(e),
                            success=False,
                            event_type="api_call_error",
                            exc_info=True,
                        )
                    except Exception:
                        print(f"API call failed: {function_name} - {str(e)}")

                    raise

            except Exception as outer_e:
                # Fallback para execução sem logging em caso de erro crítico
                try:
                    print(f"Critical error in log_api_call decorator for {function_name}: {str(outer_e)}")
                    return func(*args, **kwargs)
                except Exception:
                    raise outer_e

        return wrapper

    return decorator


def log_performance(logger: StructuredLogger, threshold_seconds: float = 1.0) -> Callable:
    """
    Decorador para logar performance de funções.

    Args:
        logger: Instância do StructuredLogger
        threshold_seconds: Limite em segundos para considerar como lento
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                # Validar threshold_seconds
                if not isinstance(threshold_seconds, (int, float)) or threshold_seconds <= 0:
                    threshold_seconds_safe = 1.0
                else:
                    threshold_seconds_safe = float(threshold_seconds)

                start_time = time.time()
                function_name = getattr(func, "__name__", "unknown_function")

                try:
                    result = func(*args, **kwargs)
                    execution_time = time.time() - start_time

                    try:
                        if execution_time > threshold_seconds_safe:
                            logger.warning(
                                f"Função lenta detectada: {function_name}",
                                function=function_name,
                                execution_time_seconds=round(execution_time, 4),
                                threshold_seconds=threshold_seconds_safe,
                                event_type="slow_function",
                            )
                        else:
                            logger.debug(
                                f"Performance da função: {function_name}",
                                function=function_name,
                                execution_time_seconds=round(execution_time, 4),
                                event_type="function_performance",
                            )
                    except Exception:
                        # Fallback para log básico
                        if execution_time > threshold_seconds_safe:
                            print(f"Slow function detected: {function_name} took {execution_time:.4f}s")

                    return result

                except Exception as e:
                    execution_time = time.time() - start_time

                    try:
                        logger.error(
                            f"Erro na função: {function_name}",
                            function=function_name,
                            execution_time_seconds=round(execution_time, 4),
                            error_type=type(e).__name__,
                            error_message=str(e),
                            event_type="function_error",
                            exc_info=True,
                        )
                    except Exception:
                        print(f"Function error: {function_name} - {str(e)}")

                    raise

            except Exception as outer_e:
                # Fallback para execução sem logging em caso de erro crítico
                try:
                    print(f"Critical error in log_performance decorator for {function_name}: {str(outer_e)}")
                    return func(*args, **kwargs)
                except Exception:
                    raise outer_e

        return wrapper

    return decorator


def log_api_response(
    logger: StructuredLogger,
    response_data: Any,
    status_code: Optional[int] = None,
    response_time: Optional[float] = None,
) -> None:
    """
    Loga resposta de API de forma estruturada.

    Args:
        logger: Instância do StructuredLogger
        response_data: Dados da resposta
        status_code: Código de status HTTP
        response_time: Tempo de resposta em segundos
    """
    try:
        # Preparar dados da resposta para log (limitar tamanho)
        try:
            if isinstance(response_data, (dict, list)):
                response_str = json.dumps(response_data, default=str)
                if len(response_str) > 1000:
                    safe_response = f"{response_str[:1000]}..."
                else:
                    safe_response = response_str
            else:
                safe_response_str = str(response_data) if response_data is not None else "None"
                safe_response = safe_response_str[:1000] + ("..." if len(safe_response_str) > 1000 else "")
        except Exception:
            safe_response = "<failed_to_serialize_response>"

        log_data = {"response_data": safe_response, "event_type": "api_response"}

        # Validar e adicionar status_code
        if status_code is not None:
            try:
                if isinstance(status_code, int) and 100 <= status_code <= 599:
                    log_data["status_code"] = str(status_code)
                else:
                    log_data["status_code"] = "invalid"
            except Exception:
                log_data["status_code"] = "error"

        # Validar e adicionar response_time
        if response_time is not None:
            try:
                if isinstance(response_time, (int, float)) and response_time >= 0:
                    log_data["response_time_seconds"] = str(round(float(response_time), 4))
                else:
                    log_data["response_time_seconds"] = "invalid"
            except Exception:
                log_data["response_time_seconds"] = "error"

        # Logar com nível apropriado
        try:
            if status_code and isinstance(status_code, int) and status_code >= 400:
                logger.error("Resposta de API com erro", **log_data)
            else:
                logger.info("Resposta de API recebida", **log_data)
        except Exception:
            # Fallback para log básico
            if status_code and isinstance(status_code, int) and status_code >= 400:
                print(f"API response error: status {status_code}")
            else:
                print("API response received")

    except Exception as e:
        # Último recurso para log de erro
        try:
            print(f"Critical error in log_api_response: {str(e)}")
        except Exception:
            pass


def create_glpi_logger(level: str = "INFO") -> StructuredLogger:
    """
    Cria um logger estruturado específico para o serviço GLPI.

    Args:
        level: Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Instância configurada do StructuredLogger
    """
    try:
        # Validar nível de log
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if level.upper() not in valid_levels:
            level = "INFO"

        return StructuredLogger("glpi_service", level)
    except Exception as e:
        # Fallback para logger básico
        try:
            print(f"Warning: Failed to create GLPI logger: {str(e)}. Using fallback.")
            return StructuredLogger("glpi_service_fallback", "INFO")
        except Exception:
            # Último recurso - criar logger mínimo
            fallback_logger = StructuredLogger("emergency_glpi", "INFO")
            return fallback_logger
