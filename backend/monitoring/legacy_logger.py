# ===========================================
# SISTEMA DE LOGS ESTRUTURADOS LEGACY
# ===========================================

import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum
import traceback
import os

class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class LogCategory(Enum):
    SYSTEM = "system"
    GLPI = "glpi"
    LEGACY_ADAPTER = "legacy_adapter"
    PERFORMANCE = "performance"
    SECURITY = "security"
    MIGRATION = "migration"
    API = "api"

class StructuredLogger:
    def __init__(self, name: str = "legacy_monitoring"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Configurar handler para arquivo
        log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # Handler para logs gerais
        file_handler = logging.FileHandler(
            os.path.join(log_dir, 'legacy_monitoring.log'),
            encoding='utf-8'
        )
        file_handler.setLevel(logging.INFO)
        
        # Handler para logs de erro
        error_handler = logging.FileHandler(
            os.path.join(log_dir, 'legacy_errors.log'),
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        
        # Handler para console
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        
        # Formatter estruturado
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        file_handler.setFormatter(formatter)
        error_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(error_handler)
        self.logger.addHandler(console_handler)
    
    def _create_log_entry(self, 
                         level: LogLevel, 
                         category: LogCategory, 
                         message: str, 
                         **kwargs) -> Dict[str, Any]:
        """Cria entrada de log estruturada"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'level': level.value,
            'category': category.value,
            'message': message,
            'metadata': kwargs
        }
        
        # Adicionar informações de contexto se disponíveis
        if 'request_id' not in kwargs:
            log_entry['metadata']['session_id'] = id(self)
        
        return log_entry
    
    def log(self, level: LogLevel, category: LogCategory, message: str, **kwargs):
        """Log genérico estruturado"""
        log_entry = self._create_log_entry(level, category, message, **kwargs)
        log_message = json.dumps(log_entry, ensure_ascii=False)
        
        if level == LogLevel.DEBUG:
            self.logger.debug(log_message)
        elif level == LogLevel.INFO:
            self.logger.info(log_message)
        elif level == LogLevel.WARNING:
            self.logger.warning(log_message)
        elif level == LogLevel.ERROR:
            self.logger.error(log_message)
        elif level == LogLevel.CRITICAL:
            self.logger.critical(log_message)
    
    def log_system_event(self, message: str, **kwargs):
        """Log de eventos do sistema"""
        self.log(LogLevel.INFO, LogCategory.SYSTEM, message, **kwargs)
    
    def log_glpi_event(self, message: str, **kwargs):
        """Log de eventos GLPI"""
        self.log(LogLevel.INFO, LogCategory.GLPI, message, **kwargs)
    
    def log_legacy_event(self, message: str, **kwargs):
        """Log de eventos do adapter legacy"""
        self.log(LogLevel.INFO, LogCategory.LEGACY_ADAPTER, message, **kwargs)
    
    def log_performance(self, operation: str, duration_ms: float, **kwargs):
        """Log de métricas de performance"""
        self.log(
            LogLevel.INFO, 
            LogCategory.PERFORMANCE, 
            f"Operation '{operation}' completed",
            operation=operation,
            duration_ms=duration_ms,
            **kwargs
        )
    
    def log_error(self, message: str, exception: Optional[Exception] = None, **kwargs):
        """Log de erros com stack trace"""
        error_data = kwargs.copy()
        
        if exception:
            error_data.update({
                'exception_type': type(exception).__name__,
                'exception_message': str(exception),
                'stack_trace': traceback.format_exc()
            })
        
        self.log(LogLevel.ERROR, LogCategory.SYSTEM, message, **error_data)
    
    def log_security_event(self, message: str, **kwargs):
        """Log de eventos de segurança"""
        self.log(LogLevel.WARNING, LogCategory.SECURITY, message, **kwargs)
    
    def log_migration_event(self, message: str, **kwargs):
        """Log de eventos de migração"""
        self.log(LogLevel.INFO, LogCategory.MIGRATION, message, **kwargs)
    
    def log_api_request(self, method: str, endpoint: str, status_code: int, duration_ms: float, **kwargs):
        """Log de requisições API"""
        self.log(
            LogLevel.INFO,
            LogCategory.API,
            f"{method} {endpoint} - {status_code}",
            method=method,
            endpoint=endpoint,
            status_code=status_code,
            duration_ms=duration_ms,
            **kwargs
        )

class PerformanceLogger:
    """Logger especializado para métricas de performance"""
    
    def __init__(self, logger: StructuredLogger):
        self.logger = logger
        self.active_operations = {}
    
    def start_operation(self, operation_id: str, operation_name: str, **kwargs):
        """Inicia tracking de uma operação"""
        self.active_operations[operation_id] = {
            'name': operation_name,
            'start_time': datetime.now(),
            'metadata': kwargs
        }
        
        self.logger.log(
            LogLevel.DEBUG,
            LogCategory.PERFORMANCE,
            f"Started operation: {operation_name}",
            operation_id=operation_id,
            **kwargs
        )
    
    def end_operation(self, operation_id: str, success: bool = True, **kwargs):
        """Finaliza tracking de uma operação"""
        if operation_id not in self.active_operations:
            self.logger.log_error(f"Operation {operation_id} not found in active operations")
            return
        
        operation = self.active_operations.pop(operation_id)
        end_time = datetime.now()
        duration = (end_time - operation['start_time']).total_seconds() * 1000
        
        log_data = {
            'operation_id': operation_id,
            'operation_name': operation['name'],
            'duration_ms': round(duration, 2),
            'success': success,
            **operation['metadata'],
            **kwargs
        }
        
        level = LogLevel.INFO if success else LogLevel.WARNING
        message = f"Completed operation: {operation['name']} ({'success' if success else 'failed'})"
        
        self.logger.log(level, LogCategory.PERFORMANCE, message, **log_data)
    
    def log_metric(self, metric_name: str, value: float, unit: str = "", **kwargs):
        """Log de métrica específica"""
        self.logger.log(
            LogLevel.INFO,
            LogCategory.PERFORMANCE,
            f"Metric: {metric_name} = {value} {unit}",
            metric_name=metric_name,
            value=value,
            unit=unit,
            **kwargs
        )

class AlertLogger:
    """Logger especializado para alertas"""
    
    def __init__(self, logger: StructuredLogger):
        self.logger = logger
    
    def log_threshold_alert(self, metric: str, current_value: float, threshold: float, **kwargs):
        """Log de alerta por threshold"""
        self.logger.log(
            LogLevel.WARNING,
            LogCategory.SYSTEM,
            f"Threshold alert: {metric} = {current_value} (threshold: {threshold})",
            alert_type="threshold",
            metric=metric,
            current_value=current_value,
            threshold=threshold,
            **kwargs
        )
    
    def log_service_alert(self, service: str, status: str, **kwargs):
        """Log de alerta de serviço"""
        level = LogLevel.ERROR if status == 'down' else LogLevel.WARNING
        
        self.logger.log(
            level,
            LogCategory.SYSTEM,
            f"Service alert: {service} is {status}",
            alert_type="service",
            service=service,
            status=status,
            **kwargs
        )
    
    def log_connectivity_alert(self, target: str, error: str, **kwargs):
        """Log de alerta de conectividade"""
        self.logger.log(
            LogLevel.ERROR,
            LogCategory.SYSTEM,
            f"Connectivity alert: Failed to connect to {target}",
            alert_type="connectivity",
            target=target,
            error=error,
            **kwargs
        )

# Instâncias globais
legacy_logger = StructuredLogger("legacy_monitoring")
performance_logger = PerformanceLogger(legacy_logger)
alert_logger = AlertLogger(legacy_logger)

# Funções de conveniência
def log_system_event(message: str, **kwargs):
    legacy_logger.log_system_event(message, **kwargs)

def log_glpi_event(message: str, **kwargs):
    legacy_logger.log_glpi_event(message, **kwargs)

def log_legacy_event(message: str, **kwargs):
    legacy_logger.log_legacy_event(message, **kwargs)

def log_performance(operation: str, duration_ms: float, **kwargs):
    legacy_logger.log_performance(operation, duration_ms, **kwargs)

def log_error(message: str, exception: Optional[Exception] = None, **kwargs):
    legacy_logger.log_error(message, exception, **kwargs)

def log_migration_event(message: str, **kwargs):
    legacy_logger.log_migration_event(message, **kwargs)

def log_api_request(method: str, endpoint: str, status_code: int, duration_ms: float, **kwargs):
    legacy_logger.log_api_request(method, endpoint, status_code, duration_ms, **kwargs)