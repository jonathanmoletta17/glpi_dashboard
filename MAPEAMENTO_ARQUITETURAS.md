# Mapeamento Completo entre Arquiteturas

## Tabela de Mapeamento Principal

| MetricsFacade Method | Legacy Method | Conversion Required | Status |
|---------------------|---------------|--------------------|---------|
| `get_dashboard_metrics()` | `get_dashboard_summary()` | DashboardMetrics model | ✅ Implementado |
| `get_technician_ranking()` | `get_technician_performance()` | TechnicianRanking model | ✅ Implementado |
| `get_new_tickets()` | `get_recent_tickets()` | NewTickets model | ✅ Implementado |
| `get_system_status()` | `get_system_health()` | SystemStatus model | ✅ Implementado |

## Mapeamento Detalhado de Métodos

### 1. Dashboard Metrics

**MetricsFacade → Legacy → Pydantic**
- `get_dashboard_metrics()` → `GLPIServiceFacade.get_dashboard_metrics()` → `DashboardMetrics`
- `get_dashboard_metrics_with_date_filter()` → `GLPIServiceFacade.get_dashboard_metrics()` + filtros → `DashboardMetrics`
- `get_dashboard_metrics_with_modification_date_filter()` → `GLPIServiceFacade.get_dashboard_metrics()` + filtros → `DashboardMetrics`

### 2. Technician Ranking

**MetricsFacade → Legacy → Pydantic**
- `get_technician_ranking()` → `GLPIServiceFacade.get_all_technician_ids_and_names()` → `List[TechnicianRanking]`
- `get_technician_ranking_with_filters()` → `GLPIServiceFacade.get_all_technician_ids_and_names()` + filtros → `List[TechnicianRanking]`

### 3. New Tickets

**MetricsFacade → Legacy → Pydantic**
- `get_new_tickets()` → `GLPIServiceFacade.get_new_tickets()` → `List[NewTicket]`
- `get_new_tickets_with_filters()` → `GLPIServiceFacade.get_new_tickets()` + filtros → `List[NewTicket]`

### 4. System Status

**MetricsFacade → Legacy → Pydantic**
- `get_system_status()` → `GLPIServiceFacade.health_check()` → `SystemStatus`
- `authenticate_with_retry()` → `GLPIServiceFacade.authenticate()` → `bool`

## Conversores Implementados

### LegacyDataConverter

Localização: `backend/core/infrastructure/converters/legacy_data_converter.py`

#### Métodos de Conversão:

1. **`convert_dashboard_data()`** - Converte dados legacy para DashboardMetrics
2. **`convert_technician_ranking()`** - Converte ranking de técnicos
3. **`convert_new_tickets()`** - Converte lista de novos tickets
4. **`_convert_ticket_status()`** - Converte status de tickets
5. **`_convert_niveis_metrics()`** - Converte métricas de níveis
6. **`_convert_tendencias_metrics()`** - Converte métricas de tendências
7. **`_convert_filters_applied()`** - Converte filtros aplicados

#### Características dos Conversores:

- ✅ **Validação de tipos de entrada**
- ✅ **Transformação para Pydantic models**
- ✅ **Tratamento de campos opcionais/ausentes**
- ✅ **Normalização de formatos (datas, números, strings)**
- ✅ **Logging estruturado para debugging**
- ✅ **Tratamento robusto de erros**

## Estruturas de Dados Mapeadas

### 1. Estruturas de Tickets

**Legacy Format:**
```json
{
  "ticket_status": {
    "new": 10,
    "assigned": 25,
    "planned": 15,
    "waiting": 8,
    "solved": 42,
    "total": 100
  }
}
```

**Pydantic Model:**
```python
class DashboardMetrics(BaseModel):
    novos: int
    pendentes: int  # assigned + waiting
    progresso: int  # planned
    resolvidos: int  # solved
    total: int
```

### 2. Dados de Usuários/Técnicos

**Legacy Format:**
```json
{
  "technician_ranking": [
    {
      "name": "João Silva",
      "tickets_resolved": 45,
      "avg_resolution_time": 2.5,
      "satisfaction_score": 4.2,
      "level": "nivel2"
    }
  ]
}
```

**Pydantic Model:**
```python
class TechnicianRanking(BaseModel):
    name: str
    tickets_resolved: int
    avg_resolution_time: float
    satisfaction_score: float
    level: TechnicianLevel
```

### 3. Métricas de Performance

**Legacy Format:**
```json
{
  "niveis": {
    "nivel1": {"total": 30, "percentual": 30.0},
    "nivel2": {"total": 50, "percentual": 50.0},
    "nivel3": {"total": 20, "percentual": 20.0}
  }
}
```

**Pydantic Model:**
```python
class NiveisMetrics(BaseModel):
    nivel1: LevelMetrics
    nivel2: LevelMetrics
    nivel3: LevelMetrics
```

### 4. Status do Sistema

**Legacy Format:**
```json
{
  "status": "healthy",
  "database": "connected",
  "api": "responsive"
}
```

**Enhanced Format:**
```json
{
  "status": "healthy",
  "database": "connected",
  "api": "responsive",
  "adapter_status": "healthy",
  "legacy_facade_status": "connected",
  "timestamp": "2024-01-15T10:30:00",
  "correlation_id": "abc-123"
}
```

## Tratamento de Erros e Validação

### Estratégias Implementadas:

1. **Retry Logic**: Decorator `@retry_on_failure` com backoff exponencial
2. **Validação de Entrada**: Verificação de estruturas de dados obrigatórias
3. **Valores Padrão**: Fallback para valores seguros quando dados estão ausentes
4. **Logging Estruturado**: Rastreamento completo de conversões e erros
5. **Correlation IDs**: Rastreamento de requisições end-to-end

### Exemplo de Tratamento de Erro:

```python
try:
    # Validar dados de entrada
    if not legacy_data or 'tickets' not in legacy_data:
        raise ValueError("Dados legacy inválidos")
    
    # Converter estrutura
    converted_data = {
        'total_tickets': legacy_data.get('tickets', {}).get('total', 0),
        'open_tickets': legacy_data.get('tickets', {}).get('open', 0),
        # ...
    }
    
    # Validar com Pydantic
    return DashboardMetrics(**converted_data)
    
except Exception as e:
    self.logger.error(f"Erro na conversão de dados: {e}")
    raise
```

## Normalização de Formatos

### Datas
- **Entrada**: Múltiplos formatos (`YYYY-MM-DD`, `DD/MM/YYYY`, etc.)
- **Saída**: ISO 8601 (`datetime` objects)
- **Método**: `_parse_datetime()` com fallback para formatos comuns

### Números
- **Entrada**: Strings, integers, floats
- **Saída**: Tipos apropriados (int, float, Decimal)
- **Validação**: Verificação de ranges válidos

### Strings
- **Entrada**: Dados brutos do GLPI
- **Saída**: Strings sanitizadas e normalizadas
- **Tratamento**: Remoção de caracteres especiais, trim, encoding

## Testes e Robustez

### Características dos Conversores:

- ✅ **Testáveis**: Métodos isolados com dependências injetáveis
- ✅ **Robustos**: Tratamento de casos extremos e dados malformados
- ✅ **Observáveis**: Logging detalhado para debugging
- ✅ **Performáticos**: Conversões otimizadas com cache quando apropriado
- ✅ **Compatíveis**: Suporte a diferentes versões de dados legacy

### Exemplo de Teste:

```python
def test_convert_dashboard_data_with_missing_fields():
    converter = LegacyDataConverter()
    
    # Dados incompletos
    legacy_data = {
        "ticket_status": {"new": 5}  # Campos ausentes
    }
    
    result = converter.convert_dashboard_data(legacy_data)
    
    assert result.novos == 5
    assert result.pendentes == 0  # Valor padrão
    assert result.total >= 0
```

## Status da Implementação

- ✅ **LegacyServiceAdapter**: Implementado com todos os métodos principais
- ✅ **LegacyDataConverter**: Implementado com conversores robustos
- ✅ **Retry Logic**: Implementado com backoff exponencial
- ✅ **Logging**: Estruturado com correlation IDs
- ✅ **Validação**: Pydantic models com validação automática
- ✅ **Tratamento de Erros**: Robusto com fallbacks apropriados

## Próximos Passos

1. **Testes Unitários**: Expandir cobertura de testes para todos os conversores
2. **Testes de Integração**: Validar fluxo completo com dados reais
3. **Performance**: Otimizar conversões para grandes volumes de dados
4. **Monitoramento**: Adicionar métricas de performance dos conversores
5. **Documentação**: Expandir documentação com mais exemplos de uso