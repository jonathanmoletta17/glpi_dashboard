# Relatório de Análise Detalhada - Serviços Legacy GLPI

## 📋 Resumo Executivo

Este relatório apresenta uma análise completa da estrutura dos serviços legacy em `backend/services/legacy/`, incluindo mapeamento de métodos, dependências, compatibilidade com contratos e recomendações de adaptação.

## 🗂️ 1. Lista Completa de Métodos Mapeados

### GLPIServiceFacade - Métodos Públicos (Total: 19 métodos)

#### 🔐 Autenticação (3 métodos)
| Método | Assinatura | Retorno | Descrição |
|--------|------------|---------|----------|
| `authenticate()` | `() -> bool` | `bool` | Autentica no GLPI com retry |
| `get_api_headers()` | `() -> Optional[Dict[str, str]]` | `Optional[Dict[str, str]]` | Retorna headers de autenticação |
| `is_authenticated()` | `() -> bool` | `bool` | Verifica se está autenticado |

#### 🔍 Descoberta de Fields (4 métodos)
| Método | Assinatura | Retorno | Descrição |
|--------|------------|---------|----------|
| `discover_field_ids()` | `() -> bool` | `bool` | Descobre IDs dos campos GLPI |
| `get_field_id(field_name)` | `(field_name: str) -> Optional[str]` | `Optional[str]` | Obtém ID de um campo específico |
| `refresh_field_mappings()` | `() -> bool` | `bool` | Atualiza mapeamentos de campos |
| `invalidate_field_cache()` | `() -> None` | `None` | Invalida cache de campos |

#### 💾 Cache (2 métodos)
| Método | Assinatura | Retorno | Descrição |
|--------|------------|---------|----------|
| `get_cache_stats()` | `() -> Dict[str, Any]` | `Dict[str, Any]` | Estatísticas do cache |
| `invalidate_cache(cache_type)` | `(cache_type: str = None) -> None` | `None` | Invalida cache específico |

#### 📊 Métricas (4 métodos)
| Método | Assinatura | Retorno | Descrição |
|--------|------------|---------|----------|
| `get_ticket_count_by_hierarchy()` | `(start_date: str = None, end_date: str = None, level: str = None, status: str = None, use_cache: bool = True) -> Dict[str, Any]` | `Dict[str, Any]` | Contagem por hierarquia |
| `get_ticket_count()` | `(start_date: str = None, end_date: str = None, status: str = None, group_id: int = None, use_cache: bool = True) -> Dict[str, Any]` | `Dict[str, Any]` | Contagem geral de tickets |
| `get_metrics_by_level()` | `(start_date: str = None, end_date: str = None) -> Dict[str, Any]` | `Dict[str, Any]` | Métricas agregadas por nível |
| `get_technician_name(tech_id)` | `(tech_id: str) -> str` | `str` | Nome do técnico por ID |

#### 📈 Dashboard (3 métodos)
| Método | Assinatura | Retorno | Descrição |
|--------|------------|---------|----------|
| `get_dashboard_metrics()` | `(start_date: str = None, end_date: str = None) -> Dict[str, Any]` | `Dict[str, Any]` | Métricas do dashboard |
| `get_dashboard_metrics_with_filters()` | `(start_date: str = None, end_date: str = None, include_trends: bool = False) -> Dict[str, Any]` | `Dict[str, Any]` | Dashboard com filtros |
| `get_general_metrics()` | `(start_date: str = None, end_date: str = None) -> Dict[str, Any]` | `Dict[str, Any]` | Métricas gerais |

#### 📉 Tendências (2 métodos)
| Método | Assinatura | Retorno | Descrição |
|--------|------------|---------|----------|
| `calculate_trends()` | `(current_start: str, current_end: str, comparison_days: int = 30) -> Dict[str, Any]` | `Dict[str, Any]` | Calcula tendências |
| `get_historical_data()` | `(start_date: str, end_date: str, interval_days: int = 7) -> Dict[str, Any]` | `Dict[str, Any]` | Dados históricos |

#### 🔧 Utilitários (1 método + 2 propriedades)
| Método/Propriedade | Assinatura | Retorno | Descrição |
|-------------------|------------|---------|----------|
| `health_check()` | `() -> Dict[str, Any]` | `Dict[str, Any]` | Status de saúde do sistema |
| `glpi_url` | `@property` | `str` | URL do GLPI |
| `session_token` | `@property` | `Optional[str]` | Token da sessão |

## 🔗 2. Matriz de Dependências

### Dependências Diretas

| Serviço | Depende De | Tipo de Dependência |
|---------|------------|--------------------|
| **GLPIServiceFacade** | Todos os serviços | Composição |
| **GLPIHttpClientService** | GLPIAuthenticationService | Injeção ⚠️ |
| **GLPIFieldDiscoveryService** | GLPIHttpClientService, GLPICacheService | Injeção |
| **GLPIMetricsService** | GLPIHttpClientService, GLPICacheService, GLPIFieldDiscoveryService | Injeção |
| **GLPIDashboardService** | GLPIHttpClientService, GLPICacheService, GLPIMetricsService | Injeção |
| **GLPITrendsService** | GLPIHttpClientService, GLPICacheService, GLPIMetricsService | Injeção |

### Dependências Externas

| Serviço | Bibliotecas/Módulos Externos |
|---------|-----------------------------|
| **GLPIAuthenticationService** | `requests`, `config.settings`, `utils.structured_logger` |
| **GLPICacheService** | `time`, `typing` |
| **GLPIHttpClientService** | `requests`, `utils.prometheus_metrics`, `utils.structured_logging` |
| **GLPITrendsService** | `DateValidator` |

### ⚠️ Pontos Críticos de Dependência

1. **Dependência Circular**: HttpClient ↔ Authentication
2. **Cache Compartilhado**: Todos os serviços usam a mesma instância
3. **Estado Global**: Session token compartilhado

## ✅❌ 3. Compatibilidade com UnifiedGLPIServiceContract

### Métodos Compatíveis (5/12 - 42%)

| Contrato | Implementação Legacy | Status |
|----------|---------------------|--------|
| `get_dashboard_metrics()` | ✅ `get_dashboard_metrics()` | **COMPATÍVEL** |
| `get_dashboard_metrics_with_date_filter()` | ✅ `get_dashboard_metrics(start_date, end_date)` | **COMPATÍVEL** |
| `authenticate_with_retry()` | ✅ `authenticate()` | **COMPATÍVEL** |
| `get_system_status()` | ✅ `health_check()` | **COMPATÍVEL** |
| `get_technician_ranking()` | ⚠️ `get_technician_name()` (parcial) | **PARCIAL** |

### Métodos Ausentes (7/12 - 58%)

| Contrato | Status | Impacto |
|----------|--------|--------|
| `get_dashboard_metrics_with_modification_date_filter()` | ❌ **AUSENTE** | Alto |
| `get_dashboard_metrics_with_filters()` | ❌ **AUSENTE** | Alto |
| `get_all_technician_ids_and_names()` | ❌ **AUSENTE** | Médio |
| `get_technician_ranking_with_filters()` | ❌ **AUSENTE** | Médio |
| `get_new_tickets()` | ❌ **AUSENTE** | Alto |
| `get_new_tickets_with_filters()` | ❌ **AUSENTE** | Alto |

### Incompatibilidades de Assinatura

| Aspecto | Contrato Esperado | Legacy Atual | Impacto |
|---------|------------------|--------------|--------|
| **Correlation ID** | `correlation_id: Optional[str]` | Não suportado | Médio |
| **Entity ID** | `entity_id: Optional[int]` | Não suportado | Alto |
| **Tipos de Retorno** | `DashboardMetrics`, `TechnicianRanking`, `NewTicket` | `Dict[str, Any]` | Alto |
| **Estruturas Pydantic** | Schemas tipados | Dicionários genéricos | Alto |

## 🎯 4. Análise Focada

### 🎫 Dados de Tickets, Usuários e Computadores

#### Tickets
- **Implementado**: Contagem, métricas por hierarquia, status breakdown
- **Ausente**: Listagem de tickets novos, filtros avançados
- **Cache**: TTL de 180s para métricas de dashboard

#### Usuários/Técnicos
- **Implementado**: Obtenção de nome por ID, ranking básico
- **Ausente**: Listagem completa, ranking com filtros
- **Cache**: TTL de 300s para ranking

#### Computadores
- **Status**: Não implementado nos serviços legacy

### 💾 Sistema de Cache

#### Configurações Atuais
| Cache Key | TTL | Uso |
|-----------|-----|-----|
| `technician_ranking` | 300s | Ranking de técnicos |
| `field_ids` | 1800s/600s | IDs de campos (discovered/fallback) |
| `dashboard_metrics` | 180s | Métricas do dashboard |
| `trends_data` | 300s | Dados de tendências |

#### Pontos de Atenção
- Cache em memória (não persistente)
- Sem invalidação automática por mudanças
- Possível contenção em operações concorrentes

### 🔐 Sistema de Autenticação

#### Funcionalidades
- ✅ Autenticação automática com retry (3 tentativas)
- ✅ Validação de expiração de token
- ✅ Headers de API automáticos
- ✅ Logout controlado

#### Configurações
- **Retry delay**: Base de 2s com backoff
- **Token management**: Automático com verificação de expiração
- **Session persistence**: Em memória apenas

### 🚨 Tratamento de Erros e Logging

#### Estratégias Implementadas
- **HTTP Retry**: 3 tentativas com backoff exponencial
- **Authentication Retry**: Reautenticação automática em caso de token expirado
- **Structured Logging**: Via `utils.structured_logger`
- **Metrics**: Prometheus metrics via `utils.prometheus_metrics`

#### Pontos de Melhoria
- Falta de circuit breaker
- Logs não estruturados em alguns serviços
- Ausência de correlation IDs

### 🔍 Descoberta Automática de Field IDs

#### Funcionalidades
- ✅ Descoberta automática via API GLPI
- ✅ Cache com TTL diferenciado (discovered vs fallback)
- ✅ Fallback para IDs conhecidos
- ✅ Refresh manual de mapeamentos

#### Field Mappings Suportados
```python
FIELD_MAPPINGS = {
    'status': ['12'],
    'priority': ['3'], 
    'category': ['7'],
    'technician': ['5', '8'],
    'entity': ['80'],
    'group': ['8'],
    'date_creation': ['15'],
    'date_mod': ['19']
}
```

## 🔧 5. Recomendações de Adaptação

### 🚀 Prioridade Alta

#### 1. Implementar Métodos Ausentes
```python
# Métodos críticos para compatibilidade
def get_new_tickets(limit: int = 20) -> List[NewTicket]
def get_new_tickets_with_filters(...) -> List[NewTicket]
def get_dashboard_metrics_with_filters(...) -> DashboardMetrics
def get_all_technician_ids_and_names(...) -> Tuple[List[int], List[str]]
```

#### 2. Adaptar Tipos de Retorno
- Migrar de `Dict[str, Any]` para schemas Pydantic
- Implementar `DashboardMetrics`, `TechnicianRanking`, `NewTicket`
- Adicionar validação de dados de entrada/saída

#### 3. Adicionar Suporte a Correlation ID
```python
# Adicionar em todos os métodos públicos
def method_name(..., correlation_id: Optional[str] = None) -> ReturnType
```

### 📊 Prioridade Média

#### 4. Melhorar Sistema de Cache
- Implementar cache distribuído (Redis)
- Adicionar invalidação por eventos
- Implementar cache warming
- Adicionar métricas de hit/miss ratio

#### 5. Aprimorar Tratamento de Erros
- Implementar circuit breaker pattern
- Adicionar correlation IDs em logs
- Implementar retry policies configuráveis
- Adicionar health checks mais robustos

#### 6. Suporte a Entity ID
```python
# Adicionar filtro por entidade em métodos relevantes
def get_technician_ranking(..., entity_id: Optional[int] = None)
```

### 🔄 Prioridade Baixa

#### 7. Refatoração de Arquitetura
- Resolver dependência circular HttpClient ↔ Authentication
- Implementar injeção de dependência mais robusta
- Separar responsabilidades do Facade

#### 8. Otimizações de Performance
- Implementar connection pooling
- Adicionar compressão HTTP
- Otimizar queries GLPI
- Implementar paginação eficiente

## 📈 6. Plano de Migração Sugerido

### Fase 1: Compatibilidade Básica (2-3 semanas)
1. Implementar métodos ausentes críticos
2. Adicionar suporte a correlation_id
3. Migrar tipos de retorno para Pydantic
4. Testes de compatibilidade

### Fase 2: Melhorias de Sistema (3-4 semanas)
1. Implementar cache distribuído
2. Aprimorar tratamento de erros
3. Adicionar suporte a entity_id
4. Implementar métricas avançadas

### Fase 3: Otimizações (2-3 semanas)
1. Refatorar arquitetura
2. Otimizações de performance
3. Documentação completa
4. Testes de carga

## 📊 7. Métricas de Sucesso

- **Compatibilidade**: 100% dos métodos do contrato implementados
- **Performance**: Tempo de resposta < 500ms para 95% das requests
- **Confiabilidade**: Uptime > 99.9%
- **Cache Hit Ratio**: > 80% para dados frequentemente acessados
- **Cobertura de Testes**: > 90%

## 🎯 8. Conclusão

Os serviços legacy apresentam uma base sólida com 42% de compatibilidade com os contratos esperados. As principais lacunas estão na ausência de métodos para listagem de tickets e filtros avançados. A migração é viável com esforço estimado de 7-10 semanas para compatibilidade completa.

**Pontos Fortes:**
- Arquitetura bem estruturada com separação de responsabilidades
- Sistema de cache funcional
- Autenticação robusta com retry
- Descoberta automática de field IDs

**Principais Desafios:**
- Métodos ausentes críticos (58%)
- Incompatibilidade de tipos de retorno
- Ausência de correlation IDs
- Cache não distribuído

**Recomendação:** Proceder com migração incremental priorizando compatibilidade básica antes de otimizações avançadas.