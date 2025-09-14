"""Módulo de logging estruturado JSON para observabilidade.

Este módulo implementa logging estruturado em formato JSON com correlação,
contexto e integração com métricas Prometheus.
"""

import json
import logging
import re
import time
import uuid
from contextvars import ContextVar
from datetime import datetime
from functools import wraps
from typing import Any, Dict, List, Optional, Union, Pattern
from urllib.parse import urlparse, parse_qs

from .prometheus_metrics import prometheus_metrics

# Context variables para correlação
correlation_id_var: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)
operation_context_var: ContextVar[Optional[Dict[str, Any]]] = ContextVar("operation_context", default=None)


class JSONFormatter(logging.Formatter):
    """Formatter para logs estruturados em JSON."""

    def __init__(self, include_extra: bool = True, exclude_fields: Optional[List[str]] = None):
        super().__init__()
        self.include_extra = include_extra
        self.exclude_fields = exclude_fields or []

    def format(self, record: logging.LogRecord) -> str:
        """Formata o log record em JSON estruturado."""
        # Campos base do log
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Adicionar correlation_id se disponível
        correlation_id = correlation_id_var.get()
        if correlation_id:
            log_data["correlation_id"] = correlation_id

        # Adicionar contexto da operação
        operation_context = operation_context_var.get()
        if operation_context:
            log_data["operation"] = operation_context

        # Adicionar informações de exceção com redação
        if record.exc_info:
            exception_message = str(record.exc_info[1]) if record.exc_info[1] else None
            traceback_text = self.formatException(record.exc_info)

            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": SensitiveDataRedactor.redact_exception_message(exception_message) if exception_message else None,
                "traceback": SensitiveDataRedactor.redact_traceback(traceback_text),
            }

        # Adicionar campos extras do record
        if self.include_extra:
            for key, value in record.__dict__.items():
                if (
                    key
                    not in {
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
                        "getMessage",
                        "exc_info",
                        "exc_text",
                        "stack_info",
                    }
                    and key not in self.exclude_fields
                ):
                    try:
                        # Tentar serializar o valor
                        json.dumps(value)
                        log_data[key] = value
                    except (TypeError, ValueError):
                        # Se não conseguir serializar, converter para string
                        log_data[key] = str(value)

        # Sanitizar dados sensíveis
        log_data = self._sanitize_sensitive_data(log_data)

        return json.dumps(log_data, ensure_ascii=False, separators=(",", ":"))

    def _sanitize_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove ou anonimiza dados sensíveis dos logs com redação abrangente."""
        return SensitiveDataRedactor.redact_data(data)


class SensitiveDataRedactor:
    """Sistema de redação de dados sensíveis para logs estruturados."""

    # Cache para compilação de padrões regex (otimização de performance)
    _compiled_patterns_cache = None
    _redaction_enabled = True
    _max_redaction_depth = 10
    _performance_mode = False

    # Padrões de campos sensíveis (expansivo)
    SENSITIVE_FIELD_PATTERNS = {
        r".*password.*": "***REDACTED_PASSWORD***",
        r".*token.*": "***REDACTED_TOKEN***",
        r".*secret.*": "***REDACTED_SECRET***",
        r".*key.*": "***REDACTED_KEY***",
        r".*auth.*": "***REDACTED_AUTH***",
        r".*credential.*": "***REDACTED_CREDENTIAL***",
        r".*cookie.*": "***REDACTED_COOKIE***",
        r".*session.*": "***REDACTED_SESSION***",
        r".*csrf.*": "***REDACTED_CSRF***",
        r".*bearer.*": "***REDACTED_BEARER***",
        r".*api[_-]key.*": "***REDACTED_API_KEY***",
        r".*access[_-]token.*": "***REDACTED_ACCESS_TOKEN***",
        r".*refresh[_-]token.*": "***REDACTED_REFRESH_TOKEN***",
        r".*client[_-]secret.*": "***REDACTED_CLIENT_SECRET***",
        r".*private[_-]key.*": "***REDACTED_PRIVATE_KEY***",
        r".*ssh[_-]key.*": "***REDACTED_SSH_KEY***",
        r".*x[_-]api[_-]key.*": "***REDACTED_X_API_KEY***",
        r".*glpi[_-]user[_-]token.*": "***REDACTED_GLPI_USER_TOKEN***",
        r".*glpi[_-]app[_-]token.*": "***REDACTED_GLPI_APP_TOKEN***",
        r".*database[_-]url.*": "***REDACTED_DB_URL***",
        r".*db[_-]password.*": "***REDACTED_DB_PASSWORD***",
        r".*redis[_-]url.*": "***REDACTED_REDIS_URL***",
        r".*aws[_-]secret.*": "***REDACTED_AWS_SECRET***",
        r".*azure[_-]key.*": "***REDACTED_AZURE_KEY***",
        r".*gcp[_-]key.*": "***REDACTED_GCP_KEY***",
        r".*encryption[_-]key.*": "***REDACTED_ENCRYPTION_KEY***",
        r".*signing[_-]key.*": "***REDACTED_SIGNING_KEY***",
        r".*webhook[_-]secret.*": "***REDACTED_WEBHOOK_SECRET***",
        r".*oauth[_-]secret.*": "***REDACTED_OAUTH_SECRET***",
        r".*jwt[_-]secret.*": "***REDACTED_JWT_SECRET***",
    }

    # Padrões de valores sensíveis (detecta por conteúdo)
    SENSITIVE_VALUE_PATTERNS: List[Pattern] = [
        # Tokens Bearer
        re.compile(r"bearer\s+[a-z0-9_\-\.]+", re.IGNORECASE),
        # API Keys (formato comum)
        re.compile(r"[a-z0-9]{32,}", re.IGNORECASE),
        # JWT Tokens (formato padrão)
        re.compile(r"ey[a-z0-9]+\.[a-z0-9]+\.[a-z0-9_\-]+", re.IGNORECASE),
        # UUIDs em contexto de token/secret
        re.compile(r"[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}", re.IGNORECASE),
        # Base64 encoded strings (potenciais secrets)
        re.compile(r"^[a-z0-9+/]{40,}={0,2}$", re.IGNORECASE),
        # Database URLs com credenciais
        re.compile(r"\w+://[^:/]+:[^@/]+@[^/]+", re.IGNORECASE),
        # URLs Redis com auth
        re.compile(r"redis://[^:/]+:[^@/]+@[^/]+", re.IGNORECASE),
        # SSH Keys (começos típicos)
        re.compile(r"-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----", re.IGNORECASE),
        # AWS Access Keys
        re.compile(r"AKIA[0-9A-Z]{16}", re.IGNORECASE),
        # AWS Secret Keys
        re.compile(r"[a-z0-9+/]{40}", re.IGNORECASE),
        # Azure Keys
        re.compile(r"[a-z0-9]{88}", re.IGNORECASE),
        # Google Cloud Keys (JSON key files)
        re.compile(r'"type":\s*"service_account"', re.IGNORECASE),
        # Flask Secret Keys (development patterns)
        re.compile(r"dev-secret-key[\w\-]*", re.IGNORECASE),
        # Common password patterns
        re.compile(r'password[=:]\s*["\']?[\w@#$%^&*()]+["\']?', re.IGNORECASE),
        # Environment variables with credentials
        re.compile(r"[A-Z_]*(?:TOKEN|KEY|SECRET|PASSWORD|AUTH)[A-Z_]*=[\w\-@#$%^&*()]+", re.IGNORECASE),
        # GLPI specific tokens (long alphanumeric strings)
        re.compile(r"[a-z0-9]{20,}", re.IGNORECASE),
    ]

    # Headers HTTP sensíveis
    SENSITIVE_HEADERS = {
        "authorization",
        "cookie",
        "set-cookie",
        "x-api-key",
        "x-auth-token",
        "x-access-token",
        "x-csrf-token",
        "x-session-token",
        "x-user-token",
        "authentication",
        "proxy-authorization",
        "www-authenticate",
        "x-glpi-user-token",
        "x-glpi-app-token",
        "x-webhook-signature",
        "x-hub-signature",
        "x-github-token",
        "x-gitlab-token",
    }

    # Parâmetros de query sensíveis
    SENSITIVE_QUERY_PARAMS = {
        "token",
        "api_key",
        "apikey",
        "key",
        "secret",
        "password",
        "auth",
        "access_token",
        "refresh_token",
        "client_secret",
        "user_token",
        "app_token",
        "session_id",
        "csrf_token",
        "state",
        "code",
        "glpi_user_token",
        "glpi_app_token",
        "backend_api_key",
    }

    # Variáveis de ambiente sensíveis (para configuração)
    SENSITIVE_ENV_VARS = {
        "SECRET_KEY",
        "FLASK_SECRET_KEY",
        "GLPI_USER_TOKEN",
        "GLPI_APP_TOKEN",
        "API_KEY",
        "BACKEND_API_KEY",
        "REDIS_URL",
        "CACHE_REDIS_URL",
        "DATABASE_URL",
        "DB_PASSWORD",
        "DB_USER",
        "POSTGRES_PASSWORD",
        "AWS_SECRET_ACCESS_KEY",
        "AWS_ACCESS_KEY_ID",
        "AZURE_CLIENT_SECRET",
        "GCP_SERVICE_ACCOUNT_KEY",
        "PROMETHEUS_GATEWAY_URL",
        "WEBHOOK_SECRET",
        "OAUTH_CLIENT_SECRET",
        "JWT_SECRET_KEY",
        "ENCRYPTION_KEY",
    }

    @classmethod
    def configure_performance(cls, enabled: bool = True, performance_mode: bool = False, max_depth: int = 10):
        """Configura as opções de performance do redator."""
        cls._redaction_enabled = enabled
        cls._performance_mode = performance_mode
        cls._max_redaction_depth = max_depth

        # Em modo de performance, compilar padrões uma vez
        if performance_mode and cls._compiled_patterns_cache is None:
            cls._compiled_patterns_cache = {
                "field_patterns": {
                    pattern: re.compile(pattern, re.IGNORECASE) for pattern in cls.SENSITIVE_FIELD_PATTERNS.keys()
                },
                "value_patterns": cls.SENSITIVE_VALUE_PATTERNS.copy(),
            }

    @classmethod
    def redact_data(cls, data: Any, max_depth: int = None) -> Any:
        """Redacta dados sensíveis de forma recursiva com otimizações."""
        # Verificação rápida se redação está desabilitada
        if not cls._redaction_enabled:
            return data

        if max_depth is None:
            max_depth = cls._max_redaction_depth

        if max_depth <= 0:
            return "***MAX_DEPTH_REACHED***"

        # Otimização: retornar rapidamente para tipos simples
        if data is None or isinstance(data, (bool, int, float)):
            return data

        if isinstance(data, dict):
            return cls._redact_dict(data, max_depth - 1)
        elif isinstance(data, list):
            return cls._redact_list(data, max_depth - 1)
        elif isinstance(data, str):
            return cls._redact_string_value(data)
        else:
            return data

    @classmethod
    def _redact_dict(cls, data: Dict[str, Any], max_depth: int) -> Dict[str, Any]:
        """Redacta um dicionário."""
        redacted = {}

        for key, value in data.items():
            redacted_key = str(key)

            # Verificar se a chave é sensível
            if cls._is_sensitive_field(redacted_key):
                redacted[redacted_key] = cls._get_redacted_placeholder(redacted_key, value)
            else:
                redacted[redacted_key] = cls.redact_data(value, max_depth)

        return redacted

    @classmethod
    def _redact_list(cls, data: List[Any], max_depth: int) -> List[Any]:
        """Redacta uma lista."""
        return [cls.redact_data(item, max_depth) for item in data]

    @classmethod
    def _is_sensitive_field(cls, field_name: str) -> bool:
        """Verifica se um nome de campo é sensível (otimizado)."""
        if not cls._redaction_enabled:
            return False

        field_lower = field_name.lower()

        # Otimização: verificação rápida para campos comuns
        quick_checks = ["password", "token", "secret", "key", "auth"]
        if any(check in field_lower for check in quick_checks):
            return True

        # Usa cache compilado se disponível (modo performance)
        if cls._performance_mode and cls._compiled_patterns_cache:
            compiled_patterns = cls._compiled_patterns_cache["field_patterns"]
            for pattern_regex in compiled_patterns.values():
                if pattern_regex.match(field_lower):
                    return True
        else:
            # Verificação padrão
            for pattern in cls.SENSITIVE_FIELD_PATTERNS:
                if re.match(pattern, field_lower):
                    return True

        return False

    @classmethod
    def _get_redacted_placeholder(cls, field_name: str, value: Any) -> str:
        """Obtém o placeholder apropriado para redação."""
        field_lower = field_name.lower()

        for pattern, placeholder in cls.SENSITIVE_FIELD_PATTERNS.items():
            if re.match(pattern, field_lower):
                return placeholder

        # Fallback genérico com preservação parcial para debugging
        if isinstance(value, str) and len(value) > 8:
            return f"{value[:3]}***{value[-3:]}"
        return "***REDACTED***"

    @classmethod
    def _redact_string_value(cls, value: str) -> str:
        """Redacta valores string que podem conter dados sensíveis (otimizado)."""
        if not cls._redaction_enabled or not isinstance(value, str) or len(value) < 8:
            return value

        # Otimização: evita redação para strings muito longas em modo performance
        if cls._performance_mode and len(value) > 10000:
            return value

        # Cache de padrões compilados se disponível
        patterns_to_check = (
            cls._compiled_patterns_cache["value_patterns"]
            if cls._performance_mode and cls._compiled_patterns_cache
            else cls.SENSITIVE_VALUE_PATTERNS
        )

        # Verificar padrões de valores sensíveis
        for pattern in patterns_to_check:
            if pattern.search(value):
                # Se encontrar padrão sensível, redactar preservando formato
                if len(value) > 20:
                    return f"{value[:4]}***REDACTED***{value[-4:]}"
                else:
                    return "***REDACTED***"

        return value

    @classmethod
    def redact_http_headers(cls, headers: Dict[str, Any]) -> Dict[str, Any]:
        """Redacta headers HTTP sensíveis."""
        if not isinstance(headers, dict):
            return headers

        redacted = {}
        for key, value in headers.items():
            if isinstance(key, str) and key.lower() in cls.SENSITIVE_HEADERS:
                redacted[key] = "***REDACTED_HEADER***"
            else:
                redacted[key] = cls.redact_data(value)

        return redacted

    @classmethod
    def redact_query_params(cls, params: Dict[str, Any]) -> Dict[str, Any]:
        """Redacta parâmetros de query sensíveis."""
        if not isinstance(params, dict):
            return params

        redacted = {}
        for key, value in params.items():
            if isinstance(key, str) and key.lower() in cls.SENSITIVE_QUERY_PARAMS:
                redacted[key] = "***REDACTED_PARAM***"
            else:
                redacted[key] = cls.redact_data(value)

        return redacted

    @classmethod
    def redact_url(cls, url: str) -> str:
        """Redacta URLs que podem conter credenciais."""
        if not isinstance(url, str):
            return url

        try:
            parsed = urlparse(url)

            # Redactar credenciais na URL
            if parsed.username or parsed.password:
                # Reconstruir URL sem credenciais
                netloc = parsed.hostname
                if parsed.port:
                    netloc += f":{parsed.port}"

                redacted_url = f"{parsed.scheme}://***REDACTED_CREDENTIALS***@{netloc}{parsed.path}"
                if parsed.query:
                    redacted_url += f"?{parsed.query}"
                if parsed.fragment:
                    redacted_url += f"#{parsed.fragment}"

                return redacted_url

            # Redactar query parameters sensíveis
            if parsed.query:
                query_params = parse_qs(parsed.query, keep_blank_values=True)
                redacted_params = cls.redact_query_params(query_params)

                # Reconstruir query string se houve redação
                if redacted_params != query_params:
                    from urllib.parse import urlencode

                    redacted_query = urlencode(redacted_params, doseq=True)
                    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{redacted_query}"

        except Exception:
            # Em caso de erro no parsing, aplicar redação básica
            for pattern in cls.SENSITIVE_VALUE_PATTERNS:
                if pattern.search(url):
                    return "***REDACTED_URL***"

        return url

    @classmethod
    def redact_traceback(cls, traceback_text: str) -> str:
        """Redacta tracebacks que podem conter dados sensíveis."""
        if not isinstance(traceback_text, str):
            return traceback_text

        lines = traceback_text.split("\n")
        redacted_lines = []

        for line in lines:
            redacted_line = line

            # Redactar valores sensíveis na linha
            for pattern in cls.SENSITIVE_VALUE_PATTERNS:
                redacted_line = pattern.sub("***REDACTED***", redacted_line)

            # Redactar URLs com credenciais
            redacted_line = cls.redact_url(redacted_line)

            redacted_lines.append(redacted_line)

        return "\n".join(redacted_lines)

    @classmethod
    def redact_exception_message(cls, message: str) -> str:
        """Redacta mensagens de exceção que podem conter dados sensíveis."""
        if not isinstance(message, str):
            return message

        redacted_message = message

        # Aplicar redação de valores sensíveis
        for pattern in cls.SENSITIVE_VALUE_PATTERNS:
            redacted_message = pattern.sub("***REDACTED***", redacted_message)

        # Redactar URLs com credenciais
        redacted_message = cls.redact_url(redacted_message)

        return redacted_message

    @classmethod
    def redact_configuration_data(cls, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Redacta dados de configuração que podem conter informações sensíveis."""
        if not isinstance(config_data, dict):
            return config_data

        redacted = {}

        for key, value in config_data.items():
            key_str = str(key).upper()

            # Verificar se é uma variável de ambiente sensível
            if any(env_var in key_str for env_var in cls.SENSITIVE_ENV_VARS):
                redacted[key] = "***REDACTED_CONFIG***"
            # Verificar padrões sensíveis no nome da chave
            elif cls._is_sensitive_field(key_str):
                redacted[key] = cls._get_redacted_placeholder(key_str, value)
            # Redactar valores que podem conter dados sensíveis
            elif isinstance(value, str):
                redacted[key] = cls._redact_string_value(value)
            # Recursivamente redactar objetos aninhados
            else:
                redacted[key] = cls.redact_data(value)

        return redacted

    @classmethod
    def redact_environment_variables(cls, env_vars: Dict[str, str]) -> Dict[str, str]:
        """Redacta variáveis de ambiente sensíveis."""
        if not isinstance(env_vars, dict):
            return env_vars

        redacted = {}

        for key, value in env_vars.items():
            key_upper = str(key).upper()

            if key_upper in cls.SENSITIVE_ENV_VARS:
                redacted[key] = "***REDACTED_ENV_VAR***"
            elif any(sensitive in key_upper for sensitive in ["TOKEN", "KEY", "SECRET", "PASSWORD", "AUTH"]):
                redacted[key] = "***REDACTED_ENV_VAR***"
            else:
                # Ainda aplicar redação de valores para detectar padrões sensíveis
                redacted[key] = cls._redact_string_value(str(value)) if value else value

        return redacted

    @classmethod
    def create_safe_config_summary(cls, config_obj: Any) -> Dict[str, Any]:
        """Cria um resumo seguro de configuração sem dados sensíveis."""
        safe_summary = {}

        # Lista de atributos seguros para incluir no resumo
        safe_attributes = {
            "DEBUG",
            "HOST",
            "PORT",
            "LOG_LEVEL",
            "CACHE_TYPE",
            "CACHE_DEFAULT_TIMEOUT",
            "PERFORMANCE_TARGET_P95",
            "API_TIMEOUT",
            "CORS_ORIGINS",
            "MAX_CONTENT_LENGTH",
            "RATE_LIMIT_PER_MINUTE",
        }

        # URLs podem ser incluídas mas devem ser redactadas
        url_attributes = {"GLPI_URL", "BACKEND_API_URL", "PROMETHEUS_GATEWAY_URL"}

        try:
            for attr in safe_attributes:
                if hasattr(config_obj, attr):
                    value = getattr(config_obj, attr)
                    safe_summary[attr.lower()] = value

            for attr in url_attributes:
                if hasattr(config_obj, attr):
                    value = getattr(config_obj, attr)
                    safe_summary[attr.lower()] = cls.redact_url(str(value)) if value else None

            # Adicionar informações sobre presença de configurações sensíveis (sem valores)
            sensitive_config_status = {}
            for env_var in ["GLPI_USER_TOKEN", "GLPI_APP_TOKEN", "SECRET_KEY", "API_KEY"]:
                if hasattr(config_obj, env_var):
                    value = getattr(config_obj, env_var)
                    sensitive_config_status[f"{env_var.lower()}_configured"] = bool(value)

            safe_summary["sensitive_config_status"] = sensitive_config_status

        except Exception as e:
            safe_summary = {"error": "Failed to create config summary", "error_type": type(e).__name__}

        return safe_summary


class StructuredLogger:
    """Logger estruturado com contexto e correlação."""

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self._setup_formatter()

    def _setup_formatter(self):
        """Configura o formatter JSON se não estiver configurado."""
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(JSONFormatter())
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def generate_correlation_id(self) -> str:
        """Gera um novo correlation ID."""
        return str(uuid.uuid4())

    def set_correlation_id(self, correlation_id: str):
        """Define o correlation ID para o contexto atual."""
        correlation_id_var.set(correlation_id)

    def get_correlation_id(self) -> Optional[str]:
        """Obtém o correlation ID atual."""
        return correlation_id_var.get()

    def set_operation_context(self, operation: str, **kwargs):
        """Define o contexto da operação atual."""
        context = {
            "name": operation,
            "start_time": datetime.utcnow().isoformat() + "Z",
            **kwargs,
        }
        operation_context_var.set(context)

    def clear_operation_context(self):
        """Limpa o contexto da operação."""
        operation_context_var.set(None)

    def log_operation_start(self, operation: str, **kwargs):
        """Registra o início de uma operação."""
        correlation_id = self.get_correlation_id() or self.generate_correlation_id()
        self.set_correlation_id(correlation_id)
        self.set_operation_context(operation, **kwargs)

        self.logger.info(
            f"Iniciando operação: {operation}",
            extra={
                "operation_phase": "start",
                "operation_name": operation,
                "parameters": kwargs,
            },
        )

    def log_operation_step(self, step: str, **kwargs):
        """Registra uma etapa da operação."""
        self.logger.info(
            f"Executando etapa: {step}",
            extra={"operation_phase": "step", "step_name": step, "step_data": kwargs},
        )

    def log_operation_end(self, operation: str, success: bool = True, **kwargs):
        """Registra o fim de uma operação."""
        operation_context = operation_context_var.get()
        duration = None

        if operation_context and "start_time" in operation_context:
            start_time = datetime.fromisoformat(operation_context["start_time"].replace("Z", "+00:00"))
            duration = (datetime.utcnow().replace(tzinfo=start_time.tzinfo) - start_time).total_seconds()

        level = logging.INFO if success else logging.ERROR
        status = "success" if success else "error"

        self.logger.log(
            level,
            f"Operação {status}: {operation}",
            extra={
                "operation_phase": "end",
                "operation_name": operation,
                "operation_status": status,
                "duration_seconds": duration,
                "result": kwargs,
            },
        )

        self.clear_operation_context()

    def log_warning_with_context(self, warning_type: str, message: str, **kwargs):
        """Registra um warning com contexto específico."""
        self.logger.warning(message, extra={"warning_type": warning_type, "warning_data": kwargs})

        # Registrar alerta no Prometheus
        prometheus_metrics.record_alert(warning_type, "warning")

    def log_error_with_context(
        self,
        error_type: str,
        message: str,
        exception: Optional[Exception] = None,
        **kwargs,
    ):
        """Registra um erro com contexto específico."""
        extra_data = {"error_type": error_type, "error_data": kwargs}

        if exception:
            extra_data["exception_type"] = type(exception).__name__
            extra_data["exception_message"] = str(exception)

        self.logger.error(message, extra=extra_data, exc_info=exception is not None)

        # Registrar erro no Prometheus
        prometheus_metrics.record_error(error_type, kwargs.get("component", "unknown"))

    def log_performance_metric(self, metric_name: str, value: float, unit: str = "seconds", **kwargs):
        """Registra uma métrica de performance."""
        self.logger.info(
            f"Métrica de performance: {metric_name} = {value} {unit}",
            extra={
                "metric_type": "performance",
                "metric_name": metric_name,
                "metric_value": value,
                "metric_unit": unit,
                "metric_context": kwargs,
            },
        )

    def log_business_metric(self, metric_name: str, value: Union[int, float], **kwargs):
        """Registra uma métrica de negócio."""
        self.logger.info(
            f"Métrica de negócio: {metric_name} = {value}",
            extra={
                "metric_type": "business",
                "metric_name": metric_name,
                "metric_value": value,
                "metric_context": kwargs,
            },
        )

    def log_audit_event(self, event_type: str, user_id: Optional[str] = None, **kwargs):
        """Registra um evento de auditoria."""
        self.logger.info(
            f"Evento de auditoria: {event_type}",
            extra={
                "event_type": "audit",
                "audit_event": event_type,
                "user_id": user_id,
                "audit_data": kwargs,
            },
        )


# Decorador para instrumentação automática
def with_structured_logging(operation_name: str, logger_name: Optional[str] = None):
    """Decorador para adicionar logging estruturado automático."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = StructuredLogger(logger_name or func.__module__)

            # Extrair parâmetros relevantes (evitar dados sensíveis)
            safe_kwargs = {
                k: v
                for k, v in kwargs.items()
                if not any(sensitive in k.lower() for sensitive in ["password", "token", "secret", "key"])
            }

            logger.log_operation_start(operation_name, **safe_kwargs)

            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time

                logger.log_operation_end(
                    operation_name,
                    success=True,
                    duration=duration,
                    result_type=type(result).__name__,
                )

                logger.log_performance_metric(f"{operation_name}_duration", duration, "seconds")

                return result

            except Exception as e:
                duration = time.time() - start_time

                logger.log_operation_end(operation_name, success=False, duration=duration, error=str(e))

                logger.log_error_with_context(
                    f"{operation_name}_error",
                    f"Erro na operação {operation_name}: {str(e)}",
                    exception=e,
                    component=func.__module__,
                )

                raise

        return wrapper

    return decorator


# Instâncias globais para uso direto
api_logger = StructuredLogger("glpi.api")
glpi_logger = StructuredLogger("glpi.external")
metrics_logger = StructuredLogger("glpi.metrics")
system_logger = StructuredLogger("glpi.system")
audit_logger = StructuredLogger("glpi.audit")


# Funções de conveniência
def log_api_request(method: str, endpoint: str, status_code: int, duration: float, **kwargs):
    """Log estruturado para requisições da API."""
    api_logger.log_performance_metric(
        "api_request_duration",
        duration,
        "seconds",
        method=method,
        endpoint=endpoint,
        status_code=status_code,
        **kwargs,
    )

    if duration > 0.3:  # Alerta para respostas lentas
        api_logger.log_warning_with_context(
            "slow_response",
            f"Resposta lenta detectada: {method} {endpoint} - {duration:.3f}s",
            method=method,
            endpoint=endpoint,
            duration=duration,
            threshold=0.3,
        )


def log_glpi_request(endpoint: str, status_code: int, duration: float, **kwargs):
    """Log estruturado para requisições ao GLPI."""
    glpi_logger.log_performance_metric(
        "glpi_request_duration",
        duration,
        "seconds",
        endpoint=endpoint,
        status_code=status_code,
        **kwargs,
    )


def log_metrics_processing(query_type: str, duration: float, result_count: int = 0, **kwargs):
    """Log estruturado para processamento de métricas."""
    metrics_logger.log_performance_metric(
        "metrics_processing_duration",
        duration,
        "seconds",
        query_type=query_type,
        result_count=result_count,
        **kwargs,
    )

    if result_count == 0:
        metrics_logger.log_warning_with_context(
            "zero_metrics",
            f"Métricas zeradas detectadas: {query_type}",
            query_type=query_type,
            **kwargs,
        )


def log_system_health(component: str, status: str, **kwargs):
    """Log estruturado para saúde do sistema."""
    system_logger.log_business_metric(
        f"{component}_health",
        1 if status == "healthy" else 0,
        component=component,
        status=status,
        **kwargs,
    )
