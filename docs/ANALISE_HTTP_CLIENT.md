# Análise do Arquivo httpClient.ts

## Status Atual da Configuração HTTP

### ✅ Pontos Funcionais Identificados

1. **URL Base da API** - ✅ CORRETO
   - Configuração dinâmica baseada no ambiente
   - Desenvolvimento: `/api` (usa proxy do Vite)
   - Produção: `VITE_API_BASE_URL` ou fallback para `http://localhost:5000`

2. **Timeout Configurado** - ✅ CORRETO
   - Valor: 30000ms (conforme recomendado)
   - Configurável via `VITE_API_TIMEOUT`

3. **Interceptors Básicos** - ✅ PARCIALMENTE IMPLEMENTADO
   - Request interceptor: logs em desenvolvimento
   - Response interceptor: logs básicos

### ❌ Problemas Identificados

1. **Falta Tratamento de Erro Específico para Status HTTP**
   - Não há tratamento específico para 401 (Unauthorized)
   - Não há tratamento específico para 403 (Forbidden)
   - Não há tratamento específico para 500 (Internal Server Error)
   - Não há dispatch para logout em caso de 401

2. **Ausência de Retry Automático**
   - Configuração existe (`RETRY_ATTEMPTS`, `RETRY_DELAY`) mas não está implementada
   - Não há lógica de retry para falhas de rede

3. **Headers de Autenticação Não Implementados**
   - Não há adição automática de tokens de autenticação
   - Interceptor de request não adiciona headers de auth

4. **Falta Context de Autenticação**
   - Não existe AuthContext ou sistema de gerenciamento de auth
   - Não há hooks de autenticação (useAuth)

## Estrutura Funcional Recomendada

### Configuração API_CONFIG
```typescript
export const API_CONFIG = {
  BASE_URL: getApiBaseUrl(),
  TIMEOUT: 30000,
  RETRY_ATTEMPTS: 3,
  RETRY_DELAY: 1000,
};
```
✅ **Status**: IMPLEMENTADO

### Interceptors para Tokens Automáticos
```typescript
// Request interceptor para adicionar token
httpClient.interceptors.request.use((config) => {
  const token = getAuthToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```
❌ **Status**: NÃO IMPLEMENTADO

### Tratamento de Erro com Dispatch para Logout
```typescript
// Response interceptor para tratar erros
httpClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Dispatch logout
      store.dispatch(logout());
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
```
❌ **Status**: NÃO IMPLEMENTADO

### Retry Automático
```typescript
// Implementação de retry com axios-retry ou lógica customizada
import axiosRetry from 'axios-retry';

axiosRetry(httpClient, {
  retries: API_CONFIG.RETRY_ATTEMPTS,
  retryDelay: () => API_CONFIG.RETRY_DELAY,
  retryCondition: (error) => {
    return axiosRetry.isNetworkOrIdempotentRequestError(error) ||
           error.response?.status >= 500;
  }
});
```
❌ **Status**: NÃO IMPLEMENTADO

## Impacto dos Problemas

1. **Segurança**: Sem tratamento de 401/403, usuários podem ficar em estados inconsistentes
2. **Experiência do Usuário**: Sem retry, falhas temporárias de rede causam erros desnecessários
3. **Autenticação**: Sem headers automáticos, todas as requisições autenticadas falham
4. **Monitoramento**: Logs básicos não fornecem informações suficientes para debug

## Próximos Passos

1. Implementar tratamento específico de status HTTP (401, 403, 500)
2. Adicionar sistema de retry automático
3. Criar sistema de autenticação com tokens
4. Implementar interceptor para adicionar headers de auth automaticamente
5. Criar AuthContext e hooks de autenticação
6. Melhorar sistema de logs e monitoramento

## Arquivos Relacionados

- `frontend/services/httpClient.ts` - Arquivo principal analisado
- `frontend/.env.example` - Configurações de ambiente
- `frontend/hooks/useMetrics.ts` - Exemplo de uso do httpClient
- `frontend/hooks/useTickets.ts` - Exemplo de uso do httpClient
- `frontend/hooks/useRanking.ts` - Exemplo de uso do httpClient