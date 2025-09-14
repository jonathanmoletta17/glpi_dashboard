# ===========================================
# SISTEMA DE ALERTAS AUTOMÁTICOS LEGACY
# ===========================================

import smtplib
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dataclasses import dataclass
from enum import Enum
import threading
import time
from backend.monitoring.legacy_logger import legacy_logger, alert_logger
from backend.config.settings import Config

class AlertSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AlertStatus(Enum):
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"

@dataclass
class Alert:
    id: str
    title: str
    description: str
    severity: AlertSeverity
    category: str
    source: str
    timestamp: datetime
    status: AlertStatus = AlertStatus.ACTIVE
    metadata: Dict[str, Any] = None
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class AlertRule:
    def __init__(self, 
                 rule_id: str, 
                 name: str, 
                 condition: Callable[[Dict[str, Any]], bool],
                 severity: AlertSeverity,
                 category: str,
                 description: str,
                 cooldown_minutes: int = 5):
        self.rule_id = rule_id
        self.name = name
        self.condition = condition
        self.severity = severity
        self.category = category
        self.description = description
        self.cooldown_minutes = cooldown_minutes
        self.last_triggered = None
        self.enabled = True
    
    def can_trigger(self) -> bool:
        """Verifica se a regra pode ser disparada (cooldown)"""
        if not self.enabled:
            return False
        
        if self.last_triggered is None:
            return True
        
        cooldown_period = timedelta(minutes=self.cooldown_minutes)
        return datetime.now() - self.last_triggered > cooldown_period
    
    def evaluate(self, metrics: Dict[str, Any]) -> bool:
        """Avalia se a condição da regra é atendida"""
        try:
            return self.condition(metrics)
        except Exception as e:
            legacy_logger.log_error(f"Error evaluating alert rule {self.rule_id}", e)
            return False

class AlertManager:
    def __init__(self):
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_rules: Dict[str, AlertRule] = {}
        self.notification_handlers = []
        self.alert_history: List[Alert] = []
        self.running = False
        self.monitor_thread = None
        
        # Configurar regras padrão
        self._setup_default_rules()
        
        # Configurar handlers de notificação
        self._setup_notification_handlers()
    
    def _setup_default_rules(self):
        """Configura regras de alerta padrão"""
        
        # Regra: CPU alta
        self.add_rule(AlertRule(
            rule_id="high_cpu",
            name="High CPU Usage",
            condition=lambda m: m.get('system', {}).get('cpu_percent', 0) > 80,
            severity=AlertSeverity.HIGH,
            category="system",
            description="CPU usage is above 80%",
            cooldown_minutes=5
        ))
        
        # Regra: Memória alta
        self.add_rule(AlertRule(
            rule_id="high_memory",
            name="High Memory Usage",
            condition=lambda m: m.get('system', {}).get('memory_percent', 0) > 85,
            severity=AlertSeverity.HIGH,
            category="system",
            description="Memory usage is above 85%",
            cooldown_minutes=5
        ))
        
        # Regra: Disco cheio
        self.add_rule(AlertRule(
            rule_id="disk_full",
            name="Disk Space Critical",
            condition=lambda m: m.get('system', {}).get('disk_percent', 0) > 90,
            severity=AlertSeverity.CRITICAL,
            category="system",
            description="Disk usage is above 90%",
            cooldown_minutes=10
        ))
        
        # Regra: GLPI indisponível
        self.add_rule(AlertRule(
            rule_id="glpi_down",
            name="GLPI Service Down",
            condition=lambda m: m.get('services', {}).get('glpi', {}).get('status') == 'unhealthy',
            severity=AlertSeverity.CRITICAL,
            category="service",
            description="GLPI service is not responding",
            cooldown_minutes=2
        ))
        
        # Regra: Legacy adapter indisponível
        self.add_rule(AlertRule(
            rule_id="legacy_adapter_down",
            name="Legacy Adapter Down",
            condition=lambda m: m.get('services', {}).get('legacy_adapter', {}).get('status') == 'unhealthy',
            severity=AlertSeverity.CRITICAL,
            category="service",
            description="Legacy adapter service is not responding",
            cooldown_minutes=2
        ))
        
        # Regra: Performance degradada
        self.add_rule(AlertRule(
            rule_id="performance_degraded",
            name="Performance Degraded",
            condition=lambda m: (
                m.get('services', {}).get('glpi', {}).get('response_time_ms', 0) > 3000 or
                m.get('services', {}).get('legacy_adapter', {}).get('response_time_ms', 0) > 3000
            ),
            severity=AlertSeverity.MEDIUM,
            category="performance",
            description="Service response time is above 3 seconds",
            cooldown_minutes=10
        ))
    
    def _setup_notification_handlers(self):
        """Configura handlers de notificação"""
        # Handler de email (se configurado)
        if hasattr(Config, 'SMTP_SERVER') and Config.SMTP_SERVER:
            self.add_notification_handler(self._send_email_notification)
        
        # Handler de log (sempre ativo)
        self.add_notification_handler(self._log_notification)
        
        # Handler de webhook (se configurado)
        if hasattr(Config, 'ALERT_WEBHOOK_URL') and Config.ALERT_WEBHOOK_URL:
            self.add_notification_handler(self._send_webhook_notification)
    
    def add_rule(self, rule: AlertRule):
        """Adiciona uma regra de alerta"""
        self.alert_rules[rule.rule_id] = rule
        legacy_logger.log_system_event(f"Alert rule added: {rule.name}", rule_id=rule.rule_id)
    
    def remove_rule(self, rule_id: str):
        """Remove uma regra de alerta"""
        if rule_id in self.alert_rules:
            del self.alert_rules[rule_id]
            legacy_logger.log_system_event(f"Alert rule removed: {rule_id}")
    
    def add_notification_handler(self, handler: Callable[[Alert], None]):
        """Adiciona um handler de notificação"""
        self.notification_handlers.append(handler)
    
    def evaluate_metrics(self, metrics: Dict[str, Any]):
        """Avalia métricas contra todas as regras"""
        for rule in self.alert_rules.values():
            if rule.can_trigger() and rule.evaluate(metrics):
                self._trigger_alert(rule, metrics)
    
    def _trigger_alert(self, rule: AlertRule, metrics: Dict[str, Any]):
        """Dispara um alerta"""
        alert_id = f"{rule.rule_id}_{int(datetime.now().timestamp())}"
        
        alert = Alert(
            id=alert_id,
            title=rule.name,
            description=rule.description,
            severity=rule.severity,
            category=rule.category,
            source="legacy_monitoring",
            timestamp=datetime.now(),
            metadata={
                'rule_id': rule.rule_id,
                'metrics_snapshot': metrics,
                'triggered_condition': rule.description
            }
        )
        
        # Registrar alerta
        self.active_alerts[alert_id] = alert
        self.alert_history.append(alert)
        
        # Atualizar timestamp da regra
        rule.last_triggered = datetime.now()
        
        # Enviar notificações
        self._send_notifications(alert)
        
        # Log do alerta
        alert_logger.log_service_alert(
            service=rule.category,
            status="alert_triggered",
            alert_id=alert_id,
            severity=rule.severity.value,
            rule_id=rule.rule_id
        )
    
    def _send_notifications(self, alert: Alert):
        """Envia notificações para todos os handlers"""
        for handler in self.notification_handlers:
            try:
                handler(alert)
            except Exception as e:
                legacy_logger.log_error(f"Failed to send notification via handler", e)
    
    def _log_notification(self, alert: Alert):
        """Handler de notificação via log"""
        legacy_logger.log(
            legacy_logger.LogLevel.WARNING,
            legacy_logger.LogCategory.SYSTEM,
            f"ALERT: {alert.title} - {alert.description}",
            alert_id=alert.id,
            severity=alert.severity.value,
            category=alert.category
        )
    
    def _send_email_notification(self, alert: Alert):
        """Handler de notificação via email"""
        try:
            if not hasattr(Config, 'SMTP_SERVER'):
                return
            
            msg = MIMEMultipart()
            msg['From'] = getattr(Config, 'SMTP_FROM', 'noreply@glpidashboard.com')
            msg['To'] = getattr(Config, 'ALERT_EMAIL_TO', 'admin@company.com')
            msg['Subject'] = f"[{alert.severity.value.upper()}] {alert.title}"
            
            body = f"""
            Alerta do Sistema de Monitoramento Legacy
            
            Título: {alert.title}
            Severidade: {alert.severity.value.upper()}
            Categoria: {alert.category}
            Timestamp: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
            
            Descrição:
            {alert.description}
            
            Metadados:
            {json.dumps(alert.metadata, indent=2, ensure_ascii=False)}
            
            ---
            Sistema de Monitoramento GLPI Dashboard
            """
            
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            server = smtplib.SMTP(Config.SMTP_SERVER, getattr(Config, 'SMTP_PORT', 587))
            if getattr(Config, 'SMTP_USE_TLS', True):
                server.starttls()
            
            if hasattr(Config, 'SMTP_USERNAME'):
                server.login(Config.SMTP_USERNAME, Config.SMTP_PASSWORD)
            
            server.send_message(msg)
            server.quit()
            
            legacy_logger.log_system_event("Email alert sent", alert_id=alert.id)
            
        except Exception as e:
            legacy_logger.log_error("Failed to send email alert", e, alert_id=alert.id)
    
    def _send_webhook_notification(self, alert: Alert):
        """Handler de notificação via webhook"""
        try:
            import requests
            
            payload = {
                'alert_id': alert.id,
                'title': alert.title,
                'description': alert.description,
                'severity': alert.severity.value,
                'category': alert.category,
                'timestamp': alert.timestamp.isoformat(),
                'metadata': alert.metadata
            }
            
            response = requests.post(
                Config.ALERT_WEBHOOK_URL,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                legacy_logger.log_system_event("Webhook alert sent", alert_id=alert.id)
            else:
                legacy_logger.log_error(
                    f"Webhook alert failed with status {response.status_code}",
                    alert_id=alert.id
                )
                
        except Exception as e:
            legacy_logger.log_error("Failed to send webhook alert", e, alert_id=alert.id)
    
    def acknowledge_alert(self, alert_id: str, acknowledged_by: str):
        """Reconhece um alerta"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.status = AlertStatus.ACKNOWLEDGED
            alert.acknowledged_by = acknowledged_by
            alert.acknowledged_at = datetime.now()
            
            legacy_logger.log_system_event(
                f"Alert acknowledged: {alert.title}",
                alert_id=alert_id,
                acknowledged_by=acknowledged_by
            )
    
    def resolve_alert(self, alert_id: str):
        """Resolve um alerta"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.status = AlertStatus.RESOLVED
            alert.resolved_at = datetime.now()
            
            # Remove da lista de alertas ativos
            del self.active_alerts[alert_id]
            
            legacy_logger.log_system_event(
                f"Alert resolved: {alert.title}",
                alert_id=alert_id
            )
    
    def get_active_alerts(self) -> List[Alert]:
        """Retorna alertas ativos"""
        return list(self.active_alerts.values())
    
    def get_alert_history(self, limit: int = 100) -> List[Alert]:
        """Retorna histórico de alertas"""
        return self.alert_history[-limit:] if self.alert_history else []
    
    def start_monitoring(self, interval_seconds: int = 60):
        """Inicia monitoramento automático"""
        if self.running:
            return
        
        self.running = True
        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(interval_seconds,),
            daemon=True
        )
        self.monitor_thread.start()
        
        legacy_logger.log_system_event(
            "Alert monitoring started",
            interval_seconds=interval_seconds
        )
    
    def stop_monitoring(self):
        """Para monitoramento automático"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        legacy_logger.log_system_event("Alert monitoring stopped")
    
    def _monitoring_loop(self, interval_seconds: int):
        """Loop principal de monitoramento"""
        from backend.monitoring.legacy_dashboard import monitoring_service
        
        while self.running:
            try:
                # Obter métricas atuais
                health_data = monitoring_service.get_system_health()
                
                # Avaliar regras de alerta
                self.evaluate_metrics(health_data)
                
                # Aguardar próximo ciclo
                time.sleep(interval_seconds)
                
            except Exception as e:
                legacy_logger.log_error("Error in monitoring loop", e)
                time.sleep(interval_seconds)

# Instância global do gerenciador de alertas
alert_manager = AlertManager()

# Funções de conveniência
def start_alert_monitoring(interval_seconds: int = 60):
    """Inicia monitoramento de alertas"""
    alert_manager.start_monitoring(interval_seconds)

def stop_alert_monitoring():
    """Para monitoramento de alertas"""
    alert_manager.stop_monitoring()

def get_active_alerts():
    """Retorna alertas ativos"""
    return alert_manager.get_active_alerts()

def acknowledge_alert(alert_id: str, acknowledged_by: str):
    """Reconhece um alerta"""
    alert_manager.acknowledge_alert(alert_id, acknowledged_by)

def resolve_alert(alert_id: str):
    """Resolve um alerta"""
    alert_manager.resolve_alert(alert_id)