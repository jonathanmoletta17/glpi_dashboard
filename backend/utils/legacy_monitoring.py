import time
import logging
from functools import wraps
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque
import threading

class LegacyServiceMonitor:
    """Monitor avançado para serviços legacy"""
    
    def __init__(self):
        self.metrics = defaultdict(lambda: {
            'call_count': 0,
            'total_time': 0,
            'error_count': 0,
            'last_call': None,
            'response_times': deque(maxlen=100),  # Últimas 100 chamadas
            'errors': deque(maxlen=50)  # Últimos 50 erros
        })
        self.lock = threading.Lock()
        self.logger = logging.getLogger('legacy_monitor')
    
    def monitor_method(self, method_name: str):
        """Decorator para monitorar métodos dos serviços legacy"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                
                try:
                    result = func(*args, **kwargs)
                    response_time = time.time() - start_time
                    
                    # Registrar sucesso
                    self._record_success(method_name, response_time)
                    
                    return result
                    
                except Exception as e:
                    response_time = time.time() - start_time
                    
                    # Registrar erro
                    self._record_error(method_name, response_time, str(e))
                    
                    raise
            
            return wrapper
        return decorator
    
    def _record_success(self, method_name: str, response_time: float):
        """Registra chamada bem-sucedida"""
        with self.lock:
            metrics = self.metrics[method_name]
            metrics['call_count'] += 1
            metrics['total_time'] += response_time
            metrics['last_call'] = datetime.now()
            metrics['response_times'].append(response_time)
    
    def _record_error(self, method_name: str, response_time: float, error_msg: str):
        """Registra erro"""
        with self.lock:
            metrics = self.metrics[method_name]
            metrics['call_count'] += 1
            metrics['error_count'] += 1
            metrics['total_time'] += response_time
            metrics['last_call'] = datetime.now()
            metrics['response_times'].append(response_time)
            metrics['errors'].append({
                'timestamp': datetime.now(),
                'error': error_msg,
                'response_time': response_time
            })
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Retorna resumo das métricas"""
        with self.lock:
            summary = {}
            
            for method_name, metrics in self.metrics.items():
                response_times = list(metrics['response_times'])
                
                if response_times:
                    avg_response_time = sum(response_times) / len(response_times)
                    min_response_time = min(response_times)
                    max_response_time = max(response_times)
                    
                    # Calcular percentis
                    sorted_times = sorted(response_times)
                    p95_index = int(len(sorted_times) * 0.95)
                    p95_response_time = sorted_times[p95_index] if p95_index < len(sorted_times) else max_response_time
                else:
                    avg_response_time = min_response_time = max_response_time = p95_response_time = 0
                
                error_rate = (metrics['error_count'] / metrics['call_count'] * 100) if metrics['call_count'] > 0 else 0
                
                summary[method_name] = {
                    'call_count': metrics['call_count'],
                    'error_count': metrics['error_count'],
                    'error_rate_percent': round(error_rate, 2),
                    'avg_response_time': round(avg_response_time, 3),
                    'min_response_time': round(min_response_time, 3),
                    'max_response_time': round(max_response_time, 3),
                    'p95_response_time': round(p95_response_time, 3),
                    'last_call': metrics['last_call'].isoformat() if metrics['last_call'] else None,
                    'recent_errors': [
                        {
                            'timestamp': error['timestamp'].isoformat(),
                            'error': error['error'],
                            'response_time': error['response_time']
                        }
                        for error in list(metrics['errors'])[-5:]  # Últimos 5 erros
                    ]
                }
            
            return summary
    
    def get_health_status(self) -> Dict[str, Any]:
        """Retorna status de saúde dos serviços"""
        summary = self.get_metrics_summary()
        
        overall_health = "healthy"
        issues = []
        
        for method_name, metrics in summary.items():
            # Verificar taxa de erro
            if metrics['error_rate_percent'] > 5:
                overall_health = "degraded"
                issues.append(f"{method_name}: alta taxa de erro ({metrics['error_rate_percent']}%)")
            
            # Verificar tempo de resposta
            if metrics['p95_response_time'] > 1.0:
                overall_health = "degraded"
                issues.append(f"{method_name}: tempo de resposta alto (P95: {metrics['p95_response_time']}s)")
            
            # Verificar se houve chamadas recentes
            if metrics['last_call']:
                last_call_time = datetime.fromisoformat(metrics['last_call'])
                if datetime.now() - last_call_time > timedelta(minutes=10):
                    issues.append(f"{method_name}: sem chamadas recentes")
        
        if len(issues) > 3:
            overall_health = "unhealthy"
        
        return {
            'status': overall_health,
            'timestamp': datetime.now().isoformat(),
            'issues': issues,
            'metrics_summary': summary
        }

# Instância global do monitor
legacy_monitor = LegacyServiceMonitor()