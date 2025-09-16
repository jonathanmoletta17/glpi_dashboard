# Plano de Ação: Hook useMetrics

## Insights extraídos
- Hook atual busca métricas, controla loading/error e faz refresh a cada 30s.【F:docs/endpoints/frontend_useMetrics.md†L9-L63】
- Tipagem interna usa chaves `N1`-`N4`, diferindo do contrato backend (`n1`-`n4`).【F:docs/endpoints/frontend_useMetrics.md†L25-L63】
- Estrutura do hook não expõe metadados (`cached`, `correlation_id`, `tendencias`) além do objeto principal.【F:frontend/services/api.ts†L13-L57】

## Lacunas identificadas
- Hook depende de `apiService.getMetrics` que retorna fallback mock quando não encontra `response.data.data.data`, mascarando inconsistências de contrato.【F:frontend/services/api.ts†L13-L57】
- Falta suporte a filtros (datas, tipos) mesmo sendo previstos pela API, e o interval fixo não considera o volume de dados.【F:docs/endpoints/backend_metrics.md†L16-L20】【F:docs/endpoints/frontend_useMetrics.md†L41-L63】
- Ausência de cache local (ex.: React Query) e invalidação manual dificulta reutilização em múltiplos componentes.

## Próximas ações prioritárias
1. **Realinhar tipagem e parsing**  
   - Atualizar tipo `DashboardMetrics` para chaves em minúsculo e incluir opcional `geral`, `tendencias`, `metadata` (cached, correlation).【F:docs/endpoints/backend_metrics.md†L22-L115】
   - Ajustar hook para receber objeto `ApiResponse<DashboardMetrics>` e expor metadados separados.
2. **Adicionar suporte a filtros**  
   - Permitir `useMetrics({ startDate, endDate, filterType })`, repassando ao serviço e recalculando interval de refresh conforme configuração do usuário.【F:docs/endpoints/backend_metrics.md†L16-L20】
   - Implementar memorização via `useMemo`/`useRef` para evitar refetchs desnecessários.
3. **Melhorar resiliência**  
   - Integrar com biblioteca de data fetching (TanStack Query/SWR) ou construir cache manual com TTL configurável.
   - Expor estado `source` (GLPI vs mock) e `lastUpdated` para UI mostrar badges de confiabilidade.

## Prompt sugerido para execução
> **Identidade**: Agente `DashboardDesigner` encarregado das métricas.
> **Objetivo**: Atualizar `useMetrics` para consumir o contrato real, suportar filtros e expor metadados completos.
> **Contexto**: Modificar `frontend/hooks/useMetrics.ts`, `frontend/services/api.ts`, `frontend/types/api.ts` e testes relacionados.
> **Passos**: (1) Refatorar serviço para retornar envelope correto, (2) atualizar hook com opções de filtros e metadados, (3) adicionar testes com dados reais/mocks, (4) documentar uso no README.

## Validações recomendadas
- `npm run test -- useMetrics` cobrindo novos casos de filtros e metadados.
- Storybook ou playground exibindo badges de fonte (GLPI/Mock) e timestamp atualizado.
- Teste manual com `curl` comparando resposta `/metrics` e dados apresentados pelo hook.
