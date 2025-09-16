# Plano de Ação: appConfig

## Insights extraídos
- Documento recomenda centralizar configurações de API, cache, refresh e feature flags, além de validar variáveis obrigatórias.【F:docs/endpoints/frontend_appConfig.md†L15-L200】
- Implementação atual em `appConfig.ts` combina `API_CONFIG` (do httpClient) com `ENV_CONFIG`, mas mantém endpoints hardcoded (ex.: `/ranking`, `/tickets`) que não correspondem às rotas reais do backend.【F:frontend/config/appConfig.ts†L12-L101】

## Lacunas identificadas
- Endpoints definidos (`ranking: '/ranking'`, `tickets: '/tickets'`) não refletem caminhos reais (`/technicians/ranking`, `/tickets/new`), causando URLs incorretas se `getApiUrl` for usado diretamente.【F:frontend/config/appConfig.ts†L12-L101】
- Validação de variáveis obrigatórias (ex.: `VITE_API_BASE_URL`) não ocorre; fallback default pode mascarar erro de configuração.【F:docs/endpoints/frontend_appConfig.md†L48-L200】
- Feature flags/documentação `.env.example` não estão sincronizadas com necessidades atuais (alertas, performance, mocks).

## Próximas ações prioritárias
1. **Revisar mapa de endpoints**  
   - Atualizar `endpointsConfig` para refletir rotas reais (`/technicians/ranking`, `/tickets/new`, `/alerts`, etc.) e incluir funções helper específicas (ex.: `getApiUrl('techniciansRanking')`).【F:frontend/config/appConfig.ts†L12-L101】
   - Garantir que `getApiUrl` não duplique `/api` quando `VITE_API_BASE_URL` já inclui o prefixo.
2. **Validar variáveis de ambiente**  
   - Implementar função `validateConfig()` lançando erro claro quando variáveis obrigatórias estiverem ausentes, conforme sugerido na documentação.【F:docs/endpoints/frontend_appConfig.md†L96-L200】
   - Adicionar `.env.example` atualizado com todas as chaves necessárias (API, retries, alertas, performance, toggles de mock).
3. **Consolidar feature flags**  
   - Agrupar flags (`enableRealTimeUpdates`, `enableNotifications`, `enableMocks`) em objeto único e sincronizar com componentes que usam essas flags.
   - Documentar impacto de cada flag no README.

## Prompt sugerido para execução
> **Identidade**: Agente `DashboardDesigner` encarregado de configurações de frontend.
> **Objetivo**: Corrigir endpoints, validar variáveis e alinhar feature flags em `appConfig`.
> **Contexto**: Atualizar `frontend/config/appConfig.ts`, criar/ajustar `.env.example`, revisar componentes que utilizam `getApiUrl` e feature flags.
> **Passos**: (1) Corrigir `endpointsConfig` e helpers, (2) adicionar validação de env + mensagens claras, (3) atualizar documentação/env de exemplo, (4) ajustar consumidores (serviços/hooks).

## Validações recomendadas
- Executar `npm run build` para garantir que `appConfig` não lança erros em produção.
- Teste manual verificando `getApiUrl('techniciansRanking')` e `getApiUrl('ticketsNew')` tanto em dev quanto build.
- Revisar Storybook/Playground para confirmar que feature flags afetam componentes esperados.
