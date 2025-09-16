# Plano de Ação: Cliente HTTP (httpClient.ts)

## Insights extraídos
- Cliente atual define `BASE_URL` dinamicamente (`/api` em desenvolvimento, `VITE_API_BASE_URL` em produção) e configura retries com backoff manual.【F:frontend/services/httpClient.ts†L14-L99】
- Documentação enfatiza interceptadores para logging, enriquecimento de erros e cabeçalhos adicionais.【F:docs/endpoints/frontend_httpClient.md†L27-L183】

## Lacunas identificadas
- Configuração duplicada entre `httpClient.ts` (usa `API_CONFIG`) e `appConfig.api` (espera `apiUrl`), podendo gerar inconsistência de base URL.【F:frontend/services/httpClient.ts†L14-L58】【F:frontend/config/appConfig.ts†L6-L85】
- Retries são implementados manualmente mas não respeitam cabeçalhos `Retry-After` nem exibem jitter configurável, mesmo após melhorias recentes no backend.【F:frontend/services/httpClient.ts†L60-L104】
- Logs condicionados a `process.env.NODE_ENV` (API do Vite) podem não funcionar em build ESM; recomendável usar `import.meta.env`.

## Próximas ações prioritárias
1. **Unificar fonte da base URL**  
   - Centralizar cálculo da base URL em `appConfig` e reutilizar no cliente HTTP (evitar divergência entre `API_CONFIG.BASE_URL` e `appConfig.api.BASE_URL`).【F:frontend/services/httpClient.ts†L14-L38】【F:frontend/config/appConfig.ts†L12-L99】
   - Garantir suporte a caminhos relativos quando `VITE_API_BASE_URL` inclui `/api` explícito.
2. **Melhorar estratégia de retry**  
   - Respeitar cabeçalhos `Retry-After` e incluir jitter exponencial configurável via env (`VITE_API_RETRY_*`).【F:frontend/services/httpClient.ts†L60-L104】
   - Registrar métricas de tentativa (`retryCount`) para observabilidade.
3. **Higienizar logging e headers**  
   - Trocar `process.env.NODE_ENV` por `import.meta.env.DEV/PROD` para compatibilidade com Vite.【F:frontend/services/httpClient.ts†L32-L52】
   - Permitir injeção opcional de header `X-Correlation-ID` (gerado no front) para rastrear chamadas.

## Prompt sugerido para execução
> **Identidade**: Agente `GLPIDataIngestor` focado em infraestrutura de cliente HTTP.
> **Objetivo**: Consolidar configuração do `httpClient`, aprimorar retries e alinhar logging com Vite.
> **Contexto**: Atualizar `frontend/services/httpClient.ts` e `frontend/config/appConfig.ts`; revisar uso em `apiService` e hooks.
> **Passos**: (1) Criar utilitário único para base URL, (2) implementar retry com jitter/Retry-After, (3) ajustar logs/headers e adicionar testes.

## Validações recomendadas
- `npm run test -- httpClient` exercitando interceptadores e retries com mocks (ex.: axios-mock-adapter).
- Teste manual no browser verificando base URL correta tanto em dev (proxy `/api`) quanto em build (`VITE_API_BASE_URL`).
- Monitorar console para garantir logs controlados e presença de `X-Correlation-ID` quando habilitado.
