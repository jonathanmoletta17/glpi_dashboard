# 🔍 Relatório de Análise - Inconsistências Dashboard GLPI

## 📋 Problema Identificado

**Sintoma**: Todas as requisições retornam dados zerados:
```json
{
  "niveis": {
    "n1": { "novos": 0, "pendentes": 0, "progresso": 0, "resolvidos": 0, "total": 0 },
    "n2": { "novos": 0, "pendentes": 0, "progresso": 0, "resolvidos": 0, "total": 0 },
    "n3": { "novos": 0, "pendentes": 0, "progresso": 0, "resolvidos": 0, "total": 0 },
    "n4": { "novos": 0, "pendentes": 0, "progresso": 0, "resolvidos": 0, "total": 0 }
  },
  "novos": 0, "pendentes": 0, "progresso": 0, "resolvidos": 0, "total": 0
}
```

**Configuração Atual**:
- Backend: Porta 5000
- Frontend: Porta 5173
- Projeto: `C:\Users\jonathan-moletta.PPIRATINI\projetos_dashboard\glpidashboard\`

---

## 🎯 Principais Causas Prováveis

### 1. 🔧 Configuração de Proxy Incorreta

**Problema**: Frontend na porta 5173 (Vite padrão) pode não ter proxy configurado corretamente.

**Verificar em `vite.config.ts`**:
```typescript
// ❌ CONFIGURAÇÃO INCORRETA
export default defineConfig({
  server: {
    port: 5173,  // Porta padrão do Vite
    // ❌ PROXY AUSENTE OU INCORRETO
  }
});

// ✅ CONFIGURAÇÃO CORRETA
export default defineConfig({
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
        secure: false,
      },
    },
  },
});
```

### 2. 🌐 Problema na URL Base da API

**Verificar em `httpClient.ts` ou arquivo similar**:
```typescript
// ❌ CONFIGURAÇÃO PROBLEMÁTICA
function getApiBaseUrl(): string {
  // Pode estar retornando URL absoluta em desenvolvimento
  return 'http://localhost:5000';  // Causa problemas de CORS
}

// ✅ CONFIGURAÇÃO CORRETA
function getApiBaseUrl(): string {
  if (import.meta.env.DEV) {
    return '/api';  // URL relativa para usar proxy
  }
  return 'http://localhost:5000';
}
```

### 3. 🔑 Credenciais GLPI Inválidas

**Verificar em arquivo de configuração (`.env`, `docker.env`, `settings.py`)**:
```bash
# ❌ TOKENS EXPIRADOS OU INCORRETOS
GLPI_URL=http://servidor.glpi/apirest.php
GLPI_USER_TOKEN=token_expirado_ou_incorreto
GLPI_APP_TOKEN=app_token_expirado_ou_incorreto

# ✅ VERIFICAR VALIDADE DOS TOKENS
# Testar manualmente:
curl -H "App-Token: SEU_APP_TOKEN" \
     -H "Session-Token: SEU_USER_TOKEN" \
     "http://servidor.glpi/apirest.php/ticket"
```

### 4. ⏱️ Timeout de Conexão

**Verificar configurações de timeout**:
```python
# Backend - settings.py
@property
def API_TIMEOUT(self) -> int:
    return 30  # ❌ Muito baixo para GLPI
    # return 90  # ✅ Valor adequado
```

```typescript
// Frontend - httpClient.ts
const API_CONFIG = {
  TIMEOUT: 10000,  // ❌ 10 segundos muito baixo
  // TIMEOUT: 30000,  // ✅ 30 segundos adequado
};
```

### 5. 🚫 Problemas de CORS

**Verificar configuração CORS no backend**:
```python
# ❌ CORS não inclui porta 5173
CORS_ORIGINS = ["http://localhost:3000", "http://localhost:3001"]

# ✅ CORS incluindo porta correta
CORS_ORIGINS = ["http://localhost:3000", "http://localhost:3001", "http://localhost:5173"]
```

### 6. 📡 Problemas na API GLPI

**Verificações necessárias**:
- Servidor GLPI acessível
- API REST habilitada no GLPI
- Tokens não expirados
- Permissões adequadas para o usuário

---

## 🔍 Checklist de Diagnóstico

### 1. 🧪 Testes de Conectividade

```bash
# Testar backend diretamente
curl http://localhost:5000/api/health
curl http://localhost:5000/api/dashboard

# Testar proxy do frontend
curl http://localhost:5173/api/health
curl http://localhost:5173/api/dashboard

# Testar GLPI diretamente
curl -H "App-Token: SEU_TOKEN" "http://servidor.glpi/apirest.php/ticket"
```

### 2. 📋 Verificações de Configuração

**Frontend (`vite.config.ts`)**:
- [ ] Proxy `/api` configurado
- [ ] Target apontando para `http://localhost:5000`
- [ ] `changeOrigin: true`
- [ ] Porta correta (5173)

**Frontend (`httpClient.ts`)**:
- [ ] URL base retorna `/api` em desenvolvimento
- [ ] Timeout adequado (≥30s)
- [ ] Headers corretos

**Backend (configuração)**:
- [ ] Porta 5000 configurada
- [ ] CORS inclui `http://localhost:5173`
- [ ] Timeout GLPI adequado (≥90s)
- [ ] Tokens GLPI válidos

### 3. 🔧 Verificações de Ambiente

**Variáveis de Ambiente**:
- [ ] `GLPI_URL` correto e acessível
- [ ] `GLPI_USER_TOKEN` válido
- [ ] `GLPI_APP_TOKEN` válido
- [ ] `PORT=5000` no backend
- [ ] `CORS_ORIGINS` inclui porta 5173

---

## 🛠️ Soluções Recomendadas

### 1. 🔧 Corrigir Configuração do Vite

```typescript
// vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path.replace(/^\/api/, '')
      },
    },
  },
})
```

### 2. 🌐 Corrigir httpClient

```typescript
// httpClient.ts
function getApiBaseUrl(): string {
  // Em desenvolvimento, usar proxy relativo
  if (import.meta.env.DEV) {
    return '/api';
  }
  // Em produção, usar URL absoluta
  return import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000';
}

const httpClient = axios.create({
  baseURL: getApiBaseUrl(),
  timeout: 30000, // 30 segundos
  headers: {
    'Content-Type': 'application/json',
  },
});
```

### 3. 🔑 Atualizar Configuração Backend

```python
# settings.py ou arquivo de configuração
class Config:
    # CORS incluindo porta 5173
    CORS_ORIGINS = [
        "http://localhost:3000",
        "http://localhost:3001", 
        "http://localhost:5173"  # ✅ Adicionar esta linha
    ]
    
    # Timeout adequado
    API_TIMEOUT = 90
    GLPI_TIMEOUT = 120
```

### 4. 🔍 Debug e Monitoramento

```typescript
// Adicionar logs para debug
console.log('🔧 Configuração API:', {
  baseURL: httpClient.defaults.baseURL,
  timeout: httpClient.defaults.timeout,
  isDev: import.meta.env.DEV,
  mode: import.meta.env.MODE
});

// Interceptor para log de requisições
httpClient.interceptors.request.use(request => {
  console.log('📡 Requisição:', request.method?.toUpperCase(), request.url);
  return request;
});

httpClient.interceptors.response.use(
  response => {
    console.log('✅ Resposta:', response.status, response.config.url);
    return response;
  },
  error => {
    console.error('❌ Erro:', error.message, error.config?.url);
    return Promise.reject(error);
  }
);
```

---

## 🎯 Plano de Ação Prioritário

### Fase 1: Verificação Imediata
1. **Testar conectividade GLPI** - Verificar se tokens estão válidos
2. **Verificar logs do backend** - Identificar erros de conexão
3. **Testar endpoints diretamente** - Bypass do frontend

### Fase 2: Correção de Configuração
1. **Corrigir proxy Vite** - Garantir redirecionamento correto
2. **Atualizar CORS** - Incluir porta 5173
3. **Ajustar timeouts** - Valores adequados para GLPI

### Fase 3: Validação
1. **Testar fluxo completo** - Frontend → Backend → GLPI
2. **Verificar dados reais** - Confirmar retorno de dados válidos
3. **Monitorar performance** - Tempos de resposta adequados

---

## 📊 Comandos de Teste

```bash
# 1. Testar backend diretamente
curl -v http://localhost:5000/api/dashboard

# 2. Testar com proxy
curl -v http://localhost:5173/api/dashboard

# 3. Verificar CORS
curl -H "Origin: http://localhost:5173" \
     -H "Access-Control-Request-Method: GET" \
     -H "Access-Control-Request-Headers: Content-Type" \
     -X OPTIONS \
     http://localhost:5000/api/dashboard

# 4. Testar GLPI diretamente
curl -H "App-Token: SEU_APP_TOKEN" \
     -H "Session-Token: SEU_USER_TOKEN" \
     "http://servidor.glpi/apirest.php/ticket?range=0-10"
```

---

## 🔍 Indicadores de Sucesso

- ✅ Requisições retornam dados reais (não zerados)
- ✅ Tempo de resposta < 5 segundos
- ✅ Sem erros de CORS no console
- ✅ Logs mostram conexão bem-sucedida com GLPI
- ✅ Dashboard exibe métricas reais

---

## 📝 Conclusão

O problema de dados zerados geralmente está relacionado a:

1. **Configuração de proxy incorreta** (mais provável)
2. **Tokens GLPI expirados ou inválidos**
3. **Problemas de CORS**
4. **Timeouts inadequados**

Siga o plano de ação prioritário para identificar e corrigir a causa raiz. A configuração que funciona no projeto atual (`return '/api'` + proxy Vite) deve ser replicada no outro projeto.

**Próximos Passos**: Implementar as correções sugeridas e testar cada componente isoladamente antes de testar o fluxo completo.