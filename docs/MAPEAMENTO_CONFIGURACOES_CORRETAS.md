# 🔧 Mapeamento de Configurações Corretas - GLPI Dashboard

## 📋 Resumo Executivo

Este documento mapeia as **inconsistências críticas** encontradas entre frontend e backend e fornece as **configurações corretas** para resolver os problemas de comunicação.

## 🚨 Problemas Identificados

### 1. **INCONSISTÊNCIA CRÍTICA: URLs e Portas**

#### ❌ Configuração Atual (INCORRETA)
- **Backend .env**: `PORT=5000` e `BACKEND_API_URL=http://localhost:8000`
- **Frontend .env**: `VITE_API_BASE_URL=http://backend:5000/api`
- **Vite proxy**: Target `http://localhost:5000`
- **Backend settings.py**: Padrão `BACKEND_API_URL=http://localhost:8000`

#### ✅ Configuração Correta
```bash
# Backend .env
PORT=5000
BACKEND_API_URL=http://localhost:5000  # ← CORRIGIR: deve ser 5000, não 8000
HOST=0.0.0.0

# Frontend .env
VITE_API_BASE_URL=http://localhost:5000/api  # ← CORRIGIR: localhost, não backend
```

### 2. **INCONSISTÊNCIA: Contratos de Dados**

#### ❌ Problemas nos Tipos

**Frontend (api.ts)**:
```typescript
export interface TechnicianRanking {
  id: string;        // ← ERRO: Backend usa int
  name: string;
  level: string;
  // ... outros campos diferentes
}
```

**Backend (dashboard.py)**:
```python
class TechnicianRanking(BaseModel):
    id: int           # ← Backend usa int, não string
    name: str
    ticket_count: int # ← Campo ausente no frontend
    level: str
```

## 🛠️ Correções Necessárias

### 1. Corrigir Backend .env

```bash
# ===== ARQUIVO: backend/.env =====
# Ambiente Flask
FLASK_ENV=dev
FLASK_DEBUG=true

# Segurança
SECRET_KEY=your-secret-key-here

# ⭐ CORREÇÃO CRÍTICA: Porta e Host
PORT=5000
HOST=0.0.0.0

# ⭐ CORREÇÃO CRÍTICA: Backend API URL
BACKEND_API_URL=http://localhost:5000  # ← ERA: http://localhost:8000

# GLPI API (manter como está)
GLPI_URL=http://cau.ppiratini.intra.rs.gov.br/glpi/apirest.php
GLPI_USER_TOKEN=TQdSxqg2e56PfF8ZJSX3iEJ1wCpHwhCkQJ2QtRnq
GLPI_APP_TOKEN=aY3f9F5aNHJmY8op0vTE4koguiPwpEYANp1JULid

# Modo Mock
USE_MOCK_DATA=false

# ⭐ CORREÇÃO: CORS Origins para desenvolvimento
CORS_ORIGINS=http://localhost:3001,http://localhost:5173,http://127.0.0.1:3001,http://127.0.0.1:5173
```

### 2. Corrigir Frontend .env

```bash
# ===== ARQUIVO: frontend/.env =====
# 🌐 Configurações da API
# ⭐ CORREÇÃO CRÍTICA: URL da API
VITE_API_BASE_URL=http://localhost:5000/api  # ← ERA: http://backend:5000/api
VITE_API_URL=http://localhost:5000/api       # ← ERA: http://backend:5000/api
VITE_API_TIMEOUT=30000
VITE_API_RETRY_ATTEMPTS=3
VITE_API_RETRY_DELAY=1000

# 📊 Configurações de Log e Debug
VITE_LOG_LEVEL=info
VITE_SHOW_PERFORMANCE=true   # ← Ativar para debug
VITE_SHOW_API_CALLS=true     # ← Ativar para debug
VITE_SHOW_CACHE_HITS=false

# 🎯 Configurações de Ambiente
VITE_APP_NAME=GLPI Dashboard
VITE_APP_VERSION=1.0.0
```

### 3. Corrigir Tipos do Frontend

```typescript
// ===== ARQUIVO: frontend/types/api.ts =====

// ⭐ CORREÇÃO: Interface TechnicianRanking
export interface TechnicianRanking {
  id: number;                    // ← CORRIGIDO: era string, agora number
  name: string;
  ticket_count: number;          // ← ADICIONADO: campo do backend
  level: string;
  performance_score?: number;    // ← ADICIONADO: campo do backend
  
  // Campos opcionais para compatibilidade
  rank?: number;
  total?: number;
  score?: number;
  ticketsResolved?: number;
  ticketsInProgress?: number;
  averageResolutionTime?: number;
  
  // Campos de identificação de fonte
  data_source: 'glpi' | 'mock';
  is_mock_data: boolean;
}

// ⭐ CORREÇÃO: Interface DashboardMetrics
export interface DashboardMetrics {
  // Campos principais do backend
  novos: number;
  pendentes: number;
  progresso: number;
  resolvidos: number;
  total: number;
  
  // Estrutura de níveis
  niveis: {
    n1: LevelMetrics;
    n2: LevelMetrics;
    n3: LevelMetrics;
    n4: LevelMetrics;
    // ⚠️ NOTA: 'geral' é calculado no frontend, não vem do backend
  };
  
  tendencias: {
    novos: string;
    pendentes: string;
    progresso: string;
    resolvidos: string;
  };
  
  timestamp: string;
  period_start?: string;
  period_end?: string;
  
  // Campos de identificação de fonte
  data_source: 'glpi' | 'mock';
  is_mock_data: boolean;
}
```

### 4. Atualizar httpClient.ts

```typescript
// ===== ARQUIVO: frontend/services/httpClient.ts =====

// Função que determina a URL base da API baseada no ambiente
function getApiBaseUrl(): string {
  // Em desenvolvimento, usa proxy relativo
  if (process.env.NODE_ENV === 'development') {
    return '/api';  // ⭐ Mantém proxy do Vite
  }
  
  // ⭐ CORREÇÃO: Em produção, usa URL das variáveis de ambiente
  return import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api';
}

export const API_CONFIG = {
  BASE_URL: getApiBaseUrl(),
  TIMEOUT: parseInt(import.meta.env.VITE_API_TIMEOUT || '30000'),
  RETRY_ATTEMPTS: parseInt(import.meta.env.VITE_API_RETRY_ATTEMPTS || '3'),
  RETRY_DELAY: parseInt(import.meta.env.VITE_API_RETRY_DELAY || '1000'),
};
```

### 5. Verificar vite.config.ts

```typescript
// ===== ARQUIVO: frontend/vite.config.ts =====

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './'),
    },
  },
  server: {
    port: 3001,        // ⭐ Porta do frontend
    strictPort: true,
    allowedHosts: true,
    proxy: {
      '/api': {
        target: 'http://localhost:5000',  // ⭐ CORRETO: aponta para porta 5000
        changeOrigin: true,
        secure: false,
        configure: (proxy, options) => {
          proxy.on('error', (err, req, res) => {
            console.log('proxy error', err);
          });
          proxy.on('proxyReq', (proxyReq, req, res) => {
            console.log('Sending Request to the Target:', req.method, req.url);
          });
          proxy.on('proxyRes', (proxyRes, req, res) => {
            console.log('Received Response from the Target:', proxyRes.statusCode, req.url);
          });
        },
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
  },
})
```

## 🔄 Fluxo de Comunicação Correto

### Desenvolvimento
```
Frontend (localhost:3001) 
    ↓ requisição para /api/health
Vite Proxy 
    ↓ redireciona para http://localhost:5000/api/health
Backend (localhost:5000)
    ↓ resposta JSON
Frontend recebe dados
```

### Produção
```
Frontend (dominio.com)
    ↓ requisição para http://backend-url:5000/api/health
Backend (backend-url:5000)
    ↓ resposta JSON com CORS correto
Frontend recebe dados
```

## 🧪 Comandos de Teste

### 1. Testar Backend Diretamente
```powershell
# Testar se backend está respondendo
Invoke-WebRequest -Uri "http://localhost:5000/api/health" -Verbose

# Testar CORS
Invoke-WebRequest -Uri "http://localhost:5000/api/health" -Headers @{"Origin"="http://localhost:3001"} -Verbose
```

### 2. Testar Proxy do Frontend
```powershell
# Com frontend rodando, testar proxy
curl -v http://localhost:3001/api/health
```

### 3. Testar Endpoints Principais
```powershell
# Métricas do dashboard
Invoke-WebRequest -Uri "http://localhost:5000/api/metrics" -Verbose

# Ranking de técnicos
Invoke-WebRequest -Uri "http://localhost:5000/api/technicians/ranking" -Verbose

# Tickets novos
Invoke-WebRequest -Uri "http://localhost:5000/api/tickets/new" -Verbose
```

## 🚀 Sequência de Inicialização

### 1. Aplicar Correções
```bash
# 1. Corrigir backend/.env
# 2. Corrigir frontend/.env
# 3. Corrigir frontend/types/api.ts
```

### 2. Reiniciar Serviços
```bash
# Terminal 1: Backend
cd backend
python -m flask run --host=0.0.0.0 --port=5000

# Terminal 2: Frontend
cd frontend
npm run dev
```

### 3. Verificar Comunicação
```bash
# Testar health check via proxy
curl http://localhost:3001/api/health

# Testar health check direto
curl http://localhost:5000/api/health
```

## 📊 Checklist de Validação

- [ ] Backend rodando na porta 5000
- [ ] Frontend rodando na porta 3001
- [ ] Proxy do Vite configurado para localhost:5000
- [ ] CORS configurado para localhost:3001
- [ ] Tipos TypeScript alinhados com schemas Python
- [ ] Variáveis de ambiente corretas
- [ ] Health check funcionando via proxy
- [ ] Health check funcionando direto
- [ ] Endpoints principais respondendo
- [ ] Dados sendo renderizados no frontend

## 🔍 Debugging

### Logs Importantes
```bash
# Backend: Verificar se está ouvindo na porta correta
* Running on http://0.0.0.0:5000

# Frontend: Verificar se proxy está funcionando
Sending Request to the Target: GET /api/health
Received Response from the Target: 200 /api/health

# Browser: Verificar se não há erros de CORS
# Deve aparecer: Access-Control-Allow-Origin: http://localhost:3001
```

## 🎯 Resultado Esperado

Após aplicar todas as correções:
1. ✅ Backend responde em `http://localhost:5000`
2. ✅ Frontend acessa via proxy `http://localhost:3001/api/*`
3. ✅ CORS permite requisições do frontend
4. ✅ Tipos de dados são consistentes
5. ✅ Dashboard carrega dados corretamente

---

**📝 Nota**: Este mapeamento resolve as inconsistências críticas identificadas. Após aplicar as correções, o sistema deve funcionar corretamente tanto em desenvolvimento quanto em produção.