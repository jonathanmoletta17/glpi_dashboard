# ===========================================
# MÓDULO DE MONITORAMENTO LEGACY
# ===========================================

"""
Módulo de monitoramento completo para serviços legacy.

Este módulo fornece:
- Dashboard de monitoramento em tempo real
- Sistema de logs estruturados
- Alertas automáticos com notificações
- Métricas de performance
- Histórico de eventos

Componentes principais:
- LegacyMonitoringService: Serviço principal de monitoramento
- StructuredLogger: Sistema de logs estruturados
- AlertManager: Gerenciador de alertas automáticos

Uso básico:
    from backend.monitoring import (
        monitoring_service,
        legacy_logger,
        alert_manager,
        start_monitoring
    )
    
    # Iniciar monitoramento completo
    start_monitoring()
    
    # Obter status atual
    health = monitoring_service.get_system_health()
    
    # Log de evento
    legacy_logger.log_system_event("Sistema iniciado")
    
    # Verificar alertas
    alerts = alert_manager.get_active_alerts()
"""

from .legacy_dashboard import (
    monitoring_service,
    monitoring_bp,
    LegacyMonitoringService
)

from .legacy_logger import (
    legacy_logger,
    performance_logger,
    alert_logger,
    StructuredLogger,
    PerformanceLogger,
    AlertLogger,
    LogLevel,
    LogCategory,
    log_system_event,
    log_glpi_event,
    log_legacy_event,
    log_performance,
    log_error,
    log_migration_event,
    log_api_request
)

from .legacy_alerts import (
    alert_manager,
    Alert,
    AlertRule,
    AlertManager,
    AlertSeverity,
    AlertStatus,
    start_alert_monitoring,
    stop_alert_monitoring,
    get_active_alerts,
    acknowledge_alert,
    resolve_alert
)

# Função de inicialização completa
def start_monitoring(alert_interval: int = 60, auto_start_alerts: bool = True):
    """
    Inicia o sistema de monitoramento completo.
    
    Args:
        alert_interval: Intervalo em segundos para verificação de alertas
        auto_start_alerts: Se deve iniciar automaticamente o monitoramento de alertas
    """
    try:
        # Log de inicialização
        legacy_logger.log_system_event(
            "Iniciando sistema de monitoramento legacy",
            alert_interval=alert_interval,
            auto_start_alerts=auto_start_alerts
        )
        
        # Iniciar monitoramento de alertas se solicitado
        if auto_start_alerts:
            start_alert_monitoring(alert_interval)
        
        # Log de sucesso
        legacy_logger.log_system_event(
            "Sistema de monitoramento legacy iniciado com sucesso"
        )
        
        return True
        
    except Exception as e:
        legacy_logger.log_error(
            "Falha ao iniciar sistema de monitoramento legacy",
            exception=e
        )
        return False

def stop_monitoring():
    """
    Para o sistema de monitoramento completo.
    """
    try:
        legacy_logger.log_system_event("Parando sistema de monitoramento legacy")
        
        # Parar monitoramento de alertas
        stop_alert_monitoring()
        
        legacy_logger.log_system_event(
            "Sistema de monitoramento legacy parado com sucesso"
        )
        
        return True
        
    except Exception as e:
        legacy_logger.log_error(
            "Falha ao parar sistema de monitoramento legacy",
            exception=e
        )
        return False

def get_monitoring_status():
    """
    Retorna status completo do sistema de monitoramento.
    """
    try:
        # Obter dados de saúde
        health_data = monitoring_service.get_system_health()
        
        # Obter métricas de performance
        performance_data = monitoring_service.get_performance_metrics()
        
        # Obter alertas ativos
        active_alerts = alert_manager.get_active_alerts()
        
        # Compilar status
        status = {
            'timestamp': health_data.get('timestamp'),
            'overall_status': health_data.get('overall_status', 'unknown'),
            'system_health': health_data.get('system', {}),
            'services_health': health_data.get('services', {}),
            'performance': {
                'overall': performance_data.get('overall_performance', 'unknown'),
                'operations': performance_data.get('operations', {})
            },
            'alerts': {
                'active_count': len(active_alerts),
                'active_alerts': [{
                    'id': alert.id,
                    'title': alert.title,
                    'severity': alert.severity.value,
                    'category': alert.category,
                    'timestamp': alert.timestamp.isoformat()
                } for alert in active_alerts]
            },
            'monitoring': {
                'alert_monitoring_active': alert_manager.running,
                'rules_count': len(alert_manager.alert_rules),
                'notification_handlers': len(alert_manager.notification_handlers)
            }
        }
        
        return status
        
    except Exception as e:
        legacy_logger.log_error(
            "Falha ao obter status do monitoramento",
            exception=e
        )
        return {
            'timestamp': None,
            'overall_status': 'error',
            'error': str(e)
        }

# Exportar principais componentes
__all__ = [
    # Serviços principais
    'monitoring_service',
    'legacy_logger',
    'alert_manager',
    
    # Blueprints
    'monitoring_bp',
    
    # Classes
    'LegacyMonitoringService',
    'StructuredLogger',
    'PerformanceLogger',
    'AlertLogger',
    'AlertManager',
    'Alert',
    'AlertRule',
    
    # Enums
    'LogLevel',
    'LogCategory',
    'AlertSeverity',
    'AlertStatus',
    
    # Funções de conveniência - Logging
    'log_system_event',
    'log_glpi_event',
    'log_legacy_event',
    'log_performance',
    'log_error',
    'log_migration_event',
    'log_api_request',
    
    # Funções de conveniência - Alertas
    'start_alert_monitoring',
    'stop_alert_monitoring',
    'get_active_alerts',
    'acknowledge_alert',
    'resolve_alert',
    
    # Funções de controle
    'start_monitoring',
    'stop_monitoring',
    'get_monitoring_status'
]