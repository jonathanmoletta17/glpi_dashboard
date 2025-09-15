/**
 * 🎯 Configuração Principal da Aplicação
 * Centraliza todas as configurações do frontend
 */

import { API_CONFIG } from '../services/httpClient';
import { ENV_CONFIG, getCurrentEnvironment } from './environment';

/**
 * 🛣️ Configuração de Endpoints da API
 */
const endpointsConfig = {
  // 📊 Dashboard
  dashboard: '/dashboard',
  metrics: '/metrics',
  
  // 🏆 Ranking
  ranking: '/ranking',
  
  // 🔍 Consultas
  tickets: '/tickets',
  users: '/users',
  categories: '/categories',
  
  // 🏥 Sistema
  health: '/health',
  status: '/status',
};

/**
 * 🌍 Configurações por Ambiente
 */
const environmentConfigs = {
  development: {
    enableDebug: true,
    enableMocks: false,
    enablePerformanceMonitoring: true,
    apiTimeout: 30000,
  },
  production: {
    enableDebug: false,
    enableMocks: false,
    enablePerformanceMonitoring: false,
    apiTimeout: 90000,
  },
  test: {
    enableDebug: true,
    enableMocks: true,
    enablePerformanceMonitoring: false,
    apiTimeout: 5000,
  },
};

/**
 * 🎯 Configuração Principal Exportada
 */
export const appConfig = {
  // 🌐 API
  api: {
    ...API_CONFIG,
    endpoints: endpointsConfig,
  },
  
  // 🌍 Ambiente
  environment: {
    ...ENV_CONFIG,
    ...environmentConfigs[getCurrentEnvironment()],
  },
  
  // 🎨 UI
  ui: {
    theme: 'light',
    language: 'pt-BR',
    dateFormat: 'DD/MM/YYYY',
    timeFormat: 'HH:mm:ss',
  },
  
  // 📊 Features
  features: {
    enableRealTimeUpdates: true,
    enableNotifications: true,
    enableExport: true,
    enableFilters: true,
  },
};

/**
 * 🔍 Função utilitária para obter URL completa de endpoint
 */
export function getApiUrl(endpoint: keyof typeof endpointsConfig): string {
  const baseUrl = appConfig.api.BASE_URL;
  const endpointPath = endpointsConfig[endpoint];
  
  if (baseUrl === '/api') {
    return `${baseUrl}${endpointPath}`;
  }
  
  return `${baseUrl}/api${endpointPath}`;
}

export default appConfig;