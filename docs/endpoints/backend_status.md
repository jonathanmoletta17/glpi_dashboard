# Endpoint: /status

## Arquivo(s) de origem
- `backend/api/routes.py` (linha ~1200-1250)
- `frontend/services/api.ts` (método `getSystemStatus`)

## Método HTTP
`GET`

## Descrição técnica
Endpoint que retorna o status resumido do sistema, focado em informações essenciais para o dashboard principal. Versão simplificada do `/health` para consumo do frontend.

## Parâmetros de entrada
Nenhum parâmetro necessário.

## Resposta esperada (contract)
```json
{
  "success": true,
  "data": {
    "status": "operational",
    "glpi_status": "connected",
    "cache_status": "active",
    "last_update": "2025-01-27T10:30:00Z",
    "active_tickets": 156,
    "system_load": "normal",
    "data_source": "glpi",
    "is_mock_data": false
  },
  "cached": true,
  "response_time_ms": 12.5,
  "correlation_id": "status_123456789"
}
```

## Resposta em caso de problemas
```json
{
  "success": true,
  "data": {
    "status": "degraded",
    "glpi_status": "disconnected",
    "cache_status": "active",
    "last_update": "2025-01-27T09:45:00Z",
    "active_tickets": 0,
    "system_load": "high",
    "data_source": "mock",
    "is_mock_data": true,
    "issues": [
      "GLPI connection timeout",
      "Using fallback data"
    ]
  },
  "cached": false,
  "response_time_ms": 45.2,
  "correlation_id": "status_987654321"
}
```

## Tipagem equivalente em TypeScript
```typescript
type SystemStatus = 'operational' | 'degraded' | 'maintenance' | 'offline';
type ServiceStatus = 'connected' | 'disconnected' | 'timeout' | 'error';
type SystemLoad = 'low' | 'normal' | 'high' | 'critical';

interface SystemStatusData {
  status: SystemStatus;
  glpi_status: ServiceStatus;
  cache_status: ServiceStatus;
  last_update: string;
  active_tickets: number;
  system_load: SystemLoad;
  
  // Campos de identificação de fonte (obrigatórios)
  data_source: 'glpi' | 'mock' | 'unknown';
  is_mock_data: boolean;
  
  // Campos opcionais
  issues?: string[];
  maintenance_window?: {
    start: string;
    end: string;
    description: string;
  };
}

interface SystemStatusResponse {
  success: boolean;
  data: SystemStatusData;
  cached: boolean;
  response_time_ms: number;
  correlation_id: string;
}
```

## Dependências

### Backend
- `GLPIServiceFacade` - Verificação rápida de conectividade
- `unified_cache` - Status do cache Redis
- `PerformanceMonitor` - Métricas de carga do sistema
- `ResponseFormatter` - Formatação de respostas

### Frontend
- **Service**: `apiService.getSystemStatus()`
- **Componente**: Status indicator no header/dashboard
- **Tipos**: `SystemStatusData` em `types/api.ts`
- **Não possui hook dedicado** - Chamado diretamente pelo service

### Variáveis de ambiente
- `GLPI_URL` - URL para verificação de conectividade
- `CACHE_DEFAULT_TIMEOUT` - Configuração de cache
- `SYSTEM_STATUS_CACHE_TTL` - TTL específico para status (padrão: 60s)

## Análise técnica

### Consistência
✅ **Boa**: Endpoint bem estruturado para consumo frontend
✅ **Campos de fonte**: Implementação correta de `data_source` e `is_mock_data`
✅ **Resposta padronizada**: Segue padrão de resposta da API
⚠️ **Sem tipagem completa**: Interface TypeScript não implementada no frontend

### Possíveis problemas
- ⚠️ **Cache agressivo**: Cache de 60s pode mascarar problemas rápidos
- ⚠️ **Informações limitadas**: Menos detalhado que `/health`
- ⚠️ **Sem alertas**: Não fornece informações sobre alertas ativos
- ⚠️ **Polling**: Frontend pode fazer polling excessivo

### Sugestões de melhorias
1. **WebSocket/SSE**: Implementar push de status em tempo real
2. **Níveis de severidade**: Adicionar níveis de criticidade para issues
3. **Métricas de tendência**: Incluir tendências de performance
4. **Alertas ativos**: Integrar com sistema de alertas
5. **Cache inteligente**: Cache mais curto em caso de problemas
6. **Tipagem frontend**: Implementar interface TypeScript completa
7. **Indicadores visuais**: Melhorar indicadores no frontend
8. **Histórico**: Manter histórico de status para análise

## Diferenças com /health

| Aspecto | /status | /health |
|---------|---------|----------|
| **Propósito** | Dashboard frontend | Monitoramento infraestrutura |
| **Detalhamento** | Resumido | Completo |
| **Cache** | 60s | Sem cache |
| **Consumidor** | Frontend | Load balancers, monitoring |
| **Informações** | Essenciais | Técnicas detalhadas |

## Implementações recentes
✅ **Campos de fonte**: Adicionados `data_source` e `is_mock_data`
✅ **Fallback inteligente**: Retorna dados mock quando GLPI indisponível
✅ **Cache otimizado**: Cache de 60s para reduzir carga

## Status de implementação
✅ **Implementado** - Funcional no backend
✅ **Consumido pelo frontend** - Método `getSystemStatus()` implementado
✅ **Com indicadores de fonte** - Campos de identificação implementados
✅ **Cached** - Sistema de cache otimizado
❌ **Sem tipagem frontend** - Interface TypeScript não criada
⚠️ **Sem indicadores visuais** - Frontend não exibe status visualmente
⚠️ **Sem tempo real** - Depende de polling manual