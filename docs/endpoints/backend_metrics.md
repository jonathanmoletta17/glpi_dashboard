# Endpoint: /metrics

## Arquivo(s) de origem
- `backend/api/routes.py` (linha ~120-200)
- `frontend/services/api.ts` (método `getMetrics`)
- `frontend/hooks/useMetrics.ts`

## Método HTTP
`GET`

## Descrição técnica
Endpoint principal que retorna métricas consolidadas do dashboard GLPI, incluindo contadores por nível de suporte (N1-N4), totais gerais, tendências e informações de fonte de dados.

## Parâmetros de entrada

| Nome | Tipo | Obrigatório | Exemplo | Descrição |
|------|------|-------------|---------|----------|
| `start_date` | string | Não | `2025-01-01` | Data inicial para filtro (formato YYYY-MM-DD) |
| `end_date` | string | Não | `2025-01-31` | Data final para filtro (formato YYYY-MM-DD) |
| `filter_type` | string | Não | `creation` | Tipo de filtro: `creation`, `modification`, `current_status` |

## Resposta esperada (contract)
```json
{
  "success": true,
  "data": {
    "niveis": {
      "n1": {
        "novos": 45,
        "pendentes": 23,
        "progresso": 12,
        "resolvidos": 156,
        "total": 236
      },
      "n2": {
        "novos": 12,
        "pendentes": 8,
        "progresso": 5,
        "resolvidos": 89,
        "total": 114
      },
      "n3": {
        "novos": 3,
        "pendentes": 2,
        "progresso": 1,
        "resolvidos": 34,
        "total": 40
      },
      "n4": {
        "novos": 1,
        "pendentes": 0,
        "progresso": 0,
        "resolvidos": 12,
        "total": 13
      }
    },
    "total": 403,
    "novos": 61,
    "pendentes": 33,
    "progresso": 18,
    "resolvidos": 291,
    "tendencias": {
      "novos": "+12%",
      "pendentes": "-5%",
      "progresso": "+8%",
      "resolvidos": "+15%"
    },
    "data_source": "glpi",
    "is_mock_data": false,
    "timestamp": "2025-01-27T10:30:00Z",
    "period_start": "2025-01-01T00:00:00Z",
    "period_end": "2025-01-31T23:59:59Z"
  },
  "cached": true,
  "response_time_ms": 45.2,
  "correlation_id": "req_123456789"
}
```

## Tipagem equivalente em TypeScript
```typescript
interface LevelMetrics {
  novos: number;
  pendentes: number;
  progresso: number;
  resolvidos: number;
  total: number;
}

interface NiveisMetrics {
  n1: LevelMetrics;
  n2: LevelMetrics;
  n3: LevelMetrics;
  n4: LevelMetrics;
}

interface DashboardMetrics {
  niveis: NiveisMetrics;
  total: number;
  novos: number;
  pendentes: number;
  progresso: number;
  resolvidos: number;
  tendencias: {
    novos: string;
    pendentes: string;
    progresso: string;
    resolvidos: string;
  };
  timestamp: string;
  period_start?: string;
  period_end?: string;
  data_source: 'glpi' | 'mock';
  is_mock_data: boolean;
}
```

## Dependências

### Backend
- `GLPIServiceFacade` - Busca dados do GLPI
- `unified_cache` - Sistema de cache Redis
- `ResponseFormatter` - Formatação de respostas
- `performance_monitor` - Monitoramento de performance

### Frontend
- **Hook**: `useMetrics.ts`
- **Service**: `apiService.getMetrics()`
- **Componente**: Usado no dashboard principal

### Variáveis de ambiente
- `GLPI_URL` - URL da API GLPI
- `GLPI_USER_TOKEN` - Token de usuário GLPI
- `GLPI_APP_TOKEN` - Token da aplicação GLPI
- `CACHE_DEFAULT_TIMEOUT` - Timeout do cache (padrão: 300s)

## Análise técnica

### Consistência
✅ **Excelente**: Perfeita consistência entre backend e frontend
✅ **Tipagem completa**: Interface TypeScript bem definida
✅ **Tratamento de erros**: Fallback para dados padrão

### Possíveis problemas
- ⚠️ **Complexidade de resposta**: Estrutura aninhada pode ser confusa
- ⚠️ **Cache**: Dependência do Redis pode causar falhas
- ⚠️ **Performance**: Consultas GLPI podem ser lentas

### Sugestões de melhorias
1. **DTO específico**: Criar DTO Pydantic para validação de entrada
2. **Paginação**: Adicionar suporte a paginação para grandes volumes
3. **Filtros avançados**: Expandir opções de filtro (por técnico, categoria)
4. **Cache inteligente**: Implementar invalidação seletiva de cache
5. **Documentação OpenAPI**: Melhorar documentação dos parâmetros
6. **Métricas de performance**: Adicionar métricas de tempo de resposta

## Status de implementação
✅ **Totalmente implementado** - Backend e frontend funcionais
✅ **Bem tipado** - Interfaces TypeScript completas
✅ **Testado** - Endpoint validado e funcionando
✅ **Cached** - Sistema de cache implementado