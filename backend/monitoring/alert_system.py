# ===========================================
# SISTEMA DE ALERTAS LEGACY
# ===========================================

import smtplib
import json
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import logging
from backend.config.settings import Config

class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class Alert:
    level: AlertLevel
    title: str
    message: str
    component: str
    timestamp: datetime
    metadata: Dict = None
    
    def to_dict(self):
        return {
            'level': self.level.value,
            'title': self.title,
            'message': self.message,
            'component': self.component,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata or {}
        }

class AlertManager:
    def __init__(self):
        self.config = Config()
        self.logger = logging.getLogger(__name__)
        self.alert_history = []
        self.alert_thresholds = {
            'cpu_percent': 80,
            'memory_percent': 85,
            'disk_percent': 90,
            'response_time_ms': 5000,
            'error_rate_percent': 10
        }
        self.cooldown_periods = {}  # Para evitar spam de alertas
    
    def check_system_health(self, health_data: Dict) -> List[Alert]:
        """Verifica saúde do sistema e gera alertas"""
        alerts = []
        
        # Verificar status geral
        overall_status = health_data.get('overall_status')
        if overall_status == 'error':
            alerts.append(Alert(
                level=AlertLevel.CRITICAL,
                title="Sistema com Falha Crítica",
                message="O sistema está com falha crítica. Verificação imediata necessária.",
                component="system",
                timestamp=datetime.now(),
                metadata=health_data
            ))
        elif overall_status == 'degraded':
            alerts.append(Alert(
                level=AlertLevel.WARNING,
                title="Sistema Degradado",
                message="O sistema está operando em modo degradado.",
                component="system",
                timestamp=datetime.now(),
                metadata=health_data
            ))
        
        # Verificar métricas do sistema
        system_data = health_data.get('system', {})
        
        if system_data.get('cpu_percent', 0) > self.alert_thresholds['cpu_percent']:
            alerts.append(Alert(
                level=AlertLevel.WARNING,
                title="Alto Uso de CPU",
                message=f"CPU em {system_data['cpu_percent']}% (limite: {self.alert_thresholds['cpu_percent']}%)",
                component="system.cpu",
                timestamp=datetime.now(),
                metadata={'cpu_percent': system_data['cpu_percent']}
            ))
        
        if system_data.get('memory_percent', 0) > self.alert_thresholds['memory_percent']:
            alerts.append(Alert(
                level=AlertLevel.WARNING,
                title="Alto Uso de Memória",
                message=f"Memória em {system_data['memory_percent']}% (limite: {self.alert_thresholds['memory_percent']}%)",
                component="system.memory",
                timestamp=datetime.now(),
                metadata={'memory_percent': system_data['memory_percent']}
            ))
        
        # Verificar serviços
        services = health_data.get('services', {})
        
        for service_name, service_data in services.items():
            if service_data.get('status') != 'healthy':
                level = AlertLevel.CRITICAL if service_data.get('status') == 'error' else AlertLevel.WARNING
                alerts.append(Alert(
                    level=level,
                    title=f"Serviço {service_name} com Problema",
                    message=f"Serviço {service_name} está {service_data.get('status')}",
                    component=f"service.{service_name}",
                    timestamp=datetime.now(),
                    metadata=service_data
                ))
            
            response_time = service_data.get('response_time_ms', 0)
            if response_time > self.alert_thresholds['response_time_ms']:
                alerts.append(Alert(
                    level=AlertLevel.WARNING,
                    title=f"Serviço {service_name} Lento",
                    message=f"Tempo de resposta: {response_time}ms (limite: {self.alert_thresholds['response_time_ms']}ms)",
                    component=f"service.{service_name}.performance",
                    timestamp=datetime.now(),
                    metadata={'response_time_ms': response_time}
                ))
        
        return alerts
    
    def check_performance_metrics(self, metrics_data: Dict) -> List[Alert]:
        """Verifica métricas de performance e gera alertas"""
        alerts = []
        
        operations = metrics_data.get('operations', {})
        overall_performance = metrics_data.get('overall_performance')
        
        if overall_performance == 'poor':
            alerts.append(Alert(
                level=AlertLevel.ERROR,
                title="Performance Degradada",
                message="Performance geral do sistema está ruim. Múltiplas operações falhando.",
                component="performance",
                timestamp=datetime.now(),
                metadata=metrics_data
            ))
        elif overall_performance == 'acceptable':
            alerts.append(Alert(
                level=AlertLevel.WARNING,
                title="Performance Aceitável",
                message="Performance do sistema está apenas aceitável. Monitoramento necessário.",
                component="performance",
                timestamp=datetime.now(),
                metadata=metrics_data
            ))
        
        # Verificar operações específicas
        for operation_name, operation_data in operations.items():
            if not operation_data.get('success'):
                alerts.append(Alert(
                    level=AlertLevel.ERROR,
                    title=f"Operação {operation_name} Falhando",
                    message=f"Operação {operation_name} está falhando: {operation_data.get('error', 'Erro desconhecido')}",
                    component=f"operation.{operation_name}",
                    timestamp=datetime.now(),
                    metadata=operation_data
                ))
            elif operation_data.get('status') == 'slow':
                alerts.append(Alert(
                    level=AlertLevel.WARNING,
                    title=f"Operação {operation_name} Lenta",
                    message=f"Operação {operation_name} está lenta: {operation_data.get('response_time_ms')}ms",
                    component=f"operation.{operation_name}",
                    timestamp=datetime.now(),
                    metadata=operation_data
                ))
        
        return alerts
    
    def process_alerts(self, alerts: List[Alert]):
        """Processa lista de alertas aplicando cooldown e enviando notificações"""
        for alert in alerts:
            # Verificar cooldown
            cooldown_key = f"{alert.component}_{alert.level.value}"
            last_alert_time = self.cooldown_periods.get(cooldown_key)
            
            if last_alert_time:
                time_since_last = datetime.now() - last_alert_time
                cooldown_minutes = 15 if alert.level == AlertLevel.CRITICAL else 30
                
                if time_since_last < timedelta(minutes=cooldown_minutes):
                    continue  # Pular alerta devido ao cooldown
            
            # Registrar alerta
            self.alert_history.append(alert)
            self.cooldown_periods[cooldown_key] = datetime.now()
            
            # Log estruturado
            self.logger.warning(
                f"ALERT: {alert.title}",
                extra={
                    'alert_level': alert.level.value,
                    'component': alert.component,
                    'message': alert.message,
                    'metadata': alert.metadata
                }
            )
            
            # Enviar notificações
            self._send_notifications(alert)
    
    def _send_notifications(self, alert: Alert):
        """Envia notificações do alerta"""
        try:
            # Email (apenas para alertas críticos e erros)
            if alert.level in [AlertLevel.CRITICAL, AlertLevel.ERROR]:
                self._send_email_alert(alert)
            
            # Slack (todos os alertas)
            self._send_slack_alert(alert)
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar notificações: {e}")
    
    def _send_email_alert(self, alert: Alert):
        """Envia alerta por email"""
        try:
            smtp_server = getattr(self.config, 'SMTP_SERVER', None)
            smtp_port = getattr(self.config, 'SMTP_PORT', 587)
            smtp_user = getattr(self.config, 'SMTP_USER', None)
            smtp_password = getattr(self.config, 'SMTP_PASSWORD', None)
            alert_emails = getattr(self.config, 'ALERT_EMAILS', '').split(',')
            
            if not all([smtp_server, smtp_user, smtp_password]) or not alert_emails:
                return
            
            msg = MIMEMultipart()
            msg['From'] = smtp_user
            msg['To'] = ', '.join(alert_emails)
            msg['Subject'] = f"[GLPI Dashboard] {alert.level.value.upper()}: {alert.title}"
            
            body = f"""
            ALERTA DO SISTEMA GLPI DASHBOARD
            
            Nível: {alert.level.value.upper()}
            Componente: {alert.component}
            Timestamp: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
            
            Mensagem:
            {alert.message}
            
            Metadados:
            {json.dumps(alert.metadata, indent=2) if alert.metadata else 'Nenhum'}
            
            ---
            Sistema de Monitoramento GLPI Dashboard
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
            server.quit()
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar email: {e}")
    
    def _send_slack_alert(self, alert: Alert):
        """Envia alerta para Slack"""
        try:
            slack_webhook = getattr(self.config, 'SLACK_WEBHOOK_URL', None)
            if not slack_webhook:
                return
            
            # Mapear níveis para cores
            color_map = {
                AlertLevel.INFO: '#36a64f',
                AlertLevel.WARNING: '#ff9500',
                AlertLevel.ERROR: '#ff0000',
                AlertLevel.CRITICAL: '#8b0000'
            }
            
            # Mapear níveis para emojis
            emoji_map = {
                AlertLevel.INFO: ':information_source:',
                AlertLevel.WARNING: ':warning:',
                AlertLevel.ERROR: ':x:',
                AlertLevel.CRITICAL: ':rotating_light:'
            }
            
            payload = {
                'username': 'GLPI Dashboard Monitor',
                'icon_emoji': ':computer:',
                'attachments': [{
                    'color': color_map[alert.level],
                    'title': f"{emoji_map[alert.level]} {alert.title}",
                    'text': alert.message,
                    'fields': [
                        {
                            'title': 'Nível',
                            'value': alert.level.value.upper(),
                            'short': True
                        },
                        {
                            'title': 'Componente',
                            'value': alert.component,
                            'short': True
                        },
                        {
                            'title': 'Timestamp',
                            'value': alert.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                            'short': True
                        }
                    ],
                    'footer': 'GLPI Dashboard Monitor',
                    'ts': int(alert.timestamp.timestamp())
                }]
            }
            
            response = requests.post(slack_webhook, json=payload, timeout=10)
            response.raise_for_status()
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar Slack: {e}")
    
    def get_alert_history(self, hours: int = 24) -> List[Dict]:
        """Retorna histórico de alertas"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_alerts = [
            alert for alert in self.alert_history 
            if alert.timestamp > cutoff_time
        ]
        return [alert.to_dict() for alert in recent_alerts]

# Instância global
alert_manager = AlertManager()