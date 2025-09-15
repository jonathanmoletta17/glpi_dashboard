# Cliente HTTP: httpClient

## Arquivo(s) de origem
- `frontend/services/httpClient.ts`
- `frontend/config/appConfig.ts` (configurações)

## Descrição técnica
Cliente HTTP baseado em Axios configurado com interceptadores, timeout e URL base para todas as requisições da aplicação.

## Configuração base

```typescript
import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import { appConfig } from '../config/appConfig';

// Configuração base do cliente
const httpClient: AxiosInstance = axios.create({
  baseURL: appConfig.apiUrl,
  timeout: appConfig.apiTimeout || 10000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
});
```

## Interceptadores

### Request Interceptor
```typescript
httpClient.interceptors.request.use(
  (config: AxiosRequestConfig) => {
    // Log da requisição
    console.log(`🚀 ${config.method?.toUpperCase()} ${config.url}`);
    
    // Adicionar timestamp
    config.metadata = { startTime: Date.now() };
    
    // Headers adicionais se necessário
    if (config.headers) {
      config.headers['X-Requested-With'] = 'XMLHttpRequest';
    }
    
    return config;
  },
  (error) => {
    console.error('❌ Erro na configuração da requisição:', error);
    return Promise.reject(error);
  }
);
```

### Response Interceptor
```typescript
httpClient.interceptors.response.use(
  (response: AxiosResponse) => {
    // Calcular tempo de resposta
    const duration = Date.now() - response.config.metadata?.startTime;
    
    console.log(
      `✅ ${response.config.method?.toUpperCase()} ${response.config.url} - ` +
      `${response.status} (${duration}ms)`
    );
    
    return response;
  },
  (error) => {
    // Calcular tempo de resposta mesmo em erro
    const duration = error.config?.metadata?.startTime 
      ? Date.now() - error.config.metadata.startTime 
      : 0;
    
    console.error(
      `❌ ${error.config?.method?.toUpperCase()} ${error.config?.url} - ` +
      `${error.response?.status || 'Network Error'} (${duration}ms)`
    );
    
    // Tratamento específico por tipo de erro
    if (error.response) {
      // Erro HTTP com resposta do servidor
      const { status, data } = error.response;
      
      switch (status) {
        case 401:
          console.warn('🔐 Token expirado ou inválido');
          // Aqui poderia redirecionar para login
          break;
        case 403:
          console.warn('🚫 Acesso negado');
          break;
        case 404:
          console.warn('🔍 Recurso não encontrado');
          break;
        case 429:
          console.warn('⏱️ Rate limit excedido');
          break;
        case 500:
        case 502:
        case 503:
        case 504:
          console.error('🔥 Erro do servidor');
          break;
      }
      
      // Enriquecer erro com informações úteis
      error.message = data?.message || data?.error || error.message;
      error.statusCode = status;
      error.timestamp = new Date().toISOString();
    } else if (error.request) {
      // Erro de rede (sem resposta)
      console.error('🌐 Erro de rede - sem resposta do servidor');
      error.message = 'Erro de conexão. Verifique sua internet.';
      error.isNetworkError = true;
    } else {
      // Erro na configuração da requisição
      console.error('⚙️ Erro na configuração:', error.message);
    }
    
    return Promise.reject(error);
  }
);
```

## Implementação completa

```typescript
import axios, { 
  AxiosInstance, 
  AxiosRequestConfig, 
  AxiosResponse, 
  AxiosError 
} from 'axios';
import { appConfig } from '../config/appConfig';

// Estender AxiosRequestConfig para incluir metadata
declare module 'axios' {
  interface AxiosRequestConfig {
    metadata?: {
      startTime: number;
      retryCount?: number;
    };
  }
}

/**
 * Cliente HTTP configurado para a aplicação
 * - Base URL configurável via environment
 * - Timeout configurável
 * - Interceptadores para logging e tratamento de erros
 * - Headers padrão para JSON
 */
class HttpClient {
  private client: AxiosInstance;
  
  constructor() {
    this.client = axios.create({
      baseURL: appConfig.apiUrl,
      timeout: appConfig.apiTimeout || 10000,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-Requested-With': 'XMLHttpRequest'
      }
    });
    
    this.setupInterceptors();
  }
  
  /**
   * Configurar interceptadores de request e response
   */
  private setupInterceptors(): void {
    // Request interceptor
    this.client.interceptors.request.use(
      this.handleRequest.bind(this),
      this.handleRequestError.bind(this)
    );
    
    // Response interceptor
    this.client.interceptors.response.use(
      this.handleResponse.bind(this),
      this.handleResponseError.bind(this)
    );
  }
  
  /**
   * Manipular requisições antes do envio
   */
  private handleRequest(config: AxiosRequestConfig): AxiosRequestConfig {
    // Adicionar metadata para timing
    config.metadata = {
      startTime: Date.now(),
      retryCount: config.metadata?.retryCount || 0
    };
    
    // Log da requisição em desenvolvimento
    if (appConfig.isDevelopment) {
      console.log(`🚀 ${config.method?.toUpperCase()} ${config.url}`);
      
      if (config.data) {
        console.log('📤 Request data:', config.data);
      }
      
      if (config.params) {
        console.log('🔍 Query params:', config.params);
      }
    }
    
    return config;
  }
  
  /**
   * Manipular erros de configuração de requisição
   */
  private handleRequestError(error: AxiosError): Promise<AxiosError> {
    console.error('❌ Erro na configuração da requisição:', error.message);
    return Promise.reject(error);
  }
  
  /**
   * Manipular respostas bem-sucedidas
   */
  private handleResponse(response: AxiosResponse): AxiosResponse {
    const duration = Date.now() - (response.config.metadata?.startTime || 0);
    
    if (appConfig.isDevelopment) {
      console.log(
        `✅ ${response.config.method?.toUpperCase()} ${response.config.url} - ` +
        `${response.status} (${duration}ms)`
      );
      
      if (response.data) {
        console.log('📥 Response data:', response.data);
      }
    }
    
    // Adicionar metadata à resposta
    response.metadata = {
      duration,
      timestamp: new Date().toISOString()
    };
    
    return response;
  }
  
  /**
   * Manipular erros de resposta
   */
  private handleResponseError(error: AxiosError): Promise<AxiosError> {
    const duration = error.config?.metadata?.startTime 
      ? Date.now() - error.config.metadata.startTime 
      : 0;
    
    // Log do erro
    if (appConfig.isDevelopment) {
      console.error(
        `❌ ${error.config?.method?.toUpperCase()} ${error.config?.url} - ` +
        `${error.response?.status || 'Network Error'} (${duration}ms)`
      );
      
      if (error.response?.data) {
        console.error('📥 Error response:', error.response.data);
      }
    }
    
    // Enriquecer erro com informações úteis
    this.enrichError(error, duration);
    
    return Promise.reject(error);
  }
  
  /**
   * Enriquecer erro com informações adicionais
   */
  private enrichError(error: AxiosError, duration: number): void {
    // Adicionar metadata do erro
    (error as any).metadata = {
      duration,
      timestamp: new Date().toISOString(),
      url: error.config?.url,
      method: error.config?.method?.toUpperCase()
    };
    
    if (error.response) {
      // Erro HTTP com resposta do servidor
      const { status, data } = error.response;
      
      (error as any).statusCode = status;
      (error as any).errorData = data;
      
      // Mensagem mais específica baseada no status
      switch (status) {
        case 400:
          error.message = data?.message || 'Requisição inválida';
          break;
        case 401:
          error.message = 'Não autorizado. Token inválido ou expirado.';
          (error as any).isAuthError = true;
          break;
        case 403:
          error.message = 'Acesso negado. Permissões insuficientes.';
          (error as any).isAuthError = true;
          break;
        case 404:
          error.message = 'Recurso não encontrado.';
          break;
        case 409:
          error.message = data?.message || 'Conflito de dados.';
          break;
        case 422:
          error.message = 'Dados inválidos.';
          (error as any).validationErrors = data?.errors || data?.details;
          break;
        case 429:
          error.message = 'Muitas requisições. Tente novamente em alguns segundos.';
          (error as any).isRateLimited = true;
          break;
        case 500:
          error.message = 'Erro interno do servidor.';
          (error as any).isServerError = true;
          break;
        case 502:
        case 503:
        case 504:
          error.message = 'Serviço temporariamente indisponível.';
          (error as any).isServerError = true;
          break;
        default:
          error.message = data?.message || `Erro HTTP ${status}`;
      }
    } else if (error.request) {
      // Erro de rede (sem resposta)
      error.message = 'Erro de conexão. Verifique sua internet e tente novamente.';
      (error as any).isNetworkError = true;
    } else {
      // Erro na configuração da requisição
      error.message = error.message || 'Erro na configuração da requisição';
      (error as any).isConfigError = true;
    }
  }
  
  /**
   * Métodos HTTP públicos
   */
  get<T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.client.get<T>(url, config);
  }
  
  post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.client.post<T>(url, data, config);
  }
  
  put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.client.put<T>(url, data, config);
  }
  
  patch<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.client.patch<T>(url, data, config);
  }
  
  delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.client.delete<T>(url, config);
  }
  
  /**
   * Configurar header de autorização
   */
  setAuthToken(token: string): void {
    this.client.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  }
  
  /**
   * Remover header de autorização
   */
  clearAuthToken(): void {
    delete this.client.defaults.headers.common['Authorization'];
  }
  
  /**
   * Configurar timeout dinamicamente
   */
  setTimeout(timeout: number): void {
    this.client.defaults.timeout = timeout;
  }
  
  /**
   * Obter instância do Axios para uso avançado
   */
  getInstance(): AxiosInstance {
    return this.client;
  }
}

// Instância singleton
export const httpClient = new HttpClient();
export default httpClient;
```

## Configurações utilizadas

### Variáveis de ambiente
- `VITE_API_URL` - URL base da API (obrigatório)
- `VITE_API_TIMEOUT` - Timeout em ms (padrão: 10000)
- `VITE_NODE_ENV` - Ambiente (development/production)

### Headers padrão
```typescript
{
  'Content-Type': 'application/json',
  'Accept': 'application/json',
  'X-Requested-With': 'XMLHttpRequest'
}
```

### Timeout
- **Padrão**: 10 segundos (10000ms)
- **Configurável**: Via `VITE_API_TIMEOUT`
- **Dinâmico**: Método `setTimeout()`

## Funcionalidades

### ✅ Implementadas
- **Base URL configurável** - Via environment
- **Timeout configurável** - Padrão 10s
- **Headers padrão** - JSON content-type
- **Request interceptor** - Logging e metadata
- **Response interceptor** - Timing e tratamento de erros
- **Error enrichment** - Informações adicionais nos erros
- **Métodos HTTP** - GET, POST, PUT, PATCH, DELETE
- **Auth token** - Métodos para configurar/limpar
- **Logging condicional** - Apenas em desenvolvimento

### ❌ Não implementadas
- **Retry automático** - Sem retry em falhas
- **Request/Response cache** - Sem cache
- **Request cancellation** - Sem AbortController
- **Request queuing** - Sem fila de requisições
- **Offline detection** - Sem detecção de conectividade
- **Request deduplication** - Sem deduplicação
- **Progress tracking** - Sem tracking de upload/download
- **Request/Response transformation** - Transformações customizadas

## Análise técnica

### Pontos fortes
✅ **Configuração centralizada** - Uma instância para toda a app
✅ **Interceptadores robustos** - Logging e error handling
✅ **Error enrichment** - Erros com informações úteis
✅ **Tipagem TypeScript** - Métodos tipados
✅ **Singleton pattern** - Instância única
✅ **Logging condicional** - Apenas em desenvolvimento
✅ **Metadata tracking** - Timing e informações de requisição
✅ **Auth token management** - Métodos para autenticação

### Possíveis problemas
⚠️ **Sem retry** - Falhas de rede não são reprocessadas
⚠️ **Sem cache** - Requisições duplicadas não são otimizadas
⚠️ **Sem cancellation** - Requisições não podem ser canceladas
⚠️ **Logging verboso** - Muitos logs em desenvolvimento
⚠️ **Error handling genérico** - Não há tratamento específico por endpoint
⚠️ **Sem offline support** - Não detecta perda de conectividade

### Sugestões de melhorias

1. **Retry automático com backoff**
```typescript
class HttpClient {
  private async withRetry<T>(
    operation: () => Promise<AxiosResponse<T>>,
    maxAttempts = 3,
    baseDelay = 1000
  ): Promise<AxiosResponse<T>> {
    let lastError: AxiosError;
    
    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
      try {
        return await operation();
      } catch (error) {
        lastError = error as AxiosError;
        
        if (attempt === maxAttempts || !this.shouldRetry(error)) {
          throw error;
        }
        
        const delay = baseDelay * Math.pow(2, attempt - 1); // Exponential backoff
        await this.sleep(delay);
        
        // Atualizar retry count
        if (lastError.config?.metadata) {
          lastError.config.metadata.retryCount = attempt;
        }
      }
    }
    
    throw lastError!;
  }
  
  private shouldRetry(error: any): boolean {
    if (!error.response) return true; // Network error
    const status = error.response.status;
    return status >= 500 || status === 429; // Server errors or rate limit
  }
  
  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
  
  get<T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.withRetry(() => this.client.get<T>(url, config));
  }
}
```

2. **Request cancellation**
```typescript
class HttpClient {
  private pendingRequests = new Map<string, AbortController>();
  
  private createRequestKey(config: AxiosRequestConfig): string {
    return `${config.method}:${config.url}:${JSON.stringify(config.params || {})}`;
  }
  
  get<T = any>(url: string, config?: AxiosRequestConfig & { cancelPrevious?: boolean }): Promise<AxiosResponse<T>> {
    const requestKey = this.createRequestKey({ method: 'GET', url, ...config });
    
    // Cancelar requisição anterior se solicitado
    if (config?.cancelPrevious && this.pendingRequests.has(requestKey)) {
      this.pendingRequests.get(requestKey)?.abort();
    }
    
    // Criar novo AbortController
    const abortController = new AbortController();
    this.pendingRequests.set(requestKey, abortController);
    
    const requestConfig = {
      ...config,
      signal: abortController.signal
    };
    
    return this.client.get<T>(url, requestConfig)
      .finally(() => {
        this.pendingRequests.delete(requestKey);
      });
  }
  
  cancelRequest(url: string, method = 'GET'): void {
    const requestKey = this.createRequestKey({ method, url });
    const controller = this.pendingRequests.get(requestKey);
    if (controller) {
      controller.abort();
      this.pendingRequests.delete(requestKey);
    }
  }
  
  cancelAllRequests(): void {
    this.pendingRequests.forEach(controller => controller.abort());
    this.pendingRequests.clear();
  }
}
```

3. **Request cache com TTL**
```typescript
interface CacheEntry<T> {
  data: AxiosResponse<T>;
  timestamp: number;
  ttl: number;
}

class HttpClient {
  private cache = new Map<string, CacheEntry<any>>();
  
  private getCacheKey(method: string, url: string, params?: any): string {
    const paramsStr = params ? JSON.stringify(params) : '';
    return `${method}:${url}:${paramsStr}`;
  }
  
  private getFromCache<T>(key: string): AxiosResponse<T> | null {
    const entry = this.cache.get(key);
    if (!entry) return null;
    
    if (Date.now() - entry.timestamp > entry.ttl) {
      this.cache.delete(key);
      return null;
    }
    
    return entry.data;
  }
  
  private setCache<T>(key: string, data: AxiosResponse<T>, ttl: number): void {
    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      ttl
    });
  }
  
  get<T = any>(
    url: string, 
    config?: AxiosRequestConfig & { cache?: { ttl: number; key?: string } }
  ): Promise<AxiosResponse<T>> {
    const cacheConfig = config?.cache;
    
    if (cacheConfig) {
      const cacheKey = cacheConfig.key || this.getCacheKey('GET', url, config?.params);
      const cached = this.getFromCache<T>(cacheKey);
      
      if (cached) {
        return Promise.resolve(cached);
      }
      
      return this.client.get<T>(url, config)
        .then(response => {
          this.setCache(cacheKey, response, cacheConfig.ttl);
          return response;
        });
    }
    
    return this.client.get<T>(url, config);
  }
}
```

4. **Offline detection**
```typescript
class HttpClient {
  private isOnline = navigator.onLine;
  private offlineQueue: Array<() => Promise<any>> = [];
  
  constructor() {
    // ... configuração existente
    this.setupOfflineHandling();
  }
  
  private setupOfflineHandling(): void {
    window.addEventListener('online', () => {
      this.isOnline = true;
      this.processOfflineQueue();
    });
    
    window.addEventListener('offline', () => {
      this.isOnline = false;
    });
  }
  
  private async processOfflineQueue(): Promise<void> {
    while (this.offlineQueue.length > 0) {
      const request = this.offlineQueue.shift();
      if (request) {
        try {
          await request();
        } catch (error) {
          console.error('Erro ao processar requisição da fila offline:', error);
        }
      }
    }
  }
  
  private handleOfflineRequest<T>(
    operation: () => Promise<AxiosResponse<T>>
  ): Promise<AxiosResponse<T>> {
    if (this.isOnline) {
      return operation();
    }
    
    return new Promise((resolve, reject) => {
      this.offlineQueue.push(async () => {
        try {
          const result = await operation();
          resolve(result);
        } catch (error) {
          reject(error);
        }
      });
      
      // Rejeitar imediatamente se não quiser enfileirar
      reject(new Error('Aplicação offline. Requisição enfileirada.'));
    });
  }
}
```

## Dependências

### Principais
- **axios** - Cliente HTTP
- **appConfig** - Configurações da aplicação

### Tipos TypeScript
- `AxiosInstance` - Instância do Axios
- `AxiosRequestConfig` - Configuração de requisição
- `AxiosResponse` - Resposta HTTP
- `AxiosError` - Erro HTTP

### Variáveis de ambiente
- `VITE_API_URL` - URL base da API
- `VITE_API_TIMEOUT` - Timeout das requisições
- `VITE_NODE_ENV` - Ambiente de execução

## Status de implementação
✅ **Cliente funcional** - Implementação básica completa
✅ **Interceptadores** - Request/Response interceptors
✅ **Error handling** - Tratamento robusto de erros
✅ **Logging** - Logs condicionais por ambiente
✅ **Auth management** - Métodos para token
✅ **Tipagem TypeScript** - Interfaces completas
❌ **Retry automático** - Sem retry em falhas
❌ **Request cache** - Sem cache de requisições
❌ **Request cancellation** - Sem cancelamento
❌ **Offline support** - Sem detecção offline
❌ **Progress tracking** - Sem tracking de progresso

## Integração com serviços
✅ **apiService** - Integração completa
✅ **Configuração centralizada** - Via appConfig
✅ **Error propagation** - Erros enriquecidos
✅ **Logging consistente** - Padrão de logs

## Próximos passos
1. **Implementar retry automático** - Com exponential backoff
2. **Adicionar request cancellation** - AbortController
3. **Implementar cache** - Com TTL configurável
4. **Offline detection** - Queue de requisições
5. **Progress tracking** - Para uploads/downloads
6. **Request deduplication** - Evitar requisições duplicadas
7. **Performance monitoring** - Métricas de latência
8. **Error recovery** - Estratégias de recuperação