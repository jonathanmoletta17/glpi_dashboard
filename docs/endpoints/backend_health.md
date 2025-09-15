# Endpoint: /health

## Arquivo(s) de origem
- `backend/api/routes.py` (linha ~1300-1350)
- `backend/utils/observability_middleware.py` (endpoint adicional)

## Método HTTP
`GET`

## Descrição técnica
Endpoint de health check que verifica o status geral da aplicação, incluindo conectividade com serviços externos (GLPI, Redis) e métricas básicas de sistema.

## Parâmetros de entrada
Nenhum parâmetro necessário.

## Resposta esperada (contract)
```json
{
  "status": "healthy",
  "timestamp": "2025-01-27T10:30:00Z",
  "version": "1.0.0",
  "uptime_seconds": 3600,
  "services": {
    "glpi": {
      "status": "healthy",
      "response_time_ms": 45.2,
      "last_check": "2025-01-27T10:29:55Z"
    },
    "redis": {
      "status": "healthy",
      "response_time_ms": 2.1,
      "last_check": "2025-01-27T10:29:55Z"
    },
    "database": {
      "status": "not_configured",
      "response_time_ms": null,
      "last_check": null
    }
  },
  "system": {
    "memory_usage_mb": 256.7,
    "cpu_usage_percent": 12.5,
    "disk_usage_percent": 45.2
  },
  "environment": "development",
  "correlation_id": "health_123456789"
}
```

## Resposta em caso de problemas
```json
{
  "status": "unhealthy",
  "timestamp": "2025-01-27T10:30:00Z",
  "version": "1.0.0",
  "uptime_seconds": 3600,
  "services": {
    "glpi": {
      "status": "unhealthy",
      "response_time_ms": null,
      "last_check": "2025-01-27T10:29:55Z",
      "error": "Connection timeout after 30s"
    },
    "redis": {
      "status": "healthy",
      "response_time_ms": 2.1,
      "last_check": "2025-01-27T10:29:55Z"
    }
  },
  "errors": [
    "GLPI service unavailable",
    "High memory usage detected (>80%)"
  ],
  "environment": "production",
  "correlation_id": "health_987654321"
}
```

## Tipagem equivalente em TypeScript
```typescript
type ServiceStatus = 'healthy' | 'unhealthy' | 'not_configured';
type SystemStatus = 'healthy' | 'degraded' | 'unhealthy';

interface ServiceHealth {
  status: ServiceStatus;
  response_time_ms: number | null;
  last_check: string | null;
  error?: string;
}

interface SystemMetrics {
  memory_usage_mb: number;
  cpu_usage_percent: number;
  disk_usage_percent: number;
}

interface HealthResponse {
  status: SystemStatus;
  timestamp: string;
  version: string;
  uptime_seconds: number;
  services: {
    glpi: ServiceHealth;
    redis: ServiceHealth;
    database?: ServiceHealth;
  };
  system: SystemMetrics;
  environment: 'development' | 'staging' | 'production';
  correlation_id: string;
  errors?: string[];
}
```

## Dependências

### Backend
- `GLPIServiceFacade` - Verificação de conectividade GLPI
- `unified_cache` - Verificação de conectividade Redis
- `psutil` - Métricas de sistema (se disponível)
- `app.config` - Configurações da aplicação
- `performance_monitor` - Métricas de performance

### Frontend
- **Service**: `apiService.getSystemStatus()` (se implementado)
- **Não consumido diretamente** pelos hooks principais
- **Uso**: Monitoramento, dashboards administrativos

### Variáveis de ambiente
- `GLPI_URL` - URL para teste de conectividade
- `GLPI_USER_TOKEN` - Token para autenticação
- `REDIS_URL` - URL do Redis para teste
- `ENVIRONMENT` - Ambiente atual (dev/staging/prod)

## Análise técnica

### Consistência
✅ **Boa**: Endpoint padrão para health checks
✅ **Informativo**: Fornece detalhes úteis sobre serviços
⚠️ **Sem tipagem frontend**: Não há interface TypeScript correspondente

### Possíveis problemas
- ⚠️ **Timeout**: Verificações podem ser lentas em caso de problemas
- ⚠️ **Exposição de informações**: Pode revelar detalhes internos
- ⚠️ **Sem cache**: Verificações são executadas a cada chamada
- ⚠️ **Métricas limitadas**: Poucas métricas de sistema disponíveis

### Sugestões de melhorias
1. **Cache de health checks**: Implementar cache curto (30-60s) para evitar sobrecarga
2. **Níveis de detalhamento**: Parâmetro para controlar nível de informações
3. **Alertas proativos**: Integração com sistemas de monitoramento
4. **Métricas avançadas**: Adicionar métricas de:
   - Número de requests por minuto
   - Tempo médio de resposta
   - Taxa de erro
   - Uso de conexões de banco
5. **Segurança**: Limitar informações expostas em produção
6. **Tipagem frontend**: Criar interface TypeScript
7. **Documentação OpenAPI**: Documentar no Swagger
8. **Health check dependencies**: Verificar dependências críticas vs não-críticas

## Códigos de status HTTP
- `200 OK`: Sistema saudável
- `503 Service Unavailable`: Sistema com problemas críticos
- `200 OK` com `status: "degraded"`: Problemas não-críticos

## Uso recomendado
- **Load balancers**: Verificação de saúde da instância
- **Monitoramento**: Alertas automáticos
- **Deploy**: Verificação pós-deploy
- **Debugging**: Diagnóstico de problemas

## Status de implementação
✅ **Implementado** - Funcional no backend
✅ **Verificações básicas** - GLPI e Redis
❌ **Sem tipagem frontend** - Interface TypeScript não criada
❌ **Sem cache** - Verificações executadas sempre
⚠️ **Métricas limitadas** - Apenas métricas básicas disponíveis