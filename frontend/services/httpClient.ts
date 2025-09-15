import axios, { AxiosError, AxiosResponse } from 'axios';

// Funcao para obter token de autenticacao (placeholder - implementar conforme necessario)
function getAuthToken(): string | null {
  return localStorage.getItem('auth_token') || null;
}

// Funcao para fazer logout (placeholder - implementar conforme necessario)
function handleLogout(): void {
  localStorage.removeItem('auth_token');
  // Redirecionar para login ou dispatch action
  window.location.href = '/login';
}

// Funcao que determina a URL base da API baseada no ambiente
function getApiBaseUrl(): string {
  // Em desenvolvimento, usa proxy relativo
  if (import.meta.env.DEV) {
    return '/api';  // Usa proxy do Vite
  }
  
  // Em producao, usa URL absoluta das variaveis de ambiente
  return import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000';
}

export const API_CONFIG = {
  BASE_URL: getApiBaseUrl(),
  TIMEOUT: parseInt(import.meta.env.VITE_API_TIMEOUT || '30000'),
  RETRY_ATTEMPTS: parseInt(import.meta.env.VITE_API_RETRY_ATTEMPTS || '3'),
  RETRY_DELAY: parseInt(import.meta.env.VITE_API_RETRY_DELAY || '1000'),
};

const httpClient = axios.create({
  baseURL: API_CONFIG.BASE_URL,
  timeout: API_CONFIG.TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
});

// Interceptador de requisicao
httpClient.interceptors.request.use(
  (config) => {
    // Adicionar token de autenticacao automaticamente
    const token = getAuthToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // Log da requisicao em desenvolvimento
    if (process.env.NODE_ENV === 'development') {
      console.log(`Request ${config.method?.toUpperCase()} ${config.url}`, {
        params: config.params,
        data: config.data,
        headers: config.headers,
      });
    }
    return config;
  },
  (error) => {
    console.error('Request error:', error);
    return Promise.reject(error);
  }
);

// Interceptador de resposta com tratamento especifico de erros
httpClient.interceptors.response.use(
  (response: AxiosResponse) => {
    // Log da resposta em desenvolvimento
    if (process.env.NODE_ENV === 'development') {
      console.log(`Response from ${response.config.url}:`, response.data);
    }
    return response;
  },
  async (error: AxiosError) => {
    const originalRequest = error.config;

    if (error.response) {
      const status = error.response.status;
      
      // Tratamento especifico por status HTTP
      switch (status) {
        case 401:
          console.error('Unauthorized - Token invalido ou expirado');
          handleLogout();
          break;
        
        case 403:
          console.error('Forbidden - Acesso negado');
          // Pode implementar redirecionamento ou notificacao especifica
          break;
        
        case 500:
          console.error('Internal Server Error - Erro no servidor');
          // Pode implementar retry ou notificacao de erro do servidor
          break;
        
        default:
          console.error(`Response error ${status}:`, error.response.data);
      }
    } else if (error.request) {
      console.error('No response received:', error.request);
    } else {
      console.error('Error:', error.message);
    }
    
    return Promise.reject(error);
  }
);

// Implementacao de retry automatico
const retryRequest = async (error: AxiosError, retryCount = 0): Promise<any> => {
  const maxRetries = API_CONFIG.RETRY_ATTEMPTS;
  const retryDelay = API_CONFIG.RETRY_DELAY;
  
  // Condicoes para retry
  const shouldRetry = (
    retryCount < maxRetries &&
    (
      !error.response || // Erro de rede
      error.response.status >= 500 || // Erro do servidor
      error.code === 'ECONNABORTED' // Timeout
    )
  );
  
  if (shouldRetry && error.config) {
    console.log(`Retry attempt ${retryCount + 1}/${maxRetries} in ${retryDelay}ms...`);
    
    await new Promise(resolve => setTimeout(resolve, retryDelay));
    
    try {
      return await httpClient.request(error.config);
    } catch (retryError) {
      return retryRequest(retryError as AxiosError, retryCount + 1);
    }
  }
  
  throw error;
};

// Wrapper para requisicoes com retry automatico
export const httpClientWithRetry = {
  get: async (url: string, config?: any) => {
    try {
      return await httpClient.get(url, config);
    } catch (error) {
      return retryRequest(error as AxiosError);
    }
  },
  
  post: async (url: string, data?: any, config?: any) => {
    try {
      return await httpClient.post(url, data, config);
    } catch (error) {
      return retryRequest(error as AxiosError);
    }
  },
  
  put: async (url: string, data?: any, config?: any) => {
    try {
      return await httpClient.put(url, data, config);
    } catch (error) {
      return retryRequest(error as AxiosError);
    }
  },
  
  delete: async (url: string, config?: any) => {
    try {
      return await httpClient.delete(url, config);
    } catch (error) {
      return retryRequest(error as AxiosError);
    }
  }
};

// Exportar ambos os clientes
export { httpClient };
export default httpClientWithRetry;