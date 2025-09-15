# Hook: useRanking

## Arquivo(s) de origem
- `frontend/hooks/useRanking.ts`
- `frontend/services/api.ts` (método `getTechnicianRanking`)
- `frontend/types/api.ts` (interface `TechnicianRanking`)

## Endpoint consumido
`GET /technicians/ranking`

## Descrição técnica
Hook React customizado que gerencia o estado do ranking de técnicos, fornecendo dados de performance dos técnicos com refresh automático e controle de loading/error.

## Parâmetros de entrada
Nenhum parâmetro direto. O hook aceita configurações internas:
- **Refresh automático**: A cada 60 segundos (maior intervalo que métricas)
- **Fetch inicial**: Executado no mount do componente

## Interface do Hook
```typescript
interface UseRankingReturn {
  data: TechnicianRanking[] | null;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

function useRanking(): UseRankingReturn
```

## Resposta esperada (contract)
```typescript
interface TechnicianRanking {
  id: number;
  name: string;
  level: 'N1' | 'N2' | 'N3' | 'N4' | 'UNKNOWN';
  ticket_count: number;
  performance_score: number;
  data_source: 'glpi' | 'mock' | 'unknown';
  is_mock_data: boolean;
}

// Retorna array de técnicos ordenados por performance
type RankingResponse = TechnicianRanking[];
```

## Tipagem completa em TypeScript
```typescript
import { useState, useEffect, useCallback } from 'react';
import { apiService } from '../services/api';
import type { TechnicianRanking } from '../types/api';

interface UseRankingReturn {
  data: TechnicianRanking[] | null;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

export function useRanking(): UseRankingReturn {
  const [data, setData] = useState<TechnicianRanking[] | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchRanking = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const ranking = await apiService.getTechnicianRanking();
      setData(ranking);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao carregar ranking');
      console.error('Erro ao buscar ranking:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchRanking();
    
    // Refresh automático a cada 60 segundos
    const interval = setInterval(fetchRanking, 60000);
    
    return () => clearInterval(interval);
  }, [fetchRanking]);

  return {
    data,
    loading,
    error,
    refetch: fetchRanking
  };
}
```

## Dependências

### Hooks React
- `useState` - Gerenciamento de estado local
- `useEffect` - Efeitos colaterais e lifecycle
- `useCallback` - Memoização da função de fetch

### Serviços
- `apiService.getTechnicianRanking()` - Chamada HTTP para `/technicians/ranking`
- `httpClient` - Cliente HTTP configurado

### Tipos
- `TechnicianRanking` - Interface do técnico no ranking
- `UseRankingReturn` - Interface de retorno do hook

### Variáveis de ambiente
- `VITE_API_URL` - URL base da API (via apiService)
- `VITE_API_TIMEOUT` - Timeout das requisições

## Componentes que consomem
```typescript
// Exemplo de uso em componente
import { useRanking } from '../hooks/useRanking';

function RankingComponent() {
  const { data, loading, error, refetch } = useRanking();

  if (loading) return <div>Carregando ranking...</div>;
  if (error) return <div>Erro: {error}</div>;
  if (!data || data.length === 0) return <div>Nenhum técnico encontrado</div>;

  return (
    <div>
      <h2>Ranking de Técnicos</h2>
      <button onClick={refetch}>Atualizar Ranking</button>
      
      <table>
        <thead>
          <tr>
            <th>Posição</th>
            <th>Nome</th>
            <th>Nível</th>
            <th>Tickets</th>
            <th>Score</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {data.map((technician, index) => (
            <tr key={technician.id}>
              <td>{index + 1}º</td>
              <td>{technician.name}</td>
              <td>
                <span className={`level-badge level-${technician.level.toLowerCase()}`}>
                  {technician.level}
                </span>
              </td>
              <td>{technician.ticket_count}</td>
              <td>{technician.performance_score.toFixed(2)}</td>
              <td>
                {technician.is_mock_data ? (
                  <span style={{color: 'orange'}}>📊 Mock</span>
                ) : (
                  <span style={{color: 'green'}}>✅ GLPI</span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      
      {data.some(t => t.is_mock_data) && (
        <p style={{color: 'orange', fontSize: '0.9em'}}>
          ⚠️ Alguns dados são simulados
        </p>
      )}
    </div>
  );
}
```

## Análise técnica

### Consistência
✅ **Interface bem definida**: Tipagem TypeScript completa
✅ **Padrão de hooks**: Segue convenções React
✅ **Error handling**: Tratamento adequado de erros
✅ **Loading states**: Estados de carregamento bem gerenciados
✅ **Refresh automático**: Atualização periódica (60s)
✅ **Array handling**: Trata corretamente arrays vazios

### Possíveis problemas
- ⚠️ **Interval fixo**: Refresh de 60s pode ser inadequado
- ⚠️ **Memory leak**: Interval pode vazar se componente desmontar
- ⚠️ **Error recovery**: Não há retry automático em caso de erro
- ⚠️ **Cache**: Não há cache entre re-renders
- ⚠️ **Sorting**: Depende do backend para ordenação
- ⚠️ **Filtering**: Não há filtros por nível ou performance

### Sugestões de melhorias

1. **Configurabilidade e filtros**
```typescript
interface UseRankingOptions {
  refreshInterval?: number;
  autoRefresh?: boolean;
  limit?: number;
  level?: 'N1' | 'N2' | 'N3' | 'N4';
  sortBy?: 'performance_score' | 'ticket_count' | 'name';
  sortOrder?: 'asc' | 'desc';
}

export function useRanking(options: UseRankingOptions = {}) {
  const {
    refreshInterval = 60000,
    autoRefresh = true,
    limit,
    level,
    sortBy = 'performance_score',
    sortOrder = 'desc'
  } = options;
  
  const fetchRanking = useCallback(async () => {
    const params = new URLSearchParams();
    if (limit) params.append('limit', limit.toString());
    if (level) params.append('level', level);
    if (sortBy) params.append('sort_by', sortBy);
    if (sortOrder) params.append('sort_order', sortOrder);
    
    const ranking = await apiService.getTechnicianRanking(params.toString());
    setData(ranking);
  }, [limit, level, sortBy, sortOrder]);
  
  // ...
}
```

2. **Filtros locais**
```typescript
export function useRanking(options: UseRankingOptions = {}) {
  const [data, setData] = useState<TechnicianRanking[] | null>(null);
  const [filteredData, setFilteredData] = useState<TechnicianRanking[] | null>(null);
  
  const applyFilters = useCallback((rawData: TechnicianRanking[]) => {
    let filtered = [...rawData];
    
    if (options.level) {
      filtered = filtered.filter(t => t.level === options.level);
    }
    
    if (options.minScore) {
      filtered = filtered.filter(t => t.performance_score >= options.minScore!);
    }
    
    // Ordenação local
    filtered.sort((a, b) => {
      const field = options.sortBy || 'performance_score';
      const order = options.sortOrder === 'asc' ? 1 : -1;
      return (a[field] - b[field]) * order;
    });
    
    if (options.limit) {
      filtered = filtered.slice(0, options.limit);
    }
    
    return filtered;
  }, [options]);
  
  useEffect(() => {
    if (data) {
      setFilteredData(applyFilters(data));
    }
  }, [data, applyFilters]);
  
  return {
    data: filteredData,
    rawData: data,
    // ...
  };
}
```

3. **Paginação**
```typescript
interface UseRankingPaginatedReturn extends UseRankingReturn {
  currentPage: number;
  totalPages: number;
  pageSize: number;
  goToPage: (page: number) => void;
  nextPage: () => void;
  prevPage: () => void;
}

export function useRankingPaginated(pageSize = 10): UseRankingPaginatedReturn {
  const [currentPage, setCurrentPage] = useState(1);
  const { data: allData, loading, error, refetch } = useRanking();
  
  const totalPages = Math.ceil((allData?.length || 0) / pageSize);
  const startIndex = (currentPage - 1) * pageSize;
  const data = allData?.slice(startIndex, startIndex + pageSize) || null;
  
  const goToPage = useCallback((page: number) => {
    setCurrentPage(Math.max(1, Math.min(page, totalPages)));
  }, [totalPages]);
  
  return {
    data,
    loading,
    error,
    refetch,
    currentPage,
    totalPages,
    pageSize,
    goToPage,
    nextPage: () => goToPage(currentPage + 1),
    prevPage: () => goToPage(currentPage - 1)
  };
}
```

4. **Busca e filtros avançados**
```typescript
interface UseRankingSearchReturn extends UseRankingReturn {
  searchTerm: string;
  setSearchTerm: (term: string) => void;
  levelFilter: string;
  setLevelFilter: (level: string) => void;
  sortConfig: { field: string; direction: 'asc' | 'desc' };
  setSortConfig: (config: { field: string; direction: 'asc' | 'desc' }) => void;
}

export function useRankingSearch(): UseRankingSearchReturn {
  const [searchTerm, setSearchTerm] = useState('');
  const [levelFilter, setLevelFilter] = useState('');
  const [sortConfig, setSortConfig] = useState({ field: 'performance_score', direction: 'desc' as const });
  
  const { data: rawData, loading, error, refetch } = useRanking();
  
  const filteredData = useMemo(() => {
    if (!rawData) return null;
    
    let filtered = rawData.filter(technician => {
      const matchesSearch = technician.name.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesLevel = !levelFilter || technician.level === levelFilter;
      return matchesSearch && matchesLevel;
    });
    
    // Ordenação
    filtered.sort((a, b) => {
      const aValue = a[sortConfig.field as keyof TechnicianRanking];
      const bValue = b[sortConfig.field as keyof TechnicianRanking];
      
      if (typeof aValue === 'string' && typeof bValue === 'string') {
        return sortConfig.direction === 'asc' 
          ? aValue.localeCompare(bValue)
          : bValue.localeCompare(aValue);
      }
      
      if (typeof aValue === 'number' && typeof bValue === 'number') {
        return sortConfig.direction === 'asc' 
          ? aValue - bValue
          : bValue - aValue;
      }
      
      return 0;
    });
    
    return filtered;
  }, [rawData, searchTerm, levelFilter, sortConfig]);
  
  return {
    data: filteredData,
    loading,
    error,
    refetch,
    searchTerm,
    setSearchTerm,
    levelFilter,
    setLevelFilter,
    sortConfig,
    setSortConfig
  };
}
```

5. **Comparação e analytics**
```typescript
interface RankingAnalytics {
  totalTechnicians: number;
  averageScore: number;
  topPerformer: TechnicianRanking | null;
  levelDistribution: Record<string, number>;
  scoreDistribution: {
    excellent: number; // > 90
    good: number;      // 70-90
    average: number;   // 50-70
    poor: number;      // < 50
  };
}

export function useRankingAnalytics(): RankingAnalytics | null {
  const { data } = useRanking();
  
  return useMemo(() => {
    if (!data || data.length === 0) return null;
    
    const totalTechnicians = data.length;
    const averageScore = data.reduce((sum, t) => sum + t.performance_score, 0) / totalTechnicians;
    const topPerformer = data[0]; // Assumindo que já vem ordenado
    
    const levelDistribution = data.reduce((acc, t) => {
      acc[t.level] = (acc[t.level] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);
    
    const scoreDistribution = data.reduce((acc, t) => {
      if (t.performance_score > 90) acc.excellent++;
      else if (t.performance_score > 70) acc.good++;
      else if (t.performance_score > 50) acc.average++;
      else acc.poor++;
      return acc;
    }, { excellent: 0, good: 0, average: 0, poor: 0 });
    
    return {
      totalTechnicians,
      averageScore,
      topPerformer,
      levelDistribution,
      scoreDistribution
    };
  }, [data]);
}
```

## Status de implementação
✅ **Hook funcional** - Implementação básica completa
✅ **Tipagem TypeScript** - Interfaces bem definidas
✅ **Error handling** - Tratamento de erros básico
✅ **Loading states** - Estados de carregamento
✅ **Refresh automático** - Atualização periódica (60s)
✅ **Array handling** - Trata arrays vazios
❌ **Filtros** - Sem filtros por nível/performance
❌ **Busca** - Sem busca por nome
❌ **Paginação** - Sem paginação
❌ **Ordenação local** - Depende do backend
❌ **Analytics** - Sem métricas derivadas

## Integração com backend
✅ **Endpoint correto** - Consome `/technicians/ranking`
✅ **Tipagem alinhada** - Interface corresponde ao backend
✅ **Error handling** - Trata erros HTTP adequadamente
⚠️ **Parâmetros** - Não envia parâmetros de filtro
⚠️ **Limit** - Não controla quantidade retornada
⚠️ **Sorting** - Não especifica ordenação

## Próximos passos
1. **Implementar filtros**: Por nível, score mínimo, etc.
2. **Adicionar busca**: Por nome do técnico
3. **Implementar paginação**: Para grandes volumes
4. **Analytics derivadas**: Métricas e distribuições
5. **Comparação temporal**: Evolução do ranking
6. **Export/Share**: Funcionalidades de compartilhamento