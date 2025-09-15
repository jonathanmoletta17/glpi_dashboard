from flask import Blueprint, jsonify, request
from datetime import datetime
import time
import logging
import asyncio
from typing import Dict, Any, Optional

from core.application.services.metrics_facade import MetricsFacade
from core.infrastructure.adapters.legacy_service_adapter import LegacyServiceAdapter
from services.legacy.glpi_service_facade import GLPIServiceFacade
from config.settings import active_config
from utils.performance import monitor_performance
from utils.prometheus_metrics import monitor_api_endpoint

comparison_bp = Blueprint('comparison', __name__, url_prefix='/api/comparison')
logger = logging.getLogger('comparison')

@comparison_bp.route('/metrics', methods=['GET'])
@monitor_api_endpoint('compare_metrics')
@monitor_performance
def compare_metrics():
    """Compara métricas entre nova arquitetura e serviços legacy"""
    try:
        correlation_id = request.headers.get('X-Correlation-ID', f"comp_{int(time.time())}")
        
        # Instanciar ambos os adapters
        legacy_adapter = LegacyServiceAdapter()
        new_adapter = GLPIServiceFacade()
        
        results = {
            'correlation_id': correlation_id,
            'timestamp': datetime.now().isoformat(),
            'comparison': {}
        }
        
        # Testar get_dashboard_metrics
        results['comparison']['dashboard_metrics'] = _compare_dashboard_metrics(
            legacy_adapter, new_adapter, correlation_id
        )
        
        # Testar get_general_metrics (disponível em ambos)
        results['comparison']['general_metrics'] = _compare_general_metrics(
            legacy_adapter, new_adapter, correlation_id
        )
        
        # Testar get_metrics_by_level (disponível em ambos)
        results['comparison']['metrics_by_level'] = _compare_metrics_by_level(
            legacy_adapter, new_adapter, correlation_id
        )
        
        # Calcular resumo
        results['summary'] = _calculate_comparison_summary(results['comparison'])
        
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"Erro na comparação: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

def _compare_dashboard_metrics(legacy_adapter, new_adapter, correlation_id):
    """Compara métricas de dashboard entre adapters"""
    comparison = {
        'legacy': {'status': 'pending', 'data': None, 'performance': {}},
        'new': {'status': 'pending', 'data': None, 'performance': {}}
    }
    
    # Testar Legacy Adapter
    try:
        start_time = time.time()
        legacy_data = legacy_adapter.get_dashboard_metrics(correlation_id)
        legacy_time = time.time() - start_time
        
        comparison['legacy'] = {
            'status': 'success',
            'data': legacy_data.dict() if hasattr(legacy_data, 'dict') else str(legacy_data),
            'performance': {
                'response_time': round(legacy_time, 3),
                'data_points': len(legacy_data.dict()) if hasattr(legacy_data, 'dict') else 0
            }
        }
    except Exception as e:
        comparison['legacy'] = {
            'status': 'error',
            'error': str(e),
            'performance': {'response_time': None}
        }
    
    # Testar New Adapter
    try:
        start_time = time.time()
        new_data = new_adapter.get_dashboard_metrics(correlation_id)
        new_time = time.time() - start_time
        
        comparison['new'] = {
            'status': 'success',
            'data': new_data.dict() if hasattr(new_data, 'dict') else str(new_data),
            'performance': {
                'response_time': round(new_time, 3),
                'data_points': len(new_data.dict()) if hasattr(new_data, 'dict') else 0
            }
        }
    except Exception as e:
        comparison['new'] = {
            'status': 'error',
            'error': str(e),
            'performance': {'response_time': None}
        }
    
    # Comparar dados se ambos tiveram sucesso
    if comparison['legacy']['status'] == 'success' and comparison['new']['status'] == 'success':
        comparison['data_consistency'] = _compare_data_consistency(
            comparison['legacy']['data'],
            comparison['new']['data']
        )
    
    return comparison

def _compare_general_metrics(legacy_adapter, new_adapter, correlation_id):
    """Compara métricas gerais entre adapters"""
    comparison = {
        'legacy': {'status': 'pending', 'data': None, 'performance': {}},
        'new': {'status': 'pending', 'data': None, 'performance': {}}
    }
    
    # Testar Legacy Adapter
    try:
        start_time = time.time()
        legacy_data = legacy_adapter.get_general_metrics(correlation_id)
        legacy_time = time.time() - start_time
        
        comparison['legacy'] = {
            'status': 'success',
            'data': legacy_data.dict() if hasattr(legacy_data, 'dict') else str(legacy_data),
            'performance': {
                'response_time': round(legacy_time, 3),
                'data_points': len(legacy_data.dict()) if hasattr(legacy_data, 'dict') else 0
            }
        }
    except Exception as e:
        comparison['legacy'] = {
            'status': 'error',
            'error': str(e),
            'performance': {'response_time': None}
        }
    
    # Testar New Adapter
    try:
        start_time = time.time()
        new_data = new_adapter.get_general_metrics()
        new_time = time.time() - start_time
        
        comparison['new'] = {
            'status': 'success',
            'data': new_data if isinstance(new_data, dict) else str(new_data),
            'performance': {
                'response_time': round(new_time, 3),
                'data_points': len(new_data) if isinstance(new_data, dict) else 0
            }
        }
    except Exception as e:
        comparison['new'] = {
            'status': 'error',
            'error': str(e),
            'performance': {'response_time': None}
        }
    
    # Comparar dados se ambos tiveram sucesso
    if comparison['legacy']['status'] == 'success' and comparison['new']['status'] == 'success':
        comparison['data_consistency'] = _compare_data_consistency(
            comparison['legacy']['data'],
            comparison['new']['data']
        )
    
    return comparison

def _compare_metrics_by_level(legacy_adapter, new_adapter, correlation_id):
    """Compara métricas por nível entre adapters"""
    comparison = {
        'legacy': {'status': 'pending', 'data': None, 'performance': {}},
        'new': {'status': 'pending', 'data': None, 'performance': {}}
    }
    
    # Testar Legacy Adapter
    try:
        start_time = time.time()
        legacy_data = legacy_adapter.get_metrics_by_level(correlation_id=correlation_id)
        legacy_time = time.time() - start_time
        
        comparison['legacy'] = {
            'status': 'success',
            'data': legacy_data.dict() if hasattr(legacy_data, 'dict') else str(legacy_data),
            'performance': {
                'response_time': round(legacy_time, 3),
                'data_points': len(legacy_data.dict()) if hasattr(legacy_data, 'dict') else 0
            }
        }
    except Exception as e:
        comparison['legacy'] = {
            'status': 'error',
            'error': str(e),
            'performance': {'response_time': None}
        }
    
    # Testar New Adapter
    try:
        start_time = time.time()
        new_data = new_adapter.get_metrics_by_level()
        new_time = time.time() - start_time
        
        comparison['new'] = {
            'status': 'success',
            'data': new_data if isinstance(new_data, dict) else str(new_data),
            'performance': {
                'response_time': round(new_time, 3),
                'data_points': len(new_data) if isinstance(new_data, dict) else 0
            }
        }
    except Exception as e:
        comparison['new'] = {
            'status': 'error',
            'error': str(e),
            'performance': {'response_time': None}
        }
    
    # Comparar dados se ambos tiveram sucesso
    if comparison['legacy']['status'] == 'success' and comparison['new']['status'] == 'success':
        comparison['data_consistency'] = _compare_data_consistency(
            comparison['legacy']['data'],
            comparison['new']['data']
        )
    
    return comparison

def _compare_technician_ranking(legacy_adapter, new_adapter, correlation_id):
    """Compara ranking de técnicos entre adapters"""
    comparison = {
        'legacy': {'status': 'pending', 'data': None, 'performance': {}},
        'new': {'status': 'pending', 'data': None, 'performance': {}}
    }
    
    # Testar Legacy Adapter
    try:
        start_time = time.time()
        legacy_data = legacy_adapter.get_technician_ranking(correlation_id)
        legacy_time = time.time() - start_time
        
        comparison['legacy'] = {
            'status': 'success',
            'data': legacy_data.dict() if hasattr(legacy_data, 'dict') else str(legacy_data),
            'performance': {
                'response_time': round(legacy_time, 3),
                'data_points': len(legacy_data.dict()) if hasattr(legacy_data, 'dict') else 0
            }
        }
    except Exception as e:
        comparison['legacy'] = {
            'status': 'error',
            'error': str(e),
            'performance': {'response_time': None}
        }
    
    # Testar New Adapter
    try:
        start_time = time.time()
        new_data = new_adapter.get_technician_ranking(correlation_id)
        new_time = time.time() - start_time
        
        comparison['new'] = {
            'status': 'success',
            'data': new_data.dict() if hasattr(new_data, 'dict') else str(new_data),
            'performance': {
                'response_time': round(new_time, 3),
                'data_points': len(new_data.dict()) if hasattr(new_data, 'dict') else 0
            }
        }
    except Exception as e:
        comparison['new'] = {
            'status': 'error',
            'error': str(e),
            'performance': {'response_time': None}
        }
    
    # Comparar dados se ambos tiveram sucesso
    if comparison['legacy']['status'] == 'success' and comparison['new']['status'] == 'success':
        comparison['data_consistency'] = _compare_data_consistency(
            comparison['legacy']['data'],
            comparison['new']['data']
        )
    
    return comparison

def _compare_new_tickets(legacy_adapter, new_adapter, correlation_id):
    """Compara novos tickets entre adapters"""
    comparison = {
        'legacy': {'status': 'pending', 'data': None, 'performance': {}},
        'new': {'status': 'pending', 'data': None, 'performance': {}}
    }
    
    # Testar Legacy Adapter
    try:
        start_time = time.time()
        legacy_data = legacy_adapter.get_new_tickets(correlation_id)
        legacy_time = time.time() - start_time
        
        comparison['legacy'] = {
            'status': 'success',
            'data': legacy_data.dict() if hasattr(legacy_data, 'dict') else str(legacy_data),
            'performance': {
                'response_time': round(legacy_time, 3),
                'data_points': len(legacy_data.dict()) if hasattr(legacy_data, 'dict') else 0
            }
        }
    except Exception as e:
        comparison['legacy'] = {
            'status': 'error',
            'error': str(e),
            'performance': {'response_time': None}
        }
    
    # Testar New Adapter
    try:
        start_time = time.time()
        new_data = new_adapter.get_new_tickets(correlation_id)
        new_time = time.time() - start_time
        
        comparison['new'] = {
            'status': 'success',
            'data': new_data.dict() if hasattr(new_data, 'dict') else str(new_data),
            'performance': {
                'response_time': round(new_time, 3),
                'data_points': len(new_data.dict()) if hasattr(new_data, 'dict') else 0
            }
        }
    except Exception as e:
        comparison['new'] = {
            'status': 'error',
            'error': str(e),
            'performance': {'response_time': None}
        }
    
    # Comparar dados se ambos tiveram sucesso
    if comparison['legacy']['status'] == 'success' and comparison['new']['status'] == 'success':
        comparison['data_consistency'] = _compare_data_consistency(
            comparison['legacy']['data'],
            comparison['new']['data']
        )
    
    return comparison

def _compare_data_consistency(legacy_data: Any, new_data: Any) -> Dict[str, Any]:
    """Compara consistência entre dados dos adapters"""
    try:
        consistency = {
            'match_percentage': 0.0,
            'differences': [],
            'legacy_unique': [],
            'new_unique': [],
            'common_fields': []
        }
        
        # Se ambos são dicionários, comparar campos
        if isinstance(legacy_data, dict) and isinstance(new_data, dict):
            legacy_keys = set(legacy_data.keys())
            new_keys = set(new_data.keys())
            
            consistency['common_fields'] = list(legacy_keys.intersection(new_keys))
            consistency['legacy_unique'] = list(legacy_keys - new_keys)
            consistency['new_unique'] = list(new_keys - legacy_keys)
            
            # Calcular porcentagem de match
            total_fields = len(legacy_keys.union(new_keys))
            common_fields = len(consistency['common_fields'])
            consistency['match_percentage'] = round((common_fields / total_fields) * 100, 2) if total_fields > 0 else 0
            
            # Verificar diferenças nos valores dos campos comuns
            for field in consistency['common_fields']:
                if legacy_data[field] != new_data[field]:
                    consistency['differences'].append({
                        'field': field,
                        'legacy_value': legacy_data[field],
                        'new_value': new_data[field]
                    })
        
        return consistency
        
    except Exception as e:
        logger.error(f"Erro ao comparar consistência de dados: {e}")
        return {
            'match_percentage': 0.0,
            'error': str(e)
        }

def _calculate_comparison_summary(comparison_data: Dict[str, Any]) -> Dict[str, Any]:
    """Calcula resumo da comparação"""
    summary = {
        'total_tests': 0,
        'successful_tests': 0,
        'failed_tests': 0,
        'performance_comparison': {},
        'consistency_score': 0.0,
        'recommendations': []
    }
    
    try:
        # Contar testes
        for test_name, test_data in comparison_data.items():
            summary['total_tests'] += 2  # legacy + new
            
            if test_data.get('legacy', {}).get('status') == 'success':
                summary['successful_tests'] += 1
            else:
                summary['failed_tests'] += 1
                
            if test_data.get('new', {}).get('status') == 'success':
                summary['successful_tests'] += 1
            else:
                summary['failed_tests'] += 1
            
            # Comparar performance
            legacy_time = test_data.get('legacy', {}).get('performance', {}).get('response_time')
            new_time = test_data.get('new', {}).get('performance', {}).get('response_time')
            
            if legacy_time is not None and new_time is not None:
                summary['performance_comparison'][test_name] = {
                    'legacy_time': legacy_time,
                    'new_time': new_time,
                    'improvement': round(((legacy_time - new_time) / legacy_time) * 100, 2) if legacy_time > 0 else 0
                }
            
            # Calcular score de consistência
            if 'data_consistency' in test_data:
                consistency = test_data['data_consistency'].get('match_percentage', 0)
                summary['consistency_score'] += consistency
        
        # Média do score de consistência
        if len(comparison_data) > 0:
            summary['consistency_score'] = round(summary['consistency_score'] / len(comparison_data), 2)
        
        # Gerar recomendações
        if summary['failed_tests'] > 0:
            summary['recommendations'].append("Investigar falhas nos adapters")
        
        if summary['consistency_score'] < 90:
            summary['recommendations'].append("Verificar inconsistências nos dados")
        
        avg_improvement = 0
        perf_count = 0
        for perf in summary['performance_comparison'].values():
            if perf['improvement'] is not None:
                avg_improvement += perf['improvement']
                perf_count += 1
        
        if perf_count > 0:
            avg_improvement = avg_improvement / perf_count
            if avg_improvement < 0:
                summary['recommendations'].append("Nova arquitetura apresenta performance inferior")
            elif avg_improvement > 20:
                summary['recommendations'].append("Nova arquitetura apresenta melhoria significativa de performance")
        
        return summary
        
    except Exception as e:
        logger.error(f"Erro ao calcular resumo da comparação: {e}")
        return {
            'error': str(e),
            'total_tests': 0,
            'successful_tests': 0,
            'failed_tests': 0
        }

@comparison_bp.route('/report', methods=['GET'])
@monitor_api_endpoint('generate_comparison_report')
@monitor_performance
def generate_comparison_report():
    """Gera relatório detalhado de comparação"""
    try:
        correlation_id = request.headers.get('X-Correlation-ID', f"report_{int(time.time())}")
        
        # Executar comparação completa
        legacy_adapter = LegacyServiceAdapter()
        new_adapter = GLPIServiceFacade()
        
        report = {
            'correlation_id': correlation_id,
            'timestamp': datetime.now().isoformat(),
            'report_type': 'detailed_comparison',
            'adapters': {
                'legacy': {
                    'name': 'LegacyServiceAdapter',
                    'version': getattr(legacy_adapter, 'version', 'unknown'),
                    'status': 'active' if active_config.USE_LEGACY_SERVICES else 'inactive'
                },
                'new': {
                    'name': 'GLPIServiceFacade',
                    'version': getattr(new_adapter, 'version', 'unknown'),
                    'status': 'active' if not active_config.USE_LEGACY_SERVICES else 'inactive'
                }
            },
            'environment': {
                'use_legacy_services': active_config.USE_LEGACY_SERVICES,
                'use_mock_data': active_config.USE_MOCK_DATA,
                'legacy_timeout': active_config.LEGACY_ADAPTER_TIMEOUT,
                'legacy_retry_count': active_config.LEGACY_ADAPTER_RETRY_COUNT
            },
            'tests': {},
            'summary': {},
            'recommendations': []
        }
        
        # Executar testes de comparação
        report['tests']['dashboard_metrics'] = _compare_dashboard_metrics(
            legacy_adapter, new_adapter, correlation_id
        )
        
        report['tests']['general_metrics'] = _compare_general_metrics(
            legacy_adapter, new_adapter, correlation_id
        )
        
        report['tests']['metrics_by_level'] = _compare_metrics_by_level(
            legacy_adapter, new_adapter, correlation_id
        )
        
        report['tests']['new_tickets'] = _compare_new_tickets(
            legacy_adapter, new_adapter, correlation_id
        )
        
        # Gerar resumo e recomendações
        report['summary'] = _calculate_comparison_summary(report['tests'])
        
        # Recomendações específicas do relatório
        if report['summary']['consistency_score'] >= 95:
            report['recommendations'].append("Migração segura: alta consistência de dados")
        elif report['summary']['consistency_score'] >= 80:
            report['recommendations'].append("Migração com cautela: consistência moderada")
        else:
            report['recommendations'].append("Migração não recomendada: baixa consistência")
        
        # Adicionar timestamp de geração
        report['generated_at'] = datetime.now().isoformat()
        
        return jsonify(report)
        
    except Exception as e:
        logger.error(f"Erro ao gerar relatório de comparação: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@comparison_bp.route('/health', methods=['GET'])
def comparison_health():
    """Verifica saúde do sistema de comparação"""
    try:
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'adapters': {
                'legacy': {'available': False, 'error': None},
                'new': {'available': False, 'error': None}
            }
        }
        
        # Testar Legacy Adapter
        try:
            legacy_adapter = LegacyServiceAdapter()
            # Teste simples de conectividade
            health_status['adapters']['legacy']['available'] = True
        except Exception as e:
            health_status['adapters']['legacy']['error'] = str(e)
        
        # Testar New Adapter
        try:
            new_adapter = GLPIServiceFacade()
            # Teste simples de conectividade
            health_status['adapters']['new']['available'] = True
        except Exception as e:
            health_status['adapters']['new']['error'] = str(e)
        
        # Determinar status geral
        if not health_status['adapters']['legacy']['available'] and not health_status['adapters']['new']['available']:
            health_status['status'] = 'unhealthy'
        elif not health_status['adapters']['legacy']['available'] or not health_status['adapters']['new']['available']:
            health_status['status'] = 'degraded'
        
        return jsonify(health_status)
        
    except Exception as e:
        logger.error(f"Erro no health check de comparação: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500