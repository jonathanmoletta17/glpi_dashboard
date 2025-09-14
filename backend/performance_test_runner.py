#!/usr/bin/env python3
"""
Suite de Testes de Performance para LegacyServiceAdapter
"""

import time
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
import psutil
import logging
import json
from datetime import datetime

from core.infrastructure.adapters.legacy_service_adapter import LegacyServiceAdapter

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LegacyServicePerformanceTests:
    
    def __init__(self):
        self.adapter = LegacyServiceAdapter()
        self.results = {}
    
    def test_concurrent_requests_100(self):
        """Teste com 100 requisições simultâneas"""
        logger.info("Iniciando teste de 100 requisições concorrentes...")
        
        num_requests = 100
        results = []
        errors = []
        
        def make_request(request_id):
            try:
                start_time = time.time()
                correlation_id = f"load_test_{request_id}"
                
                # Executar requisição
                metrics = self.adapter.get_dashboard_metrics(correlation_id)
                
                response_time = time.time() - start_time
                return {
                    'request_id': request_id,
                    'response_time': response_time,
                    'success': True,
                    'data_points': len(metrics.dict()) if hasattr(metrics, 'dict') else 0
                }
            except Exception as e:
                return {
                    'request_id': request_id,
                    'success': False,
                    'error': str(e)
                }
        
        # Executar requisições concorrentes
        start_total = time.time()
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(make_request, i) for i in range(num_requests)]
            
            for future in as_completed(futures):
                result = future.result()
                if result['success']:
                    results.append(result)
                else:
                    errors.append(result)
        
        total_time = time.time() - start_total
        
        # Analisar resultados
        success_rate = len(results) / num_requests * 100
        response_times = [r['response_time'] for r in results]
        
        performance_metrics = {
            'test_name': 'concurrent_requests_100',
            'total_requests': num_requests,
            'successful_requests': len(results),
            'failed_requests': len(errors),
            'success_rate': round(success_rate, 2),
            'total_execution_time': round(total_time, 3),
            'requests_per_second': round(num_requests / total_time, 2),
            'response_times': {
                'min': round(min(response_times), 3) if response_times else None,
                'max': round(max(response_times), 3) if response_times else None,
                'mean': round(statistics.mean(response_times), 3) if response_times else None,
                'median': round(statistics.median(response_times), 3) if response_times else None,
                'p95': round(statistics.quantiles(response_times, n=20)[18], 3) if len(response_times) > 20 else None
            },
            'errors': errors[:5]  # Primeiros 5 erros para análise
        }
        
        # Validações
        test_passed = True
        validation_messages = []
        
        if success_rate < 95:
            test_passed = False
            validation_messages.append(f"Taxa de sucesso muito baixa: {success_rate}%")
        
        if performance_metrics['response_times']['p95'] and performance_metrics['response_times']['p95'] > 0.5:
            test_passed = False
            validation_messages.append(f"P95 muito alto: {performance_metrics['response_times']['p95']}s")
        
        performance_metrics['test_passed'] = test_passed
        performance_metrics['validation_messages'] = validation_messages
        
        logger.info(f"Teste de carga concluído: {json.dumps(performance_metrics, indent=2)}")
        self.results['concurrent_requests_100'] = performance_metrics
        return performance_metrics
    
    def test_memory_usage_under_load(self):
        """Teste de uso de memória sob carga"""
        logger.info("Iniciando teste de uso de memória...")
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Executar 50 requisições sequenciais
        start_time = time.time()
        for i in range(50):
            correlation_id = f"memory_test_{i}"
            self.adapter.get_dashboard_metrics(correlation_id)
        
        execution_time = time.time() - start_time
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        memory_metrics = {
            'test_name': 'memory_usage_under_load',
            'initial_memory_mb': round(initial_memory, 2),
            'final_memory_mb': round(final_memory, 2),
            'memory_increase_mb': round(memory_increase, 2),
            'execution_time': round(execution_time, 3),
            'requests_executed': 50
        }
        
        # Validar que não há vazamento significativo de memória
        test_passed = memory_increase < 100
        validation_messages = []
        
        if not test_passed:
            validation_messages.append(f"Possível vazamento de memória: {memory_increase}MB")
        
        memory_metrics['test_passed'] = test_passed
        memory_metrics['validation_messages'] = validation_messages
        
        logger.info(f"Teste de memória concluído: {json.dumps(memory_metrics, indent=2)}")
        self.results['memory_usage_under_load'] = memory_metrics
        return memory_metrics
    
    def test_sustained_load_1_minute(self):
        """Teste de carga sustentada por 1 minuto (reduzido para testes)"""
        logger.info("Iniciando teste de carga sustentada...")
        
        duration_seconds = 60   # 1 minuto para testes
        request_interval = 2    # 1 requisição a cada 2 segundos
        
        start_time = time.time()
        results = []
        
        request_count = 0
        while time.time() - start_time < duration_seconds:
            try:
                request_start = time.time()
                correlation_id = f"sustained_test_{request_count}"
                
                metrics = self.adapter.get_dashboard_metrics(correlation_id)
                response_time = time.time() - request_start
                
                results.append({
                    'request_id': request_count,
                    'response_time': response_time,
                    'timestamp': time.time(),
                    'success': True
                })
                
            except Exception as e:
                results.append({
                    'request_id': request_count,
                    'error': str(e),
                    'timestamp': time.time(),
                    'success': False
                })
            
            request_count += 1
            time.sleep(request_interval)
        
        # Analisar estabilidade
        successful_requests = [r for r in results if r['success']]
        success_rate = len(successful_requests) / len(results) * 100 if results else 0
        
        response_times = [r['response_time'] for r in successful_requests]
        avg_response_time = statistics.mean(response_times) if response_times else 0
        
        sustained_metrics = {
            'test_name': 'sustained_load_1_minute',
            'duration_seconds': duration_seconds,
            'total_requests': len(results),
            'successful_requests': len(successful_requests),
            'success_rate': round(success_rate, 2),
            'average_response_time': round(avg_response_time, 3),
            'requests_per_minute': round(len(results) / (duration_seconds / 60), 2)
        }
        
        # Validações de estabilidade
        test_passed = True
        validation_messages = []
        
        if success_rate < 98:
            test_passed = False
            validation_messages.append(f"Sistema instável: {success_rate}% de sucesso")
        
        if avg_response_time > 0.3:
            test_passed = False
            validation_messages.append(f"Performance degradada: {avg_response_time}s médio")
        
        sustained_metrics['test_passed'] = test_passed
        sustained_metrics['validation_messages'] = validation_messages
        
        logger.info(f"Teste sustentado concluído: {json.dumps(sustained_metrics, indent=2)}")
        self.results['sustained_load_1_minute'] = sustained_metrics
        return sustained_metrics
    
    def run_all_tests(self):
        """Executar todos os testes de performance"""
        logger.info("=== INICIANDO SUITE DE TESTES DE PERFORMANCE ===")
        
        start_time = datetime.now()
        
        try:
            # Teste 1: Requisições concorrentes
            self.test_concurrent_requests_100()
            
            # Teste 2: Uso de memória
            self.test_memory_usage_under_load()
            
            # Teste 3: Carga sustentada
            self.test_sustained_load_1_minute()
            
        except Exception as e:
            logger.error(f"Erro durante execução dos testes: {e}")
        
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        # Gerar relatório final
        report = {
            'execution_timestamp': start_time.isoformat(),
            'total_execution_time': round(execution_time, 2),
            'tests_executed': len(self.results),
            'tests_passed': sum(1 for test in self.results.values() if test.get('test_passed', False)),
            'tests_failed': sum(1 for test in self.results.values() if not test.get('test_passed', False)),
            'results': self.results
        }
        
        # Salvar relatório
        report_filename = f"performance_report_{start_time.strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"=== RELATÓRIO DE PERFORMANCE SALVO: {report_filename} ===")
        logger.info(f"Testes executados: {report['tests_executed']}")
        logger.info(f"Testes aprovados: {report['tests_passed']}")
        logger.info(f"Testes falharam: {report['tests_failed']}")
        logger.info(f"Tempo total: {report['total_execution_time']}s")
        
        return report

if __name__ == "__main__":
    tester = LegacyServicePerformanceTests()
    report = tester.run_all_tests()
    
    # Imprimir resumo
    print("\n" + "="*60)
    print("RESUMO DOS TESTES DE PERFORMANCE")
    print("="*60)
    
    for test_name, result in report['results'].items():
        status = "✓ PASSOU" if result.get('test_passed', False) else "✗ FALHOU"
        print(f"{test_name}: {status}")
        
        if result.get('validation_messages'):
            for msg in result['validation_messages']:
                print(f"  - {msg}")
    
    print(f"\nTempo total de execução: {report['total_execution_time']}s")
    print(f"Relatório salvo em: performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")