# GLPI Dashboard - Sistema de Business Intelligence para ITSM

Sistema completo de monitoramento e análise de dados de TI baseado na API GLPI, com frontend React e backend Flask seguindo arquitetura clean e padrões empresariais.

## 🏗️ Arquitetura do Sistema

### **Padrão Facade-Centric**
O sistema utiliza um padrão arquitetural centrado em MetricsFacade que serve como ponto único de entrada para todas as operações de dados:

```
API Routes → MetricsFacade → [GLPI Service | Mock Data] → Response
```

### **Estrutura do Backend**
```
backend/
├── core/application/          # Camada de aplicação (Clean Architecture)
│   ├── contracts/            # Contratos e DTOs (Data Transfer Objects)
│   ├── queries/             # Queries e consultas especializadas
│   └── services/            # Serviços de domínio
│       ├── metrics_facade.py           # 🎯 PONTO ÚNICO DE ENTRADA
│       └── progressive_refactoring_service.py
├── core/infrastructure/       # Infraestrutura e adaptadores
│   ├── cache/               # Sistema de cache unificado
│   └── adapters/           # Adaptadores para APIs externas
├── services/legacy/          # Código legado (desuso programado)
├── api/                     # Camada de API (Flask routes)
├── schemas/                 # Esquemas Pydantic (fonte única da verdade)
├── utils/                   # Utilitários e mock data
└── config/                  # Configurações e settings
```

### **Frontend Architecture** 
```
frontend/ (React + TypeScript)
├── src/
│   ├── components/          # Componentes reutilizáveis
│   ├── pages/              # Páginas da aplicação
│   ├── services/           # Camada de API service
│   ├── hooks/              # React hooks customizados
│   └── types/              # Tipos TypeScript
```

## 🚀 Configuração e Execução

### **Pré-requisitos**
- Python 3.11+
- Node.js 18+
- Redis (para cache)
- Tokens de API GLPI válidos

### **1. Configuração do Backend**

```bash
# Navegue para o diretório backend
cd backend

# Configure as variáveis de ambiente
cp .env.example .env
```

**Configuração obrigatória no .env:**
```env
# API GLPI - OBRIGATÓRIO
GLPI_URL=http://seu-glpi.com/apirest.php
GLPI_APP_TOKEN=seu_app_token_aqui
GLPI_USER_TOKEN=seu_user_token_aqui

# Chave secreta para produção
SECRET_KEY=sua_chave_secreta_super_forte_aqui

# Modo de dados (true=mock, false=real)
USE_MOCK_DATA=false

# Cache Redis
REDIS_URL=redis://localhost:6379/0

# Flask settings
FLASK_ENV=development
FLASK_DEBUG=true
```

### **2. Instalação das Dependências**

```bash
# Backend (Python)
cd backend
pip install -r requirements.txt

# Frontend (Node.js)
cd ../frontend
npm install
```

### **3. Execução do Sistema**

**Backend (Terminal 1):**
```bash
cd backend
python app.py
# Servidor rodando em http://localhost:8000
```

**Frontend (Terminal 2):**
```bash
cd frontend
npm run dev
# Interface em http://localhost:5000
```

## 🎛️ Modos de Operação

### **Modo Mock Data (Desenvolvimento)**
```bash
# No arquivo .env
USE_MOCK_DATA=true
```
- ✅ Dados simulados realistas
- ✅ Sem dependência da API GLPI
- ✅ Ideal para desenvolvimento da interface
- ✅ Testes automatizados

### **Modo Dados Reais (Produção)**
```bash
# No arquivo .env
USE_MOCK_DATA=false
```
- ✅ Integração direta com API GLPI
- ✅ Dados em tempo real
- ✅ Cache inteligente para performance
- ✅ Monitoramento e alertas

## 📊 Endpoints da API

### **Métricas Principais**
```http
GET /api/metrics
# Métricas gerais do dashboard

GET /api/metrics/v2  
# Versão otimizada com MetricsFacade

GET /api/metrics/filtered?start_date=2025-01-01&end_date=2025-12-31
# Métricas filtradas por período
```

### **Ranking de Técnicos**
```http
GET /api/technicians/ranking?limit=50
# Top técnicos por performance

GET /api/technicians/ranking/filtered?level=N1&limit=10
# Ranking filtrado por nível
```

### **Saúde do Sistema**
```http
GET /api/health
# Status geral do sistema

GET /api/
# Informações da API
```

## 🗄️ Esquemas de Dados

### **DashboardMetrics (Principal)**
```python
class DashboardMetrics(BaseModel):
    total: int                    # Total de tickets
    novos: int                   # Tickets novos
    pendentes: int               # Tickets pendentes
    resolvidos: int              # Tickets resolvidos
    niveis: NiveisMetrics        # Métricas por nível (N1-N4)
    tickets_novos: List[NewTicket] # Lista de tickets recentes
    tendencias: Dict[str, float]  # Tendências percentuais
    ultima_atualizacao: datetime  # Timestamp da atualização
```

### **Mapeamento de Níveis de Serviço**
```python
NIVEIS_MAPPING = {
    "N1": {"group_id": 89, "description": "Suporte Básico"},
    "N2": {"group_id": 90, "description": "Suporte Intermediário"},
    "N3": {"group_id": 91, "description": "Suporte Avançado"},
    "N4": {"group_id": 92, "description": "Suporte Especialista"}
}
```

## 🔧 Sistema de Cache

### **Cache Unificado (UnifiedCache)**
```python
# Uso em serviços
from core.infrastructure.cache.unified_cache import unified_cache

# Cache com namespace
result = unified_cache.get("metrics", {"query": "dashboard"})
if not result:
    result = fetch_data()
    unified_cache.set("metrics", {"query": "dashboard"}, result, timeout=300)
```

### **Configuração de TTL**
- **Métricas Dashboard**: 5 minutos
- **Ranking Técnicos**: 10 minutos  
- **Dados GLPI**: 15 minutos
- **Health Check**: 1 minuto

## 🛡️ Segurança e Produção

### **Headers de Segurança**
```python
# Configurados automaticamente
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000
```

### **CORS Configurado**
```python
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5000",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5000"
]
```

### **Rate Limiting**
- **Desenvolvimento**: 100 requests/minuto
- **Produção**: 60 requests/minuto
- **API endpoints**: Limitados individualmente

## 📈 Monitoramento e Observabilidade

### **Logs Estruturados**
```json
{
  "timestamp": "2025-09-12T23:30:37.104Z",
  "level": "INFO", 
  "logger": "glpi.api",
  "message": "Operação success: api_request",
  "correlation_id": "63d4***REDACTED***945d",
  "operation_phase": "end",
  "duration_seconds": 0.004519
}
```

### **Métricas de Performance**
- **Response Time**: < 300ms (P95)
- **Error Rate**: < 5%
- **Uptime**: > 99.9%
- **Cache Hit Rate**: > 80%

### **Sistema de Alertas**
```python
# Configuração de alertas
ALERT_RESPONSE_TIME_THRESHOLD=300    # 300ms
ALERT_ERROR_RATE_THRESHOLD=0.05      # 5%
ALERT_ZERO_TICKETS_THRESHOLD=60      # 60 segundos
```

## 🧪 Testes e Qualidade

### **Type Safety**
✅ **Zero LSP diagnostics** - 100% type safety garantida  
✅ **Pydantic models** em todas as interfaces  
✅ **TypeScript strict mode** no frontend  
✅ **Validação de schema** automática  

### **Testes Backend**
```bash
# Testes unitários
pytest tests/

# Cobertura de código
pytest --cov=backend tests/

# Testes de integração
pytest tests/integration/
```

### **Testes Frontend**
```bash
# Testes de componentes
npm test

# Testes E2E
npm run test:e2e

# Build de produção
npm run build
```

## 🔄 Estratégia de Refatoração

### **Padrão Strangler Fig**
O sistema implementa refatoração progressiva:

1. **Legacy Code** → `services/legacy/` (isolado)
2. **New Architecture** → `core/application/` (ativo)
3. **Migration Strategy** → Gradual replacement via MetricsFacade

### **Progress Tracking**
```python
# Monitoramento da migração
class ProgressiveRefactoringService:
    def track_migration_progress(self) -> Dict[str, Any]
    def validate_architectural_consistency(self) -> bool
    def generate_migration_report(self) -> str
```

## 🚀 Deploy e Produção

### **Configuração de Produção**
```env
# .env para produção
FLASK_ENV=production
FLASK_DEBUG=false
USE_MOCK_DATA=false
SECRET_KEY=chave_super_secreta_producao
REDIS_URL=redis://redis-prod:6379/0
GLPI_URL=https://glpi-prod.empresa.com/apirest.php
```

### **Docker Deployment**
```bash
# Build images
docker-compose build

# Deploy stack
docker-compose up -d

# Monitor logs
docker-compose logs -f
```

### **Health Checks**
```bash
# Verificar saúde
curl http://localhost:8000/api/health

# Verificar métricas
curl http://localhost:8000/api/metrics/v2
```

## 📚 Guias Adicionais

### **Adicionando Novos Endpoints**
1. Defina schema em `schemas/`
2. Implemente lógica em `MetricsFacade`
3. Adicione rota em `api/routes.py`
4. Teste com dados mock e reais

### **Debugging**
```bash
# Verificar logs de erro
grep "ERROR" logs/app.log

# Verificar performance
grep "api_request_duration" logs/app.log

# Verificar cache
redis-cli monitor
```

### **Contribuindo**
1. **Não quebre a arquitetura** - use sempre MetricsFacade
2. **Mantenha type safety** - zero LSP diagnostics
3. **Testes obrigatórios** para novas features
4. **Documentação atualizada** sempre

---

## 📞 Suporte

**Para issues técnicas:**
- Verifique logs em `/tmp/logs/`
- Validate configuração `.env`
- Teste com `USE_MOCK_DATA=true` primeiro
- Consulte a seção de troubleshooting

**Status do Sistema:**
- ✅ **Backend**: Production-ready com dados reais
- ✅ **Type Safety**: 100% (0 LSP diagnostics)
- ✅ **Cache**: Unificado e otimizado
- ✅ **Segurança**: Headers e CORS configurados
- ✅ **Monitoramento**: Logs estruturados e métricas

---
*Sistema desenvolvido seguindo Clean Architecture e padrões enterprise para máxima qualidade e maintainability.*