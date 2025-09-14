# Diagrama de Dependências - Serviços Legacy GLPI

## Arquitetura Geral

```
┌─────────────────────────────────────────────────────────────────┐
│                    GLPIServiceFacade                            │
│                   (Facade Principal)                            │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                 Serviços Internos                               │
├─────────────────┬───────────────┬───────────────┬───────────────┤
│ Authentication  │ Cache         │ HttpClient    │ FieldDiscovery│
│ Service         │ Service       │ Service       │ Service       │
└─────────────────┴───────────────┴───────────────┴───────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                Serviços de Negócio                              │
├─────────────────┬───────────────┬───────────────────────────────┤
│ Metrics         │ Dashboard     │ Trends                        │
│ Service         │ Service       │ Service                       │
└─────────────────┴───────────────┴───────────────────────────────┘
```

## Dependências Detalhadas

### 1. GLPIServiceFacade
**Dependências Diretas:**
- GLPIAuthenticationService
- GLPICacheService  
- GLPIHttpClientService
- GLPIFieldDiscoveryService
- GLPIMetricsService
- GLPIDashboardService
- GLPITrendsService

**Responsabilidades:**
- Orquestração de todos os serviços
- Interface unificada para clientes
- Gerenciamento de estado global

### 2. GLPIAuthenticationService
**Dependências Externas:**
- `config.settings`
- `utils.structured_logger`
- `requests`

**Funcionalidades:**
- Gerenciamento de sessão GLPI
- Autenticação com retry automático
- Validação de token de sessão

### 3. GLPICacheService
**Dependências Externas:**
- `time`
- `typing`

**Cache Keys e TTLs:**
- `technician_ranking`: 300s
- `field_ids`: 1800s (discovered) / 600s (fallback)
- `dashboard_metrics`: 180s
- `trends_data`: 300s

### 4. GLPIHttpClientService
**Dependências:**
- GLPIAuthenticationService ← **Dependência Circular**
- `requests`
- `utils.prometheus_metrics`
- `utils.structured_logging`

**Configurações:**
- Max retries: 3
- Retry delay base: 2s
- Timeout padrão: 30s

### 5. GLPIFieldDiscoveryService
**Dependências:**
- GLPIHttpClientService
- GLPICacheService

**Field Mappings:**
- status, priority, category
- technician, entity, group
- date_creation, date_mod

### 6. GLPIMetricsService
**Dependências:**
- GLPIHttpClientService
- GLPICacheService
- GLPIFieldDiscoveryService

**Service Levels:**
- N1: group_id = 4
- N2: group_id = 5  
- N3: group_id = 6

### 7. GLPIDashboardService
**Dependências:**
- GLPIHttpClientService
- GLPICacheService
- GLPIMetricsService

**Métricas Calculadas:**
- Status breakdown
- Average resolution time
- General metrics aggregation

### 8. GLPITrendsService
**Dependências:**
- GLPIHttpClientService
- GLPICacheService
- GLPIMetricsService
- `DateValidator`

**Análises:**
- Comparação de períodos
- Dados históricos por intervalo
- Cálculo de percentual de mudança

## Fluxo de Inicialização

```
1. GLPIServiceFacade.__init__()
   ├── 2. GLPIAuthenticationService()
   ├── 3. GLPICacheService()
   ├── 4. GLPIHttpClientService(auth_service)
   ├── 5. GLPIFieldDiscoveryService(http_client, cache)
   ├── 6. GLPIMetricsService(http_client, cache, field_discovery)
   ├── 7. GLPIDashboardService(http_client, cache, metrics)
   └── 8. GLPITrendsService(http_client, cache, metrics)
```

## Pontos Críticos

### ⚠️ Dependência Circular
- **HttpClient** → **Authentication** → **HttpClient**
- Resolvida via injeção de dependência no construtor

### 🔄 Cache Compartilhado
- Todos os serviços usam a mesma instância de cache
- Possível contenção em operações concorrentes

### 🌐 Estado Global
- Session token compartilhado entre todos os serviços
- Field IDs descobertos uma vez e reutilizados

### 📊 Métricas Agregadas
- Dashboard depende de Metrics para cálculos
- Trends depende de Metrics para dados históricos
- Possível duplicação de requests HTTP