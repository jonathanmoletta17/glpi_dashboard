export const ENV_CONFIG = {
  // 📊 Configurações de Log
  LOG_LEVEL: import.meta.env.VITE_LOG_LEVEL || 'info',
  SHOW_API_CALLS: import.meta.env.VITE_SHOW_API_CALLS === 'true',
  SHOW_PERFORMANCE: import.meta.env.VITE_SHOW_PERFORMANCE === 'true',
  
  // 🎯 Ambiente
  IS_DEVELOPMENT: import.meta.env.DEV,
  IS_PRODUCTION: import.meta.env.PROD,
  MODE: import.meta.env.MODE,
  
  // 🌐 API
  API_BASE_URL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000',
  API_TIMEOUT: parseInt(import.meta.env.VITE_API_TIMEOUT || '30000'),
};

export function getCurrentEnvironment(): 'development' | 'production' | 'test' {
  if (import.meta.env.DEV) return 'development';
  if (import.meta.env.PROD) return 'production';
  return 'test';
}