# Endpoint: /technicians/ranking

## Arquivo(s) de origem
- `backend/api/routes.py` (linha ~600-700)
- `frontend/services/api.ts` (método `getTechnicianRanking`)
- `frontend/hooks/useRanking.ts`

## Método HTTP
`GET`

## Descrição técnica
Endpoint que retorna o ranking de técnicos baseado em performance e quantidade de tickets resolvidos, com informações sobre fonte de dados e indicadores visuais.

## Parâmetros de entrada

| Nome | Tipo | Obrigatório | Exemplo | Descrição |
|------|------|-------------|---------|----------|
| `limit` | integer | Não | `10` | Número máximo de técnicos no ranking (padrão: 10) |
| `start_date` | string | Não | `2025-01-01` | Data inicial para cálculo do ranking |
| `end_date` | string | Não | `2025-01-31` | Data final para cálculo do ranking |
| `level` | string | Não | `N1` | Filtrar por nível específico (N1, N2, N3, N4) |

## Resposta esperada (contract)
```json
{
  "success": true,
  "data": [
    {
      "id": 123,
      "name": "João Silva",
      "level": "N1",
      "ticket_count": 45,
      "performance_score": 87.5,
      "data_source": "glpi",
      "is_mock_data": false
    },
    {
      "id": 456,
      "name": "Maria Santos",
      "level": "N2",
      "ticket_count": 38,
      "performance_score": 92.1,
      "data_source": "glpi",
      "is_mock_data": false
    },
    {
      "id": 789,
      "name": "Pedro Costa",
      "level": "N1",
      "ticket_count": 42,
      "performance_score": 85.3,
      "data_source": "unknown",
      "is_mock_data": false
    }
  ],
  "cached": false,
  "response_time_ms": 156.7,
  "correlation_id": "req_987654321",
  "filters_applied": {
    "limit": 10,
    "start_date": "2025-01-01",
    "end_date": "2025-01-31"
  }
}
```

## Tipagem equivalente em TypeScript
```typescript
interface TechnicianRanking {
  id: number;
  name: string;
  level: 'N1' | 'N2' | 'N3' | 'N4' | 'UNKNOWN';
  ticket_count: number;
  performance_score?: number;
  
  // Campos de identificação de fonte (obrigatórios)
  data_source: 'glpi' | 'unknown' | 'mock';
  is_mock_data: boolean;
  
  // Campos de compatibilidade (deprecated)
  rank?: number;
  total?: number;
}

interface RankingResponse {
  success: boolean;
  data: TechnicianRanking[];
  cached: boolean;
  response_time_ms: number;
  correlation_id: string;
  filters_applied: {
    limit: number;
    start_date?: string;
    end_date?: string;
    level?: string;
  };
}
```

## Dependências

### Backend
- `GLPIServiceFacade` - Busca dados de técnicos do GLPI
- `TechnicianPerformanceService` - Cálculo de performance
- `unified_cache` - Sistema de cache Redis
- `ResponseFormatter` - Formatação de respostas
- `safe_int_param`, `safe_string_param` - Validação de parâmetros

### Frontend
- **Hook**: `useRanking.ts`
- **Service**: `apiService.getTechnicianRanking()`
- **Componente**: Usado no componente de ranking do dashboard
- **Tipos**: `TechnicianRanking` em `types/api.ts`

### Variáveis de ambiente
- `GLPI_URL` - URL da API GLPI
- `GLPI_USER_TOKEN` - Token de usuário GLPI
- `GLPI_APP_TOKEN` - Token da aplicação GLPI
- `CACHE_DEFAULT_TIMEOUT` - Timeout do cache

## Análise técnica

### Consistência
✅ **Excelente**: Perfeita consistência entre backend e frontend
✅ **Tipagem completa**: Interface TypeScript bem definida
✅ **Campos de fonte**: Implementação correta de `data_source` e `is_mock_data`
✅ **Indicadores visuais**: Frontend exibe badges coloridos para fonte de dados

### Possíveis problemas
- ⚠️ **Performance**: Cálculo de ranking pode ser custoso para muitos técnicos
- ⚠️ **Dados inconsistentes**: Campo `data_source` pode ser 'unknown' em alguns casos
- ⚠️ **Cache**: Ranking pode ficar desatualizado com cache longo

### Sugestões de melhorias
1. **Paginação**: Implementar paginação para rankings grandes
2. **Ordenação**: Permitir ordenação por diferentes critérios (nome, tickets, score)
3. **Filtros avançados**: Adicionar filtros por departamento, período personalizado
4. **Métricas detalhadas**: Incluir tempo médio de resolução, satisfação do cliente
5. **Cache inteligente**: Invalidar cache quando dados de tickets são atualizados
6. **Validação de entrada**: Usar Pydantic para validação de parâmetros
7. **Documentação**: Melhorar documentação do cálculo de performance_score

## Implementações recentes
✅ **Campos de fonte**: Adicionados `data_source` e `is_mock_data`
✅ **Indicadores visuais**: Frontend exibe badges coloridos:
- 🟢 GLPI (verde)
- 🟡 UNKNOWN (amarelo) 
- 🔴 MOCK (vermelho)

## Status de implementação
✅ **Totalmente implementado** - Backend e frontend funcionais
✅ **Bem tipado** - Interfaces TypeScript completas
✅ **Testado** - Endpoint validado e funcionando
✅ **Com indicadores visuais** - Frontend exibe fonte de dados
✅ **Cached** - Sistema de cache implementado