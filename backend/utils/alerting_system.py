"""Sistema de alertas para monitoramento e observabilidade.

Este módulo implementa um sistema de alertas baseado em métricas e thresholds
configuráveis, com suporte a diferentes canais de notificação.
"""

import asyncio
import json
import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union

from .prometheus_metrics import prometheus_metrics
from .structured_logging import StructuredLogger, system_logger


class AlertSeverity(Enum):
    """Níveis de severidade dos alertas."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(Enum):
    """Status dos alertas."""

    ACTIVE = "active"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


@dataclass
class AlertRule:
    """Definição de uma regra de alerta."""

    name: str
    description: str
    metric_name: str
    threshold: Union[float, int]
    operator: str  # '>', '<', '>=', '<=', '==', '!='
    severity: AlertSeverity
    duration: int = 60  # segundos que a condição deve persistir
    cooldown: int = 300  # segundos antes de poder disparar novamente
    enabled: bool = True
    labels: Dict[str, str] = field(default_factory=dict)
    annotations: Dict[str, str] = field(default_factory=dict)


@dataclass
class Alert:
    """Instância de um alerta."""

    rule_name: str
    severity: AlertSeverity
    status: AlertStatus
    message: str
    metric_value: Union[float, int]
    threshold: Union[float, int]
    started_at: datetime
    resolved_at: Optional[datetime] = None
    labels: Dict[str, str] = field(default_factory=dict)
    annotations: Dict[str, str] = field(default_factory=dict)

    @property
    def duration(self) -> timedelta:
        """Duração do alerta."""
        end_time = self.resolved_at or datetime.utcnow()
        return end_time - self.started_at

    def to_dict(self) -> Dict[str, Any]:
        """Converte o alerta para dicionário."""
        return {
            "rule_name": self.rule_name,
            "severity": self.severity.value,
            "status": self.status.value,
            "message": self.message,
            "metric_value": self.metric_value,
            "threshold": self.threshold,
            "started_at": self.started_at.isoformat(),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "duration_seconds": self.duration.total_seconds(),
            "labels": self.labels,
            "annotations": self.annotations,
        }


class MetricCollector:
    """Coletor de métricas para avaliação de alertas."""

    def __init__(self):
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.logger = StructuredLogger("alerting.metrics")

    def record_metric(
        self,
        name: str,
        value: Union[float, int],
        labels: Optional[Dict[str, str]] = None,
    ):
        """Registra uma métrica."""
        timestamp = time.time()
        metric_data = {"value": value, "timestamp": timestamp, "labels": labels or {}}

        self.metrics[name].append(metric_data)

        self.logger.log_business_metric(name, value, labels=labels, timestamp=timestamp)

    def get_latest_metric(self, name: str) -> Optional[Dict[str, Any]]:
        """Obtém a métrica mais recente."""
        if name in self.metrics and self.metrics[name]:
            return self.metrics[name][-1]
        return None

    def get_metric_average(self, name: str, duration_seconds: int = 300) -> Optional[float]:
        """Calcula a média de uma métrica nos últimos N segundos."""
        if name not in self.metrics:
            return None

        cutoff_time = time.time() - duration_seconds
        recent_values = [metric["value"] for metric in self.metrics[name] if metric["timestamp"] >= cutoff_time]

        if not recent_values:
            return None

        return sum(recent_values) / len(recent_values)

    def get_metric_count(self, name: str, duration_seconds: int = 300) -> int:
        """Conta quantas vezes uma métrica foi registrada nos últimos N segundos."""
        if name not in self.metrics:
            return 0

        cutoff_time = time.time() - duration_seconds
        return sum(1 for metric in self.metrics[name] if metric["timestamp"] >= cutoff_time)


class AlertManager:
    """Gerenciador principal do sistema de alertas."""

    def __init__(self):
        self.rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.metric_collector = MetricCollector()
        self.notification_handlers: List[Callable[[Alert], None]] = []
        self.logger = StructuredLogger("alerting.manager")

        # Estado interno para tracking de condições
        self._condition_start_times: Dict[str, float] = {}
        self._last_alert_times: Dict[str, float] = {}

        self._setup_default_rules()

    def _setup_default_rules(self):
        """Configura regras de alerta padrão."""
        default_rules = [
            AlertRule(
                name="api_response_time_high",
                description="Tempo de resposta da API acima de 300ms",
                metric_name="api_response_time",
                threshold=0.3,
                operator=">",
                severity=AlertSeverity.MEDIUM,
                duration=60,
                cooldown=300,
                annotations={
                    "summary": "API respondendo lentamente",
                    "description": "O tempo de resposta da API está acima do threshold de 300ms",
                },
            ),
            AlertRule(
                name="glpi_response_time_high",
                description="Tempo de resposta do GLPI acima de 2s",
                metric_name="glpi_response_time",
                threshold=2.0,
                operator=">",
                severity=AlertSeverity.HIGH,
                duration=30,
                cooldown=300,
                annotations={
                    "summary": "GLPI respondendo lentamente",
                    "description": "O tempo de resposta do GLPI está acima do threshold de 2s",
                },
            ),
            AlertRule(
                name="zero_tickets_detected",
                description="Total de tickets zerado detectado",
                metric_name="tickets_total",
                threshold=0,
                operator="==",
                severity=AlertSeverity.HIGH,
                duration=30,
                cooldown=600,
                annotations={
                    "summary": "Nenhum ticket encontrado",
                    "description": "O sistema não está retornando tickets, possível problema na integração",
                },
            ),
            AlertRule(
                name="high_error_rate",
                description="Taxa de erro alta (>5% em 5 minutos)",
                metric_name="error_rate_5m",
                threshold=0.05,
                operator=">",
                severity=AlertSeverity.CRITICAL,
                duration=60,
                cooldown=300,
                annotations={
                    "summary": "Taxa de erro elevada",
                    "description": "A taxa de erro está acima de 5% nos últimos 5 minutos",
                },
            ),
            AlertRule(
                name="suspicious_technician_names",
                description="Nomes de técnicos suspeitos detectados",
                metric_name="suspicious_names_count",
                threshold=0,
                operator=">",
                severity=AlertSeverity.MEDIUM,
                duration=0,  # Alerta imediato
                cooldown=3600,  # 1 hora
                annotations={
                    "summary": "Nomes de técnicos suspeitos",
                    "description": "Foram detectados nomes de técnicos que podem indicar problemas nos dados",
                },
            ),
            AlertRule(
                name="unresolved_technician_ids",
                description="IDs de técnicos não resolvidos",
                metric_name="unresolved_ids_count",
                threshold=0,
                operator=">",
                severity=AlertSeverity.MEDIUM,
                duration=0,
                cooldown=1800,  # 30 minutos
                annotations={
                    "summary": "IDs de técnicos não resolvidos",
                    "description": "Existem IDs de técnicos que não puderam ser resolvidos para nomes",
                },
            ),
        ]

        for rule in default_rules:
            self.add_rule(rule)

    def add_rule(self, rule: AlertRule):
        """Adiciona uma regra de alerta."""
        self.rules[rule.name] = rule
        self.logger.log_audit_event(
            "alert_rule_added",
            rule_name=rule.name,
            severity=rule.severity.value,
            threshold=rule.threshold,
        )

    def remove_rule(self, rule_name: str):
        """Remove uma regra de alerta."""
        if rule_name in self.rules:
            del self.rules[rule_name]
            self.logger.log_audit_event("alert_rule_removed", rule_name=rule_name)

    def add_notification_handler(self, handler: Callable[[Alert], None]):
        """Adiciona um handler de notificação."""
        self.notification_handlers.append(handler)

    def record_metric(
        self,
        name: str,
        value: Union[float, int],
        labels: Optional[Dict[str, str]] = None,
    ):
        """Registra uma métrica e avalia alertas."""
        self.metric_collector.record_metric(name, value, labels)
        self._evaluate_rules()

    def _evaluate_rules(self):
        """Avalia todas as regras de alerta."""
        current_time = time.time()

        for rule_name, rule in self.rules.items():
            if not rule.enabled:
                continue

            try:
                self._evaluate_rule(rule, current_time)
            except Exception as e:
                self.logger.log_error_with_context(
                    "rule_evaluation_error",
                    f"Erro ao avaliar regra {rule_name}: {str(e)}",
                    exception=e,
                    rule_name=rule_name,
                )

    def _evaluate_rule(self, rule: AlertRule, current_time: float):
        """Avalia uma regra específica."""
        # Obter métrica mais recente
        metric_data = self.metric_collector.get_latest_metric(rule.metric_name)
        if not metric_data:
            return

        metric_value = metric_data["value"]
        condition_met = self._evaluate_condition(metric_value, rule.threshold, rule.operator)

        alert_key = f"{rule.name}_{rule.metric_name}"

        if condition_met:
            # Condição de alerta atendida
            if alert_key not in self._condition_start_times:
                self._condition_start_times[alert_key] = current_time

            # Verificar se a condição persistiu pelo tempo necessário
            condition_duration = current_time - self._condition_start_times[alert_key]

            if condition_duration >= rule.duration:
                # Verificar cooldown
                last_alert_time = self._last_alert_times.get(alert_key, 0)
                if current_time - last_alert_time >= rule.cooldown:
                    self._fire_alert(rule, metric_value, current_time)
                    self._last_alert_times[alert_key] = current_time
        else:
            # Condição não atendida, limpar estado
            if alert_key in self._condition_start_times:
                del self._condition_start_times[alert_key]

            # Resolver alerta ativo se existir
            if alert_key in self.active_alerts:
                self._resolve_alert(alert_key, current_time)

    def _evaluate_condition(self, value: Union[float, int], threshold: Union[float, int], operator: str) -> bool:
        """Avalia se uma condição de alerta é atendida."""
        if operator == ">":
            return value > threshold
        elif operator == "<":
            return value < threshold
        elif operator == ">=":
            return value >= threshold
        elif operator == "<=":
            return value <= threshold
        elif operator == "==":
            return value == threshold
        elif operator == "!=":
            return value != threshold
        else:
            raise ValueError(f"Operador não suportado: {operator}")

    def _fire_alert(self, rule: AlertRule, metric_value: Union[float, int], current_time: float):
        """Dispara um alerta."""
        alert_key = f"{rule.name}_{rule.metric_name}"

        # Criar alerta
        alert = Alert(
            rule_name=rule.name,
            severity=rule.severity,
            status=AlertStatus.ACTIVE,
            message=f"{rule.description}: {metric_value} {rule.operator} {rule.threshold}",
            metric_value=metric_value,
            threshold=rule.threshold,
            started_at=datetime.utcnow(),
            labels=rule.labels.copy(),
            annotations=rule.annotations.copy(),
        )

        # Adicionar aos alertas ativos
        self.active_alerts[alert_key] = alert
        self.alert_history.append(alert)

        # Log estruturado
        self.logger.log_warning_with_context(
            "alert_fired",
            f"Alerta disparado: {rule.name}",
            rule_name=rule.name,
            severity=rule.severity.value,
            metric_name=rule.metric_name,
            metric_value=metric_value,
            threshold=rule.threshold,
            operator=rule.operator,
        )

        # Registrar métrica Prometheus
        prometheus_metrics.record_alert(rule.name, rule.severity.value)

        # Notificar handlers
        for handler in self.notification_handlers:
            try:
                handler(alert)
            except Exception as e:
                self.logger.log_error_with_context(
                    "notification_handler_error",
                    f"Erro no handler de notificação: {str(e)}",
                    exception=e,
                    alert_rule=rule.name,
                )

    def _resolve_alert(self, alert_key: str, current_time: float):
        """Resolve um alerta ativo."""
        if alert_key in self.active_alerts:
            alert = self.active_alerts[alert_key]
            alert.status = AlertStatus.RESOLVED
            alert.resolved_at = datetime.utcnow()

            # Remover dos alertas ativos
            del self.active_alerts[alert_key]

            # Log estruturado
            self.logger.log_operation_step(
                "alert_resolved",
                rule_name=alert.rule_name,
                duration_seconds=alert.duration.total_seconds(),
            )

            # Notificar handlers sobre resolução
            for handler in self.notification_handlers:
                try:
                    handler(alert)
                except Exception as e:
                    self.logger.log_error_with_context(
                        "notification_handler_error",
                        f"Erro no handler de notificação (resolução): {str(e)}",
                        exception=e,
                        alert_rule=alert.rule_name,
                    )

    def get_active_alerts(self) -> List[Alert]:
        """Retorna lista de alertas ativos."""
        return list(self.active_alerts.values())

    def get_alert_history(self, limit: int = 100) -> List[Alert]:
        """Retorna histórico de alertas."""
        return self.alert_history[-limit:]

    def get_alert_summary(self) -> Dict[str, Any]:
        """Retorna resumo dos alertas."""
        active_by_severity = defaultdict(int)
        for alert in self.active_alerts.values():
            active_by_severity[alert.severity.value] += 1

        return {
            "active_alerts_count": len(self.active_alerts),
            "active_by_severity": dict(active_by_severity),
            "total_rules": len(self.rules),
            "enabled_rules": sum(1 for rule in self.rules.values() if rule.enabled),
            "alert_history_count": len(self.alert_history),
        }


# Handlers de notificação
def console_notification_handler(alert: Alert):
    """Handler que imprime alertas no console."""
    status_emoji = {
        AlertStatus.ACTIVE: "🚨",
        AlertStatus.RESOLVED: "✅",
        AlertStatus.SUPPRESSED: "🔇",
    }

    severity_emoji = {
        AlertSeverity.LOW: "ℹ️",
        AlertSeverity.MEDIUM: "⚠️",
        AlertSeverity.HIGH: "🔥",
        AlertSeverity.CRITICAL: "💥",
    }

    print(
        f"{status_emoji.get(alert.status, '❓')} {severity_emoji.get(alert.severity, '❓')} "
        f"[{alert.severity.value.upper()}] {alert.message}"
    )


def log_notification_handler(alert: Alert):
    """Handler que registra alertas em logs estruturados."""
    system_logger.log_audit_event(
        "alert_notification",
        alert_rule=alert.rule_name,
        severity=alert.severity.value,
        status=alert.status.value,
        message=alert.message,
        metric_value=alert.metric_value,
        threshold=alert.threshold,
    )


# Instância global
alert_manager = AlertManager()

# Adicionar handlers padrão
alert_manager.add_notification_handler(console_notification_handler)
alert_manager.add_notification_handler(log_notification_handler)


# Funções de conveniência
def record_api_response_time(duration: float, endpoint: str = "unknown"):
    """Registra tempo de resposta da API."""
    alert_manager.record_metric("api_response_time", duration, {"endpoint": endpoint})


def record_glpi_response_time(duration: float, endpoint: str = "unknown"):
    """Registra tempo de resposta do GLPI."""
    alert_manager.record_metric("glpi_response_time", duration, {"endpoint": endpoint})


def record_tickets_total(count: int, level: str = "all"):
    """Registra total de tickets."""
    alert_manager.record_metric("tickets_total", count, {"level": level})


def record_error_rate(rate: float, window: str = "5m"):
    """Registra taxa de erro."""
    alert_manager.record_metric(f"error_rate_{window}", rate)


def record_suspicious_names(count: int):
    """Registra contagem de nomes suspeitos."""
    alert_manager.record_metric("suspicious_names_count", count)


def record_unresolved_ids(count: int):
    """Registra contagem de IDs não resolvidos."""
    alert_manager.record_metric("unresolved_ids_count", count)
