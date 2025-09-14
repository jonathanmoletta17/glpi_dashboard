# ===========================================
# INTEGRAÇÃO DO SISTEMA DE MONITORAMENTO
# ===========================================

"""
Módulo de integração do sistema de monitoramento com a aplicação Flask.

Este módulo:
- Registra blueprints de monitoramento
- Configura middleware de logging
- Inicializa sistema de alertas
- Fornece decorators para monitoramento automático
"""

from functools import wraps
import time
from datetime import datetime
from flask import Flask, request, g
from backend.monitoring import (
    monitoring_bp,
    legacy_logger,
    performance_logger,
    start_monitoring,
    log_api_request,
    log_system_event,
    log_error
)
from backend.monitoring.troubleshooting_api import troubleshooting_bp, register_troubleshooting_routes

def init_monitoring(app: Flask):
    """
    Inicializa o sistema de monitoramento na aplicação Flask.
    
    Args:
        app: Instância da aplicação Flask
    """
    try:
        # Registrar blueprint de monitoramento
        app.register_blueprint(monitoring_bp)
        
        # Registrar sistema de troubleshooting
        register_troubleshooting_routes(app)
        
        # Configurar middleware de logging
        setup_request_logging(app)
        
        # Configurar handlers de erro
        setup_error_handlers(app)
        
        # Inicializar sistema de monitoramento
        monitoring_started = start_monitoring(
            alert_interval=app.config.get('MONITORING_ALERT_INTERVAL', 60),
            auto_start_alerts=app.config.get('MONITORING_AUTO_START', True)
        )
        
        if monitoring_started:
            log_system_event(
                "Sistema de monitoramento e troubleshooting integrado com sucesso",
                app_name=app.name,
                monitoring_enabled=True,
                troubleshooting_enabled=True
            )
        else:
            log_error(
                "Falha ao integrar sistema de monitoramento",
                app_name=app.name
            )
        
        return monitoring_started
        
    except Exception as e:
        log_error(
            "Erro crítico na inicialização do monitoramento",
            exception=e,
            app_name=getattr(app, 'name', 'unknown')
        )
        return False

def setup_request_logging(app: Flask):
    """
    Configura logging automático de requisições.
    """
    
    @app.before_request
    def before_request():
        """Captura início da requisição"""
        g.start_time = time.time()
        g.request_id = f"{int(time.time() * 1000)}_{id(request)}"
        
        # Log de início da requisição (apenas para endpoints críticos)
        if request.endpoint and (
            request.endpoint.startswith('api.') or 
            request.endpoint.startswith('monitoring.')
        ):
            legacy_logger.log(
                legacy_logger.LogLevel.DEBUG,
                legacy_logger.LogCategory.API,
                f"Request started: {request.method} {request.path}",
                request_id=g.request_id,
                endpoint=request.endpoint,
                remote_addr=request.remote_addr,
                user_agent=request.headers.get('User-Agent', 'unknown')
            )
    
    @app.after_request
    def after_request(response):
        """Captura fim da requisição"""
        if hasattr(g, 'start_time'):
            duration_ms = (time.time() - g.start_time) * 1000
            
            # Log de fim da requisição
            log_api_request(
                method=request.method,
                endpoint=request.path,
                status_code=response.status_code,
                duration_ms=duration_ms,
                request_id=getattr(g, 'request_id', 'unknown'),
                content_length=response.content_length or 0
            )
            
            # Log de performance se requisição for lenta
            if duration_ms > 2000:  # Mais de 2 segundos
                legacy_logger.log(
                    legacy_logger.LogLevel.WARNING,
                    legacy_logger.LogCategory.PERFORMANCE,
                    f"Slow request detected: {request.method} {request.path}",
                    duration_ms=duration_ms,
                    status_code=response.status_code,
                    request_id=getattr(g, 'request_id', 'unknown')
                )
        
        return response

def setup_error_handlers(app: Flask):
    """
    Configura handlers de erro com logging automático.
    """
    
    @app.errorhandler(404)
    def handle_404(error):
        log_error(
            f"404 Not Found: {request.path}",
            status_code=404,
            method=request.method,
            remote_addr=request.remote_addr,
            request_id=getattr(g, 'request_id', 'unknown')
        )
        return {'error': 'Resource not found'}, 404
    
    @app.errorhandler(500)
    def handle_500(error):
        log_error(
            f"500 Internal Server Error: {request.path}",
            exception=error,
            status_code=500,
            method=request.method,
            remote_addr=request.remote_addr,
            request_id=getattr(g, 'request_id', 'unknown')
        )
        return {'error': 'Internal server error'}, 500
    
    @app.errorhandler(Exception)
    def handle_exception(error):
        log_error(
            f"Unhandled exception: {request.path}",
            exception=error,
            method=request.method,
            remote_addr=request.remote_addr,
            request_id=getattr(g, 'request_id', 'unknown')
        )
        return {'error': 'An unexpected error occurred'}, 500

# Decorators para monitoramento automático
def monitor_performance(operation_name: str = None):
    """
    Decorator para monitoramento automático de performance.
    
    Args:
        operation_name: Nome da operação (opcional, usa nome da função se não fornecido)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            operation_id = f"{op_name}_{int(time.time() * 1000)}"
            
            # Iniciar tracking
            performance_logger.start_operation(
                operation_id=operation_id,
                operation_name=op_name,
                function=func.__name__,
                module=func.__module__
            )
            
            try:
                # Executar função
                result = func(*args, **kwargs)
                
                # Finalizar tracking com sucesso
                performance_logger.end_operation(
                    operation_id=operation_id,
                    success=True
                )
                
                return result
                
            except Exception as e:
                # Finalizar tracking com erro
                performance_logger.end_operation(
                    operation_id=operation_id,
                    success=False,
                    error=str(e),
                    exception_type=type(e).__name__
                )
                
                # Re-raise a exceção
                raise
        
        return wrapper
    return decorator

def monitor_glpi_operation(operation_type: str = None):
    """
    Decorator específico para operações GLPI.
    
    Args:
        operation_type: Tipo da operação GLPI
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            op_type = operation_type or func.__name__
            start_time = time.time()
            
            try:
                # Log de início
                legacy_logger.log_glpi_event(
                    f"GLPI operation started: {op_type}",
                    operation=op_type,
                    function=func.__name__
                )
                
                # Executar função
                result = func(*args, **kwargs)
                
                # Calcular duração
                duration_ms = (time.time() - start_time) * 1000
                
                # Log de sucesso
                legacy_logger.log_glpi_event(
                    f"GLPI operation completed: {op_type}",
                    operation=op_type,
                    duration_ms=duration_ms,
                    success=True
                )
                
                return result
                
            except Exception as e:
                # Calcular duração
                duration_ms = (time.time() - start_time) * 1000
                
                # Log de erro
                legacy_logger.log_error(
                    f"GLPI operation failed: {op_type}",
                    exception=e,
                    operation=op_type,
                    duration_ms=duration_ms
                )
                
                # Re-raise a exceção
                raise
        
        return wrapper
    return decorator

def monitor_legacy_adapter(adapter_method: str = None):
    """
    Decorator específico para operações do legacy adapter.
    
    Args:
        adapter_method: Nome do método do adapter
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            method_name = adapter_method or func.__name__
            start_time = time.time()
            
            try:
                # Log de início
                legacy_logger.log_legacy_event(
                    f"Legacy adapter operation started: {method_name}",
                    method=method_name,
                    function=func.__name__
                )
                
                # Executar função
                result = func(*args, **kwargs)
                
                # Calcular duração
                duration_ms = (time.time() - start_time) * 1000
                
                # Log de sucesso
                legacy_logger.log_legacy_event(
                    f"Legacy adapter operation completed: {method_name}",
                    method=method_name,
                    duration_ms=duration_ms,
                    success=True
                )
                
                return result
                
            except Exception as e:
                # Calcular duração
                duration_ms = (time.time() - start_time) * 1000
                
                # Log de erro
                legacy_logger.log_error(
                    f"Legacy adapter operation failed: {method_name}",
                    exception=e,
                    method=method_name,
                    duration_ms=duration_ms
                )
                
                # Re-raise a exceção
                raise
        
        return wrapper
    return decorator

# Função para configuração de monitoramento via configuração
def configure_monitoring_from_config(app: Flask):
    """
    Configura monitoramento baseado nas configurações da aplicação.
    
    Configurações suportadas:
    - MONITORING_ENABLED: Habilita/desabilita monitoramento
    - MONITORING_ALERT_INTERVAL: Intervalo de verificação de alertas
    - MONITORING_AUTO_START: Inicia automaticamente alertas
    - MONITORING_LOG_LEVEL: Nível de log
    """
    config = app.config
    
    # Verificar se monitoramento está habilitado
    if not config.get('MONITORING_ENABLED', True):
        log_system_event(
            "Monitoramento desabilitado via configuração",
            app_name=app.name
        )
        return False
    
    # Configurar nível de log se especificado
    if 'MONITORING_LOG_LEVEL' in config:
        log_level = config['MONITORING_LOG_LEVEL'].upper()
        legacy_logger.logger.setLevel(getattr(legacy_logger.logging, log_level, 'INFO'))
        
        log_system_event(
            f"Nível de log configurado: {log_level}",
            app_name=app.name
        )
    
    # Inicializar monitoramento
    return init_monitoring(app)