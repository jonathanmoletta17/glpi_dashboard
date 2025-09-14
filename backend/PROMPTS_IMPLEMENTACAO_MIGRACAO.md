# 🚀 PROMPTS DE IMPLEMENTAÇÃO: MIGRAÇÃO SERVIÇOS LEGACY → CLEAN ARCHITECTURE

## 📋 Documento de Execução Técnica

**Objetivo**: Guia completo com prompts específicos para implementar a migração dos serviços legacy robustos para a Clean Architecture, eliminando dados mock e garantindo 100% de dados reais do GLPI.

**Base**: Análise documentada em `connectivity_status_final.md`

---

# 🔍 FASE 1: PREPARAÇÃO E ANÁLISE (1-2 dias)

## 📊 PROMPT 1.1: Auditoria Completa dos Serviços Legacy

```
Analise detalhadamente a estrutura dos serviços legacy em `backend/services/legacy/` e:

1. Mapeie TODOS os métodos públicos da classe GLPIServiceFacade
2. Documente a assinatura de cada método (parâmetros, tipos de retorno)
3. Identifique as dependências entre os serviços (authentication, cache, http_client, etc.)
4. Crie um diagrama de dependências mostrando como os serviços se relacionam
5. Valide se os contratos de interface são compatíveis com UnifiedGLPIServiceContract

Foque especialmente em:
- Métodos que retornam dados de tickets, usuários, computadores
- Sistemas de cache e autenticação
- Tratamento de erros e logging
- Descoberta automática de field IDs

Gere um relatório detalhado com:
- Lista completa de métodos mapeados
- Matriz de dependências
- Pontos de incompatibilidade identificados
- Recomendações de adaptação
```

## 🧪 PROMPT 1.2: Testes de Baseline dos Serviços Legacy

```
Execute uma bateria completa de testes nos serviços legacy para estabelecer baseline de performance:

1. Teste isolado do GLPIServiceFacade:
   - Instancie o facade diretamente
   - Execute métodos principais (get_tickets, get_users, get_computers)
   - Meça tempo de resposta, uso de memória, taxa de sucesso
   - Valide integridade dos 10.240 tickets confirmados

2. Teste de performance individual:
   - AuthenticationService: tempo de autenticação
   - CacheService: hit rate, tempo de acesso
   - HttpClientService: latência de requisições
   - MetricsService: tempo de processamento

3. Teste de stress:
   - 100 requisições simultâneas
   - Comportamento sob carga
   - Identificação de gargalos

4. Documente métricas atuais:
   - Tempo médio de resposta por endpoint
   - Taxa de erro atual
   - Uso de recursos (CPU, memória)
   - Eficiência do cache

Crie um relatório de baseline com gráficos e métricas quantitativas.
```

## 🔗 PROMPT 1.3: Análise de Dependências e Compatibilidade

```
Analise as dependências e compatibilidade entre arquiteturas:

1. Mapeamento de imports:
   - Liste todos os imports dos serviços legacy
   - Identifique dependências circulares
   - Verifique compatibilidade com estrutura do `backend/core/`

2. Análise de schemas de dados:
   - Compare estruturas de dados retornadas pelos serviços legacy
   - Valide compatibilidade com Pydantic models em `backend/schemas/`
   - Identifique necessidades de conversão de dados

3. Validação de contratos:
   - Compare métodos do GLPIServiceFacade com UnifiedGLPIServiceContract
   - Identifique métodos ausentes ou incompatíveis
   - Documente diferenças de assinatura

4. Análise de configuração:
   - Verifique compatibilidade de configurações em `backend/config/settings.py`
   - Identifique variáveis de ambiente necessárias
   - Valide configurações de cache, logging, autenticação

Gere um mapa de compatibilidade detalhado com plano de adaptação.
```

---

# 🌉 FASE 2: CRIAÇÃO DO ADAPTER BRIDGE (2-3 dias)

## 🏗️ PROMPT 2.1: Desenvolvimento do LegacyServiceAdapter

```
Crie o arquivo `backend/core/infrastructure/adapters/legacy_service_adapter.py` com implementação completa:

1. Estrutura base:
```python
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from backend.core.domain.contracts.metrics_contracts import UnifiedGLPIServiceContract
from backend.core.domain.entities.dashboard_metrics import DashboardMetrics
from backend.services.legacy.glpi_service_facade import GLPIServiceFacade
from backend.schemas.dashboard import (
    DashboardMetricsResponse,
    TechnicianRankingResponse,
    NewTicketsResponse,
    SystemStatusResponse
)

class LegacyServiceAdapter(UnifiedGLPIServiceContract):
    """Adapter que conecta Clean Architecture aos serviços legacy robustos"""
    
    def __init__(self):
        self.legacy_facade = GLPIServiceFacade()
        self.logger = logging.getLogger("legacy_adapter")
        self._initialize_adapter()
    
    def _initialize_adapter(self):
        """Inicializa o adapter com configurações necessárias"""
        # Implementar inicialização
        pass
```

2. Implemente TODOS os métodos do contrato UnifiedGLPIServiceContract:
   - get_dashboard_metrics()
   - get_dashboard_metrics_with_date_filter()
   - get_dashboard_metrics_with_modification_date_filter()
   - get_dashboard_metrics_with_filters()
   - get_technician_ranking()
   - get_new_tickets()
   - get_system_status()

3. Para cada método:
   - Chame o método correspondente do legacy_facade
   - Converta dados para formato esperado pela Clean Architecture
   - Implemente tratamento de erros robusto
   - Adicione logging estruturado
   - Mantenha compatibilidade com correlation_id

4. Requisitos técnicos:
   - Use type hints completos
   - Implemente validação de dados com Pydantic
   - Mantenha performance otimizada
   - Adicione documentação detalhada
   - Implemente retry logic para falhas temporárias

O adapter deve ser uma ponte perfeita entre as duas arquiteturas.
```

## 🔄 PROMPT 2.2: Mapeamento e Conversão de Métodos

```
Implemente o mapeamento completo entre métodos das duas arquiteturas:

1. Crie tabela de mapeamento:
```
MetricsFacade Method          → Legacy Method                → Conversion Required
get_dashboard_metrics()       → get_dashboard_summary()      → DashboardMetrics model
get_technician_ranking()      → get_technician_performance() → TechnicianRanking model
get_new_tickets()            → get_recent_tickets()         → NewTickets model
get_system_status()          → get_system_health()          → SystemStatus model
```

2. Para cada mapeamento, implemente:
   - Função de conversão de dados
   - Validação de tipos de entrada
   - Transformação para Pydantic models
   - Tratamento de campos opcionais/ausentes
   - Normalização de formatos (datas, números, strings)

3. Exemplo de implementação:
```python
def _convert_legacy_metrics_to_dashboard(self, legacy_data: Dict[str, Any]) -> DashboardMetrics:
    """Converte dados legacy para DashboardMetrics"""
    try:
        # Validar dados de entrada
        if not legacy_data or 'tickets' not in legacy_data:
            raise ValueError("Dados legacy inválidos")
        
        # Converter estrutura
        converted_data = {
            'total_tickets': legacy_data.get('tickets', {}).get('total', 0),
            'open_tickets': legacy_data.get('tickets', {}).get('open', 0),
            'closed_tickets': legacy_data.get('tickets', {}).get('closed', 0),
            'pending_tickets': legacy_data.get('tickets', {}).get('pending', 0),
            'last_updated': datetime.now().isoformat()
        }
        
        # Validar com Pydantic
        return DashboardMetrics(**converted_data)
        
    except Exception as e:
        self.logger.error(f"Erro na conversão de dados: {e}")
        raise
```

4. Implemente conversores para:
   - Estruturas de tickets
   - Dados de usuários/técnicos
   - Métricas de performance
   - Status do sistema
   - Filtros e parâmetros de busca

Cada conversor deve ser testável e robusto.
```

## 🧪 PROMPT 2.3: Testes de Integração do Adapter

```
Crie suite completa de testes para o LegacyServiceAdapter:

1. Arquivo: `backend/tests/test_legacy_service_adapter.py`

2. Estrutura de testes:
```python
import pytest
from unittest.mock import Mock, patch
from backend.core.infrastructure.adapters.legacy_service_adapter import LegacyServiceAdapter
from backend.core.domain.entities.dashboard_metrics import DashboardMetrics

class TestLegacyServiceAdapter:
    
    @pytest.fixture
    def adapter(self):
        return LegacyServiceAdapter()
    
    @pytest.fixture
    def mock_legacy_facade(self):
        with patch('backend.services.legacy.glpi_service_facade.GLPIServiceFacade') as mock:
            yield mock
    
    def test_get_dashboard_metrics_success(self, adapter, mock_legacy_facade):
        # Teste de sucesso
        pass
    
    def test_get_dashboard_metrics_error_handling(self, adapter, mock_legacy_facade):
        # Teste de tratamento de erro
        pass
    
    def test_data_conversion_accuracy(self, adapter):
        # Teste de precisão na conversão
        pass
```

3. Categorias de teste:
   - **Testes unitários**: Cada método do adapter isoladamente
   - **Testes de conversão**: Validar transformação de dados
   - **Testes de erro**: Cenários de falha e recovery
   - **Testes de performance**: Tempo de resposta e uso de memória
   - **Testes de integração**: Adapter + serviços legacy reais

4. Cenários específicos:
   - Dados válidos do GLPI (10.240 tickets)
   - Dados parciais ou incompletos
   - Falhas de conectividade
   - Timeouts de requisição
   - Dados corrompidos ou inválidos
   - Cache hits e misses

5. Métricas de cobertura:
   - Cobertura de código > 95%
   - Todos os caminhos de erro testados
   - Performance dentro dos limites (< 300ms)

Execute os testes e garanta 100% de aprovação antes de prosseguir.
```

---

# 🔗 FASE 3: INTEGRAÇÃO GRADUAL (3-4 dias)

## ⚙️ PROMPT 3.1: Modificação do MetricsFacade

```
Modifique o arquivo `backend/core/application/services/metrics_facade.py` para suportar o LegacyServiceAdapter:

1. Adicione imports necessários:
```python
from backend.core.infrastructure.adapters.legacy_service_adapter import LegacyServiceAdapter
from backend.config.settings import active_config
```

2. Modifique o construtor:
```python
class MetricsFacade(UnifiedGLPIServiceContract):
    def __init__(self):
        self.logger = logging.getLogger("metrics_facade")
        
        # Escolher adapter baseado na configuração
        if getattr(active_config, 'USE_LEGACY_SERVICES', True):
            self.logger.info("Inicializando com LegacyServiceAdapter")
            self.adapter = LegacyServiceAdapter()
        else:
            self.logger.info("Inicializando com GLPIMetricsAdapter")
            self.adapter = GLPIMetricsAdapter(self.glpi_config)
        
        self.cache = UnifiedCache()
        self._initialize_facade()
    
    def _initialize_facade(self):
        """Inicializa facade com configurações específicas do adapter"""
        adapter_type = type(self.adapter).__name__
        self.logger.info(f"MetricsFacade inicializado com {adapter_type}")
```

3. Modifique todos os métodos para usar self.adapter:
```python
def get_dashboard_metrics(self, correlation_id: str = None) -> DashboardMetrics:
    """Obtém métricas do dashboard usando adapter configurado"""
    try:
        correlation_id = correlation_id or self._generate_correlation_id()
        
        # Log do adapter sendo usado
        adapter_type = type(self.adapter).__name__
        self.logger.info(f"Obtendo métricas via {adapter_type}", extra={
            'correlation_id': correlation_id,
            'adapter_type': adapter_type
        })
        
        # Chamar adapter
        metrics = self.adapter.get_dashboard_metrics(correlation_id)
        
        # Log de sucesso
        self.logger.info(f"Métricas obtidas com sucesso via {adapter_type}", extra={
            'correlation_id': correlation_id,
            'total_tickets': getattr(metrics, 'total_tickets', 'N/A')
        })
        
        return metrics
        
    except Exception as e:
        self.logger.error(f"Erro ao obter métricas: {e}", extra={
            'correlation_id': correlation_id,
            'adapter_type': type(self.adapter).__name__
        })
        raise
```

4. Adicione método de diagnóstico:
```python
def get_adapter_info(self) -> Dict[str, Any]:
    """Retorna informações sobre o adapter atual"""
    return {
        'adapter_type': type(self.adapter).__name__,
        'is_legacy': isinstance(self.adapter, LegacyServiceAdapter),
        'configuration': {
            'USE_LEGACY_SERVICES': getattr(active_config, 'USE_LEGACY_SERVICES', False),
            'USE_MOCK_DATA': getattr(active_config, 'USE_MOCK_DATA', False)
        }
    }
```

Garanta que a transição seja transparente para os consumidores da API.
```

## 🚩 PROMPT 3.2: Configuração de Feature Flags

```
Implemente sistema de feature flags em `backend/config/settings.py`:

1. Adicione novas configurações:
```python
# Configurações de Migração Legacy
USE_LEGACY_SERVICES = os.environ.get("USE_LEGACY_SERVICES", "True").lower() == "true"
USE_MOCK_DATA = os.environ.get("USE_MOCK_DATA", "False").lower() == "true"
LEGACY_ADAPTER_TIMEOUT = int(os.environ.get("LEGACY_ADAPTER_TIMEOUT", "30"))
LEGACY_ADAPTER_RETRY_COUNT = int(os.environ.get("LEGACY_ADAPTER_RETRY_COUNT", "3"))

# Configurações de Monitoramento
ENABLE_ADAPTER_METRICS = os.environ.get("ENABLE_ADAPTER_METRICS", "True").lower() == "true"
ADAPTER_PERFORMANCE_LOG = os.environ.get("ADAPTER_PERFORMANCE_LOG", "True").lower() == "true"
```

2. Adicione validação de configuração:
```python
def validate_migration_config():
    """Valida configurações de migração"""
    errors = []
    
    # Validar combinações inválidas
    if USE_LEGACY_SERVICES and USE_MOCK_DATA:
        errors.append("USE_LEGACY_SERVICES e USE_MOCK_DATA não podem ser True simultaneamente")
    
    # Validar timeouts
    if LEGACY_ADAPTER_TIMEOUT < 5:
        errors.append("LEGACY_ADAPTER_TIMEOUT deve ser >= 5 segundos")
    
    if LEGACY_ADAPTER_RETRY_COUNT < 1:
        errors.append("LEGACY_ADAPTER_RETRY_COUNT deve ser >= 1")
    
    if errors:
        raise ValueError(f"Configuração inválida: {'; '.join(errors)}")
    
    return True

# Executar validação na inicialização
validate_migration_config()
```

3. Crie arquivo `.env.migration` com configurações de teste:
```bash
# Configurações para Migração Legacy
USE_LEGACY_SERVICES=true
USE_MOCK_DATA=false
LEGACY_ADAPTER_TIMEOUT=30
LEGACY_ADAPTER_RETRY_COUNT=3

# Monitoramento
ENABLE_ADAPTER_METRICS=true
ADAPTER_PERFORMANCE_LOG=true

# GLPI (manter configurações existentes)
GLPI_URL=http://cau.ppiratini.intra.rs.gov.br/glpi/apirest.php
GLPI_USER_TOKEN=seu_user_token
GLPI_APP_TOKEN=seu_app_token
```

4. Adicione endpoint de configuração em `backend/api/routes.py`:
```python
@api_bp.route('/config/migration', methods=['GET'])
def get_migration_config():
    """Retorna configuração atual de migração"""
    try:
        config_info = {
            'use_legacy_services': active_config.USE_LEGACY_SERVICES,
            'use_mock_data': active_config.USE_MOCK_DATA,
            'legacy_adapter_timeout': active_config.LEGACY_ADAPTER_TIMEOUT,
            'legacy_adapter_retry_count': active_config.LEGACY_ADAPTER_RETRY_COUNT,
            'adapter_metrics_enabled': active_config.ENABLE_ADAPTER_METRICS,
            'performance_log_enabled': active_config.ADAPTER_PERFORMANCE_LOG
        }
        
        return jsonify({
            'status': 'success',
            'configuration': config_info,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
```

Implemente sistema robusto de configuração para controlar a migração.
```

## 🔬 PROMPT 3.3: Implementação de Testes A/B

```
Crie sistema de comparação entre nova arquitetura e serviços legacy:

1. Arquivo: `backend/api/comparison_routes.py`

```python
from flask import Blueprint, jsonify, request
from datetime import datetime
import time
import logging

from backend.core.application.services.metrics_facade import MetricsFacade
from backend.core.infrastructure.adapters.glpi_metrics_adapter import GLPIMetricsAdapter
from backend.core.infrastructure.adapters.legacy_service_adapter import LegacyServiceAdapter
from backend.config.settings import active_config

comparison_bp = Blueprint('comparison', __name__, url_prefix='/api/comparison')
logger = logging.getLogger('comparison')

@comparison_bp.route('/metrics', methods=['GET'])
def compare_metrics():
    """Compara métricas entre nova arquitetura e serviços legacy"""
    try:
        correlation_id = request.headers.get('X-Correlation-ID', f"comp_{int(time.time())}")
        
        # Instanciar ambos os adapters
        legacy_adapter = LegacyServiceAdapter()
        new_adapter = GLPIMetricsAdapter(active_config)
        
        results = {
            'correlation_id': correlation_id,
            'timestamp': datetime.now().isoformat(),
            'comparison': {}
        }
        
        # Testar get_dashboard_metrics
        results['comparison']['dashboard_metrics'] = await _compare_dashboard_metrics(
            legacy_adapter, new_adapter, correlation_id
        )
        
        # Testar get_technician_ranking
        results['comparison']['technician_ranking'] = await _compare_technician_ranking(
            legacy_adapter, new_adapter, correlation_id
        )
        
        # Testar get_new_tickets
        results['comparison']['new_tickets'] = await _compare_new_tickets(
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

async def _compare_dashboard_metrics(legacy_adapter, new_adapter, correlation_id):
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
```

2. Adicione endpoint de relatório de comparação:
```python
@comparison_bp.route('/report', methods=['GET'])
def generate_comparison_report():
    """Gera relatório detalhado de comparação"""
    # Implementar geração de relatório com gráficos e métricas
    pass
```

3. Registre blueprint em `backend/app.py`:
```python
from backend.api.comparison_routes import comparison_bp
app.register_blueprint(comparison_bp)
```

Crie sistema completo de comparação para validar a migração.
```

---

# ✅ FASE 4: VALIDAÇÃO E OTIMIZAÇÃO (2-3 dias)

## 🚀 PROMPT 4.1: Testes de Carga e Stress

```
Implemente suite completa de testes de performance para os serviços legacy:

1. Arquivo: `backend/tests/performance/test_legacy_load.py`

```python
import asyncio
import time
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
import pytest
import psutil
import logging

from backend.core.infrastructure.adapters.legacy_service_adapter import LegacyServiceAdapter

class TestLegacyServiceLoad:
    
    @pytest.fixture
    def adapter(self):
        return LegacyServiceAdapter()
    
    def test_concurrent_requests_100(self, adapter):
        """Teste com 100 requisições simultâneas"""
        num_requests = 100
        results = []
        errors = []
        
        def make_request(request_id):
            try:
                start_time = time.time()
                correlation_id = f"load_test_{request_id}"
                
                # Executar requisição
                metrics = adapter.get_dashboard_metrics(correlation_id)
                
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
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(make_request, i) for i in range(num_requests)]
            
            for future in as_completed(futures):
                result = future.result()
                if result['success']:
                    results.append(result)
                else:
                    errors.append(result)
        
        # Analisar resultados
        success_rate = len(results) / num_requests * 100
        response_times = [r['response_time'] for r in results]
        
        performance_metrics = {
            'total_requests': num_requests,
            'successful_requests': len(results),
            'failed_requests': len(errors),
            'success_rate': round(success_rate, 2),
            'response_times': {
                'min': round(min(response_times), 3) if response_times else None,
                'max': round(max(response_times), 3) if response_times else None,
                'mean': round(statistics.mean(response_times), 3) if response_times else None,
                'median': round(statistics.median(response_times), 3) if response_times else None,
                'p95': round(statistics.quantiles(response_times, n=20)[18], 3) if len(response_times) > 20 else None
            }
        }
        
        # Validações
        assert success_rate >= 95, f"Taxa de sucesso muito baixa: {success_rate}%"
        assert performance_metrics['response_times']['p95'] <= 0.5, f"P95 muito alto: {performance_metrics['response_times']['p95']}s"
        
        logging.info(f"Teste de carga concluído: {performance_metrics}")
        return performance_metrics
    
    def test_memory_usage_under_load(self, adapter):
        """Teste de uso de memória sob carga"""
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Executar 50 requisições sequenciais
        for i in range(50):
            correlation_id = f"memory_test_{i}"
            adapter.get_dashboard_metrics(correlation_id)
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Validar que não há vazamento significativo de memória
        assert memory_increase < 100, f"Possível vazamento de memória: {memory_increase}MB"
        
        return {
            'initial_memory_mb': round(initial_memory, 2),
            'final_memory_mb': round(final_memory, 2),
            'memory_increase_mb': round(memory_increase, 2)
        }
    
    def test_sustained_load_5_minutes(self, adapter):
        """Teste de carga sustentada por 5 minutos"""
        duration_seconds = 300  # 5 minutos
        request_interval = 2    # 1 requisição a cada 2 segundos
        
        start_time = time.time()
        results = []
        
        request_count = 0
        while time.time() - start_time < duration_seconds:
            try:
                request_start = time.time()
                correlation_id = f"sustained_test_{request_count}"
                
                metrics = adapter.get_dashboard_metrics(correlation_id)
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
        success_rate = len(successful_requests) / len(results) * 100
        
        response_times = [r['response_time'] for r in successful_requests]
        avg_response_time = statistics.mean(response_times) if response_times else 0
        
        # Validações de estabilidade
        assert success_rate >= 98, f"Sistema instável: {success_rate}% de sucesso"
        assert avg_response_time <= 0.3, f"Performance degradada: {avg_response_time}s médio"
        
        return {
            'duration_seconds': duration_seconds,
            'total_requests': len(results),
            'successful_requests': len(successful_requests),
            'success_rate': round(success_rate, 2),
            'average_response_time': round(avg_response_time, 3)
        }
```

2. Execute os testes e documente resultados:
```bash
pytest backend/tests/performance/test_legacy_load.py -v --tb=short
```

3. Crie relatório de performance com gráficos e recomendações de otimização.
```

## 📊 PROMPT 4.2: Monitoramento Avançado e Métricas

```
Implemente sistema completo de monitoramento para os serviços legacy:

1. Arquivo: `backend/utils/legacy_monitoring.py`

```python
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
```

2. Integre o monitor no LegacyServiceAdapter:
```python
# Em legacy_service_adapter.py
from backend.utils.legacy_monitoring import legacy_monitor

class LegacyServiceAdapter(UnifiedGLPIServiceContract):
    
    @legacy_monitor.monitor_method('get_dashboard_metrics')
    def get_dashboard_metrics(self, correlation_id: str = None) -> DashboardMetrics:
        # Implementação existente
        pass
    
    @legacy_monitor.monitor_method('get_technician_ranking')
    def get_technician_ranking(self, correlation_id: str = None) -> TechnicianRankingResponse:
        # Implementação existente
        pass
```

3. Adicione endpoints de monitoramento em `backend/api/routes.py`:
```python
@api_bp.route('/monitoring/legacy/metrics', methods=['GET'])
def get_legacy_metrics():
    """Retorna métricas dos serviços legacy"""
    try:
        from backend.utils.legacy_monitoring import legacy_monitor
        metrics = legacy_monitor.get_metrics_summary()
        
        return jsonify({
            'status': 'success',
            'metrics': metrics,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@api_bp.route('/monitoring/legacy/health', methods=['GET'])
def get_legacy_health():
    """Retorna status de saúde dos serviços legacy"""
    try:
        from backend.utils.legacy_monitoring import legacy_monitor
        health = legacy_monitor.get_health_status()
        
        status_code = 200
        if health['status'] == 'degraded':
            status_code = 206
        elif health['status'] == 'unhealthy':
            status_code = 503
        
        return jsonify(health), status_code
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
```

Implemente monitoramento completo para garantir observabilidade total.
```

## 📚 PROMPT 4.3: Documentação e Guias de Troubleshooting

```
Crie documentação completa para a migração implementada:

1. Arquivo: `backend/docs/LEGACY_MIGRATION_GUIDE.md`

```markdown
# Guia de Migração: Serviços Legacy para Clean Architecture

## Visão Geral

Este documento descreve a implementação da migração dos serviços legacy robustos para a Clean Architecture, mantendo 100% dos dados reais do GLPI.

## Arquitetura Implementada

```
API Routes → MetricsFacade → LegacyServiceAdapter → GLPIServiceFacade → Serviços Legacy → GLPI API
```

### Componentes Principais

#### 1. LegacyServiceAdapter
- **Localização**: `backend/core/infrastructure/adapters/legacy_service_adapter.py`
- **Função**: Bridge entre Clean Architecture e serviços legacy
- **Responsabilidades**:
  - Conversão de dados entre formatos
  - Implementação do contrato UnifiedGLPIServiceContract
  - Tratamento de erros e logging
  - Monitoramento de performance

#### 2. MetricsFacade Modificado
- **Localização**: `backend/core/application/services/metrics_facade.py`
- **Modificações**:
  - Suporte a múltiplos adapters
  - Configuração via feature flags
  - Logging detalhado de adapter utilizado

#### 3. Sistema de Monitoramento
- **Localização**: `backend/utils/legacy_monitoring.py`
- **Funcionalidades**:
  - Métricas de performance em tempo real
  - Detecção de degradação de serviço
  - Alertas automáticos

## Configuração

### Variáveis de Ambiente

```bash
# Controle de Adapter
USE_LEGACY_SERVICES=true          # Usar serviços legacy (recomendado)
USE_MOCK_DATA=false               # Nunca usar dados mock em produção

# Performance
LEGACY_ADAPTER_TIMEOUT=30         # Timeout em segundos
LEGACY_ADAPTER_RETRY_COUNT=3      # Número de tentativas

# Monitoramento
ENABLE_ADAPTER_METRICS=true       # Habilitar métricas
ADAPTER_PERFORMANCE_LOG=true      # Log de performance
```

### Configurações Recomendadas por Ambiente

#### Desenvolvimento
```bash
USE_LEGACY_SERVICES=true
USE_MOCK_DATA=false
LEGACY_ADAPTER_TIMEOUT=10
ENABLE_ADAPTER_METRICS=true
ADAPTER_PERFORMANCE_LOG=true
```

#### Produção
```bash
USE_LEGACY_SERVICES=true
USE_MOCK_DATA=false
LEGACY_ADAPTER_TIMEOUT=30
LEGACY_ADAPTER_RETRY_COUNT=3
ENABLE_ADAPTER_METRICS=true
ADAPTER_PERFORMANCE_LOG=false
```

## Endpoints de Monitoramento

### Métricas dos Serviços Legacy
```http
GET /api/monitoring/legacy/metrics
```

Retorna:
```json
{
  "status": "success",
  "metrics": {
    "get_dashboard_metrics": {
      "call_count": 1250,
      "error_count": 12,
      "error_rate_percent": 0.96,
      "avg_response_time": 0.245,
      "p95_response_time": 0.380
    }
  }
}
```

### Status de Saúde
```http
GET /api/monitoring/legacy/health
```

Retorna:
```json
{
  "status": "healthy",
  "timestamp": "2025-01-14T10:30:00Z",
  "issues": []
}
```

### Comparação de Adapters
```http
GET /api/comparison/metrics
```

## Troubleshooting

### Problemas Comuns

#### 1. Erro: "LegacyServiceAdapter não encontrado"

**Sintoma**: `ImportError: cannot import name 'LegacyServiceAdapter'`

**Causa**: Adapter não foi criado ou não está no PYTHONPATH

**Solução**:
```bash
# Verificar se arquivo existe
ls backend/core/infrastructure/adapters/legacy_service_adapter.py

# Verificar imports
python -c "from backend.core.infrastructure.adapters.legacy_service_adapter import LegacyServiceAdapter; print('OK')"
```

#### 2. Performance Degradada

**Sintoma**: Tempo de resposta > 1s

**Diagnóstico**:
```bash
# Verificar métricas
curl http://localhost:5000/api/monitoring/legacy/metrics

# Verificar logs
tail -f backend/logs/app.log | grep "legacy_adapter"
```

**Soluções**:
- Verificar conectividade com GLPI
- Aumentar timeout: `LEGACY_ADAPTER_TIMEOUT=60`
- Verificar cache do GLPI
- Analisar queries lentas

#### 3. Taxa de Erro Alta

**Sintoma**: error_rate_percent > 5%

**Diagnóstico**:
```bash
# Verificar erros recentes
curl http://localhost:5000/api/monitoring/legacy/health

# Logs detalhados
grep "ERROR" backend/logs/app.log | grep "legacy_adapter" | tail -20
```

**Soluções**:
- Verificar tokens GLPI válidos
- Verificar conectividade de rede
- Aumentar retry count: `LEGACY_ADAPTER_RETRY_COUNT=5`
- Verificar permissões no GLPI

#### 4. Dados Inconsistentes

**Sintoma**: Diferenças entre adapters na comparação

**Diagnóstico**:
```bash
# Executar comparação
curl http://localhost:5000/api/comparison/metrics

# Verificar logs de conversão
grep "conversion" backend/logs/app.log
```

**Soluções**:
- Verificar mapeamento de campos
- Validar conversões de tipo
- Atualizar schemas Pydantic
- Verificar timezone e formatação de datas

### Comandos Úteis

```bash
# Verificar status geral
curl -s http://localhost:5000/api/monitoring/legacy/health | jq '.status'

# Monitorar performance em tempo real
watch -n 5 'curl -s http://localhost:5000/api/monitoring/legacy/metrics | jq ".metrics | to_entries[] | {method: .key, avg_time: .value.avg_response_time, error_rate: .value.error_rate_percent}"'

# Testar adapter específico
python -c "
from backend.core.infrastructure.adapters.legacy_service_adapter import LegacyServiceAdapter
adapter = LegacyServiceAdapter()
result = adapter.get_dashboard_metrics('test_123')
print(f'Success: {result}')
"

# Verificar configuração atual
curl -s http://localhost:5000/api/config/migration | jq
```

## Rollback Plan

Em caso de problemas críticos:

1. **Rollback Imediato**:
```bash
# Desabilitar serviços legacy
export USE_LEGACY_SERVICES=false

# Reiniciar aplicação
sudo systemctl restart glpi-dashboard
```

2. **Rollback com Dados Mock** (apenas emergência):
```bash
# ATENÇÃO: Apenas para emergências!
export USE_LEGACY_SERVICES=false
export USE_MOCK_DATA=true

# Reiniciar aplicação
sudo systemctl restart glpi-dashboard
```

3. **Verificar Rollback**:
```bash
# Verificar configuração
curl http://localhost:5000/api/config/migration

# Testar endpoints
curl http://localhost:5000/api/metrics/v2
```

## Métricas de Sucesso

### KPIs Alvo
- **Tempo de resposta P95**: < 300ms
- **Taxa de erro**: < 1%
- **Disponibilidade**: > 99.9%
- **Cache hit rate**: > 80%
- **Dados mock**: 0% em produção

### Monitoramento Contínuo

```bash
# Script de monitoramento (executar via cron)
#!/bin/bash
HEALTH=$(curl -s http://localhost:5000/api/monitoring/legacy/health | jq -r '.status')
if [ "$HEALTH" != "healthy" ]; then
    echo "ALERT: Legacy services unhealthy - $HEALTH" | mail -s "GLPI Dashboard Alert" admin@empresa.com
fi
```

## Próximos Passos

1. **Otimizações Futuras**:
   - Implementar cache distribuído
   - Otimizar queries GLPI
   - Implementar circuit breaker

2. **Melhorias de Monitoramento**:
   - Dashboard Grafana
   - Alertas Prometheus
   - Métricas de negócio

3. **Expansão de Funcionalidades**:
   - Novos endpoints
   - Relatórios customizados
   - APIs específicas por área
```

2. Crie também `backend/docs/TROUBLESHOOTING_LEGACY.md` com cenários específicos e soluções detalhadas.

3. Documente todos os endpoints, configurações e procedimentos operacionais.
```

---

# 🚀 FASE 5: DEPLOY E MIGRAÇÃO FINAL (1-2 dias)

## 🔧 PROMPT 5.1: Configuração de Produção

```
Prepare o ambiente de produção para a migração final:

1. Arquivo: `backend/config/production.env`

```bash
# ===========================================
# CONFIGURAÇÃO DE PRODUÇÃO - MIGRAÇÃO LEGACY
# ===========================================

# Controle de Adapter (CRÍTICO)
USE_LEGACY_SERVICES=true
USE_MOCK_DATA=false

# GLPI API (Produção)
GLPI_URL=https://glpi-prod.empresa.com/apirest.php
GLPI_USER_TOKEN=seu_user_token_producao
GLPI_APP_TOKEN=seu_app_token_producao

# Performance e Timeout
LEGACY_ADAPTER_TIMEOUT=30
LEGACY_ADAPTER_RETRY_COUNT=3
LEGACY_ADAPTER_MAX_CONNECTIONS=20

# Cache (Otimizado para Produção)
CACHE_TTL=300
CACHE_MAX_SIZE=1000
UNIFIED_CACHE_ENABLED=true

# Monitoramento
ENABLE_ADAPTER_METRICS=true
ADAPTER_PERFORMANCE_LOG=false  # Reduzir logs em produção
STRUCTURED_LOGGING=true

# Segurança
SECRET_KEY=sua_chave_secreta_super_forte_aqui
API_KEY=sua_api_key_producao

# Observabilidade
PROMETHEUS_GATEWAY_URL=http://prometheus:9091
LOG_LEVEL=INFO
LOG_FILE_PATH=/var/log/glpi-dashboard/app.log

# Flask (Produção)
FLASK_ENV=production
DEBUG=false
HOST=0.0.0.0
PORT=5000

# Gunicorn
WORKERS=4
WORKER_CLASS=sync
WORKER_CONNECTIONS=1000
MAX_REQUESTS=1000
MAX_REQUESTS_JITTER=100
```

2. Script de validação pré-deploy: `scripts/validate_production.py`

```python
#!/usr/bin/env python3
"""
Script de validação pré-deploy para migração legacy
"""

import os
import sys
import requests
import time
from datetime import datetime

def validate_environment():
    """Valida variáveis de ambiente críticas"""
    print("🔍 Validando variáveis de ambiente...")
    
    required_vars = [
        'USE_LEGACY_SERVICES',
        'USE_MOCK_DATA', 
        'GLPI_URL',
        'GLPI_USER_TOKEN',
        'GLPI_APP_TOKEN',
        'SECRET_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Variáveis ausentes: {', '.join(missing_vars)}")
        return False
    
    # Validar configurações críticas
    if os.environ.get('USE_LEGACY_SERVICES', '').lower() != 'true':
        print("❌ USE_LEGACY_SERVICES deve ser 'true' em produção")
        return False
    
    if os.environ.get('USE_MOCK_DATA', '').lower() != 'false':
        print("❌ USE_MOCK_DATA deve ser 'false' em produção")
        return False
    
    print("✅ Variáveis de ambiente validadas")
    return True

def validate_glpi_connectivity():
    """Valida conectividade com GLPI"""
    print("🔍 Validando conectividade GLPI...")
    
    glpi_url = os.environ.get('GLPI_URL')
    user_token = os.environ.get('GLPI_USER_TOKEN')
    app_token = os.environ.get('GLPI_APP_TOKEN')
    
    try:
        # Testar autenticação
        auth_url = f"{glpi_url}/initSession"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'user_token {user_token}',
            'App-Token': app_token
        }
        
        response = requests.get(auth_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            session_token = response.json().get('session_token')
            if session_token:
                print("✅ Autenticação GLPI bem-sucedida")
                
                # Testar busca de dados
                test_url = f"{glpi_url}/Ticket"
                test_headers = headers.copy()
                test_headers['Session-Token'] = session_token
                
                test_response = requests.get(
                    test_url, 
                    headers=test_headers, 
                    params={'range': '0-4'},
                    timeout=10
                )
                
                if test_response.status_code in [200, 206]:
                    data = test_response.json()
                    if isinstance(data, list) and len(data) > 0:
                        print(f"✅ Dados GLPI acessíveis ({len(data)} tickets encontrados)")
                        return True
                    else:
                        print("⚠️ GLPI acessível mas sem dados")
                        return False
                else:
                    print(f"❌ Erro ao buscar dados GLPI: {test_response.status_code}")
                    return False
            else:
                print("❌ Token de sessão não recebido")
                return False
        else:
            print(f"❌ Falha na autenticação GLPI: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro de conectividade GLPI: {e}")
        return False

def validate_legacy_services():
    """Valida serviços legacy"""
    print("🔍 Validando serviços legacy...")
    
    try:
        # Importar e testar LegacyServiceAdapter
        sys.path.append('/app/backend')
        from backend.core.infrastructure.adapters.legacy_service_adapter import LegacyServiceAdapter
        
        adapter = LegacyServiceAdapter()
        
        # Testar método principal
        start_time = time.time()
        metrics = adapter.get_dashboard_metrics('validation_test')
        response_time = time.time() - start_time
        
        if metrics and hasattr(metrics, 'total_tickets'):
            print(f"✅ Serviços legacy funcionais (tempo: {response_time:.3f}s)")
            print(f"   Total de tickets: {getattr(metrics, 'total_tickets', 'N/A')}")
            return True
        else:
            print("❌ Serviços legacy retornaram dados inválidos")
            return False
            
    except ImportError as e:
        print(f"❌ Erro ao importar LegacyServiceAdapter: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro nos serviços legacy: {e}")
        return False

def validate_application_startup():
    """Valida inicialização da aplicação"""
    print("🔍 Validando inicialização da aplicação...")
    
    try:
        # Testar import da aplicação
        sys.path.append('/app/backend')
        from backend.app import create_app
        
        app = create_app()
        
        with app.test_client() as client:
            # Testar endpoint de saúde
            response = client.get('/api/health')
            if response.status_code == 200:
                print("✅ Aplicação inicializa corretamente")
                return True
            else:
                print(f"❌ Endpoint de saúde falhou: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Erro na inicialização: {e}")
        return False

def main():
    """Executa todas as validações"""
    print("🚀 Iniciando validação pré-deploy...")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 50)
    
    validations = [
        ("Ambiente", validate_environment),
        ("GLPI", validate_glpi_connectivity),
        ("Serviços Legacy", validate_legacy_services),
        ("Aplicação", validate_application_startup)
    ]
    
    results = []
    for name, validation_func in validations:
        try:
            result = validation_func()
            results.append((name, result))
            print()
        except Exception as e:
            print(f"❌ Erro crítico em {name}: {e}")
            results.append((name, False))
            print()
    
    print("=" * 50)
    print("📊 RESUMO DA VALIDAÇÃO:")
    
    all_passed = True
    for name, passed in results:
        status = "✅ PASSOU" if passed else "❌ FALHOU"
        print(f"  {name}: {status}")
        if not passed:
            all_passed = False
    
    print("=" * 50)
    
    if all_passed:
        print("🎉 TODAS AS VALIDAÇÕES PASSARAM - DEPLOY AUTORIZADO")
        sys.exit(0)
    else:
        print("🚨 VALIDAÇÕES FALHARAM - DEPLOY BLOQUEADO")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

3. Script de deploy: `scripts/deploy_production.sh`

```bash
#!/bin/bash

# ===========================================
# SCRIPT DE DEPLOY - MIGRAÇÃO LEGACY
# ===========================================

set -e  # Parar em caso de erro

echo "🚀 Iniciando deploy da migração legacy..."
echo "Timestamp: $(date -Iseconds)"
echo "========================================="

# Validar pré-requisitos
echo "🔍 Executando validações pré-deploy..."
python3 scripts/validate_production.py

if [ $? -ne 0 ]; then
    echo "❌ Validações falharam. Deploy cancelado."
    exit 1
fi

# Backup da configuração atual
echo "💾 Criando backup da configuração..."
cp .env .env.backup.$(date +%Y%m%d_%H%M%S)

# Aplicar nova configuração
echo "⚙️ Aplicando configuração de produção..."
cp backend/config/production.env .env

# Instalar dependências
echo "📦 Instalando dependências..."
pip install -r requirements.txt

# Executar testes críticos
echo "🧪 Executando testes críticos..."
pytest backend/tests/test_legacy_service_adapter.py -v

if [ $? -ne 0 ]; then
    echo "❌ Testes falharam. Restaurando backup..."
    cp .env.backup.* .env
    exit 1
fi

# Reiniciar serviços
echo "🔄 Reiniciando aplicação..."
sudo systemctl restart glpi-dashboard
sudo systemctl restart nginx

# Aguardar inicialização
echo "⏳ Aguardando inicialização..."
sleep 10

# Validar deploy
echo "✅ Validando deploy..."
for i in {1..5}; do
    if curl -f -s http://localhost:5000/api/health > /dev/null; then
        echo "✅ Aplicação respondendo"
        break
    else
        echo "⏳ Tentativa $i/5 - aguardando..."
        sleep 5
    fi
done

# Testar endpoints críticos
echo "🔍 Testando endpoints críticos..."

# Testar métricas
if curl -f -s http://localhost:5000/api/metrics/v2 > /dev/null; then
    echo "✅ Endpoint de métricas OK"
else
    echo "❌ Endpoint de métricas falhou"
    exit 1
fi

# Testar monitoramento
if curl -f -s http://localhost:5000/api/monitoring/legacy/health > /dev/null; then
    echo "✅ Monitoramento legacy OK"
else
    echo "❌ Monitoramento legacy falhou"
    exit 1
fi

echo "========================================="
echo "🎉 DEPLOY CONCLUÍDO COM SUCESSO!"
echo "📊 Status: Serviços legacy ativos"
echo "🔗 Monitoramento: http://localhost:5000/api/monitoring/legacy/health"
echo "📈 Métricas: http://localhost:5000/api/monitoring/legacy/metrics"
echo "========================================="
```

4. Torne o script executável:
```bash
chmod +x scripts/deploy_production.sh
chmod +x scripts/validate_production.py
```

Execute o deploy com validação completa e rollback automático em caso de falha.
```

## 📊 FASE 5: MONITORAMENTO E TROUBLESHOOTING

### 5.1 Configuração de Monitoramento

**Prompt:** "Configure um sistema de monitoramento completo para acompanhar a migração dos serviços legacy, incluindo métricas de performance, logs estruturados e alertas automáticos."

**Implementação:**

1. Criar dashboard de monitoramento: `backend/monitoring/legacy_dashboard.py`

```python
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

# Instância global do serviço
monitoring_service = LegacyMonitoringService()

@monitoring_bp.route('/legacy/health')
def legacy_health():
    """Endpoint de saúde dos serviços legacy"""
    health_data = monitoring_service.get_system_health()
    status_code = 200 if health_data.get('overall_status') in ['healthy', 'degraded'] else 500
    return jsonify(health_data), status_code

@monitoring_bp.route('/legacy/metrics')
def legacy_metrics():
    """Endpoint de métricas de performance"""
    metrics_data = monitoring_service.get_performance_metrics()
    return jsonify(metrics_data)

@monitoring_bp.route('/legacy/history')
def legacy_history():
    """Endpoint de histórico de métricas"""
    return jsonify({
        'timestamp': datetime.now().isoformat(),
        'history': monitoring_service.metrics_history[-50:],  # Últimas 50 medições
        'total_measurements': len(monitoring_service.metrics_history)
    })

@monitoring_bp.route('/legacy/dashboard')
def legacy_dashboard():
    """Dashboard visual de monitoramento"""
    return render_template('monitoring/legacy_dashboard.html')
```

2. Template do dashboard: `backend/templates/monitoring/legacy_dashboard.html`

```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard de Monitoramento Legacy</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: #2c3e50; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .metric-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .metric-title { font-size: 18px; font-weight: bold; margin-bottom: 10px; }
        .metric-value { font-size: 24px; font-weight: bold; }
        .status-healthy { color: #27ae60; }
        .status-degraded { color: #f39c12; }
        .status-error { color: #e74c3c; }
        .chart-container { height: 300px; margin-top: 20px; }
        .refresh-btn { background: #3498db; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; }
        .refresh-btn:hover { background: #2980b9; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 Dashboard de Monitoramento Legacy</h1>
            <p>Monitoramento em tempo real dos serviços migrados</p>
            <button class="refresh-btn" onclick="refreshData()">🔄 Atualizar</button>
        </div>
        
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-title">Status Geral</div>
                <div id="overall-status" class="metric-value">Carregando...</div>
                <div id="uptime">Uptime: --</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-title">GLPI Connectivity</div>
                <div id="glpi-status" class="metric-value">Carregando...</div>
                <div id="glpi-response-time">Tempo de resposta: --</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-title">Legacy Services</div>
                <div id="legacy-status" class="metric-value">Carregando...</div>
                <div id="legacy-response-time">Tempo de resposta: --</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-title">Sistema</div>
                <div id="cpu-usage" class="metric-value">CPU: --%</div>
                <div id="memory-usage">Memória: --%</div>
                <div id="disk-usage">Disco: --%</div>
            </div>
        </div>
        
        <div class="metric-card">
            <div class="metric-title">Performance das Operações</div>
            <div class="chart-container">
                <canvas id="performance-chart"></canvas>
            </div>
        </div>
        
        <div class="metric-card">
            <div class="metric-title">Histórico de Saúde</div>
            <div class="chart-container">
                <canvas id="health-chart"></canvas>
            </div>
        </div>
    </div>

    <script>
        let performanceChart, healthChart;
        
        async function refreshData() {
            try {
                // Buscar dados de saúde
                const healthResponse = await fetch('/api/monitoring/legacy/health');
                const healthData = await healthResponse.json();
                
                // Buscar métricas de performance
                const metricsResponse = await fetch('/api/monitoring/legacy/metrics');
                const metricsData = await metricsResponse.json();
                
                // Buscar histórico
                const historyResponse = await fetch('/api/monitoring/legacy/history');
                const historyData = await historyResponse.json();
                
                updateHealthDisplay(healthData);
                updatePerformanceChart(metricsData);
                updateHealthChart(historyData.history);
                
            } catch (error) {
                console.error('Erro ao atualizar dados:', error);
            }
        }
        
        function updateHealthDisplay(data) {
            // Status geral
            const overallStatus = document.getElementById('overall-status');
            overallStatus.textContent = data.overall_status?.toUpperCase() || 'ERRO';
            overallStatus.className = `metric-value status-${data.overall_status || 'error'}`;
            
            // Uptime
            const uptimeHours = Math.floor(data.uptime_seconds / 3600);
            const uptimeMinutes = Math.floor((data.uptime_seconds % 3600) / 60);
            document.getElementById('uptime').textContent = `Uptime: ${uptimeHours}h ${uptimeMinutes}m`;
            
            // GLPI
            const glpiStatus = document.getElementById('glpi-status');
            glpiStatus.textContent = data.services?.glpi?.status?.toUpperCase() || 'ERRO';
            glpiStatus.className = `metric-value status-${data.services?.glpi?.status || 'error'}`;
            document.getElementById('glpi-response-time').textContent = 
                `Tempo: ${data.services?.glpi?.response_time_ms || '--'}ms`;
            
            // Legacy Services
            const legacyStatus = document.getElementById('legacy-status');
            legacyStatus.textContent = data.services?.legacy_adapter?.status?.toUpperCase() || 'ERRO';
            legacyStatus.className = `metric-value status-${data.services?.legacy_adapter?.status || 'error'}`;
            document.getElementById('legacy-response-time').textContent = 
                `Tempo: ${data.services?.legacy_adapter?.response_time_ms || '--'}ms`;
            
            // Sistema
            document.getElementById('cpu-usage').textContent = `CPU: ${data.system?.cpu_percent || '--'}%`;
            document.getElementById('memory-usage').textContent = `Memória: ${data.system?.memory_percent || '--'}%`;
            document.getElementById('disk-usage').textContent = `Disco: ${data.system?.disk_percent || '--'}%`;
        }
        
        function updatePerformanceChart(data) {
            const ctx = document.getElementById('performance-chart').getContext('2d');
            
            if (performanceChart) {
                performanceChart.destroy();
            }
            
            const operations = data.operations || {};
            const labels = Object.keys(operations);
            const responseTimes = labels.map(op => operations[op].response_time_ms || 0);
            const successRates = labels.map(op => operations[op].success ? 100 : 0);
            
            performanceChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Tempo de Resposta (ms)',
                        data: responseTimes,
                        backgroundColor: 'rgba(52, 152, 219, 0.8)',
                        yAxisID: 'y'
                    }, {
                        label: 'Taxa de Sucesso (%)',
                        data: successRates,
                        backgroundColor: 'rgba(46, 204, 113, 0.8)',
                        yAxisID: 'y1'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            type: 'linear',
                            display: true,
                            position: 'left',
                            title: { display: true, text: 'Tempo (ms)' }
                        },
                        y1: {
                            type: 'linear',
                            display: true,
                            position: 'right',
                            title: { display: true, text: 'Sucesso (%)' },
                            grid: { drawOnChartArea: false },
                            max: 100
                        }
                    }
                }
            });
        }
        
        function updateHealthChart(history) {
            const ctx = document.getElementById('health-chart').getContext('2d');
            
            if (healthChart) {
                healthChart.destroy();
            }
            
            const last20 = history.slice(-20);
            const labels = last20.map(h => new Date(h.timestamp).toLocaleTimeString());
            const cpuData = last20.map(h => h.system?.cpu_percent || 0);
            const memoryData = last20.map(h => h.system?.memory_percent || 0);
            
            healthChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'CPU (%)',
                        data: cpuData,
                        borderColor: 'rgba(231, 76, 60, 1)',
                        backgroundColor: 'rgba(231, 76, 60, 0.1)',
                        tension: 0.4
                    }, {
                        label: 'Memória (%)',
                        data: memoryData,
                        borderColor: 'rgba(155, 89, 182, 1)',
                        backgroundColor: 'rgba(155, 89, 182, 0.1)',
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 100,
                            title: { display: true, text: 'Percentual (%)' }
                        }
                    }
                }
            });
        }
        
        // Atualizar dados a cada 30 segundos
        setInterval(refreshData, 30000);
        
        // Carregar dados iniciais
        refreshData();
    </script>
</body>
</html>
```

### 5.2 Sistema de Alertas

**Prompt:** "Implemente um sistema de alertas automáticos que notifique sobre problemas nos serviços legacy, incluindo alertas por email, Slack e logs estruturados."

**Implementação:**

1. Sistema de alertas: `backend/monitoring/alert_system.py`

```python
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
```

### 5.3 Troubleshooting Guide

**Prompt:** "Crie um guia completo de troubleshooting para problemas comuns na migração dos serviços legacy, incluindo diagnósticos automáticos e soluções passo a passo."

**Implementação:**

1. Sistema de diagnóstico: `backend/monitoring/diagnostic_system.py`

```python
# ===========================================
# SISTEMA DE DIAGNÓSTICO LEGACY
# ===========================================

import subprocess
import psutil
import requests
import socket
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import logging
from backend.config.settings import Config
from backend.core.infrastructure.adapters.legacy_service_adapter import LegacyServiceAdapter
from backend.services.legacy.glpi_service_facade import GLPIServiceFacade

@dataclass
class DiagnosticResult:
    test_name: str
    status: str  # 'pass', 'fail', 'warning'
    message: str
    details: Dict = None
    solution: str = None

class DiagnosticSystem:
    def __init__(self):
        self.config = Config()
        self.logger = logging.getLogger(__name__)
        self.adapter = LegacyServiceAdapter()
        self.glpi_facade = GLPIServiceFacade()
    
    def run_full_diagnostic(self) -> Dict:
        """Executa diagnóstico completo do sistema"""
        self.logger.info("Iniciando diagnóstico completo")
        
        diagnostic_tests = [
            ("Conectividade de Rede", self._test_network_connectivity),
            ("Configuração de Ambiente", self._test_environment_config),
            ("Conectividade GLPI", self._test_glpi_connectivity),
            ("Serviços Legacy", self._test_legacy_services),
            ("Performance do Sistema", self._test_system_performance),
            ("Dependências Python", self._test_python_dependencies),
            ("Logs e Arquivos", self._test_logs_and_files),
            ("Cache e Memória", self._test_cache_and_memory)
        ]
        
        results = []
        overall_status = "pass"
        
        for test_name, test_func in diagnostic_tests:
            try:
                result = test_func()
                results.append(result)
                
                if result.status == "fail":
                    overall_status = "fail"
                elif result.status == "warning" and overall_status == "pass":
                    overall_status = "warning"
                    
            except Exception as e:
                results.append(DiagnosticResult(
                    test_name=test_name,
                    status="fail",
                    message=f"Erro ao executar teste: {str(e)}",
                    solution="Verifique os logs do sistema para mais detalhes"
                ))
                overall_status = "fail"
        
        return {
            "timestamp": datetime.now().isoformat(),
            "overall_status": overall_status,
            "total_tests": len(diagnostic_tests),
            "passed_tests": len([r for r in results if r.status == "pass"]),
            "failed_tests": len([r for r in results if r.status == "fail"]),
            "warning_tests": len([r for r in results if r.status == "warning"]),
            "results": [self._result_to_dict(r) for r in results]
        }
    
    def _test_network_connectivity(self) -> DiagnosticResult:
        """Testa conectividade de rede"""
        try:
            # Testar conectividade com GLPI
            glpi_url = self.config.GLPI_URL
            if not glpi_url:
                return DiagnosticResult(
                    test_name="Conectividade de Rede",
                    status="fail",
                    message="URL do GLPI não configurada",
                    solution="Configure GLPI_URL no arquivo .env"
                )
            
            # Extrair host da URL
            from urllib.parse import urlparse
            parsed_url = urlparse(glpi_url)
            host = parsed_url.hostname
            port = parsed_url.port or (443 if parsed_url.scheme == 'https' else 80)
            
            # Testar conexão TCP
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                return DiagnosticResult(
                    test_name="Conectividade de Rede",
                    status="pass",
                    message=f"Conectividade com {host}:{port} OK",
                    details={"host": host, "port": port}
                )
            else:
                return DiagnosticResult(
                    test_name="Conectividade de Rede",
                    status="fail",
                    message=f"Não foi possível conectar com {host}:{port}",
                    details={"host": host, "port": port, "error_code": result},
                    solution="Verifique firewall, proxy ou conectividade de rede"
                )
                
        except Exception as e:
            return DiagnosticResult(
                test_name="Conectividade de Rede",
                status="fail",
                message=f"Erro no teste de rede: {str(e)}",
                solution="Verifique configuração de rede e URL do GLPI"
            )
    
    def _test_environment_config(self) -> DiagnosticResult:
        """Testa configuração do ambiente"""
        required_vars = [
            'GLPI_URL', 'GLPI_USER_TOKEN', 'GLPI_APP_TOKEN'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not getattr(self.config, var, None):
                missing_vars.append(var)
        
        if missing_vars:
            return DiagnosticResult(
                test_name="Configuração de Ambiente",
                status="fail",
                message=f"Variáveis de ambiente faltando: {', '.join(missing_vars)}",
                details={"missing_variables": missing_vars},
                solution="Configure as variáveis faltando no arquivo .env"
            )
        
        # Verificar se USE_MOCK_DATA está configurado corretamente
        use_mock = getattr(self.config, 'USE_MOCK_DATA', True)
        if use_mock:
            return DiagnosticResult(
                test_name="Configuração de Ambiente",
                status="warning",
                message="Sistema configurado para usar dados mock",
                details={"use_mock_data": use_mock},
                solution="Para usar dados reais, configure USE_MOCK_DATA=false no .env"
            )
        
        return DiagnosticResult(
            test_name="Configuração de Ambiente",
            status="pass",
            message="Configuração de ambiente OK",
            details={"use_mock_data": use_mock}
        )
    
    def _test_glpi_connectivity(self) -> DiagnosticResult:
        """Testa conectividade com GLPI"""
        try:
            # Testar autenticação
            auth_result = self.glpi_facade.authenticate()
            
            if auth_result:
                return DiagnosticResult(
                    test_name="Conectividade GLPI",
                    status="pass",
                    message="Autenticação com GLPI bem-sucedida",
                    details={"session_token": "***" if auth_result else None}
                )
            else:
                return DiagnosticResult(
                    test_name="Conectividade GLPI",
                    status="fail",
                    message="Falha na autenticação com GLPI",
                    solution="Verifique GLPI_USER_TOKEN e GLPI_APP_TOKEN no .env"
                )
                
        except Exception as e:
            return DiagnosticResult(
                test_name="Conectividade GLPI",
                status="fail",
                message=f"Erro na conectividade GLPI: {str(e)}",
                solution="Verifique URL, tokens e conectividade de rede"
            )
    
    def _test_legacy_services(self) -> DiagnosticResult:
        """Testa serviços legacy"""
        try:
            # Testar método principal do adapter
            metrics = self.adapter.get_dashboard_metrics('diagnostic_test')
            
            if metrics and hasattr(metrics, 'total_tickets'):
                return DiagnosticResult(
                    test_name="Serviços Legacy",
                    status="pass",
                    message="Serviços legacy funcionando corretamente",
                    details={
                        "total_tickets": getattr(metrics, 'total_tickets', None),
                        "has_data": True
                    }
                )
            else:
                return DiagnosticResult(
                    test_name="Serviços Legacy",
                    status="fail",
                    message="Serviços legacy não retornaram dados válidos",
                    solution="Verifique implementação do LegacyServiceAdapter"
                )
                
        except Exception as e:
            return DiagnosticResult(
                test_name="Serviços Legacy",
                status="fail",
                message=f"Erro nos serviços legacy: {str(e)}",
                solution="Verifique logs e implementação dos serviços legacy"
            )
    
    def _test_system_performance(self) -> DiagnosticResult:
        """Testa performance do sistema"""
        try:
            # Métricas do sistema
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            issues = []
            if cpu_percent > 80:
                issues.append(f"CPU alta: {cpu_percent}%")
            if memory.percent > 85:
                issues.append(f"Memória alta: {memory.percent}%")
            if disk.percent > 90:
                issues.append(f"Disco cheio: {disk.percent}%")
            
            if issues:
                return DiagnosticResult(
                    test_name="Performance do Sistema",
                    status="warning",
                    message=f"Problemas de performance: {', '.join(issues)}",
                    details={
                        "cpu_percent": cpu_percent,
                        "memory_percent": memory.percent,
                        "disk_percent": disk.percent
                    },
                    solution="Monitore recursos e considere otimizações"
                )
            
            return DiagnosticResult(
                test_name="Performance do Sistema",
                status="pass",
                message="Performance do sistema OK",
                details={
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "disk_percent": disk.percent
                }
            )
            
        except Exception as e:
            return DiagnosticResult(
                test_name="Performance do Sistema",
                status="fail",
                message=f"Erro ao verificar performance: {str(e)}",
                solution="Verifique se psutil está instalado corretamente"
            )
    
    def _test_python_dependencies(self) -> DiagnosticResult:
        """Testa dependências Python"""
        try:
            required_packages = [
                'flask', 'requests', 'psutil', 'pydantic'
            ]
            
            missing_packages = []
            for package in required_packages:
                try:
                    __import__(package)
                except ImportError:
                    missing_packages.append(package)
            
            if missing_packages:
                return DiagnosticResult(
                    test_name="Dependências Python",
                    status="fail",
                    message=f"Pacotes faltando: {', '.join(missing_packages)}",
                    details={"missing_packages": missing_packages},
                    solution="Execute: pip install -r requirements.txt"
                )
            
            return DiagnosticResult(
                test_name="Dependências Python",
                status="pass",
                message="Todas as dependências estão instaladas"
            )
            
        except Exception as e:
            return DiagnosticResult(
                test_name="Dependências Python",
                status="fail",
                message=f"Erro ao verificar dependências: {str(e)}",
                solution="Verifique instalação do Python e pip"
            )
    
    def _test_logs_and_files(self) -> DiagnosticResult:
        """Testa logs e arquivos do sistema"""
        try:
            import os
            
            # Verificar diretório de logs
            log_path = getattr(self.config, 'LOG_FILE_PATH', 'logs/app.log')
            log_dir = os.path.dirname(log_path)
            
            if not os.path.exists(log_dir):
                return DiagnosticResult(
                    test_name="Logs e Arquivos",
                    status="warning",
                    message=f"Diretório de logs não existe: {log_dir}",
                    solution=f"Crie o diretório: mkdir -p {log_dir}"
                )
            
            # Verificar permissões de escrita
            if not os.access(log_dir, os.W_OK):
                return DiagnosticResult(
                    test_name="Logs e Arquivos",
                    status="fail",
                    message=f"Sem permissão de escrita em: {log_dir}",
                    solution=f"Ajuste permissões: chmod 755 {log_dir}"
                )
            
            return DiagnosticResult(
                test_name="Logs e Arquivos",
                status="pass",
                message="Sistema de logs configurado corretamente",
                details={"log_directory": log_dir}
            )
            
        except Exception as e:
            return DiagnosticResult(
                test_name="Logs e Arquivos",
                status="fail",
                message=f"Erro ao verificar logs: {str(e)}",
                solution="Verifique configuração de logs no sistema"
            )
    
    def _test_cache_and_memory(self) -> DiagnosticResult:
        """Testa cache e uso de memória"""
        try:
            # Testar cache (se configurado)
            cache_issues = []
            
            # Verificar uso de memória da aplicação
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            
            if memory_mb > 500:  # Mais de 500MB
                cache_issues.append(f"Alto uso de memória: {memory_mb:.1f}MB")
            
            if cache_issues:
                return DiagnosticResult(
                    test_name="Cache e Memória",
                    status="warning",
                    message=f"Problemas detectados: {', '.join(cache_issues)}",
                    details={"memory_mb": memory_mb},
                    solution="Monitore uso de memória e considere otimizações"
                )
            
            return DiagnosticResult(
                test_name="Cache e Memória",
                status="pass",
                message="Cache e memória OK",
                details={"memory_mb": memory_mb}
            )
            
        except Exception as e:
            return DiagnosticResult(
                test_name="Cache e Memória",
                status="fail",
                message=f"Erro ao verificar cache: {str(e)}",
                solution="Verifique configuração de cache"
            )
    
    def _result_to_dict(self, result: DiagnosticResult) -> Dict:
        """Converte resultado para dicionário"""
        return {
            "test_name": result.test_name,
            "status": result.status,
            "message": result.message,
            "details": result.details,
            "solution": result.solution
        }
    
    def get_troubleshooting_guide(self) -> Dict:
        """Retorna guia de troubleshooting"""
        return {
            "common_issues": [
                {
                    "problem": "Erro de autenticação GLPI",
                    "symptoms": ["401 Unauthorized", "Invalid token", "Authentication failed"],
                    "solutions": [
                        "Verifique GLPI_USER_TOKEN no .env",
                        "Verifique GLPI_APP_TOKEN no .env",
                        "Confirme que os tokens estão válidos no GLPI",
                        "Teste conectividade: curl -H 'App-Token: TOKEN' URL/apirest.php"
                    ]
                },
                {
                    "problem": "Serviços legacy não respondem",
                    "symptoms": ["Timeout", "Connection refused", "Service unavailable"],
                    "solutions": [
                        "Verifique se o GLPI está rodando",
                        "Teste conectividade de rede",
                        "Verifique logs do GLPI",
                        "Reinicie os serviços: systemctl restart apache2"
                    ]
                },
                {
                    "problem": "Performance degradada",
                    "symptoms": ["Lentidão", "Timeouts", "Alto uso de CPU/memória"],
                    "solutions": [
                        "Monitore recursos do sistema",
                        "Otimize queries do banco de dados",
                        "Implemente cache mais agressivo",
                        "Considere scaling horizontal"
                    ]
                },
                {
                    "problem": "Dados inconsistentes",
                    "symptoms": ["Dados vazios", "Valores incorretos", "Estrutura inválida"],
                    "solutions": [
                        "Verifique mapeamento de dados no adapter",
                        "Valide estrutura de resposta da API GLPI",
                        "Teste com dados mock primeiro",
                        "Verifique logs de transformação de dados"
                    ]
                }
            ],
            "diagnostic_commands": [
                {
                    "description": "Testar conectividade GLPI",
                    "command": "curl -H 'App-Token: $GLPI_APP_TOKEN' -H 'Authorization: user_token $GLPI_USER_TOKEN' $GLPI_URL/apirest.php/initSession"
                },
                {
                    "description": "Verificar logs da aplicação",
                    "command": "tail -f logs/app.log | grep ERROR"
                },
                {
                    "description": "Monitorar recursos do sistema",
                    "command": "htop"
                },
                {
                    "description": "Testar endpoint de saúde",
                    "command": "curl http://localhost:5000/api/monitoring/legacy/health"
                }
            ],
            "emergency_procedures": [
                {
                    "scenario": "Sistema completamente indisponível",
                    "steps": [
                        "1. Ativar modo mock: USE_MOCK_DATA=true",
                        "2. Reiniciar aplicação",
                        "3. Verificar logs de erro",
                        "4. Testar conectividade GLPI",
                        "5. Restaurar backup se necessário"
                    ]
                },
                {
                    "scenario": "Performance crítica",
                    "steps": [
                        "1. Ativar cache agressivo",
                        "2. Reduzir frequência de polling",
                        "3. Implementar rate limiting",
                        "4. Monitorar recursos continuamente",
                        "5. Considerar scaling"
                    ]
                }
            ]
        }

# Instância global
diagnostic_system = DiagnosticSystem()
```

## 🎯 CONCLUSÃO

Este documento fornece todos os prompts necessários para uma implementação perfeita da migração dos serviços legacy para a Clean Architecture. Cada fase foi cuidadosamente planejada para garantir:

### ✅ Benefícios Esperados:
- **Dados Reais**: Substituição completa dos dados mock por dados reais do GLPI
- **Performance**: Otimização significativa com cache inteligente e queries eficientes
- **Monitoramento**: Sistema completo de observabilidade e alertas
- **Manutenibilidade**: Código limpo seguindo princípios SOLID
- **Confiabilidade**: Testes automatizados e validação contínua

### 🚀 Próximos Passos:
1. Execute cada fase sequencialmente
2. Valide cada implementação antes de prosseguir
3. Monitore métricas de performance continuamente
4. Mantenha logs estruturados para troubleshooting
5. Documente qualquer customização específica do ambiente

**Com estes prompts, você terá dados reais funcionando em produção com total confiabilidade e observabilidade!** 🎉