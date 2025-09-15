# Configurações: appConfig

## Arquivo(s) de origem
- `frontend/config/appConfig.ts`
- `frontend/.env` (variáveis de ambiente)
- `frontend/.env.local` (variáveis locais)
- `frontend/.env.development` (desenvolvimento)
- `frontend/.env.production` (produção)

## Descrição técnica
Centraliza todas as configurações da aplicação, incluindo URLs de API, timeouts, configurações de ambiente e flags de funcionalidades.

## Implementação atual

```typescript
// frontend/config/appConfig.ts
interface AppConfig {
  apiUrl: string;
  apiTimeout: number;
  isDevelopment: boolean;
  isProduction: boolean;
  environment: 'development' | 'staging' | 'production';
  version: string;
  buildTime: string;
}

const appConfig: AppConfig = {
  // URL base da API
  apiUrl: import.meta.env.VITE_API_URL || 'http://localhost:5000',
  
  // Timeout para requisições HTTP (em ms)
  apiTimeout: parseInt(import.meta.env.VITE_API_TIMEOUT || '10000'),
  
  // Flags de ambiente
  isDevelopment: import.meta.env.DEV,
  isProduction: import.meta.env.PROD,
  environment: (import.meta.env.VITE_NODE_ENV || 'development') as 'development' | 'staging' | 'production',
  
  // Informações da build
  version: import.meta.env.VITE_APP_VERSION || '1.0.0',
  buildTime: import.meta.env.VITE_BUILD_TIME || new Date().toISOString()
};

export { appConfig };
export default appConfig;
```

## Variáveis de ambiente

### Obrigatórias
```bash
# URL da API do backend
VITE_API_URL=http://localhost:5000
```

### Opcionais
```bash
# Timeout para requisições HTTP (padrão: 10000ms)
VITE_API_TIMEOUT=15000

# Ambiente da aplicação (padrão: development)
VITE_NODE_ENV=development

# Versão da aplicação (padrão: 1.0.0)
VITE_APP_VERSION=1.2.3

# Timestamp da build (gerado automaticamente)
VITE_BUILD_TIME=2024-01-15T10:30:00.000Z

# Configurações de debug
VITE_DEBUG_MODE=true
VITE_LOG_LEVEL=debug

# Configurações de API
VITE_API_RETRY_ATTEMPTS=3
VITE_API_RETRY_DELAY=1000

# Configurações de cache
VITE_CACHE_TTL=300000
VITE_CACHE_ENABLED=true

# Configurações de refresh
VITE_AUTO_REFRESH_INTERVAL=30000
VITE_AUTO_REFRESH_ENABLED=true

# Configurações de monitoramento
VITE_MONITORING_ENABLED=false
VITE_ANALYTICS_ID=

# Configurações de feature flags
VITE_FEATURE_DARK_MODE=true
VITE_FEATURE_NOTIFICATIONS=true
VITE_FEATURE_EXPORT=false
```

## Configuração completa sugerida

```typescript
// frontend/config/appConfig.ts
interface ApiConfig {
  url: string;
  timeout: number;
  retryAttempts: number;
  retryDelay: number;
}

interface CacheConfig {
  enabled: boolean;
  ttl: number;
  maxSize: number;
}

interface RefreshConfig {
  enabled: boolean;
  interval: number;
  onFocus: boolean;
  onReconnect: boolean;
}

interface MonitoringConfig {
  enabled: boolean;
  analyticsId?: string;
  errorReporting: boolean;
  performanceTracking: boolean;
}

interface FeatureFlags {
  darkMode: boolean;
  notifications: boolean;
  export: boolean;
  realTimeUpdates: boolean;
  advancedFilters: boolean;
}

interface DebugConfig {
  enabled: boolean;
  logLevel: 'error' | 'warn' | 'info' | 'debug';
  showNetworkLogs: boolean;
  showPerformanceLogs: boolean;
}

interface AppConfig {
  // Informações básicas
  version: string;
  buildTime: string;
  environment: 'development' | 'staging' | 'production';
  isDevelopment: boolean;
  isProduction: boolean;
  
  // Configurações de API
  api: ApiConfig;
  
  // Configurações de cache
  cache: CacheConfig;
  
  // Configurações de refresh
  refresh: RefreshConfig;
  
  // Configurações de monitoramento
  monitoring: MonitoringConfig;
  
  // Feature flags
  features: FeatureFlags;
  
  // Configurações de debug
  debug: DebugConfig;
}

/**
 * Função auxiliar para converter string para boolean
 */
function parseBoolean(value: string | undefined, defaultValue: boolean): boolean {
  if (value === undefined) return defaultValue;
  return value.toLowerCase() === 'true';
}

/**
 * Função auxiliar para converter string para número
 */
function parseNumber(value: string | undefined, defaultValue: number): number {
  if (value === undefined) return defaultValue;
  const parsed = parseInt(value, 10);
  return isNaN(parsed) ? defaultValue : parsed;
}

/**
 * Validar configurações obrigatórias
 */
function validateConfig(): void {
  const requiredVars = {
    VITE_API_URL: import.meta.env.VITE_API_URL
  };
  
  const missing = Object.entries(requiredVars)
    .filter(([, value]) => !value)
    .map(([key]) => key);
  
  if (missing.length > 0) {
    throw new Error(
      `Variáveis de ambiente obrigatórias não definidas: ${missing.join(', ')}`
    );
  }
  
  // Validar URL da API
  try {
    new URL(import.meta.env.VITE_API_URL);
  } catch {
    throw new Error('VITE_API_URL deve ser uma URL válida');
  }
}

// Validar configurações na inicialização
validateConfig();

/**
 * Configuração da aplicação
 */
const appConfig: AppConfig = {
  // Informações básicas
  version: import.meta.env.VITE_APP_VERSION || '1.0.0',
  buildTime: import.meta.env.VITE_BUILD_TIME || new Date().toISOString(),
  environment: (import.meta.env.VITE_NODE_ENV || 'development') as AppConfig['environment'],
  isDevelopment: import.meta.env.DEV,
  isProduction: import.meta.env.PROD,
  
  // Configurações de API
  api: {
    url: import.meta.env.VITE_API_URL,
    timeout: parseNumber(import.meta.env.VITE_API_TIMEOUT, 10000),
    retryAttempts: parseNumber(import.meta.env.VITE_API_RETRY_ATTEMPTS, 3),
    retryDelay: parseNumber(import.meta.env.VITE_API_RETRY_DELAY, 1000)
  },
  
  // Configurações de cache
  cache: {
    enabled: parseBoolean(import.meta.env.VITE_CACHE_ENABLED, true),
    ttl: parseNumber(import.meta.env.VITE_CACHE_TTL, 300000), // 5 minutos
    maxSize: parseNumber(import.meta.env.VITE_CACHE_MAX_SIZE, 100)
  },
  
  // Configurações de refresh
  refresh: {
    enabled: parseBoolean(import.meta.env.VITE_AUTO_REFRESH_ENABLED, true),
    interval: parseNumber(import.meta.env.VITE_AUTO_REFRESH_INTERVAL, 30000), // 30 segundos
    onFocus: parseBoolean(import.meta.env.VITE_REFRESH_ON_FOCUS, true),
    onReconnect: parseBoolean(import.meta.env.VITE_REFRESH_ON_RECONNECT, true)
  },
  
  // Configurações de monitoramento
  monitoring: {
    enabled: parseBoolean(import.meta.env.VITE_MONITORING_ENABLED, false),
    analyticsId: import.meta.env.VITE_ANALYTICS_ID,
    errorReporting: parseBoolean(import.meta.env.VITE_ERROR_REPORTING, false),
    performanceTracking: parseBoolean(import.meta.env.VITE_PERFORMANCE_TRACKING, false)
  },
  
  // Feature flags
  features: {
    darkMode: parseBoolean(import.meta.env.VITE_FEATURE_DARK_MODE, true),
    notifications: parseBoolean(import.meta.env.VITE_FEATURE_NOTIFICATIONS, true),
    export: parseBoolean(import.meta.env.VITE_FEATURE_EXPORT, false),
    realTimeUpdates: parseBoolean(import.meta.env.VITE_FEATURE_REAL_TIME, false),
    advancedFilters: parseBoolean(import.meta.env.VITE_FEATURE_ADVANCED_FILTERS, false)
  },
  
  // Configurações de debug
  debug: {
    enabled: parseBoolean(import.meta.env.VITE_DEBUG_MODE, import.meta.env.DEV),
    logLevel: (import.meta.env.VITE_LOG_LEVEL || 'info') as DebugConfig['logLevel'],
    showNetworkLogs: parseBoolean(import.meta.env.VITE_SHOW_NETWORK_LOGS, import.meta.env.DEV),
    showPerformanceLogs: parseBoolean(import.meta.env.VITE_SHOW_PERFORMANCE_LOGS, false)
  }
};

// Log das configurações em desenvolvimento
if (appConfig.isDevelopment && appConfig.debug.enabled) {
  console.group('🔧 Configurações da aplicação');
  console.log('Versão:', appConfig.version);
  console.log('Ambiente:', appConfig.environment);
  console.log('API URL:', appConfig.api.url);
  console.log('API Timeout:', appConfig.api.timeout + 'ms');
  console.log('Cache habilitado:', appConfig.cache.enabled);
  console.log('Auto-refresh:', appConfig.refresh.enabled);
  console.log('Features:', appConfig.features);
  console.groupEnd();
}

export { appConfig };
export type { AppConfig, ApiConfig, CacheConfig, RefreshConfig, MonitoringConfig, FeatureFlags, DebugConfig };
export default appConfig;
```

## Arquivos de ambiente

### `.env` (base)
```bash
# Configurações base para todos os ambientes
VITE_APP_VERSION=1.0.0
VITE_CACHE_ENABLED=true
VITE_FEATURE_DARK_MODE=true
VITE_FEATURE_NOTIFICATIONS=true
```

### `.env.development`
```bash
# Configurações para desenvolvimento
VITE_API_URL=http://localhost:5000
VITE_API_TIMEOUT=15000
VITE_DEBUG_MODE=true
VITE_LOG_LEVEL=debug
VITE_SHOW_NETWORK_LOGS=true
VITE_AUTO_REFRESH_ENABLED=true
VITE_AUTO_REFRESH_INTERVAL=10000
VITE_MONITORING_ENABLED=false
```

### `.env.staging`
```bash
# Configurações para staging
VITE_API_URL=https://api-staging.exemplo.com
VITE_API_TIMEOUT=10000
VITE_DEBUG_MODE=false
VITE_LOG_LEVEL=warn
VITE_SHOW_NETWORK_LOGS=false
VITE_AUTO_REFRESH_ENABLED=true
VITE_AUTO_REFRESH_INTERVAL=30000
VITE_MONITORING_ENABLED=true
VITE_ERROR_REPORTING=true
```

### `.env.production`
```bash
# Configurações para produção
VITE_API_URL=https://api.exemplo.com
VITE_API_TIMEOUT=8000
VITE_DEBUG_MODE=false
VITE_LOG_LEVEL=error
VITE_SHOW_NETWORK_LOGS=false
VITE_AUTO_REFRESH_ENABLED=true
VITE_AUTO_REFRESH_INTERVAL=60000
VITE_MONITORING_ENABLED=true
VITE_ERROR_REPORTING=true
VITE_PERFORMANCE_TRACKING=true
VITE_ANALYTICS_ID=GA-XXXXXXXXX
```

### `.env.local` (ignorado pelo Git)
```bash
# Configurações locais específicas do desenvolvedor
VITE_API_URL=http://192.168.1.100:5000
VITE_DEBUG_MODE=true
VITE_FEATURE_EXPORT=true
VITE_FEATURE_ADVANCED_FILTERS=true
```

## Uso nas aplicações

### httpClient
```typescript
import { appConfig } from '../config/appConfig';

const httpClient = axios.create({
  baseURL: appConfig.api.url,
  timeout: appConfig.api.timeout
});
```

### Hooks
```typescript
import { appConfig } from '../config/appConfig';

const useMetrics = () => {
  const [data, setData] = useState(null);
  
  useEffect(() => {
    if (appConfig.refresh.enabled) {
      const interval = setInterval(fetchData, appConfig.refresh.interval);
      return () => clearInterval(interval);
    }
  }, []);
};
```

### Componentes
```typescript
import { appConfig } from '../config/appConfig';

const Dashboard = () => {
  return (
    <div>
      {appConfig.features.darkMode && <DarkModeToggle />}
      {appConfig.features.notifications && <NotificationCenter />}
      {appConfig.features.export && <ExportButton />}
    </div>
  );
};
```

## Dependências

### Runtime
- **Vite** - Para `import.meta.env`
- **TypeScript** - Para tipagem

### Build time
- **dotenv** - Para carregar arquivos .env
- **vite** - Para processamento das variáveis

## Análise técnica

### Pontos fortes
✅ **Centralização** - Todas as configurações em um local
✅ **Tipagem TypeScript** - Interfaces bem definidas
✅ **Validação** - Verificação de variáveis obrigatórias
✅ **Ambientes múltiplos** - Suporte a dev/staging/prod
✅ **Feature flags** - Controle de funcionalidades
✅ **Parsing seguro** - Funções auxiliares para conversão
✅ **Logging condicional** - Debug apenas em desenvolvimento

### Possíveis problemas
⚠️ **Sem hot reload** - Mudanças em .env requerem restart
⚠️ **Sem validação de tipos** - Variáveis sempre são strings
⚠️ **Sem configuração remota** - Apenas variáveis locais
⚠️ **Sem criptografia** - Valores sensíveis em texto plano
⚠️ **Sem versionamento** - Não há controle de versão de config
⚠️ **Sem fallback** - Falha se variáveis obrigatórias não existem

### Sugestões de melhorias

1. **Schema validation com Zod**
```typescript
import { z } from 'zod';

const configSchema = z.object({
  api: z.object({
    url: z.string().url('URL da API deve ser válida'),
    timeout: z.number().min(1000, 'Timeout deve ser pelo menos 1000ms'),
    retryAttempts: z.number().min(0).max(10),
    retryDelay: z.number().min(100)
  }),
  cache: z.object({
    enabled: z.boolean(),
    ttl: z.number().min(1000),
    maxSize: z.number().min(1)
  }),
  features: z.object({
    darkMode: z.boolean(),
    notifications: z.boolean(),
    export: z.boolean()
  })
});

// Validar configuração
const validatedConfig = configSchema.parse(appConfig);
```

2. **Configuração remota**
```typescript
class ConfigManager {
  private localConfig: AppConfig;
  private remoteConfig: Partial<AppConfig> | null = null;
  
  constructor(localConfig: AppConfig) {
    this.localConfig = localConfig;
  }
  
  async loadRemoteConfig(): Promise<void> {
    try {
      const response = await fetch('/api/config');
      this.remoteConfig = await response.json();
    } catch (error) {
      console.warn('Falha ao carregar configuração remota:', error);
    }
  }
  
  get config(): AppConfig {
    return {
      ...this.localConfig,
      ...this.remoteConfig
    };
  }
  
  getFeatureFlag(flag: keyof FeatureFlags): boolean {
    return this.config.features[flag];
  }
}

const configManager = new ConfigManager(appConfig);
export { configManager };
```

3. **Hot reload de configuração**
```typescript
class ReactiveConfig {
  private config: AppConfig;
  private listeners: Array<(config: AppConfig) => void> = [];
  
  constructor(initialConfig: AppConfig) {
    this.config = initialConfig;
    this.setupHotReload();
  }
  
  private setupHotReload(): void {
    if (import.meta.hot) {
      import.meta.hot.accept('../config/appConfig.ts', (newModule) => {
        if (newModule) {
          this.updateConfig(newModule.appConfig);
        }
      });
    }
  }
  
  private updateConfig(newConfig: AppConfig): void {
    this.config = newConfig;
    this.listeners.forEach(listener => listener(newConfig));
  }
  
  subscribe(listener: (config: AppConfig) => void): () => void {
    this.listeners.push(listener);
    return () => {
      const index = this.listeners.indexOf(listener);
      if (index > -1) {
        this.listeners.splice(index, 1);
      }
    };
  }
  
  get current(): AppConfig {
    return this.config;
  }
}

const reactiveConfig = new ReactiveConfig(appConfig);
export { reactiveConfig };
```

4. **Configuração criptografada**
```typescript
import CryptoJS from 'crypto-js';

class SecureConfig {
  private encryptionKey: string;
  
  constructor(key: string) {
    this.encryptionKey = key;
  }
  
  encrypt(value: string): string {
    return CryptoJS.AES.encrypt(value, this.encryptionKey).toString();
  }
  
  decrypt(encryptedValue: string): string {
    const bytes = CryptoJS.AES.decrypt(encryptedValue, this.encryptionKey);
    return bytes.toString(CryptoJS.enc.Utf8);
  }
  
  getSecureValue(key: string): string {
    const encryptedValue = import.meta.env[key];
    if (!encryptedValue) return '';
    
    try {
      return this.decrypt(encryptedValue);
    } catch {
      console.error(`Falha ao descriptografar ${key}`);
      return '';
    }
  }
}

// Uso
const secureConfig = new SecureConfig(import.meta.env.VITE_ENCRYPTION_KEY || 'default-key');

const appConfig: AppConfig = {
  api: {
    url: import.meta.env.VITE_API_URL,
    apiKey: secureConfig.getSecureValue('VITE_API_KEY_ENCRYPTED')
  }
};
```

5. **React Hook para configuração**
```typescript
import { createContext, useContext, useEffect, useState } from 'react';

const ConfigContext = createContext<AppConfig>(appConfig);

export const ConfigProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [config, setConfig] = useState<AppConfig>(appConfig);
  
  useEffect(() => {
    // Carregar configuração remota
    const loadRemoteConfig = async () => {
      try {
        const response = await fetch('/api/config');
        const remoteConfig = await response.json();
        setConfig(current => ({ ...current, ...remoteConfig }));
      } catch (error) {
        console.warn('Falha ao carregar configuração remota:', error);
      }
    };
    
    loadRemoteConfig();
  }, []);
  
  return (
    <ConfigContext.Provider value={config}>
      {children}
    </ConfigContext.Provider>
  );
};

export const useConfig = (): AppConfig => {
  const config = useContext(ConfigContext);
  if (!config) {
    throw new Error('useConfig deve ser usado dentro de ConfigProvider');
  }
  return config;
};

export const useFeatureFlag = (flag: keyof FeatureFlags): boolean => {
  const config = useConfig();
  return config.features[flag];
};
```

## Status de implementação
✅ **Configuração básica** - Implementação simples funcional
✅ **Variáveis de ambiente** - Suporte a .env
✅ **Tipagem TypeScript** - Interfaces básicas
✅ **Validação simples** - Verificação de obrigatórias
❌ **Schema validation** - Sem validação robusta
❌ **Configuração remota** - Apenas local
❌ **Hot reload** - Requer restart
❌ **Criptografia** - Valores em texto plano
❌ **React integration** - Sem hooks específicos
❌ **Versionamento** - Sem controle de versão

## Integração com componentes
✅ **httpClient** - Integração completa
✅ **Hooks** - Uso direto das configurações
✅ **Componentes** - Feature flags funcionais
⚠️ **Context API** - Não implementado
⚠️ **Hot reload** - Não suportado

## Próximos passos
1. **CRÍTICO: Implementar schema validation** - Zod ou Joi
2. **Adicionar configuração remota** - API de configuração
3. **React Context** - Provider e hooks
4. **Hot reload** - Atualização sem restart
5. **Criptografia** - Valores sensíveis
6. **Versionamento** - Controle de mudanças
7. **Monitoramento** - Tracking de uso de features
8. **Documentação** - Guia de configuração