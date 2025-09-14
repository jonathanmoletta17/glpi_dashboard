# -*- coding: utf-8 -*-
"""
Configuração de logging estruturado para o GLPI Dashboard.
"""

import logging
import logging.config
import os
from typing import Any, Dict, Optional

from utils.structured_logger import JSONFormatter


def get_logging_config(log_level: str = "INFO", log_file: Optional[str] = None) -> Dict[str, Any]:
    """
    Retorna configuração de logging estruturado.

    Args:
        log_level: Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Caminho para arquivo de log (opcional)

    Returns:
        Dicionário de configuração para logging.config.dictConfig

    Raises:
        ValueError: Se log_level for inválido
    """
    # Validar log_level
    valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    if log_level.upper() not in valid_levels:
        raise ValueError(f"log_level deve ser um dos: {valid_levels}. Recebido: {log_level}")

    log_level = log_level.upper()

    config: Dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": "utils.structured_logger.JSONFormatter",
                "include_extra_fields": True,
            },
            "standard": {"format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"},
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "json",
                "stream": "ext://sys.stdout",
            }
        },
        "loggers": {
            "glpi_service": {
                "level": "DEBUG",
                "handlers": ["console"],
                "propagate": False,
            },
            "structured_logger": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False,
            },
        },
        "root": {"level": log_level, "handlers": ["console"]},
    }

    # Adicionar handler de arquivo se especificado
    if log_file:
        try:
            # Validar caminho do arquivo
            if not isinstance(log_file, str) or not log_file.strip():
                raise ValueError("log_file deve ser uma string não vazia")

            # Criar diretório se não existir
            log_dir = os.path.dirname(log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)

        except (OSError, PermissionError) as e:
            # Log de fallback para console se não conseguir criar arquivo
            print(f"Aviso: Não foi possível configurar log em arquivo {log_file}: {e}")
            print("Continuando apenas com log no console.")
            return config

        config["handlers"]["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": log_level,
            "formatter": "json",
            "filename": log_file,
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "encoding": "utf-8",
        }

        # Adicionar handler de arquivo aos loggers
        for logger_name in config["loggers"]:
            config["loggers"][logger_name]["handlers"].append("file")
        config["root"]["handlers"].append("file")

    return config


def configure_structured_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> None:
    """
    Configura o sistema de logging estruturado.

    Args:
        log_level: Nível de log
        log_file: Caminho para arquivo de log (opcional)

    Raises:
        ValueError: Se log_level for inválido
        RuntimeError: Se falhar ao configurar o logging
    """
    try:
        config = get_logging_config(log_level, log_file)
        logging.config.dictConfig(config)

        # Testar se o logging está funcionando
        logger = logging.getLogger("logging_config")
        logger.info(f"Sistema de logging configurado com sucesso. Nível: {log_level}")

    except Exception as e:
        # Fallback para configuração básica
        logging.basicConfig(
            level=getattr(logging, log_level.upper(), logging.INFO),
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        )
        logger = logging.getLogger("logging_config")
        logger.error(f"Erro ao configurar logging estruturado: {e}")
        logger.info("Usando configuração básica de logging como fallback")
        raise RuntimeError(f"Falha na configuração do logging: {e}") from e


# Configurações específicas para diferentes ambientes
class LoggingConfig:
    """Configurações de logging para diferentes ambientes."""

    @staticmethod
    def development() -> Dict[str, Any]:
        """Configuração para ambiente de desenvolvimento."""
        try:
            return {
                "log_level": "DEBUG",
                "log_file": "logs/glpi_dashboard_dev.log",
                "console_output": True,
            }
        except Exception as e:
            # Fallback para configuração mínima
            return {"log_level": "INFO", "log_file": None, "console_output": True}

    @staticmethod
    def production() -> Dict[str, Any]:
        """Configuração para ambiente de produção."""
        try:
            return {
                "log_level": "INFO",
                "log_file": "logs/glpi_dashboard_prod.log",
                "console_output": False,
            }
        except Exception as e:
            # Fallback para configuração mínima
            return {"log_level": "WARNING", "log_file": None, "console_output": True}

    @staticmethod
    def testing() -> Dict[str, Any]:
        """Configuração para ambiente de testes."""
        try:
            return {"log_level": "WARNING", "log_file": None, "console_output": True}
        except Exception as e:
            # Fallback para configuração mínima
            return {"log_level": "ERROR", "log_file": None, "console_output": True}


# Configurações para integração com serviços de monitoramento
class MonitoringIntegration:
    """Configurações para integração com serviços de monitoramento."""

    @staticmethod
    def elk_stack_config() -> Dict[str, Any]:
        """
        Configuração para integração com ELK Stack (Elasticsearch, Logstash, Kibana).

        Returns:
            Dicionário com configurações recomendadas
        """
        try:
            # Validar porta do Logstash
            logstash_port = os.getenv("LOGSTASH_PORT", "5044")
            try:
                port = int(logstash_port)
                if not (1 <= port <= 65535):
                    raise ValueError(f"Porta inválida: {port}")
            except ValueError:
                port = 5044  # Fallback para porta padrão

            return {
                "log_format": "json",
                "fields": {
                    "service": "glpi_dashboard",
                    "environment": os.getenv("ENVIRONMENT", "development"),
                    "version": os.getenv("APP_VERSION", "1.0.0"),
                },
                "logstash": {
                    "host": os.getenv("LOGSTASH_HOST", "localhost"),
                    "port": port,
                    "protocol": "tcp",
                },
                "index_pattern": "glpi-dashboard-*",
            }
        except Exception as e:
            # Fallback para configuração básica
            return {
                "log_format": "json",
                "fields": {
                    "service": "glpi_dashboard",
                    "environment": "development",
                    "version": "1.0.0",
                },
                "logstash": {"host": "localhost", "port": 5044, "protocol": "tcp"},
                "index_pattern": "glpi-dashboard-*",
            }

    @staticmethod
    def grafana_loki_config() -> Dict[str, Any]:
        """
        Configuração para integração com Grafana Loki.

        Returns:
            Dicionário com configurações recomendadas
        """
        try:
            # Validar URL do Loki
            loki_url = os.getenv("LOKI_URL", "http://localhost:3100")
            if not loki_url.startswith(("http://", "https://")):
                loki_url = "http://localhost:3100"  # Fallback

            return {
                "log_format": "json",
                "labels": {
                    "service": "glpi_dashboard",
                    "environment": os.getenv("ENVIRONMENT", "development"),
                    "level": "${level}",
                    "logger": "${logger_name}",
                },
                "loki": {"url": loki_url, "push_endpoint": "/loki/api/v1/push"},
            }
        except Exception as e:
            # Fallback para configuração básica
            return {
                "log_format": "json",
                "labels": {
                    "service": "glpi_dashboard",
                    "environment": "development",
                    "level": "${level}",
                    "logger": "${logger_name}",
                },
                "loki": {
                    "url": "http://localhost:3100",
                    "push_endpoint": "/loki/api/v1/push",
                },
            }

    @staticmethod
    def prometheus_config() -> Dict[str, Any]:
        """
        Configuração para métricas do Prometheus.

        Returns:
            Dicionário com configurações de métricas
        """
        try:
            # Validar URL do Prometheus Gateway
            gateway_url = os.getenv("PROMETHEUS_GATEWAY_URL", "http://localhost:9091")
            if not gateway_url.startswith(("http://", "https://")):
                gateway_url = "http://localhost:9091"  # Fallback

            return {
                "metrics": {
                    "api_calls_total": {
                        "type": "counter",
                        "description": "Total number of API calls",
                        "labels": ["method", "endpoint", "status"],
                    },
                    "api_call_duration_seconds": {
                        "type": "histogram",
                        "description": "API call duration in seconds",
                        "labels": ["method", "endpoint"],
                        "buckets": [0.1, 0.5, 1.0, 2.0, 5.0, 10.0],
                    },
                    "errors_total": {
                        "type": "counter",
                        "description": "Total number of errors",
                        "labels": ["error_type", "service"],
                    },
                },
                "prometheus": {
                    "gateway_url": gateway_url,
                    "job_name": "glpi_dashboard",
                },
            }
        except Exception as e:
            # Fallback para configuração básica
            return {
                "metrics": {
                    "api_calls_total": {
                        "type": "counter",
                        "description": "Total number of API calls",
                        "labels": ["method", "endpoint", "status"],
                    },
                    "api_call_duration_seconds": {
                        "type": "histogram",
                        "description": "API call duration in seconds",
                        "labels": ["method", "endpoint"],
                        "buckets": [0.1, 0.5, 1.0, 2.0, 5.0, 10.0],
                    },
                    "errors_total": {
                        "type": "counter",
                        "description": "Total number of errors",
                        "labels": ["error_type", "service"],
                    },
                },
                "prometheus": {
                    "gateway_url": "http://localhost:9091",
                    "job_name": "glpi_dashboard",
                },
            }
