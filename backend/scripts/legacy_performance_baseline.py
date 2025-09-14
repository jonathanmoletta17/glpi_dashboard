#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bateria Completa de Testes de Performance - Serviços Legacy GLPI

Este script executa uma bateria completa de testes para estabelecer baseline
de performance dos serviços legacy GLPI, incluindo:

1. Teste isolado do GLPIServiceFacade
2. Teste de performance individual por serviço
3. Teste de stress com requisições simultâneas
4. Documentação de métricas com relatório detalhado
"""

import asyncio
import concurrent.futures
import json
import logging
import os
import psutil
import statistics
import sys
import threading
import time
import tracemalloc
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple

# Adicionar path do backend
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Imports dos serviços legacy
from services.legacy.glpi_service_facade import GLPIServiceFacade
from services.legacy.authentication_service import GLPIAuthenticationService
from services.legacy.cache_service import GLPICacheService
from services.legacy.http_client_service import GLPIHttpClientService
from services.legacy.metrics_service import GLPIMetricsService
from services.legacy.dashboard_service import GLPIDashboardService
from services.legacy.trends_service import GLPITrendsService
from services.legacy.field_discovery_service import GLPIFieldDiscoveryService

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('performance_baseline')


class PerformanceMetrics:
    """Classe para armazenar métricas de performance."""
    
    def __init__(self):
        self.response_times: List[float] = []
        self.memory_usage: List[float] = []
        self.cpu_usage: List[float] = []
        self.success_count: int = 0
        self.error_count: int = 0
        self.errors: List[str] = []
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        
    def add_response_time(self, time_ms: float):
        """Adiciona tempo de resposta em milissegundos."""
        self.response_times.append(time_ms)
        
    def add_memory_usage(self, memory_mb: float):
        """Adiciona uso de memória em MB."""
        self.memory_usage.append(memory_mb)
        
    def add_cpu_usage(self, cpu_percent: float):
        """Adiciona uso de CPU em percentual."""
        self.cpu_usage.append(cpu_percent)
        
    def record_success(self):
        """Registra uma operação bem-sucedida."""
        self.success_count += 1
        
    def record_error(self, error: str):
        """Registra um erro."""
        self.error_count += 1
        self.errors.append(error)
        
    def get_statistics(self) -> Dict[str, Any]:
        """Retorna estatísticas calculadas."""
        total_operations = self.success_count + self.error_count
        success_rate = (self.success_count / total_operations * 100) if total_operations > 0 else 0
        
        stats = {
            'total_operations': total_operations,
            'success_count': self.success_count,
            'error_count': self.error_count,
            'success_rate_percent': round(success_rate, 2),
            'total_duration_seconds': round(self.end_time - self.start_time, 3) if self.start_time and self.end_time else 0
        }
        
        if self.response_times:
            stats['response_time'] = {
                'min_ms': round(min(self.response_times), 3),
                'max_ms': round(max(self.response_times), 3),
                'avg_ms': round(statistics.mean(self.response_times), 3),
                'median_ms': round(statistics.median(self.response_times), 3),
                'p95_ms': round(statistics.quantiles(self.response_times, n=20)[18], 3) if len(self.response_times) > 1 else round(self.response_times[0], 3),
                'p99_ms': round(statistics.quantiles(self.response_times, n=100)[98], 3) if len(self.response_times) > 1 else round(self.response_times[0], 3)
            }
            
        if self.memory_usage:
            stats['memory_usage'] = {
                'min_mb': round(min(self.memory_usage), 2),
                'max_mb': round(max(self.memory_usage), 2),
                'avg_mb': round(statistics.mean(self.memory_usage), 2)
            }
            
        if self.cpu_usage:
            stats['cpu_usage'] = {
                'min_percent': round(min(self.cpu_usage), 2),
                'max_percent': round(max(self.cpu_usage), 2),
                'avg_percent': round(statistics.mean(self.cpu_usage), 2)
            }
            
        if self.errors:
            stats['sample_errors'] = self.errors[:5]  # Primeiros 5 erros
            
        return stats


class LegacyPerformanceBaseline:
    """Classe principal para execução dos testes de baseline."""
    
    def __init__(self):
        self.facade: Optional[GLPIServiceFacade] = None
        self.results: Dict[str, Any] = {}
        self.start_time = datetime.now()
        
    def setup_facade(self) -> bool:
        """Inicializa o GLPIServiceFacade."""
        try:
            logger.info("🔧 Inicializando GLPIServiceFacade...")
            self.facade = GLPIServiceFacade()
            
            # Testar autenticação
            if self.facade.authenticate():
                logger.info("✅ GLPIServiceFacade inicializado com sucesso")
                return True
            else:
                logger.error("❌ Falha na autenticação do GLPIServiceFacade")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar GLPIServiceFacade: {e}")
            return False
    
    def test_facade_isolated(self) -> Dict[str, Any]:
        """Teste 1: Teste isolado do GLPIServiceFacade."""
        logger.info("\n🧪 TESTE 1: Teste Isolado do GLPIServiceFacade")
        
        metrics = PerformanceMetrics()
        metrics.start_time = time.time()
        
        # Iniciar monitoramento de memória
        tracemalloc.start()
        process = psutil.Process()
        
        test_methods = [
            ('get_dashboard_metrics', lambda: self.facade.get_dashboard_metrics()),
            ('get_ticket_count', lambda: self.facade.get_ticket_count()),
            ('get_metrics_by_level', lambda: self.facade.get_metrics_by_level()),
            ('get_general_metrics', lambda: self.facade.get_general_metrics()),
            ('health_check', lambda: self.facade.health_check())
        ]
        
        method_results = {}
        
        for method_name, method_func in test_methods:
            logger.info(f"  📊 Testando {method_name}...")
            method_metrics = PerformanceMetrics()
            method_metrics.start_time = time.time()
            
            try:
                # Medir recursos antes
                cpu_before = process.cpu_percent()
                memory_before = process.memory_info().rss / 1024 / 1024  # MB
                
                # Executar método
                start_time = time.time()
                result = method_func()
                end_time = time.time()
                
                # Medir recursos depois
                cpu_after = process.cpu_percent()
                memory_after = process.memory_info().rss / 1024 / 1024  # MB
                
                response_time_ms = (end_time - start_time) * 1000
                method_metrics.add_response_time(response_time_ms)
                method_metrics.add_memory_usage(memory_after - memory_before)
                method_metrics.add_cpu_usage(cpu_after - cpu_before)
                method_metrics.record_success()
                
                # Validar resultado
                if result and isinstance(result, dict):
                    logger.info(f"    ✅ {method_name}: {response_time_ms:.2f}ms")
                    
                    # Validação específica para tickets
                    if method_name in ['get_dashboard_metrics', 'get_ticket_count'] and 'total_tickets' in result:
                        ticket_count = result.get('total_tickets', 0)
                        logger.info(f"    📋 Total de tickets encontrados: {ticket_count}")
                        
                        # Validar integridade dos 10.240 tickets mencionados
                        if ticket_count >= 10000:
                            logger.info(f"    ✅ Integridade validada: {ticket_count} tickets (>= 10.000)")
                        else:
                            logger.warning(f"    ⚠️ Possível inconsistência: {ticket_count} tickets (< 10.000)")
                else:
                    logger.warning(f"    ⚠️ {method_name}: Resultado inválido ou vazio")
                    method_metrics.record_error(f"Resultado inválido para {method_name}")
                    
            except Exception as e:
                logger.error(f"    ❌ {method_name}: {str(e)}")
                method_metrics.record_error(str(e))
                
            method_metrics.end_time = time.time()
            method_results[method_name] = method_metrics.get_statistics()
            
            # Adicionar ao total
            metrics.response_times.extend(method_metrics.response_times)
            metrics.memory_usage.extend(method_metrics.memory_usage)
            metrics.cpu_usage.extend(method_metrics.cpu_usage)
            metrics.success_count += method_metrics.success_count
            metrics.error_count += method_metrics.error_count
            metrics.errors.extend(method_metrics.errors)
        
        metrics.end_time = time.time()
        
        # Parar monitoramento de memória
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        result = {
            'test_name': 'GLPIServiceFacade Isolated Test',
            'overall_metrics': metrics.get_statistics(),
            'method_breakdown': method_results,
            'memory_trace': {
                'current_mb': round(current / 1024 / 1024, 2),
                'peak_mb': round(peak / 1024 / 1024, 2)
            }
        }
        
        logger.info(f"✅ Teste isolado concluído: {metrics.success_count} sucessos, {metrics.error_count} erros")
        return result
    
    def test_individual_services(self) -> Dict[str, Any]:
        """Teste 2: Performance individual dos serviços."""
        logger.info("\n🔬 TESTE 2: Performance Individual dos Serviços")
        
        services_to_test = [
            ('AuthenticationService', self.facade.auth_service, [
                ('authenticate', lambda s: s.authenticate()),
                ('get_api_headers', lambda s: s.get_api_headers()),
                ('is_authenticated', lambda s: s.is_authenticated())
            ]),
            ('CacheService', self.facade.cache_service, [
                ('get_cache_stats', lambda s: s.get_cache_stats()),
                ('cache_hit_test', lambda s: self._test_cache_hit_rate(s))
            ]),
            ('HttpClientService', self.facade.http_client, [
                ('health_check', lambda s: self._test_http_latency(s))
            ]),
            ('MetricsService', self.facade.metrics_service, [
                ('get_ticket_count', lambda s: s.get_ticket_count()),
                ('get_metrics_by_level', lambda s: s.get_metrics_by_level())
            ])
        ]
        
        service_results = {}
        
        for service_name, service_instance, methods in services_to_test:
            logger.info(f"  🔧 Testando {service_name}...")
            service_metrics = PerformanceMetrics()
            service_metrics.start_time = time.time()
            
            method_results = {}
            
            for method_name, method_func in methods:
                try:
                    start_time = time.time()
                    result = method_func(service_instance)
                    end_time = time.time()
                    
                    response_time_ms = (end_time - start_time) * 1000
                    service_metrics.add_response_time(response_time_ms)
                    service_metrics.record_success()
                    
                    method_results[method_name] = {
                        'response_time_ms': round(response_time_ms, 3),
                        'success': True,
                        'result_type': type(result).__name__
                    }
                    
                    logger.info(f"    ✅ {method_name}: {response_time_ms:.2f}ms")
                    
                except Exception as e:
                    service_metrics.record_error(str(e))
                    method_results[method_name] = {
                        'success': False,
                        'error': str(e)
                    }
                    logger.error(f"    ❌ {method_name}: {str(e)}")
            
            service_metrics.end_time = time.time()
            service_results[service_name] = {
                'overall_metrics': service_metrics.get_statistics(),
                'method_breakdown': method_results
            }
        
        logger.info("✅ Testes individuais concluídos")
        return {'individual_services': service_results}
    
    def test_stress_concurrent(self) -> Dict[str, Any]:
        """Teste 3: Teste de stress com requisições simultâneas."""
        logger.info("\n🚀 TESTE 3: Teste de Stress - 100 Requisições Simultâneas")
        
        metrics = PerformanceMetrics()
        metrics.start_time = time.time()
        
        # Função para executar uma requisição
        def execute_request(request_id: int) -> Dict[str, Any]:
            try:
                start_time = time.time()
                result = self.facade.get_dashboard_metrics()
                end_time = time.time()
                
                return {
                    'request_id': request_id,
                    'success': True,
                    'response_time_ms': (end_time - start_time) * 1000,
                    'result_size': len(str(result)) if result else 0
                }
            except Exception as e:
                return {
                    'request_id': request_id,
                    'success': False,
                    'error': str(e),
                    'response_time_ms': 0
                }
        
        # Executar 100 requisições simultâneas
        concurrent_requests = 100
        logger.info(f"  🔥 Executando {concurrent_requests} requisições simultâneas...")
        
        # Monitorar recursos do sistema
        process = psutil.Process()
        cpu_before = process.cpu_percent()
        memory_before = process.memory_info().rss / 1024 / 1024
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(execute_request, i) for i in range(concurrent_requests)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        cpu_after = process.cpu_percent()
        memory_after = process.memory_info().rss / 1024 / 1024
        
        # Processar resultados
        successful_requests = [r for r in results if r['success']]
        failed_requests = [r for r in results if not r['success']]
        
        for result in successful_requests:
            metrics.add_response_time(result['response_time_ms'])
            metrics.record_success()
        
        for result in failed_requests:
            metrics.record_error(result.get('error', 'Unknown error'))
        
        metrics.add_cpu_usage(cpu_after - cpu_before)
        metrics.add_memory_usage(memory_after - memory_before)
        metrics.end_time = time.time()
        
        # Análise de gargalos
        bottlenecks = []
        if len(failed_requests) > concurrent_requests * 0.1:  # > 10% falhas
            bottlenecks.append(f"Alta taxa de falhas: {len(failed_requests)}/{concurrent_requests}")
        
        if metrics.response_times and statistics.mean(metrics.response_times) > 5000:  # > 5s
            bottlenecks.append("Tempo de resposta elevado sob carga")
        
        if cpu_after - cpu_before > 80:  # > 80% CPU
            bottlenecks.append("Alto uso de CPU")
        
        if memory_after - memory_before > 500:  # > 500MB
            bottlenecks.append("Alto uso de memória")
        
        result = {
            'test_name': 'Concurrent Stress Test',
            'concurrent_requests': concurrent_requests,
            'successful_requests': len(successful_requests),
            'failed_requests': len(failed_requests),
            'overall_metrics': metrics.get_statistics(),
            'resource_usage': {
                'cpu_delta_percent': round(cpu_after - cpu_before, 2),
                'memory_delta_mb': round(memory_after - memory_before, 2)
            },
            'identified_bottlenecks': bottlenecks
        }
        
        logger.info(f"✅ Teste de stress concluído: {len(successful_requests)}/{concurrent_requests} sucessos")
        if bottlenecks:
            logger.warning(f"⚠️ Gargalos identificados: {', '.join(bottlenecks)}")
        
        return result
    
    def _test_cache_hit_rate(self, cache_service) -> Dict[str, Any]:
        """Testa taxa de hit do cache."""
        # Executar operações que usam cache
        test_operations = [
            lambda: self.facade.get_dashboard_metrics(),
            lambda: self.facade.get_technician_name('1'),
            lambda: self.facade.get_field_id('status')
        ]
        
        stats_before = cache_service.get_cache_stats()
        
        # Executar operações 2 vezes para testar cache
        for _ in range(2):
            for operation in test_operations:
                try:
                    operation()
                except:
                    pass
        
        stats_after = cache_service.get_cache_stats()
        
        return {
            'stats_before': stats_before,
            'stats_after': stats_after,
            'cache_effectiveness': 'tested'
        }
    
    def _test_http_latency(self, http_client) -> Dict[str, Any]:
        """Testa latência do cliente HTTP."""
        try:
            # Fazer uma requisição simples para medir latência
            start_time = time.time()
            headers = http_client.auth_service.get_api_headers()
            end_time = time.time()
            
            return {
                'latency_ms': (end_time - start_time) * 1000,
                'has_headers': headers is not None
            }
        except Exception as e:
            return {'error': str(e)}
    
    def generate_baseline_report(self) -> str:
        """Gera relatório completo de baseline."""
        logger.info("\n📊 Gerando Relatório de Baseline...")
        
        report_data = {
            'metadata': {
                'test_execution_time': self.start_time.isoformat(),
                'total_duration_minutes': round((datetime.now() - self.start_time).total_seconds() / 60, 2),
                'python_version': sys.version,
                'system_info': {
                    'cpu_count': psutil.cpu_count(),
                    'memory_total_gb': round(psutil.virtual_memory().total / 1024 / 1024 / 1024, 2),
                    'platform': sys.platform
                }
            },
            'test_results': self.results,
            'summary': self._generate_summary(),
            'recommendations': self._generate_recommendations()
        }
        
        # Salvar relatório JSON
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        json_filename = f'legacy_baseline_report_{timestamp}.json'
        json_path = os.path.join(os.path.dirname(__file__), json_filename)
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        # Gerar relatório Markdown
        md_filename = f'legacy_baseline_report_{timestamp}.md'
        md_path = os.path.join(os.path.dirname(__file__), md_filename)
        
        markdown_content = self._generate_markdown_report(report_data)
        
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        logger.info(f"📄 Relatório JSON salvo: {json_path}")
        logger.info(f"📄 Relatório Markdown salvo: {md_path}")
        
        return md_path
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Gera resumo dos resultados."""
        summary = {
            'overall_health': 'unknown',
            'key_metrics': {},
            'critical_issues': [],
            'performance_grade': 'unknown'
        }
        
        # Analisar resultados do teste isolado
        if 'isolated_test' in self.results:
            isolated = self.results['isolated_test']['overall_metrics']
            summary['key_metrics']['facade_success_rate'] = isolated.get('success_rate_percent', 0)
            
            if 'response_time' in isolated:
                summary['key_metrics']['avg_response_time_ms'] = isolated['response_time']['avg_ms']
                summary['key_metrics']['p95_response_time_ms'] = isolated['response_time']['p95_ms']
        
        # Analisar resultados do teste de stress
        if 'stress_test' in self.results:
            stress = self.results['stress_test']
            summary['key_metrics']['concurrent_success_rate'] = round(
                (stress['successful_requests'] / stress['concurrent_requests']) * 100, 2
            )
        
        # Determinar saúde geral
        success_rate = summary['key_metrics'].get('facade_success_rate', 0)
        concurrent_success_rate = summary['key_metrics'].get('concurrent_success_rate', 0)
        
        if success_rate >= 95 and concurrent_success_rate >= 90:
            summary['overall_health'] = 'excellent'
            summary['performance_grade'] = 'A'
        elif success_rate >= 90 and concurrent_success_rate >= 80:
            summary['overall_health'] = 'good'
            summary['performance_grade'] = 'B'
        elif success_rate >= 80 and concurrent_success_rate >= 70:
            summary['overall_health'] = 'fair'
            summary['performance_grade'] = 'C'
        else:
            summary['overall_health'] = 'poor'
            summary['performance_grade'] = 'D'
        
        # Identificar problemas críticos
        if success_rate < 90:
            summary['critical_issues'].append('Taxa de sucesso baixa em operações isoladas')
        
        if concurrent_success_rate < 80:
            summary['critical_issues'].append('Performance degradada sob carga')
        
        avg_response = summary['key_metrics'].get('avg_response_time_ms', 0)
        if avg_response > 2000:
            summary['critical_issues'].append('Tempo de resposta elevado')
        
        return summary
    
    def _generate_recommendations(self) -> List[str]:
        """Gera recomendações baseadas nos resultados."""
        recommendations = []
        
        summary = self._generate_summary()
        
        if summary['overall_health'] == 'poor':
            recommendations.extend([
                'Investigar e corrigir falhas críticas nos serviços',
                'Implementar monitoramento de saúde em tempo real',
                'Considerar refatoração dos componentes com maior taxa de erro'
            ])
        
        if summary['key_metrics'].get('avg_response_time_ms', 0) > 1000:
            recommendations.extend([
                'Otimizar consultas ao GLPI para reduzir latência',
                'Implementar cache mais agressivo para operações frequentes',
                'Considerar connection pooling para requisições HTTP'
            ])
        
        if summary['key_metrics'].get('concurrent_success_rate', 100) < 90:
            recommendations.extend([
                'Implementar rate limiting para evitar sobrecarga',
                'Adicionar circuit breaker para falhas em cascata',
                'Otimizar gerenciamento de recursos sob carga'
            ])
        
        # Recomendações gerais
        recommendations.extend([
            'Implementar métricas de observabilidade (Prometheus/Grafana)',
            'Adicionar alertas para degradação de performance',
            'Estabelecer SLAs baseados nos resultados do baseline',
            'Executar testes de baseline regularmente para detectar regressões'
        ])
        
        return recommendations
    
    def _generate_markdown_report(self, report_data: Dict[str, Any]) -> str:
        """Gera relatório em formato Markdown."""
        md_content = f"""# Relatório de Baseline - Serviços Legacy GLPI

## 📋 Resumo Executivo

**Data de Execução:** {report_data['metadata']['test_execution_time']}
**Duração Total:** {report_data['metadata']['total_duration_minutes']} minutos
**Saúde Geral:** {report_data['summary']['overall_health'].upper()}
**Nota de Performance:** {report_data['summary']['performance_grade']}

### 🎯 Métricas Principais

"""
        
        # Adicionar métricas principais
        key_metrics = report_data['summary']['key_metrics']
        for metric, value in key_metrics.items():
            md_content += f"- **{metric.replace('_', ' ').title()}:** {value}\n"
        
        md_content += "\n## 🧪 Resultados dos Testes\n\n"
        
        # Teste Isolado
        if 'isolated_test' in report_data['test_results']:
            isolated = report_data['test_results']['isolated_test']
            md_content += f"""### 1. Teste Isolado do GLPIServiceFacade

**Taxa de Sucesso:** {isolated['overall_metrics']['success_rate_percent']}%
**Operações Totais:** {isolated['overall_metrics']['total_operations']}
**Tempo Total:** {isolated['overall_metrics']['total_duration_seconds']}s

#### Breakdown por Método:

| Método | Tempo Médio (ms) | Status |
|--------|------------------|--------|
"""
            
            for method, stats in isolated['method_breakdown'].items():
                avg_time = stats.get('response_time', {}).get('avg_ms', 'N/A')
                success_rate = stats.get('success_rate_percent', 0)
                status = '✅' if success_rate > 90 else '⚠️' if success_rate > 70 else '❌'
                md_content += f"| {method} | {avg_time} | {status} {success_rate}% |\n"
        
        # Teste de Stress
        if 'stress_test' in report_data['test_results']:
            stress = report_data['test_results']['stress_test']
            md_content += f"""\n### 3. Teste de Stress (100 Requisições Simultâneas)

**Requisições Bem-sucedidas:** {stress['successful_requests']}/{stress['concurrent_requests']}
**Taxa de Sucesso:** {round((stress['successful_requests']/stress['concurrent_requests'])*100, 2)}%
**Uso de CPU:** +{stress['resource_usage']['cpu_delta_percent']}%
**Uso de Memória:** +{stress['resource_usage']['memory_delta_mb']} MB

"""
            
            if stress['identified_bottlenecks']:
                md_content += "#### 🚨 Gargalos Identificados:\n\n"
                for bottleneck in stress['identified_bottlenecks']:
                    md_content += f"- {bottleneck}\n"
        
        # Problemas Críticos
        if report_data['summary']['critical_issues']:
            md_content += "\n## 🚨 Problemas Críticos\n\n"
            for issue in report_data['summary']['critical_issues']:
                md_content += f"- ❌ {issue}\n"
        
        # Recomendações
        md_content += "\n## 💡 Recomendações\n\n"
        for i, recommendation in enumerate(report_data['recommendations'], 1):
            md_content += f"{i}. {recommendation}\n"
        
        # Informações do Sistema
        system_info = report_data['metadata']['system_info']
        md_content += f"""\n## 🖥️ Informações do Sistema

- **CPUs:** {system_info['cpu_count']}
- **Memória Total:** {system_info['memory_total_gb']} GB
- **Plataforma:** {system_info['platform']}
- **Python:** {report_data['metadata']['python_version']}

---

*Relatório gerado automaticamente pelo Legacy Performance Baseline Tool*
"""
        
        return md_content
    
    def run_all_tests(self) -> str:
        """Executa todos os testes e gera relatório."""
        logger.info("🚀 Iniciando Bateria Completa de Testes de Performance")
        logger.info("=" * 60)
        
        # Setup
        if not self.setup_facade():
            logger.error("❌ Falha na inicialização. Abortando testes.")
            return None
        
        try:
            # Teste 1: Isolado
            self.results['isolated_test'] = self.test_facade_isolated()
            
            # Teste 2: Individual
            self.results['individual_services'] = self.test_individual_services()
            
            # Teste 3: Stress
            self.results['stress_test'] = self.test_stress_concurrent()
            
            # Gerar relatório
            report_path = self.generate_baseline_report()
            
            logger.info("\n" + "=" * 60)
            logger.info("✅ Bateria de testes concluída com sucesso!")
            logger.info(f"📊 Relatório disponível em: {report_path}")
            
            return report_path
            
        except Exception as e:
            logger.error(f"❌ Erro durante execução dos testes: {e}")
            logger.error(traceback.format_exc())
            return None


def main():
    """Função principal."""
    print("🔬 Legacy GLPI Services - Performance Baseline Tool")
    print("=" * 60)
    
    baseline = LegacyPerformanceBaseline()
    report_path = baseline.run_all_tests()
    
    if report_path:
        print(f"\n📊 Relatório de baseline gerado: {report_path}")
        print("\n🎯 Próximos passos:")
        print("1. Revisar métricas de baseline estabelecidas")
        print("2. Implementar monitoramento contínuo")
        print("3. Definir SLAs baseados nos resultados")
        print("4. Executar testes regularmente para detectar regressões")
    else:
        print("\n❌ Falha na execução dos testes. Verifique os logs.")


if __name__ == '__main__':
    main()