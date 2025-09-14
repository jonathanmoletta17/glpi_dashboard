# ===========================================
# CONFIGURAÇÕES DO SISTEMA DE MONITORAMENTO
# ===========================================

"""
Configuração centralizada do sistema de monitoramento legacy.

Este módulo define:
- Configurações de alertas e thresholds
- Configurações de logging
- Configurações de performance
- Configurações de notificações
"""

import os
from datetime import timedelta
from typing import Dict, Any

class MonitoringConfig:
    """
    Configurações centralizadas do sistema de monitoramento.
    """
    
    # ===========================================
    # CONFIGURAÇÕES GERAIS
    # ===========================================
    
    # Habilitar/desabilitar monitoramento
    ENABLED = os.getenv('MONITORING_ENABLED', 'true').lower() == 'true'
    
    # Intervalo de verificação de alertas (segundos)
    ALERT_CHECK_INTERVAL = int(os.getenv('MONITORING_ALERT_INTERVAL', '60'))
    
    # Auto-iniciar sistema de alertas
    AUTO_START_ALERTS = os.getenv('MONITORING_AUTO_START', 'true').lower() == 'true'
    
    # Diretório para logs de monitoramento
    LOG_DIR = os.getenv('MONITORING_LOG_DIR', 'logs/monitoring')
    
    # Nível de log padrão
    LOG_LEVEL = os.getenv('MONITORING_LOG_LEVEL', 'INFO').upper()
    
    # ===========================================
    # THRESHOLDS DE SISTEMA
    # ===========================================
    
    class SystemThresholds:
        """Thresholds para alertas de sistema"""
        
        # CPU
        CPU_WARNING = float(os.getenv('MONITORING_CPU_WARNING', '70.0'))
        CPU_CRITICAL = float(os.getenv('MONITORING_CPU_CRITICAL', '85.0'))
        
        # Memória
        MEMORY_WARNING = float(os.getenv('MONITORING_MEMORY_WARNING', '75.0'))
        MEMORY_CRITICAL = float(os.getenv('MONITORING_MEMORY_CRITICAL', '90.0'))
        
        # Disco
        DISK_WARNING = float(os.getenv('MONITORING_DISK_WARNING', '80.0'))
        DISK_CRITICAL = float(os.getenv('MONITORING_DISK_CRITICAL', '95.0'))
        
        # Tempo de resposta (segundos)
        RESPONSE_TIME_WARNING = float(os.getenv('MONITORING_RESPONSE_WARNING', '2.0'))
        RESPONSE_TIME_CRITICAL = float(os.getenv('MONITORING_RESPONSE_CRITICAL', '5.0'))
    
    # ===========================================
    # THRESHOLDS DE APLICAÇÃO
    # ===========================================
    
    class ApplicationThresholds:
        """Thresholds para alertas de aplicação"""
        
        # GLPI
        GLPI_TIMEOUT = float(os.getenv('MONITORING_GLPI_TIMEOUT', '10.0'))
        GLPI_MAX_RETRIES = int(os.getenv('MONITORING_GLPI_RETRIES', '3'))
        
        # Legacy Services
        LEGACY_TIMEOUT = float(os.getenv('MONITORING_LEGACY_TIMEOUT', '15.0'))
        LEGACY_MAX_RETRIES = int(os.getenv('MONITORING_LEGACY_RETRIES', '2'))
        
        # API Endpoints
        API_TIMEOUT = float(os.getenv('MONITORING_API_TIMEOUT', '30.0'))
        API_ERROR_RATE_WARNING = float(os.getenv('MONITORING_API_ERROR_WARNING', '5.0'))  # %
        API_ERROR_RATE_CRITICAL = float(os.getenv('MONITORING_API_ERROR_CRITICAL', '15.0'))  # %
    
    # ===========================================
    # CONFIGURAÇÕES DE LOGGING
    # ===========================================
    
    class LoggingConfig:
        """Configurações de logging estruturado"""
        
        # Formato de timestamp
        TIMESTAMP_FORMAT = '%Y-%m-%d %H:%M:%S.%f'
        
        # Rotação de logs
        MAX_LOG_SIZE_MB = int(os.getenv('MONITORING_MAX_LOG_SIZE', '100'))
        MAX_LOG_FILES = int(os.getenv('MONITORING_MAX_LOG_FILES', '10'))
        
        # Retenção de logs (dias)
        LOG_RETENTION_DAYS = int(os.getenv('MONITORING_LOG_RETENTION', '30'))
        
        # Categorias de log habilitadas
        ENABLED_CATEGORIES = [
            'SYSTEM',
            'API', 
            'GLPI',
            'LEGACY',
            'PERFORMANCE',
            'SECURITY',
            'ERROR'
        ]
        
        # Níveis de log por categoria
        CATEGORY_LEVELS = {
            'SYSTEM': os.getenv('MONITORING_SYSTEM_LOG_LEVEL', 'INFO'),
            'API': os.getenv('MONITORING_API_LOG_LEVEL', 'INFO'),
            'GLPI': os.getenv('MONITORING_GLPI_LOG_LEVEL', 'INFO'),
            'LEGACY': os.getenv('MONITORING_LEGACY_LOG_LEVEL', 'INFO'),
            'PERFORMANCE': os.getenv('MONITORING_PERFORMANCE_LOG_LEVEL', 'INFO'),
            'SECURITY': os.getenv('MONITORING_SECURITY_LOG_LEVEL', 'WARNING'),
            'ERROR': os.getenv('MONITORING_ERROR_LOG_LEVEL', 'ERROR')
        }
    
    # ===========================================
    # CONFIGURAÇÕES DE ALERTAS
    # ===========================================
    
    class AlertConfig:
        """Configurações do sistema de alertas"""
        
        # Intervalo mínimo entre alertas do mesmo tipo (segundos)
        MIN_ALERT_INTERVAL = int(os.getenv('MONITORING_MIN_ALERT_INTERVAL', '300'))  # 5 min
        
        # Máximo de alertas por hora
        MAX_ALERTS_PER_HOUR = int(os.getenv('MONITORING_MAX_ALERTS_HOUR', '20'))
        
        # Retenção de histórico de alertas (dias)
        ALERT_RETENTION_DAYS = int(os.getenv('MONITORING_ALERT_RETENTION', '90'))
        
        # Escalação automática
        AUTO_ESCALATION_ENABLED = os.getenv('MONITORING_AUTO_ESCALATION', 'true').lower() == 'true'
        ESCALATION_THRESHOLD_MINUTES = int(os.getenv('MONITORING_ESCALATION_THRESHOLD', '30'))
        
        # Notificações
        EMAIL_ENABLED = os.getenv('MONITORING_EMAIL_ENABLED', 'false').lower() == 'true'
        WEBHOOK_ENABLED = os.getenv('MONITORING_WEBHOOK_ENABLED', 'false').lower() == 'true'
        
        # Configurações de email
        EMAIL_SMTP_HOST = os.getenv('MONITORING_SMTP_HOST', 'localhost')
        EMAIL_SMTP_PORT = int(os.getenv('MONITORING_SMTP_PORT', '587'))
        EMAIL_USERNAME = os.getenv('MONITORING_SMTP_USERNAME', '')
        EMAIL_PASSWORD = os.getenv('MONITORING_SMTP_PASSWORD', '')
        EMAIL_FROM = os.getenv('MONITORING_EMAIL_FROM', 'monitoring@glpi-dashboard.local')
        EMAIL_TO = os.getenv('MONITORING_EMAIL_TO', '').split(',')
        
        # Configurações de webhook
        WEBHOOK_URL = os.getenv('MONITORING_WEBHOOK_URL', '')
        WEBHOOK_TIMEOUT = float(os.getenv('MONITORING_WEBHOOK_TIMEOUT', '10.0'))
    
    # ===========================================
    # CONFIGURAÇÕES DE PERFORMANCE
    # ===========================================
    
    class PerformanceConfig:
        """Configurações de monitoramento de performance"""
        
        # Histórico de métricas
        METRICS_HISTORY_SIZE = int(os.getenv('MONITORING_METRICS_HISTORY', '1000'))
        METRICS_RETENTION_HOURS = int(os.getenv('MONITORING_METRICS_RETENTION', '24'))
        
        # Sampling de operações
        OPERATION_SAMPLING_RATE = float(os.getenv('MONITORING_SAMPLING_RATE', '1.0'))  # 100%
        
        # Benchmark automático
        AUTO_BENCHMARK_ENABLED = os.getenv('MONITORING_AUTO_BENCHMARK', 'true').lower() == 'true'
        BENCHMARK_INTERVAL_MINUTES = int(os.getenv('MONITORING_BENCHMARK_INTERVAL', '15'))
        
        # Thresholds de performance
        SLOW_OPERATION_THRESHOLD = float(os.getenv('MONITORING_SLOW_THRESHOLD', '1.0'))  # segundos
        VERY_SLOW_OPERATION_THRESHOLD = float(os.getenv('MONITORING_VERY_SLOW_THRESHOLD', '5.0'))  # segundos
    
    # ===========================================
    # CONFIGURAÇÕES DE DASHBOARD
    # ===========================================
    
    class DashboardConfig:
        """Configurações do dashboard de monitoramento"""
        
        # Atualização automática
        AUTO_REFRESH_ENABLED = os.getenv('MONITORING_AUTO_REFRESH', 'true').lower() == 'true'
        REFRESH_INTERVAL_SECONDS = int(os.getenv('MONITORING_REFRESH_INTERVAL', '30'))
        
        # Dados exibidos
        SHOW_SYSTEM_METRICS = os.getenv('MONITORING_SHOW_SYSTEM', 'true').lower() == 'true'
        SHOW_APPLICATION_METRICS = os.getenv('MONITORING_SHOW_APP', 'true').lower() == 'true'
        SHOW_PERFORMANCE_METRICS = os.getenv('MONITORING_SHOW_PERF', 'true').lower() == 'true'
        SHOW_ALERT_HISTORY = os.getenv('MONITORING_SHOW_ALERTS', 'true').lower() == 'true'
        
        # Limites de exibição
        MAX_RECENT_ALERTS = int(os.getenv('MONITORING_MAX_RECENT_ALERTS', '50'))
        MAX_PERFORMANCE_ENTRIES = int(os.getenv('MONITORING_MAX_PERF_ENTRIES', '100'))
    
    # ===========================================
    # MÉTODOS UTILITÁRIOS
    # ===========================================
    
    @classmethod
    def get_all_config(cls) -> Dict[str, Any]:
        """Retorna todas as configurações como dicionário"""
        config = {}
        
        # Configurações gerais
        config['general'] = {
            'enabled': cls.ENABLED,
            'alert_check_interval': cls.ALERT_CHECK_INTERVAL,
            'auto_start_alerts': cls.AUTO_START_ALERTS,
            'log_dir': cls.LOG_DIR,
            'log_level': cls.LOG_LEVEL
        }
        
        # Thresholds
        config['system_thresholds'] = {
            'cpu_warning': cls.SystemThresholds.CPU_WARNING,
            'cpu_critical': cls.SystemThresholds.CPU_CRITICAL,
            'memory_warning': cls.SystemThresholds.MEMORY_WARNING,
            'memory_critical': cls.SystemThresholds.MEMORY_CRITICAL,
            'disk_warning': cls.SystemThresholds.DISK_WARNING,
            'disk_critical': cls.SystemThresholds.DISK_CRITICAL,
            'response_time_warning': cls.SystemThresholds.RESPONSE_TIME_WARNING,
            'response_time_critical': cls.SystemThresholds.RESPONSE_TIME_CRITICAL
        }
        
        config['application_thresholds'] = {
            'glpi_timeout': cls.ApplicationThresholds.GLPI_TIMEOUT,
            'glpi_max_retries': cls.ApplicationThresholds.GLPI_MAX_RETRIES,
            'legacy_timeout': cls.ApplicationThresholds.LEGACY_TIMEOUT,
            'legacy_max_retries': cls.ApplicationThresholds.LEGACY_MAX_RETRIES,
            'api_timeout': cls.ApplicationThresholds.API_TIMEOUT,
            'api_error_rate_warning': cls.ApplicationThresholds.API_ERROR_RATE_WARNING,
            'api_error_rate_critical': cls.ApplicationThresholds.API_ERROR_RATE_CRITICAL
        }
        
        # Logging
        config['logging'] = {
            'timestamp_format': cls.LoggingConfig.TIMESTAMP_FORMAT,
            'max_log_size_mb': cls.LoggingConfig.MAX_LOG_SIZE_MB,
            'max_log_files': cls.LoggingConfig.MAX_LOG_FILES,
            'log_retention_days': cls.LoggingConfig.LOG_RETENTION_DAYS,
            'enabled_categories': cls.LoggingConfig.ENABLED_CATEGORIES,
            'category_levels': cls.LoggingConfig.CATEGORY_LEVELS
        }
        
        # Alertas
        config['alerts'] = {
            'min_alert_interval': cls.AlertConfig.MIN_ALERT_INTERVAL,
            'max_alerts_per_hour': cls.AlertConfig.MAX_ALERTS_PER_HOUR,
            'alert_retention_days': cls.AlertConfig.ALERT_RETENTION_DAYS,
            'auto_escalation_enabled': cls.AlertConfig.AUTO_ESCALATION_ENABLED,
            'escalation_threshold_minutes': cls.AlertConfig.ESCALATION_THRESHOLD_MINUTES,
            'email_enabled': cls.AlertConfig.EMAIL_ENABLED,
            'webhook_enabled': cls.AlertConfig.WEBHOOK_ENABLED
        }
        
        # Performance
        config['performance'] = {
            'metrics_history_size': cls.PerformanceConfig.METRICS_HISTORY_SIZE,
            'metrics_retention_hours': cls.PerformanceConfig.METRICS_RETENTION_HOURS,
            'operation_sampling_rate': cls.PerformanceConfig.OPERATION_SAMPLING_RATE,
            'auto_benchmark_enabled': cls.PerformanceConfig.AUTO_BENCHMARK_ENABLED,
            'benchmark_interval_minutes': cls.PerformanceConfig.BENCHMARK_INTERVAL_MINUTES,
            'slow_operation_threshold': cls.PerformanceConfig.SLOW_OPERATION_THRESHOLD,
            'very_slow_operation_threshold': cls.PerformanceConfig.VERY_SLOW_OPERATION_THRESHOLD
        }
        
        # Dashboard
        config['dashboard'] = {
            'auto_refresh_enabled': cls.DashboardConfig.AUTO_REFRESH_ENABLED,
            'refresh_interval_seconds': cls.DashboardConfig.REFRESH_INTERVAL_SECONDS,
            'show_system_metrics': cls.DashboardConfig.SHOW_SYSTEM_METRICS,
            'show_application_metrics': cls.DashboardConfig.SHOW_APPLICATION_METRICS,
            'show_performance_metrics': cls.DashboardConfig.SHOW_PERFORMANCE_METRICS,
            'show_alert_history': cls.DashboardConfig.SHOW_ALERT_HISTORY,
            'max_recent_alerts': cls.DashboardConfig.MAX_RECENT_ALERTS,
            'max_performance_entries': cls.DashboardConfig.MAX_PERFORMANCE_ENTRIES
        }
        
        return config
    
    @classmethod
    def validate_config(cls) -> Dict[str, Any]:
        """Valida configurações e retorna relatório"""
        issues = []
        warnings = []
        
        # Validar thresholds
        if cls.SystemThresholds.CPU_WARNING >= cls.SystemThresholds.CPU_CRITICAL:
            issues.append("CPU warning threshold deve ser menor que critical")
        
        if cls.SystemThresholds.MEMORY_WARNING >= cls.SystemThresholds.MEMORY_CRITICAL:
            issues.append("Memory warning threshold deve ser menor que critical")
        
        if cls.SystemThresholds.DISK_WARNING >= cls.SystemThresholds.DISK_CRITICAL:
            issues.append("Disk warning threshold deve ser menor que critical")
        
        # Validar configurações de email
        if cls.AlertConfig.EMAIL_ENABLED:
            if not cls.AlertConfig.EMAIL_SMTP_HOST:
                issues.append("SMTP host é obrigatório quando email está habilitado")
            if not cls.AlertConfig.EMAIL_TO:
                warnings.append("Nenhum destinatário de email configurado")
        
        # Validar configurações de webhook
        if cls.AlertConfig.WEBHOOK_ENABLED:
            if not cls.AlertConfig.WEBHOOK_URL:
                issues.append("Webhook URL é obrigatória quando webhook está habilitado")
        
        # Validar intervalos
        if cls.ALERT_CHECK_INTERVAL < 10:
            warnings.append("Intervalo de verificação de alertas muito baixo (< 10s)")
        
        if cls.PerformanceConfig.OPERATION_SAMPLING_RATE > 1.0:
            issues.append("Taxa de sampling não pode ser maior que 1.0")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings,
            'total_issues': len(issues),
            'total_warnings': len(warnings)
        }
    
    @classmethod
    def get_environment_template(cls) -> str:
        """Retorna template de variáveis de ambiente"""
        return """
# ===========================================
# CONFIGURAÇÕES DE MONITORAMENTO
# ===========================================

# Geral
MONITORING_ENABLED=true
MONITORING_ALERT_INTERVAL=60
MONITORING_AUTO_START=true
MONITORING_LOG_DIR=logs/monitoring
MONITORING_LOG_LEVEL=INFO

# Thresholds de Sistema
MONITORING_CPU_WARNING=70.0
MONITORING_CPU_CRITICAL=85.0
MONITORING_MEMORY_WARNING=75.0
MONITORING_MEMORY_CRITICAL=90.0
MONITORING_DISK_WARNING=80.0
MONITORING_DISK_CRITICAL=95.0
MONITORING_RESPONSE_WARNING=2.0
MONITORING_RESPONSE_CRITICAL=5.0

# Thresholds de Aplicação
MONITORING_GLPI_TIMEOUT=10.0
MONITORING_GLPI_RETRIES=3
MONITORING_LEGACY_TIMEOUT=15.0
MONITORING_LEGACY_RETRIES=2
MONITORING_API_TIMEOUT=30.0
MONITORING_API_ERROR_WARNING=5.0
MONITORING_API_ERROR_CRITICAL=15.0

# Alertas
MONITORING_MIN_ALERT_INTERVAL=300
MONITORING_MAX_ALERTS_HOUR=20
MONITORING_ALERT_RETENTION=90
MONITORING_AUTO_ESCALATION=true
MONITORING_ESCALATION_THRESHOLD=30

# Notificações por Email
MONITORING_EMAIL_ENABLED=false
MONITORING_SMTP_HOST=localhost
MONITORING_SMTP_PORT=587
MONITORING_SMTP_USERNAME=
MONITORING_SMTP_PASSWORD=
MONITORING_EMAIL_FROM=monitoring@glpi-dashboard.local
MONITORING_EMAIL_TO=admin@company.com,ops@company.com

# Notificações por Webhook
MONITORING_WEBHOOK_ENABLED=false
MONITORING_WEBHOOK_URL=
MONITORING_WEBHOOK_TIMEOUT=10.0

# Performance
MONITORING_METRICS_HISTORY=1000
MONITORING_METRICS_RETENTION=24
MONITORING_SAMPLING_RATE=1.0
MONITORING_AUTO_BENCHMARK=true
MONITORING_BENCHMARK_INTERVAL=15
MONITORING_SLOW_THRESHOLD=1.0
MONITORING_VERY_SLOW_THRESHOLD=5.0

# Dashboard
MONITORING_AUTO_REFRESH=true
MONITORING_REFRESH_INTERVAL=30
MONITORING_SHOW_SYSTEM=true
MONITORING_SHOW_APP=true
MONITORING_SHOW_PERF=true
MONITORING_SHOW_ALERTS=true
MONITORING_MAX_RECENT_ALERTS=50
MONITORING_MAX_PERF_ENTRIES=100
"""

# Instância global de configuração
monitoring_config = MonitoringConfig()