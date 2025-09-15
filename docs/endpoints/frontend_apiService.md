# Serviço: apiService

## Arquivo(s) de origem
- `frontend/services/api.ts`
- `frontend/services/httpClient.ts` (cliente HTTP base)
- `frontend/config/appConfig.ts` (configurações)

## Descrição técnica
Serviço centralizado que encapsula todas as chamadas HTTP para a API do backend, fornecendo métodos tipados e tratamento de erros consistente.

## Métodos disponíveis

### 1. getMetrics()
**Endpoint**: `GET /metrics`
**Descrição**: Obtém métricas consolidadas do dashboard

```typescript
async getMetrics(): Promise<DashboardMetrics> {
  const response = await httpClient.get<DashboardMetrics>('/metrics');
  return response.data;
}
```

### 2. getTechnicianRanking()
**Endpoint**: `GET /technicians/ranking`
**Descrição**: Obtém ranking de técnicos por performance

```typescript
async getTechnicianRanking(): Promise<TechnicianRanking[]> {
  const response = await httpClient.get<TechnicianRanking[]>('/technicians/ranking');
  return response.data;
}
```

### 3. getNewTickets()
**Endpoint**: `GET /tickets/new`
**Descrição**: Obtém lista de tickets novos/recentes

```typescript
async getNewTickets(): Promise<Ticket[]> {
  const response = await httpClient.get<Ticket[]>('/tickets/new');
  return response.data;
}
```

### 4. getSystemStatus()
**Endpoint**: `GET /status`
**Descrição**: Obtém status do sistema e conectividade

```typescript
async getSystemStatus(): Promise<SystemStatus> {
  const response = await httpClient.get<SystemStatus>('/status');
  return response.data;
}
```

## Implementação completa

```typescript
import { httpClient } from './httpClient';
import type { 
  DashboardMetrics, 
  TechnicianRanking, 
  Ticket, 
  SystemStatus 
} from '../types/api';

class ApiService {
  /**
   * Obtém métricas consolidadas do dashboard
   */
  async getMetrics(): Promise<DashboardMetrics> {
    try {
      const response = await httpClient.get<DashboardMetrics>('/metrics');
      return response.data;
    } catch (error) {
      console.error('Erro ao buscar métricas:', error);
      throw this.handleError(error, 'Falha ao carregar métricas do dashboard');
    }
  }

  /**
   * Obtém ranking de técnicos por performance
   * @param params - Parâmetros de filtro opcionais
   */
  async getTechnicianRanking(params?: string): Promise<TechnicianRanking[]> {
    try {
      const url = params ? `/technicians/ranking?${params}` : '/technicians/ranking';
      const response = await httpClient.get<TechnicianRanking[]>(url);
      return response.data;
    } catch (error) {
      console.error('Erro ao buscar ranking:', error);
      throw this.handleError(error, 'Falha ao carregar ranking de técnicos');
    }
  }

  /**
   * Obtém lista de tickets novos/recentes
   * @param params - Parâmetros de filtro opcionais
   */
  async getNewTickets(params?: string): Promise<Ticket[]> {
    try {
      const url = params ? `/tickets/new?${params}` : '/tickets/new';
      const response = await httpClient.get<Ticket[]>(url);
      return response.data;
    } catch (error) {
      console.error('Erro ao buscar tickets:', error);
      throw this.handleError(error, 'Falha ao carregar tickets');
    }
  }

  /**
   * Obtém status do sistema e conectividade
   */
  async getSystemStatus(): Promise<SystemStatus> {
    try {
      const response = await httpClient.get<SystemStatus>('/status');
      return response.data;
    } catch (error) {
      console.error('Erro ao buscar status:', error);
      throw this.handleError(error, 'Falha ao verificar status do sistema');
    }
  }

  /**
   * Função auxiliar para criar dados padrão em caso de falha
   */
  createDefaultMetrics(): DashboardMetrics {
    return {
      niveis: { N1: 0, N2: 0, N3: 0, N4: 0 },
      total: 0,
      novos: 0,
      pendentes: 0,
      progresso: 0,
      resolvidos: 0,
      data_source: 'unknown',
      is_mock_data: true,
      timestamp: new Date().toISOString()
    };
  }

  /**
   * Tratamento centralizado de erros
   */
  private handleError(error: any, defaultMessage: string): Error {
    if (error.response) {
      // Erro HTTP com resposta do servidor
      const status = error.response.status;
      const message = error.response.data?.message || error.response.data?.error || defaultMessage;
      
      switch (status) {
        case 400:
          return new Error(`Requisição inválida: ${message}`);
        case 401:
          return new Error('Não autorizado. Verifique suas credenciais.');
        case 403:
          return new Error('Acesso negado. Permissões insuficientes.');
        case 404:
          return new Error('Recurso não encontrado.');
        case 429:
          return new Error('Muitas requisições. Tente novamente em alguns segundos.');
        case 500:
          return new Error('Erro interno do servidor. Tente novamente mais tarde.');
        case 502:
        case 503:
        case 504:
          return new Error('Serviço temporariamente indisponível.');
        default:
          return new Error(`Erro HTTP ${status}: ${message}`);
      }
    } else if (error.request) {
      // Erro de rede (sem resposta)
      return new Error('Erro de conexão. Verifique sua internet e tente novamente.');
    } else {
      // Erro na configuração da requisição
      return new Error(error.message || defaultMessage);
    }
  }
}

// Instância singleton
export const apiService = new ApiService();
export default apiService;
```

## Dependências

### Cliente HTTP
- `httpClient` - Cliente Axios configurado
- **Interceptadores**: Request/Response interceptors
- **Timeout**: Configuração de timeout
- **Base URL**: URL base da API

### Tipos TypeScript
- `DashboardMetrics` - Interface das métricas
- `TechnicianRanking` - Interface do ranking
- `Ticket` - Interface dos tickets (precisa ser definida)
- `SystemStatus` - Interface do status (precisa ser definida)

### Configurações
- `VITE_API_URL` - URL base da API
- `VITE_API_TIMEOUT` - Timeout das requisições
- `VITE_API_RETRY_ATTEMPTS` - Tentativas de retry

## Análise técnica

### Pontos fortes
✅ **Centralização**: Todas as chamadas HTTP em um local
✅ **Tipagem**: Métodos tipados com TypeScript
✅ **Error handling**: Tratamento de erros básico
✅ **Singleton**: Instância única reutilizável
✅ **Logging**: Console.error para debugging
✅ **Fallback**: Método createDefaultMetrics

### Possíveis problemas
- ⚠️ **Tipos incompletos**: `Ticket` e `SystemStatus` não definidos
- ⚠️ **Error handling básico**: Poderia ser mais robusto
- ⚠️ **Sem retry**: Não há retry automático
- ⚠️ **Sem cache**: Não há cache de respostas
- ⚠️ **Sem interceptadores específicos**: Apenas os do httpClient
- ⚠️ **Parâmetros limitados**: Métodos não aceitam parâmetros complexos

### Sugestões de melhorias

1. **Definir interfaces completas**
```typescript
// Em types/api.ts
export interface SystemStatus {
  status: 'healthy' | 'degraded' | 'down';
  glpi_connection: boolean;
  database_connection: boolean;
  last_sync: string;
  uptime: number;
  version: string;
  environment: 'development' | 'staging' | 'production';
}

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
```

2. **Parâmetros tipados**
```typescript
interface GetMetricsParams {
  start_date?: string;
  end_date?: string;
  include_mock?: boolean;
}

interface GetRankingParams {
  limit?: number;
  level?: 'N1' | 'N2' | 'N3' | 'N4';
  sort_by?: 'performance_score' | 'ticket_count' | 'name';
  sort_order?: 'asc' | 'desc';
}

interface GetTicketsParams {
  status?: TicketStatus[];
  priority?: TicketPriority[];
  assigned_to?: number;
  limit?: number;
  offset?: number;
  sort_by?: 'created_at' | 'updated_at' | 'priority';
  sort_order?: 'asc' | 'desc';
}

class ApiService {
  async getMetrics(params?: GetMetricsParams): Promise<DashboardMetrics> {
    const searchParams = new URLSearchParams();
    if (params?.start_date) searchParams.append('start_date', params.start_date);
    if (params?.end_date) searchParams.append('end_date', params.end_date);
    if (params?.include_mock !== undefined) searchParams.append('include_mock', params.include_mock.toString());
    
    const url = searchParams.toString() ? `/metrics?${searchParams}` : '/metrics';
    const response = await httpClient.get<DashboardMetrics>(url);
    return response.data;
  }
}
```

3. **Retry automático**
```typescript
class ApiService {
  private async withRetry<T>(
    operation: () => Promise<T>, 
    maxAttempts = 3, 
    delay = 1000
  ): Promise<T> {
    let lastError: Error;
    
    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
      try {
        return await operation();
      } catch (error) {
        lastError = error as Error;
        
        if (attempt === maxAttempts) {
          throw lastError;
        }
        
        // Retry apenas para erros de rede ou 5xx
        if (this.shouldRetry(error)) {
          await this.sleep(delay * attempt);
          continue;
        }
        
        throw error;
      }
    }
    
    throw lastError!;
  }
  
  private shouldRetry(error: any): boolean {
    if (!error.response) return true; // Erro de rede
    const status = error.response.status;
    return status >= 500 || status === 429; // Server errors ou rate limit
  }
  
  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
  
  async getMetrics(): Promise<DashboardMetrics> {
    return this.withRetry(async () => {
      const response = await httpClient.get<DashboardMetrics>('/metrics');
      return response.data;
    });
  }
}
```

4. **Cache com TTL**
```typescript
interface CacheEntry<T> {
  data: T;
  timestamp: number;
  ttl: number;
}

class ApiService {
  private cache = new Map<string, CacheEntry<any>>();
  
  private getCacheKey(endpoint: string, params?: any): string {
    return params ? `${endpoint}?${JSON.stringify(params)}` : endpoint;
  }
  
  private getFromCache<T>(key: string): T | null {
    const entry = this.cache.get(key);
    if (!entry) return null;
    
    if (Date.now() - entry.timestamp > entry.ttl) {
      this.cache.delete(key);
      return null;
    }
    
    return entry.data;
  }
  
  private setCache<T>(key: string, data: T, ttl: number): void {
    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      ttl
    });
  }
  
  async getMetrics(params?: GetMetricsParams, useCache = true): Promise<DashboardMetrics> {
    const cacheKey = this.getCacheKey('/metrics', params);
    
    if (useCache) {
      const cached = this.getFromCache<DashboardMetrics>(cacheKey);
      if (cached) return cached;
    }
    
    const data = await this.withRetry(async () => {
      const response = await httpClient.get<DashboardMetrics>('/metrics');
      return response.data;
    });
    
    this.setCache(cacheKey, data, 30000); // Cache por 30 segundos
    return data;
  }
}
```

5. **Interceptadores específicos**
```typescript
class ApiService {
  constructor() {
    this.setupInterceptors();
  }
  
  private setupInterceptors(): void {
    // Request interceptor para adicionar headers específicos
    httpClient.interceptors.request.use(
      (config) => {
        // Adicionar timestamp para debugging
        config.headers['X-Request-Time'] = Date.now().toString();
        
        // Adicionar ID de correlação
        config.headers['X-Correlation-ID'] = this.generateCorrelationId();
        
        return config;
      },
      (error) => Promise.reject(error)
    );
    
    // Response interceptor para logging e métricas
    httpClient.interceptors.response.use(
      (response) => {
        const requestTime = response.config.headers['X-Request-Time'];
        const duration = Date.now() - parseInt(requestTime as string);
        
        console.log(`API Call: ${response.config.method?.toUpperCase()} ${response.config.url} - ${response.status} (${duration}ms)`);
        
        return response;
      },
      (error) => {
        const requestTime = error.config?.headers['X-Request-Time'];
        const duration = requestTime ? Date.now() - parseInt(requestTime) : 0;
        
        console.error(`API Error: ${error.config?.method?.toUpperCase()} ${error.config?.url} - ${error.response?.status || 'Network Error'} (${duration}ms)`);
        
        return Promise.reject(error);
      }
    );
  }
  
  private generateCorrelationId(): string {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }
}
```

6. **Validação de resposta**
```typescript
import Joi from 'joi';

class ApiService {
  private validateResponse<T>(data: any, schema: Joi.Schema): T {
    const { error, value } = schema.validate(data);
    if (error) {
      throw new Error(`Resposta inválida da API: ${error.message}`);
    }
    return value;
  }
  
  async getMetrics(): Promise<DashboardMetrics> {
    const response = await httpClient.get('/metrics');
    
    const schema = Joi.object({
      niveis: Joi.object({
        N1: Joi.number().required(),
        N2: Joi.number().required(),
        N3: Joi.number().required(),
        N4: Joi.number().required()
      }).required(),
      total: Joi.number().required(),
      novos: Joi.number().required(),
      pendentes: Joi.number().required(),
      progresso: Joi.number().required(),
      resolvidos: Joi.number().required(),
      data_source: Joi.string().valid('glpi', 'mock', 'unknown').required(),
      is_mock_data: Joi.boolean().required(),
      timestamp: Joi.string().isoDate().required()
    });
    
    return this.validateResponse<DashboardMetrics>(response.data, schema);
  }
}
```

## Status de implementação
✅ **Serviço funcional** - Implementação básica completa
✅ **Tipagem parcial** - Algumas interfaces definidas
✅ **Error handling básico** - Tratamento de erros simples
✅ **Singleton pattern** - Instância única
✅ **Logging básico** - Console.error
❌ **Tipos completos** - `Ticket` e `SystemStatus` não definidos
❌ **Retry automático** - Sem retry em falhas
❌ **Cache** - Sem cache de respostas
❌ **Parâmetros tipados** - Parâmetros como string
❌ **Validação** - Sem validação de resposta
❌ **Métricas** - Sem coleta de métricas de performance

## Integração com hooks
✅ **useMetrics** - Integração completa
✅ **useRanking** - Integração completa
✅ **useTickets** - Integração completa
⚠️ **useSystemStatus** - Hook não implementado

## Próximos passos
1. **CRÍTICO: Definir interfaces completas** - `Ticket`, `SystemStatus`
2. **Implementar parâmetros tipados** - Substituir strings por interfaces
3. **Adicionar retry automático** - Para falhas de rede
4. **Implementar cache** - Com TTL configurável
5. **Validação de resposta** - Schema validation
6. **Métricas de performance** - Timing e success rate
7. **Interceptadores específicos** - Headers e logging
8. **Testes unitários** - Cobertura completa do serviço