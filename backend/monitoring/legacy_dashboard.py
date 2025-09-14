# ===========================================
# DASHBOARD DE MONITORAMENTO LEGACY
# ===========================================

from flask import Blueprint, jsonify, render_template
from datetime import datetime, timedelta
import psutil
import time
from backend.core.infrastructure.adapters.legacy_service_adapter import LegacyServiceAdapter
from backend.services.legacy.glpi_service_facade import GLPIServiceFacade
from backend.config.settings import Config

monitoring_bp = Blueprint('monitoring', __name__, url_prefix='/api/monitoring')

class LegacyMonitoringService:
    def __init__(self):
        self.adapter = LegacyServiceAdapter()
        self.glpi_facade = GLPIServiceFacade()
        self.start_time = datetime.now()
        self.metrics_history = []
    
    def get_system_health(self):
        """Retorna saúde geral do sistema"""
        try:
            # Métricas do sistema
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Teste de conectividade GLPI
            glpi_start = time.time()
            glpi_health = self._test_glpi_connectivity()
            glpi_response_time = time.time() - glpi_start
            
            # Teste dos serviços legacy
            legacy_start = time.time()
            legacy_health = self._test_legacy_services()
            legacy_response_time = time.time() - legacy_start
            
            uptime = datetime.now() - self.start_time
            
            health_data = {
                'timestamp': datetime.now().isoformat(),
                'uptime_seconds': int(uptime.total_seconds()),
                'system': {
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'memory_available_gb': round(memory.available / (1024**3), 2),
                    'disk_percent': disk.percent,
                    'disk_free_gb': round(disk.free / (1024**3), 2)
                },
                'services': {
                    'glpi': {
                        'status': 'healthy' if glpi_health else 'unhealthy',
                        'response_time_ms': round(glpi_response_time * 1000, 2),
                        'last_check': datetime.now().isoformat()
                    },
                    'legacy_adapter': {
                        'status': 'healthy' if legacy_health else 'unhealthy',
                        'response_time_ms': round(legacy_response_time * 1000, 2),
                        'last_check': datetime.now().isoformat()
                    }
                },
                'overall_status': 'healthy' if (glpi_health and legacy_health and cpu_percent < 80 and memory.percent < 80) else 'degraded'
            }
            
            # Armazenar histórico
            self.metrics_history.append(health_data)
            if len(self.metrics_history) > 100:  # Manter apenas últimas 100 medições
                self.metrics_history.pop(0)
            
            return health_data
            
        except Exception as e:
            return {
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'overall_status': 'error'
            }
    
    def _test_glpi_connectivity(self):
        """Testa conectividade com GLPI"""
        try:
            # Usar método de autenticação do facade
            auth_result = self.glpi_facade.authenticate()
            return auth_result is not None
        except:
            return False
    
    def _test_legacy_services(self):
        """Testa serviços legacy"""
        try:
            # Testar método principal do adapter
            metrics = self.adapter.get_dashboard_metrics('health_check')
            return metrics is not None
        except:
            return False
    
    def get_performance_metrics(self):
        """Retorna métricas de performance detalhadas"""
        try:
            # Testar performance de diferentes operações
            operations = {
                'dashboard_metrics': self._benchmark_dashboard_metrics,
                'ticket_count': self._benchmark_ticket_count,
                'technician_ranking': self._benchmark_technician_ranking
            }
            
            results = {}
            for operation_name, operation_func in operations.items():
                start_time = time.time()
                try:
                    success = operation_func()
                    response_time = time.time() - start_time
                    results[operation_name] = {
                        'success': success,
                        'response_time_ms': round(response_time * 1000, 2),
                        'status': 'ok' if success and response_time < 2.0 else 'slow' if success else 'error'
                    }
                except Exception as e:
                    response_time = time.time() - start_time
                    results[operation_name] = {
                        'success': False,
                        'response_time_ms': round(response_time * 1000, 2),
                        'status': 'error',
                        'error': str(e)
                    }
            
            return {
                'timestamp': datetime.now().isoformat(),
                'operations': results,
                'overall_performance': self._calculate_overall_performance(results)
            }
            
        except Exception as e:
            return {
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }
    
    def _benchmark_dashboard_metrics(self):
        """Benchmark do método principal"""
        metrics = self.adapter.get_dashboard_metrics('benchmark')
        return metrics is not None
    
    def _benchmark_ticket_count(self):
        """Benchmark de contagem de tickets"""
        count = self.glpi_facade.get_ticket_count_by_hierarchy()
        return count is not None
    
    def _benchmark_technician_ranking(self):
        """Benchmark de ranking de técnicos"""
        ranking = self.glpi_facade.get_technician_ranking()
        return ranking is not None
    
    def _calculate_overall_performance(self, results):
        """Calcula performance geral"""
        if not results:
            return 'unknown'
        
        total_operations = len(results)
        successful_operations = sum(1 for r in results.values() if r['success'])
        fast_operations = sum(1 for r in results.values() if r['success'] and r['response_time_ms'] < 1000)
        
        success_rate = successful_operations / total_operations
        speed_rate = fast_operations / total_operations
        
        if success_rate >= 0.9 and speed_rate >= 0.8:
            return 'excellent'
        elif success_rate >= 0.8 and speed_rate >= 0.6:
            return 'good'
        elif success_rate >= 0.6:
            return 'acceptable'
        else:
            return 'poor'
    
    def get_metrics_history(self, limit=50):
        """Retorna histórico de métricas"""
        return self.metrics_history[-limit:] if self.metrics_history else []
    
    def get_alerts(self):
        """Retorna alertas ativos"""
        alerts = []
        
        if self.metrics_history:
            latest = self.metrics_history[-1]
            
            # Alertas de sistema
            if latest.get('system', {}).get('cpu_percent', 0) > 80:
                alerts.append({
                    'type': 'warning',
                    'category': 'system',
                    'message': f"CPU usage high: {latest['system']['cpu_percent']:.1f}%",
                    'timestamp': latest['timestamp']
                })
            
            if latest.get('system', {}).get('memory_percent', 0) > 80:
                alerts.append({
                    'type': 'warning',
                    'category': 'system',
                    'message': f"Memory usage high: {latest['system']['memory_percent']:.1f}%",
                    'timestamp': latest['timestamp']
                })
            
            # Alertas de serviços
            glpi_status = latest.get('services', {}).get('glpi', {}).get('status')
            if glpi_status == 'unhealthy':
                alerts.append({
                    'type': 'error',
                    'category': 'service',
                    'message': 'GLPI service is unhealthy',
                    'timestamp': latest['timestamp']
                })
            
            legacy_status = latest.get('services', {}).get('legacy_adapter', {}).get('status')
            if legacy_status == 'unhealthy':
                alerts.append({
                    'type': 'error',
                    'category': 'service',
                    'message': 'Legacy adapter service is unhealthy',
                    'timestamp': latest['timestamp']
                })
        
        return alerts

# Instância global do serviço
monitoring_service = LegacyMonitoringService()

# Rotas do Blueprint
@monitoring_bp.route('/legacy/health')
def get_health():
    """Endpoint de saúde do sistema"""
    health_data = monitoring_service.get_system_health()
    return jsonify(health_data)

@monitoring_bp.route('/legacy/metrics')
def get_metrics():
    """Endpoint de métricas de performance"""
    metrics_data = monitoring_service.get_performance_metrics()
    return jsonify(metrics_data)

@monitoring_bp.route('/legacy/history')
def get_history():
    """Endpoint de histórico de métricas"""
    history_data = monitoring_service.get_metrics_history()
    return jsonify({
        'timestamp': datetime.now().isoformat(),
        'history': history_data,
        'count': len(history_data)
    })

@monitoring_bp.route('/legacy/alerts')
def get_alerts():
    """Endpoint de alertas ativos"""
    alerts_data = monitoring_service.get_alerts()
    return jsonify({
        'timestamp': datetime.now().isoformat(),
        'alerts': alerts_data,
        'count': len(alerts_data)
    })

@monitoring_bp.route('/legacy/dashboard')
def get_dashboard():
    """Endpoint completo do dashboard"""
    health_data = monitoring_service.get_system_health()
    metrics_data = monitoring_service.get_performance_metrics()
    alerts_data = monitoring_service.get_alerts()
    
    return jsonify({
        'timestamp': datetime.now().isoformat(),
        'health': health_data,
        'performance': metrics_data,
        'alerts': alerts_data,
        'summary': {
            'overall_status': health_data.get('overall_status', 'unknown'),
            'overall_performance': metrics_data.get('overall_performance', 'unknown'),
            'active_alerts': len(alerts_data),
            'uptime_seconds': health_data.get('uptime_seconds', 0)
        }
    })