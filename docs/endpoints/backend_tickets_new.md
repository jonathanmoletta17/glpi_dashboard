# Endpoint: /tickets/new

## Arquivo(s) de origem
- `backend/api/routes.py` (linha ~900-1000)
- `frontend/services/api.ts` (método `getNewTickets`)
- `frontend/hooks/useTickets.ts`

## Método HTTP
`GET`

## Descrição técnica
Endpoint que retorna a lista de tickets novos/recentes do GLPI, com informações sobre fonte de dados e indicadores visuais para identificação da origem dos dados.

## Parâmetros de entrada

| Nome | Tipo | Obrigatório | Exemplo | Descrição |
|------|------|-------------|---------|----------|
| `limit` | integer | Não | `20` | Número máximo de tickets a retornar (padrão: 10) |
| `status` | string | Não | `new` | Filtrar por status específico |
| `priority` | string | Não | `high` | Filtrar por prioridade |
| `assigned_to` | integer | Não | `123` | ID do técnico responsável |

## Resposta esperada (contract)
```json
{
  "success": true,
  "data": [
    {
      "id": 12345,
      "title": "Impressora não funciona - Setor Financeiro",
      "description": "A impressora HP do setor financeiro parou de funcionar após atualização",
      "status": "new",
      "priority": "medium",
      "category": "Hardware",
      "requester": {
        "id": 456,
        "name": "Ana Silva",
        "email": "ana.silva@empresa.com"
      },
      "assigned_to": {
        "id": 789,
        "name": "João Santos",
        "level": "N1"
      },
      "created_at": "2025-01-27T08:30:00Z",
      "updated_at": "2025-01-27T08:30:00Z",
      "due_date": "2025-01-29T17:00:00Z",
      "data_source": "glpi",
      "is_mock_data": false
    },
    {
      "id": 12346,
      "title": "Acesso negado ao sistema ERP",
      "description": "Usuário não consegue acessar o sistema ERP desde ontem",
      "status": "new",
      "priority": "high",
      "category": "Software",
      "requester": {
        "id": 457,
        "name": "Carlos Oliveira",
        "email": "carlos.oliveira@empresa.com"
      },
      "assigned_to": null,
      "created_at": "2025-01-27T09:15:00Z",
      "updated_at": "2025-01-27T09:15:00Z",
      "due_date": "2025-01-27T17:00:00Z",
      "data_source": "glpi",
      "is_mock_data": false
    }
  ],
  "total_count": 45,
  "cached": true,
  "response_time_ms": 89.3,
  "correlation_id": "req_456789123",
  "filters_applied": {
    "limit": 20,
    "status": "new"
  }
}
```

## Tipagem equivalente em TypeScript
```typescript
interface TicketRequester {
  id: number;
  name: string;
  email: string;
}

interface TicketAssignee {
  id: number;
  name: string;
  level: 'N1' | 'N2' | 'N3' | 'N4';
}

interface NewTicket {
  id: number;
  title: string;
  description: string;
  status: 'new' | 'assigned' | 'pending' | 'solved' | 'closed';
  priority: 'very_low' | 'low' | 'medium' | 'high' | 'very_high';
  category: string;
  requester: TicketRequester;
  assigned_to: TicketAssignee | null;
  created_at: string;
  updated_at: string;
  due_date: string | null;
  
  // Campos de identificação de fonte (obrigatórios)
  data_source: 'glpi' | 'unknown' | 'mock';
  is_mock_data: boolean;
}

interface NewTicketsResponse {
  success: boolean;
  data: NewTicket[];
  total_count: number;
  cached: boolean;
  response_time_ms: number;
  correlation_id: string;
  filters_applied: {
    limit: number;
    status?: string;
    priority?: string;
    assigned_to?: number;
  };
}
```

## Dependências

### Backend
- `GLPIServiceFacade` - Busca tickets do GLPI
- `TicketService` - Processamento e formatação de tickets
- `unified_cache` - Sistema de cache Redis
- `ResponseFormatter` - Formatação de respostas
- `safe_int_param`, `safe_string_param` - Validação de parâmetros

### Frontend
- **Hook**: `useTickets.ts`
- **Service**: `apiService.getNewTickets()`
- **Componente**: Usado no componente de lista de tickets
- **Tipos**: `NewTicket` em `types/api.ts`

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
✅ **Tratamento de nulos**: Campo `assigned_to` pode ser null

### Possíveis problemas
- ⚠️ **Performance**: Busca de tickets pode ser lenta para grandes volumes
- ⚠️ **Paginação**: Falta paginação adequada para muitos tickets
- ⚠️ **Filtros limitados**: Poucos filtros disponíveis
- ⚠️ **Dados sensíveis**: Emails dos usuários são expostos

### Sugestões de melhorias
1. **Paginação completa**: Implementar paginação com offset/cursor
2. **Filtros avançados**: Adicionar filtros por:
   - Data de criação (range)
   - Departamento/setor
   - Tipo de equipamento
   - SLA restante
3. **Ordenação**: Permitir ordenação por prioridade, data, SLA
4. **Campos opcionais**: Tornar alguns campos opcionais para reduzir payload
5. **Privacidade**: Mascarar ou omitir emails sensíveis
6. **Cache inteligente**: Invalidar cache quando novos tickets são criados
7. **Validação robusta**: Usar Pydantic para validação de entrada
8. **Métricas de SLA**: Adicionar informações sobre tempo restante

## Implementações recentes
✅ **Campos de fonte**: Adicionados `data_source` e `is_mock_data`
✅ **Indicadores visuais**: Frontend pode exibir badges coloridos para fonte
✅ **Tratamento de erros**: Fallback para dados padrão em caso de falha

## Status de implementação
✅ **Totalmente implementado** - Backend e frontend funcionais
✅ **Bem tipado** - Interfaces TypeScript completas
✅ **Testado** - Endpoint validado e funcionando
✅ **Com indicadores de fonte** - Campos de identificação implementados
✅ **Cached** - Sistema de cache implementado
⚠️ **Paginação pendente** - Necessita implementação de paginação robusta