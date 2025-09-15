# BYTEROVER HANDBOOK - GLPI Dashboard

*Sistema de Business Intelligence para ITSM baseado em GLPI API*

---

## 🏗️ LAYER 1: SYSTEM OVERVIEW

### Purpose
Sistema completo de monitoramento e análise de dados de TI baseado na API GLPI, com frontend React e backend Flask seguindo arquitetura clean e padrões empresariais. O sistema fornece dashboards interativos para análise de performance de técnicos, métricas de tickets e indicadores de ITSM.

### Tech Stack

**Backend (Python)**
- **Framework**: Flask 3.1.1+ com Blueprint architecture
- **Database**: PostgreSQL com SQLAlchemy ORM
- **Cache**: Redis 5.0+ com hiredis para performance
- **API Client**: httpx + requests para integração GLPI
- **Validation**: Pydantic 2.0+ para schemas e DTOs
- **Monitoring**: Prometheus metrics + structured logging
- **Deployment**: Gunicorn + Docker

**Frontend (TypeScript/React)**
- **Framework**: React 18.2+ com TypeScript
- **Build Tool**: Vite com hot reload
- **UI Library**: Radix UI components + Tailwind CSS
- **HTTP Client**: Axios para API calls
- **Icons**: Lucide React
- **Styling**: Tailwind CSS + class-variance-authority

### Architecture Pattern
**Facade-Centric Clean Architecture** com migração progressiva de código legacy:

```
API Routes → MetricsFacade → [GLPI Service | Mock Data] → Response
     ↓              ↓                    ↓
  Blueprint    Clean Arch         Legacy/External
```

### Key Technical Decisions
- **Clean Architecture**: Separação clara entre domínio, aplicação e infraestrutura
- **Progressive Refactoring**: Migração gradual de código legacy para nova arquitetura
- **Unified Cache**: Sistema de cache centralizado com Redis
- **Observability-First**: Logging estruturado e métricas Prometheus
- **Type Safety**: Pydantic schemas como "fonte única da verdade"

---

## 🗺️ LAYER 2: MODULE MAP

### Core Modules

#### 1. **MetricsFacade** (`core/application/services/`)
**Responsibility**: Ponto único de entrada para todas as operações de dados
- Orquestra chamadas para serviços GLPI
- Aplica regras de negócio e transformações
- Gerencia cache e observabilidade
- Interface limpa para controllers

#### 2. **API Layer** (`api/`)
**Responsibility**: Endpoints REST e validação de entrada
- `routes.py`: Endpoints principais (/metrics, /technicians, /tickets)
- `comparison_routes.py`: Comparação entre arquiteturas
- `server_metrics.py`: Métricas de servidor e health checks
- Decorators para cache, performance e validação

#### 3. **GLPI Integration** (`services/legacy/`)
**Responsibility**: Integração com API GLPI (código legacy em migração)
- `glpi_service_facade.py`: Facade para operações GLPI
- `http_client_service.py`: Cliente HTTP para API GLPI
- `auth_service.py`: Autenticação e gestão de tokens

#### 4. **Infrastructure** (`core/infrastructure/`)
**Responsibility**: Adaptadores e infraestrutura técnica
- `cache/unified_cache.py`: Sistema de cache unificado
- `adapters/legacy_service_adapter.py`: Adaptador para serviços legacy
- `converters/`: Conversores de dados entre formatos

#### 5. **Monitoring & Observability** (`monitoring/`, `utils/`)
**Responsibility**: Observabilidade, métricas e alertas
- Structured logging com correlation IDs
- Métricas Prometheus para APIs
- Sistema de alertas e diagnósticos
- Performance monitoring e profiling

### Data Layer
- **Schemas** (`schemas/dashboard.py`): Pydantic models como fonte única da verdade
- **DTOs** (`core/application/dto/`): Data Transfer Objects para clean architecture
- **Contracts** (`core/application/contracts/`): Interfaces e contratos

### Utilities
- **Date Validation**: Decorators para validação automática de datas
- **Response Formatting**: Formatação padronizada de respostas API
- **Performance Monitoring**: Decorators para cache e métricas
- **Mock Data**: Geradores de dados para desenvolvimento e testes

---

## 🔌 LAYER 3: INTEGRATION GUIDE

### API Endpoints

#### Core Metrics Endpoints
```
GET /api/metrics                    # Dashboard metrics with filters
GET /api/metrics/filtered           # Advanced filtered metrics
GET /api/technicians                # Technician list and basic info
GET /api/technician-performance     # Technician performance metrics
GET /api/technicians/ranking        # Technician ranking with scores
GET /api/tickets/new                # Recent tickets with filters
```

#### System Endpoints
```
GET /api/                          # API root with available endpoints
GET /api/status                    # System status and health
GET /api/health                    # Detailed health check
GET /api/docs                      # Swagger UI documentation
GET /api/openapi.yaml              # OpenAPI specification
```

#### Monitoring Endpoints
```
GET /metrics                       # Prometheus metrics
GET /health                        # Application health
GET /alerts                        # System alerts
```

### External Integrations

#### GLPI API Integration
- **Base URL**: Configurável via `GLPI_URL`
- **Authentication**: App Token + User Token
- **Endpoints Used**:
  - `/apirest.php/initSession` - Autenticação
  - `/apirest.php/Ticket` - Dados de tickets
  - `/apirest.php/User` - Dados de usuários/técnicos
  - `/apirest.php/getMyProfiles` - Perfis do usuário

#### Cache Integration (Redis)
- **Connection**: Configurável via `REDIS_URL`
- **Strategies**: TTL-based caching com invalidação inteligente
- **Keys Pattern**: `glpi_dashboard:{endpoint}:{filters_hash}`

### Configuration Files
- **Environment**: `.env` com variáveis de ambiente
- **Settings**: `config/settings.py` com configurações por ambiente
- **Docker**: `docker-compose.yml` para desenvolvimento
- **Production**: `docker-compose.prod.yml` para produção

### Data Flow Patterns
1. **Request** → API Route → Validation Decorators
2. **Route** → MetricsFacade → Business Logic
3. **Facade** → GLPI Service → External API
4. **Response** → Cache → Format → JSON

---

## 🔧 LAYER 4: EXTENSION POINTS

### Design Patterns

#### 1. **Facade Pattern**
- `MetricsFacade`: Simplifica interface complexa do GLPI
- `GLPIServiceFacade`: Abstrai operações de API externa
- **Extension**: Adicionar novos facades para outras integrações

#### 2. **Adapter Pattern**
- `LegacyServiceAdapter`: Adapta código legacy para nova arquitetura
- **Extension**: Criar adapters para outras APIs (ServiceNow, Jira, etc.)

#### 3. **Decorator Pattern**
- `@cache_with_filters`: Cache inteligente baseado em filtros
- `@monitor_performance`: Métricas automáticas de performance
- `@standard_date_validation`: Validação automática de datas
- **Extension**: Criar novos decorators para autenticação, rate limiting

#### 4. **Strategy Pattern**
- Cache strategies (TTL, LRU, invalidation)
- Data formatting strategies
- **Extension**: Implementar strategies para diferentes fontes de dados

### Customization Areas

#### 1. **Metrics Calculation**
```python
# Extend MetricsFacade with custom metrics
class CustomMetricsFacade(MetricsFacade):
    def get_custom_kpi(self, filters):
        # Custom business logic
        pass
```

#### 2. **Data Sources**
```python
# Add new data source adapters
class ServiceNowAdapter(BaseAdapter):
    def get_tickets(self, filters):
        # ServiceNow integration
        pass
```

#### 3. **Cache Strategies**
```python
# Custom cache invalidation
class SmartCacheStrategy(CacheStrategy):
    def should_invalidate(self, key, data):
        # Custom invalidation logic
        pass
```

#### 4. **Monitoring Extensions**
```python
# Custom metrics collectors
class BusinessMetricsCollector:
    def collect_sla_metrics(self):
        # Custom SLA calculations
        pass
```

### Plugin Architecture
O sistema suporta extensões através de:
- **Blueprint Registration**: Novos endpoints via Flask Blueprints
- **Service Registration**: Novos serviços via dependency injection
- **Middleware Chain**: Interceptors para requests/responses
- **Event System**: Hooks para eventos de sistema

### Development Patterns
- **Progressive Refactoring**: Migração gradual de legacy para clean arch
- **Feature Flags**: Controle de features via configuração
- **A/B Testing**: Comparação entre implementações (comparison_routes)
- **Observability-Driven**: Métricas e logs guiam desenvolvimento

### Common Extension Scenarios
1. **New ITSM Integration**: Criar adapter + facade + routes
2. **Custom Dashboard**: Estender MetricsFacade + criar endpoints
3. **Advanced Caching**: Implementar nova strategy + configurar TTL
4. **Business Rules**: Adicionar validators + transformers
5. **Monitoring**: Criar collectors + dashboards + alertas

---

## 📋 DEBUGGING GUIDE - Dados Zerados

### Checklist Diagnóstico Rápido

#### 1. **Verificação de Conectividade GLPI**
```bash
# Teste básico de conectividade
curl -X GET "$GLPI_URL/apirest.php" -H "App-Token: $GLPI_APP_TOKEN"

# Teste de autenticação
curl -X GET "$GLPI_URL/apirest.php/initSession" \
  -H "App-Token: $GLPI_APP_TOKEN" \
  -H "Authorization: user_token $GLPI_USER_TOKEN"
```

#### 2. **Validação de Dados na Fonte**
```sql
-- Verificar tickets existentes
SELECT COUNT(*) FROM glpi_tickets WHERE is_deleted = 0;

-- Verificar técnicos ativos
SELECT COUNT(*) FROM glpi_users WHERE is_active = 1 AND is_deleted = 0;

-- Verificar atribuições
SELECT COUNT(*) FROM glpi_tickets_users WHERE type = 2; -- assigned
```

#### 3. **Debug de Filtros API**
```python
# Verificar filtros restritivos
print(f"Período: {start_date} - {end_date}")
if start_date and end_date:
    delta = end_date - start_date
    if delta.days < 1:
        print("⚠️ PROBLEMA: Período muito restritivo!")
```

#### 4. **Análise de Performance Scores**
```python
# Verificar cálculo de performance
def debug_performance_calculation(resolved, avg_time, total):
    if total == 0:
        return None  # ⚠️ PROBLEMA IDENTIFICADO!
    
    base_score = (resolved / total) * 100
    print(f"Base score: {base_score}% ({resolved}/{total})")
    return base_score
```

### Padrões Comuns de Problemas
- **Filtros OR incorretos**: Sintaxe `criteria[0][link]=OR`
- **Status inadequados**: Verificar mapeamento de status GLPI
- **Permissões GLPI**: Validar perfis e entidades acessíveis
- **Cache stale**: Invalidar cache com dados antigos
- **Timezone issues**: Verificar conversão de datas UTC/local

---

*Handbook gerado automaticamente pelo Byterover MCP*
*Última atualização: $(date)*