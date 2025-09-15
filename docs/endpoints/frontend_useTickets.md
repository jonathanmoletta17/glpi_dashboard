# Hook: useTickets

## Arquivo(s) de origem
- `frontend/hooks/useTickets.ts`
- `frontend/services/api.ts` (método `getNewTickets`)
- `frontend/types/api.ts` (interface para tickets)

## Endpoint consumido
`GET /tickets/new`

## Descrição técnica
Hook React customizado que gerencia o estado dos tickets novos/recentes, fornecendo dados de tickets do GLPI com refresh automático e controle de loading/error.

## Parâmetros de entrada
Nenhum parâmetro direto. O hook aceita configurações internas:
- **Refresh automático**: A cada 45 segundos (intervalo intermediário)
- **Fetch inicial**: Executado no mount do componente

## Interface do Hook
```typescript
interface UseTicketsReturn {
  data: Ticket[] | null;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

function useTickets(): UseTicketsReturn
```

## Resposta esperada (contract)
```typescript
// Interface inferida baseada no endpoint backend
interface Ticket {
  id: number;
  title: string;
  description?: string;
  status: 'new' | 'assigned' | 'pending' | 'solved' | 'closed';
  priority: 'very_low' | 'low' | 'medium' | 'high' | 'very_high';
  category?: string;
  requester: {
    id: number;
    name: string;
    email?: string;
  };
  assigned_to?: {
    id: number;
    name: string;
    level?: 'N1' | 'N2' | 'N3' | 'N4';
  };
  created_at: string;
  updated_at: string;
  due_date?: string;
  data_source: 'glpi' | 'mock' | 'unknown';
  is_mock_data: boolean;
}

// Retorna array de tickets novos
type NewTicketsResponse = Ticket[];
```

## Tipagem completa em TypeScript
```typescript
import { useState, useEffect, useCallback } from 'react';
import { apiService } from '../services/api';

// Interface do ticket (deve ser definida em types/api.ts)
interface Ticket {
  id: number;
  title: string;
  description?: string;
  status: 'new' | 'assigned' | 'pending' | 'solved' | 'closed';
  priority: 'very_low' | 'low' | 'medium' | 'high' | 'very_high';
  category?: string;
  requester: {
    id: number;
    name: string;
    email?: string;
  };
  assigned_to?: {
    id: number;
    name: string;
    level?: 'N1' | 'N2' | 'N3' | 'N4';
  };
  created_at: string;
  updated_at: string;
  due_date?: string;
  data_source: 'glpi' | 'mock' | 'unknown';
  is_mock_data: boolean;
}

interface UseTicketsReturn {
  data: Ticket[] | null;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

export function useTickets(): UseTicketsReturn {
  const [data, setData] = useState<Ticket[] | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchTickets = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const tickets = await apiService.getNewTickets();
      setData(tickets);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao carregar tickets');
      console.error('Erro ao buscar tickets:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchTickets();
    
    // Refresh automático a cada 45 segundos
    const interval = setInterval(fetchTickets, 45000);
    
    return () => clearInterval(interval);
  }, [fetchTickets]);

  return {
    data,
    loading,
    error,
    refetch: fetchTickets
  };
}
```

## Dependências

### Hooks React
- `useState` - Gerenciamento de estado local
- `useEffect` - Efeitos colaterais e lifecycle
- `useCallback` - Memoização da função de fetch

### Serviços
- `apiService.getNewTickets()` - Chamada HTTP para `/tickets/new`
- `httpClient` - Cliente HTTP configurado

### Tipos
- `Ticket` - Interface do ticket (precisa ser definida)
- `UseTicketsReturn` - Interface de retorno do hook

### Variáveis de ambiente
- `VITE_API_URL` - URL base da API (via apiService)
- `VITE_API_TIMEOUT` - Timeout das requisições

## Componentes que consomem
```typescript
// Exemplo de uso em componente
import { useTickets } from '../hooks/useTickets';
import { formatDistanceToNow } from 'date-fns';
import { ptBR } from 'date-fns/locale';

function TicketsComponent() {
  const { data, loading, error, refetch } = useTickets();

  if (loading) return <div>Carregando tickets...</div>;
  if (error) return <div>Erro: {error}</div>;
  if (!data || data.length === 0) return <div>Nenhum ticket novo encontrado</div>;

  const getPriorityColor = (priority: string) => {
    const colors = {
      very_high: '#ff4444',
      high: '#ff8800',
      medium: '#ffbb00',
      low: '#00bb00',
      very_low: '#888888'
    };
    return colors[priority as keyof typeof colors] || '#888888';
  };

  const getStatusBadge = (status: string) => {
    const badges = {
      new: { color: '#007bff', text: 'Novo' },
      assigned: { color: '#28a745', text: 'Atribuído' },
      pending: { color: '#ffc107', text: 'Pendente' },
      solved: { color: '#17a2b8', text: 'Resolvido' },
      closed: { color: '#6c757d', text: 'Fechado' }
    };
    return badges[status as keyof typeof badges] || { color: '#6c757d', text: status };
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <h2>Tickets Novos ({data.length})</h2>
        <button onClick={refetch}>🔄 Atualizar</button>
      </div>
      
      <div className="tickets-grid">
        {data.map((ticket) => {
          const statusBadge = getStatusBadge(ticket.status);
          const priorityColor = getPriorityColor(ticket.priority);
          
          return (
            <div key={ticket.id} className="ticket-card" style={{ border: `2px solid ${priorityColor}` }}>
              <div className="ticket-header">
                <h3>#{ticket.id} - {ticket.title}</h3>
                <span 
                  className="status-badge" 
                  style={{ backgroundColor: statusBadge.color, color: 'white', padding: '2px 8px', borderRadius: '4px' }}
                >
                  {statusBadge.text}
                </span>
              </div>
              
              <div className="ticket-meta">
                <p><strong>Prioridade:</strong> 
                  <span style={{ color: priorityColor, fontWeight: 'bold' }}>
                    {ticket.priority.replace('_', ' ').toUpperCase()}
                  </span>
                </p>
                
                {ticket.category && (
                  <p><strong>Categoria:</strong> {ticket.category}</p>
                )}
                
                <p><strong>Solicitante:</strong> {ticket.requester.name}</p>
                
                {ticket.assigned_to && (
                  <p><strong>Atribuído para:</strong> {ticket.assigned_to.name}
                    {ticket.assigned_to.level && (
                      <span className={`level-badge level-${ticket.assigned_to.level.toLowerCase()}`}>
                        {ticket.assigned_to.level}
                      </span>
                    )}
                  </p>
                )}
                
                <p><strong>Criado:</strong> {formatDistanceToNow(new Date(ticket.created_at), { 
                  addSuffix: true, 
                  locale: ptBR 
                })}</p>
                
                {ticket.due_date && (
                  <p><strong>Prazo:</strong> {formatDistanceToNow(new Date(ticket.due_date), { 
                    addSuffix: true, 
                    locale: ptBR 
                  })}</p>
                )}
              </div>
              
              {ticket.description && (
                <div className="ticket-description">
                  <p><strong>Descrição:</strong></p>
                  <p style={{ fontSize: '0.9em', color: '#666' }}>
                    {ticket.description.length > 100 
                      ? `${ticket.description.substring(0, 100)}...` 
                      : ticket.description
                    }
                  </p>
                </div>
              )}
              
              <div className="ticket-footer">
                {ticket.is_mock_data && (
                  <span style={{ color: 'orange', fontSize: '0.8em' }}>📊 Dados simulados</span>
                )}
                <span style={{ fontSize: '0.8em', color: '#888' }}>
                  Fonte: {ticket.data_source.toUpperCase()}
                </span>
              </div>
            </div>
          );
        })}
      </div>
      
      {data.some(t => t.is_mock_data) && (
        <p style={{ color: 'orange', fontSize: '0.9em', textAlign: 'center', marginTop: '1rem' }}>
          ⚠️ Alguns tickets são dados simulados
        </p>
      )}
    </div>
  );
}
```

## Análise técnica

### Consistência
✅ **Padrão de hooks**: Segue convenções React
✅ **Error handling**: Tratamento adequado de erros
✅ **Loading states**: Estados de carregamento bem gerenciados
✅ **Refresh automático**: Atualização periódica (45s)
✅ **Array handling**: Trata corretamente arrays vazios
⚠️ **Interface não definida**: Tipo `Ticket` precisa ser criado
⚠️ **Tipagem incompleta**: Falta definir interface completa

### Possíveis problemas
- ❌ **Interface ausente**: Tipo `Ticket` não está definido em `types/api.ts`
- ⚠️ **Interval fixo**: Refresh de 45s pode ser inadequado
- ⚠️ **Memory leak**: Interval pode vazar se componente desmontar
- ⚠️ **Error recovery**: Não há retry automático em caso de erro
- ⚠️ **Cache**: Não há cache entre re-renders
- ⚠️ **Filtros**: Não há filtros por status, prioridade, etc.
- ⚠️ **Paginação**: Pode ser problemático com muitos tickets

### Sugestões de melhorias

1. **Definir interface completa**
```typescript
// Em types/api.ts
export interface Ticket {
  id: number;
  title: string;
  description?: string;
  status: TicketStatus;
  priority: TicketPriority;
  category?: string;
  requester: User;
  assigned_to?: Technician;
  created_at: string;
  updated_at: string;
  due_date?: string;
  data_source: DataSource;
  is_mock_data: boolean;
}

export type TicketStatus = 'new' | 'assigned' | 'pending' | 'solved' | 'closed';
export type TicketPriority = 'very_low' | 'low' | 'medium' | 'high' | 'very_high';
export type DataSource = 'glpi' | 'mock' | 'unknown';

export interface User {
  id: number;
  name: string;
  email?: string;
}

export interface Technician extends User {
  level?: 'N1' | 'N2' | 'N3' | 'N4';
}
```

2. **Filtros e configurabilidade**
```typescript
interface UseTicketsOptions {
  refreshInterval?: number;
  autoRefresh?: boolean;
  status?: TicketStatus[];
  priority?: TicketPriority[];
  assignedTo?: number;
  limit?: number;
  sortBy?: 'created_at' | 'updated_at' | 'priority' | 'due_date';
  sortOrder?: 'asc' | 'desc';
}

export function useTickets(options: UseTicketsOptions = {}) {
  const {
    refreshInterval = 45000,
    autoRefresh = true,
    status,
    priority,
    assignedTo,
    limit,
    sortBy = 'created_at',
    sortOrder = 'desc'
  } = options;
  
  const fetchTickets = useCallback(async () => {
    const params = new URLSearchParams();
    if (status?.length) params.append('status', status.join(','));
    if (priority?.length) params.append('priority', priority.join(','));
    if (assignedTo) params.append('assigned_to', assignedTo.toString());
    if (limit) params.append('limit', limit.toString());
    if (sortBy) params.append('sort_by', sortBy);
    if (sortOrder) params.append('sort_order', sortOrder);
    
    const tickets = await apiService.getNewTickets(params.toString());
    setData(tickets);
  }, [status, priority, assignedTo, limit, sortBy, sortOrder]);
  
  // ...
}
```

3. **Filtros locais e busca**
```typescript
interface UseTicketsSearchReturn extends UseTicketsReturn {
  searchTerm: string;
  setSearchTerm: (term: string) => void;
  statusFilter: TicketStatus[];
  setStatusFilter: (statuses: TicketStatus[]) => void;
  priorityFilter: TicketPriority[];
  setPriorityFilter: (priorities: TicketPriority[]) => void;
  filteredCount: number;
}

export function useTicketsSearch(): UseTicketsSearchReturn {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<TicketStatus[]>([]);
  const [priorityFilter, setPriorityFilter] = useState<TicketPriority[]>([]);
  
  const { data: rawData, loading, error, refetch } = useTickets();
  
  const filteredData = useMemo(() => {
    if (!rawData) return null;
    
    return rawData.filter(ticket => {
      const matchesSearch = !searchTerm || 
        ticket.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        ticket.description?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        ticket.requester.name.toLowerCase().includes(searchTerm.toLowerCase());
      
      const matchesStatus = statusFilter.length === 0 || statusFilter.includes(ticket.status);
      const matchesPriority = priorityFilter.length === 0 || priorityFilter.includes(ticket.priority);
      
      return matchesSearch && matchesStatus && matchesPriority;
    });
  }, [rawData, searchTerm, statusFilter, priorityFilter]);
  
  return {
    data: filteredData,
    loading,
    error,
    refetch,
    searchTerm,
    setSearchTerm,
    statusFilter,
    setStatusFilter,
    priorityFilter,
    setPriorityFilter,
    filteredCount: filteredData?.length || 0
  };
}
```

4. **Paginação e ordenação**
```typescript
interface UseTicketsPaginatedReturn extends UseTicketsReturn {
  currentPage: number;
  totalPages: number;
  pageSize: number;
  totalCount: number;
  goToPage: (page: number) => void;
  nextPage: () => void;
  prevPage: () => void;
  sortBy: string;
  sortOrder: 'asc' | 'desc';
  setSorting: (field: string) => void;
}

export function useTicketsPaginated(pageSize = 20): UseTicketsPaginatedReturn {
  const [currentPage, setCurrentPage] = useState(1);
  const [sortBy, setSortBy] = useState('created_at');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  
  const { data: allData, loading, error, refetch } = useTickets();
  
  const sortedData = useMemo(() => {
    if (!allData) return null;
    
    return [...allData].sort((a, b) => {
      const aValue = a[sortBy as keyof Ticket];
      const bValue = b[sortBy as keyof Ticket];
      
      if (typeof aValue === 'string' && typeof bValue === 'string') {
        return sortOrder === 'asc' 
          ? aValue.localeCompare(bValue)
          : bValue.localeCompare(aValue);
      }
      
      if (typeof aValue === 'number' && typeof bValue === 'number') {
        return sortOrder === 'asc' ? aValue - bValue : bValue - aValue;
      }
      
      return 0;
    });
  }, [allData, sortBy, sortOrder]);
  
  const totalPages = Math.ceil((sortedData?.length || 0) / pageSize);
  const startIndex = (currentPage - 1) * pageSize;
  const data = sortedData?.slice(startIndex, startIndex + pageSize) || null;
  
  const setSorting = useCallback((field: string) => {
    if (field === sortBy) {
      setSortOrder(prev => prev === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortOrder('desc');
    }
    setCurrentPage(1); // Reset to first page
  }, [sortBy]);
  
  return {
    data,
    loading,
    error,
    refetch,
    currentPage,
    totalPages,
    pageSize,
    totalCount: sortedData?.length || 0,
    goToPage: (page: number) => setCurrentPage(Math.max(1, Math.min(page, totalPages))),
    nextPage: () => setCurrentPage(prev => Math.min(prev + 1, totalPages)),
    prevPage: () => setCurrentPage(prev => Math.max(prev - 1, 1)),
    sortBy,
    sortOrder,
    setSorting
  };
}
```

5. **Real-time updates com WebSocket**
```typescript
export function useTicketsRealtime() {
  const { data, loading, error, refetch } = useTickets({ autoRefresh: false });
  const [wsConnected, setWsConnected] = useState(false);
  
  useEffect(() => {
    const ws = new WebSocket(`${process.env.VITE_WS_URL}/tickets`);
    
    ws.onopen = () => {
      setWsConnected(true);
      console.log('WebSocket conectado para tickets');
    };
    
    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      
      if (message.type === 'ticket_created' || message.type === 'ticket_updated') {
        refetch(); // Atualizar dados quando houver mudanças
      }
    };
    
    ws.onclose = () => {
      setWsConnected(false);
      console.log('WebSocket desconectado');
    };
    
    ws.onerror = (error) => {
      console.error('Erro no WebSocket:', error);
      setWsConnected(false);
    };
    
    return () => {
      ws.close();
    };
  }, [refetch]);
  
  return {
    data,
    loading,
    error,
    refetch,
    wsConnected
  };
}
```

## Status de implementação
✅ **Hook funcional** - Implementação básica completa
❌ **Tipagem TypeScript** - Interface `Ticket` não definida
✅ **Error handling** - Tratamento de erros básico
✅ **Loading states** - Estados de carregamento
✅ **Refresh automático** - Atualização periódica (45s)
✅ **Array handling** - Trata arrays vazios
❌ **Filtros** - Sem filtros por status/prioridade
❌ **Busca** - Sem busca por título/descrição
❌ **Paginação** - Sem paginação
❌ **Ordenação** - Sem ordenação local
❌ **Real-time** - Sem updates em tempo real

## Integração com backend
✅ **Endpoint correto** - Consome `/tickets/new`
⚠️ **Tipagem alinhada** - Interface precisa ser definida
✅ **Error handling** - Trata erros HTTP adequadamente
⚠️ **Parâmetros** - Não envia parâmetros de filtro
⚠️ **Limit** - Não controla quantidade retornada
⚠️ **Sorting** - Não especifica ordenação

## Próximos passos
1. **CRÍTICO: Definir interface `Ticket`** em `types/api.ts`
2. **Implementar filtros**: Por status, prioridade, técnico
3. **Adicionar busca**: Por título, descrição, solicitante
4. **Implementar paginação**: Para grandes volumes
5. **Real-time updates**: WebSocket ou Server-Sent Events
6. **Ações**: Atribuir, alterar status, comentar
7. **Notificações**: Alertas para tickets urgentes
8. **Export**: Funcionalidades de relatório