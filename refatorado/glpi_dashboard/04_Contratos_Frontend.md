# 04 — Contratos do Frontend

## 1. Visão Geral
O novo dashboard será implementado em **React 18 + TypeScript**, com Next.js (app router) para renderização híbrida e caching avançado. Os componentes consomem apenas os contratos definidos pelo backend (`/v1` REST e `/graphql`). Não há chamadas diretas à API do GLPI.

```
Next.js (app router)
├── Layouts (dashboard, fullscreen, embeddable)
├── Feature modules (tickets, technicians, sla, observability)
├── Shared UI (design system)
└── Infrastructure (state, services, analytics)
```

## 2. Navegação e Fluxos Principais
- **Dashboard Geral** (`/dashboard`): KPIs de backlog, tickets novos, SLA e alertas.
- **Detalhe de Tickets** (`/tickets`): tabela com filtros avançados + modal de timeline.
- **Ranking de Técnicos** (`/technicians`): leaderboard, detalhes de produtividade por período.
- **Saúde do Sistema** (`/observability`): monitoramento do _lag_ de ingestão, status de jobs e uso da API.
- **Administração** (`/admin/alerts`): gestão de alertas e thresholds (feature flag inicial).

Cada rota é definida via `app/(dashboard)/[feature]/page.tsx` com carregamento por segmento.

## 3. Serviços de Dados
- Camada única `app/services/metricsClient.ts` exporta funções:
  - `fetchTicketsOverview(filters: TicketsFilters): Promise<TicketsOverviewDTO>`
  - `fetchTicketTimeline(id: TicketId): Promise<TicketTimelineDTO>`
  - `fetchTechnicianRanking(params: RankingParams): Promise<TechnicianRankingDTO>`
  - `fetchSlaBreaches(window: TimeWindow): Promise<SlaBreachesDTO>`
  - `fetchSystemHealth(): Promise<SystemHealthDTO>`
- Implementação usa `@tanstack/react-query` (server + client components) com caching e revalidação automática.
- Tratamento de erros centralizado (mapeia códigos HTTP para estados de UI).
- Requisições autenticadas via `fetch` com `Authorization: Bearer` obtido do `authClient` (Next Auth ou Auth0), nunca armazenado em `localStorage`.

## 4. Estado e Sincronização
- **React Query** para estados remotos.
- **Zustand** (`app/state/filtersStore.ts`) para estados compartilhados (filtros globais, preferências do usuário).
- **Immer** para mutações imutáveis.
- Persistência de preferências via `IndexedDB` com `idb-keyval`, versão controlada.

## 5. Design System
- Implementar `@glpi/design-system` (pasta `app/design-system/`):
  - `tokens/` (cores, tipografia, espaçamento) em formato CSS variables + TypeScript.
  - `components/` com camadas Atomic Design:
    - `atoms/`: `KpiCard`, `StatusBadge`, `TimeRangePicker`.
    - `molecules/`: `TicketsTable`, `TechnicianChartLegend`.
    - `organisms/`: `TicketsOverviewPanel`, `TechnicianRankingBoard`, `SlaTrendChart`.
  - Documentação via Storybook (rodando isolado em `apps/frontend`).
- Gráficos construídos com `@tanstack/charts` ou `echarts-for-react` encapsulados em componentes reutilizáveis (`LineChart`, `StackedBarChart`).

## 6. Contratos de UI ↔ Dados
| Componente                 | DTO esperado                              | Requisição                       | Revalidação | Estados de erro                               |
|----------------------------|-------------------------------------------|----------------------------------|-------------|-----------------------------------------------|
| `TicketsOverviewPanel`     | `TicketsOverviewDTO`                      | `fetchTicketsOverview`           | 30 s        | `empty`, `glpiLag`, `partialData`, `unauthorized` |
| `TicketTimelineModal`      | `TicketTimelineDTO`                       | `fetchTicketTimeline`            | on-demand   | `notFound`, `stale`, `unauthorized`            |
| `TechnicianRankingBoard`   | `TechnicianRankingDTO`                    | `fetchTechnicianRanking`         | 5 min       | `empty`, `degraded`                            |
| `SlaTrendChart`            | `SlaBreachesDTO`                          | `fetchSlaBreaches`               | 1 min       | `noData`, `glpiLag`                            |
| `SystemHealthPanel`        | `SystemHealthDTO`                         | `fetchSystemHealth`              | 30 s        | `critical`, `warning`, `unknown`               |

Todos os DTOs são importados do pacote `@glpi-dashboard/contracts` (gerado automaticamente a partir do backend).

## 7. Experiência do Usuário e Acessibilidade
- Layout responsivo (mobile-first) com breakpoints: `sm (640px)`, `md (768px)`, `lg (1024px)`, `xl (1280px)`.
- Navegação por teclado e leitores de tela garantidos (`aria-*`, `role` adequados).
- Dark mode padrão, com `prefers-color-scheme` e _toggle_ manual.
- Feedback imediato em loading (`Skeletons`, `Shimmer`) e erros (`InlineAlert`).

## 8. Observabilidade Cliente
- Telemetria via `PostHog` ou `Amplitude` com coleta anônima.
- _Logs_ de erros enviados para Sentry, incluindo `trace_id` recebido do backend.
- Métricas de uso capturadas (`filtros aplicados`, `tempo em página`, `latência percepcionada`).

## 9. Testes e Qualidade
- **Storybook** com `Chromatic` para _visual regression_.
- **Vitest + Testing Library** para testes de unidade/componentes.
- **Playwright** para testes E2E, cobrindo fluxos críticos (dash geral, filtros, ranking, health).
- **Contract tests**: frontend consome _mock server_ gerado a partir do OpenAPI/GraphQL do backend.
- Regras de lint (`eslint`, `typescript-eslint`, `stylelint`) aplicadas em CI.

## 10. Feature Flags e Deploy
- Configuradas via `@glpi-dashboard/flags` (SDK interno) com providers (LaunchDarkly, Unleash ou arquivo JSON).
- Deploy automático em Vercel (ou container em Kubernetes) com _preview_ para cada PR.
- Política de _progressive rollout_: 5% → 25% → 100% com monitoramento da telemetria.

> Alterações de layout ou contrato de dados exigem atualização coordenada com o backend e revisão desta especificação.
