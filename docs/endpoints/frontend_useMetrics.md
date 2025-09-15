# Hook: useMetrics

## Arquivo(s) de origem
- `frontend/hooks/useMetrics.ts`
- `frontend/services/api.ts` (método `getMetrics`)
- `frontend/types/api.ts` (interface `DashboardMetrics`)

## Endpoint consumido
`GET /metrics`

## Descrição técnica
Hook React customizado que gerencia o estado das métricas do dashboard, fornecendo dados consolidados do GLPI com refresh automático e controle de loading/error.

## Parâmetros de entrada
Nenhum parâmetro direto. O hook aceita configurações internas:
- **Refresh automático**: A cada 30 segundos
- **Fetch inicial**: Executado no mount do componente

## Interface do Hook
```typescript
interface UseMetricsReturn {
  data: DashboardMetrics | null;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

function useMetrics(): UseMetricsReturn
```

## Resposta esperada (contract)
```typescript
interface DashboardMetrics {
  niveis: {
    N1: number;
    N2: number;
    N3: number;
    N4: number;
  };
  total: number;
  novos: number;
  pendentes: number;
  progresso: number;
  resolvidos: number;
  data_source: 'glpi' | 'mock' | 'unknown';
  is_mock_data: boolean;
  timestamp: string;
}
```

## Tipagem completa em TypeScript
```typescript
import { useState, useEffect, useCallback } from 'react';
import { apiService } from '../services/api';
import type { DashboardMetrics } from '../types/api';

interface UseMetricsReturn {
  data: DashboardMetrics | null;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

export function useMetrics(): UseMetricsReturn {
  const [data, setData] = useState<DashboardMetrics | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchMetrics = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const metrics = await apiService.getMetrics();
      setData(metrics);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao carregar métricas');
      console.error('Erro ao buscar métricas:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchMetrics();
    
    // Refresh automático a cada 30 segundos
    const interval = setInterval(fetchMetrics, 30000);
    
    return () => clearInterval(interval);
  }, [fetchMetrics]);

  return {
    data,
    loading,
    error,
    refetch: fetchMetrics
  };
}
```

## Dependências

### Hooks React
- `useState` - Gerenciamento de estado local
- `useEffect` - Efeitos colaterais e lifecycle
- `useCallback` - Memoização da função de fetch

### Serviços
- `apiService.getMetrics()` - Chamada HTTP para `/metrics`
- `httpClient` - Cliente HTTP configurado

### Tipos
- `DashboardMetrics` - Interface das métricas
- `UseMetricsReturn` - Interface de retorno do hook

### Variáveis de ambiente
- `VITE_API_URL` - URL base da API (via apiService)
- `VITE_API_TIMEOUT` - Timeout das requisições

## Componentes que consomem
```typescript
// Exemplo de uso em componente
import { useMetrics } from '../hooks/useMetrics';

function DashboardComponent() {
  const { data, loading, error, refetch } = useMetrics();

  if (loading) return <div>Carregando métricas...</div>;
  if (error) return <div>Erro: {error}</div>;
  if (!data) return <div>Nenhum dado disponível</div>;

  return (
    <div>
      <h2>Métricas do Dashboard</h2>
      <p>Total de tickets: {data.total}</p>
      <p>Novos: {data.novos}</p>
      <p>Pendentes: {data.pendentes}</p>
      <p>Em progresso: {data.progresso}</p>
      <p>Resolvidos: {data.resolvidos}</p>
      
      <h3>Por Nível:</h3>
      <ul>
        <li>N1: {data.niveis.N1}</li>
        <li>N2: {data.niveis.N2}</li>
        <li>N3: {data.niveis.N3}</li>
        <li>N4: {data.niveis.N4}</li>
      </ul>
      
      <button onClick={refetch}>Atualizar</button>
      
      {data.is_mock_data && (
        <p style={{color: 'orange'}}>⚠️ Dados simulados</p>
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
✅ **Refresh automático**: Atualização periódica dos dados

### Possíveis problemas
- ⚠️ **Interval fixo**: Refresh de 30s pode ser inadequado
- ⚠️ **Memory leak**: Interval pode vazar se componente desmontar
- ⚠️ **Error recovery**: Não há retry automático em caso de erro
- ⚠️ **Cache**: Não há cache entre re-renders
- ⚠️ **Stale data**: Dados podem ficar obsoletos durante loading

### Sugestões de melhorias

1. **Configurabilidade do refresh**
```typescript
interface UseMetricsOptions {
  refreshInterval?: number;
  autoRefresh?: boolean;
  retryOnError?: boolean;
}

export function useMetrics(options: UseMetricsOptions = {}) {
  const {
    refreshInterval = 30000,
    autoRefresh = true,
    retryOnError = false
  } = options;
  // ...
}
```

2. **Retry automático**
```typescript
const fetchMetrics = useCallback(async (retryCount = 0) => {
  try {
    // ... fetch logic
  } catch (err) {
    if (retryOnError && retryCount < 3) {
      setTimeout(() => fetchMetrics(retryCount + 1), 1000 * (retryCount + 1));
      return;
    }
    setError(err instanceof Error ? err.message : 'Erro ao carregar métricas');
  }
}, [retryOnError]);
```

3. **Cache com SWR ou React Query**
```typescript
import useSWR from 'swr';

export function useMetrics() {
  const { data, error, mutate } = useSWR(
    '/metrics',
    apiService.getMetrics,
    {
      refreshInterval: 30000,
      revalidateOnFocus: true,
      errorRetryCount: 3
    }
  );

  return {
    data,
    loading: !error && !data,
    error: error?.message || null,
    refetch: mutate
  };
}
```

4. **Optimistic updates**
```typescript
const refetch = useCallback(async () => {
  // Manter dados anteriores durante loading
  setLoading(true);
  try {
    const newData = await apiService.getMetrics();
    setData(newData);
    setError(null);
  } catch (err) {
    // Manter dados anteriores em caso de erro
    setError(err instanceof Error ? err.message : 'Erro ao atualizar');
  } finally {
    setLoading(false);
  }
}, []);
```

5. **Cleanup melhorado**
```typescript
useEffect(() => {
  let mounted = true;
  
  const fetchData = async () => {
    try {
      const metrics = await apiService.getMetrics();
      if (mounted) {
        setData(metrics);
        setError(null);
      }
    } catch (err) {
      if (mounted) {
        setError(err instanceof Error ? err.message : 'Erro');
      }
    } finally {
      if (mounted) {
        setLoading(false);
      }
    }
  };

  fetchData();
  const interval = setInterval(fetchData, 30000);
  
  return () => {
    mounted = false;
    clearInterval(interval);
  };
}, []);
```

## Status de implementação
✅ **Hook funcional** - Implementação básica completa
✅ **Tipagem TypeScript** - Interfaces bem definidas
✅ **Error handling** - Tratamento de erros básico
✅ **Loading states** - Estados de carregamento
✅ **Refresh automático** - Atualização periódica
❌ **Configurabilidade** - Opções fixas
❌ **Retry logic** - Sem retry automático
❌ **Cache** - Sem cache entre renders
❌ **Optimistic updates** - Loading substitui dados

## Integração com backend
✅ **Endpoint correto** - Consome `/metrics`
✅ **Tipagem alinhada** - Interface corresponde ao backend
✅ **Error handling** - Trata erros HTTP adequadamente
⚠️ **Timeout** - Depende da configuração do httpClient
⚠️ **Retry** - Sem retry em caso de falha de rede

## Próximos passos
1. **Implementar configurabilidade**: Permitir customização do refresh
2. **Adicionar retry logic**: Retry automático em caso de erro
3. **Considerar SWR/React Query**: Para cache e sincronização
4. **Melhorar cleanup**: Evitar memory leaks
5. **Adicionar testes**: Unit tests para o hook
6. **Optimistic updates**: Manter dados durante loading