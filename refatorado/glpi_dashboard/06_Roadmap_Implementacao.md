# 06 — Roadmap de Implementação

## Visão Geral
O roadmap prioriza estabilidade e previsibilidade. Cada fase só inicia após os critérios de saída da fase anterior serem atendidos e registrados em checklist compartilhado.

## Fase 0 — Alinhamento & Preparação
- [ ] Aprovar documentos `01` a `05` com stakeholders.
- [ ] Criar RFC de migração formalizando escopo, riscos e plano de comunicação.
- [ ] Provisionar repositório limpo (`glpi_dashboard_refactor`) com CI/CD base configurada.
- [ ] Definir papéis de cada squad/tribo no plano (ingestão, backend, frontend, DevOps).

## Fase 1 — Fundações Técnicas
- [ ] Implementar skeleton da estrutura de pastas proposta (sem lógica de negócio).
- [ ] Configurar toolchain: `poetry`/`uv`, `npm`/`pnpm`, `pre-commit` com hooks obrigatórios.
- [ ] Configurar pipeline CI com estágios `lint`, `tests` (placeholders), `build`.
- [ ] Estabelecer observabilidade básica (logging estruturado, tracing stub, métricas dummy).
- [ ] Criar ADRs iniciais para escolhas de stack (Next.js, FastAPI, Redis, etc.).

**Critérios de saída:** projeto gera build vazio, pipelines passam, documentação atualizada.

## Fase 2 — Ingestão GLPI
- [ ] Construir `packages/glpi_contracts` com cliente HTTP, autenticação e builder de `criteria`.
- [ ] Implementar workers de polling com rotinas de paginação e retries.
- [ ] Definir schemas de eventos (`TicketCreatedV1`, etc.) e registrar no schema registry.
- [ ] Criar _mocks_ do GLPI para testes (`respx`, _fixtures_ reais anonimizados).
- [ ] Medir latência/lag esperado e documentar limites.

**Critérios de saída:** eventos publicados em ambiente de teste, contratos de criteria cobertos por testes automatizados.

## Fase 3 — Núcleo de Métricas
- [ ] Modelar entidades/domínios em `core_domain` (tickets, técnicos, SLA, alertas).
- [ ] Implementar agregadores em `data_pipeline` com armazenamentos temporários (Postgres in-memory).
- [ ] Escrever casos de uso `GetTicketsOverview`, `GetTechnicianRanking`, `GetSlaBreaches`, `GetSystemHealth`.
- [ ] Construir testes unitários e de integração garantindo consistência com eventos de ingestão.
- [ ] Instrumentar métricas técnicas (`ingestion.lag`, `aggregation.duration`).

**Critérios de saída:** casos de uso retornam dados coerentes a partir de eventos simulados, cobertura mínima atingida.

## Fase 4 — API Pública
- [ ] Levantar endpoints REST definidos em `03_Contratos_Backend.md` com FastAPI.
- [ ] Configurar GraphQL gateway (Strawberry ou Ariadne) com esquemas e resolvers.
- [ ] Implementar autenticação JWT + escopos, rate limiting e caching.
- [ ] Gerar documentação OpenAPI/GraphQL automatizada.
- [ ] Criar testes de contrato (Pact) e smoke tests.

**Critérios de saída:** API em ambiente de staging com documentação disponível e testes de contrato verdes.

## Fase 5 — Frontend
- [ ] Criar estrutura Next.js com módulos e design system conforme `04_Contratos_Frontend.md`.
- [ ] Implementar componentes-chave: `TicketsOverviewPanel`, `TechnicianRankingBoard`, `SlaTrendChart`, `SystemHealthPanel`.
- [ ] Integrar React Query + Zustand com serviços de dados.
- [ ] Configurar Storybook, Chromatic e testes (Vitest, Playwright).
- [ ] Implementar telemetria (PostHog/Sentry) com `trace_id`.

**Critérios de saída:** dashboard funcional em staging, Storybook publicado, testes E2E cobrindo fluxos principais.

## Fase 6 — Observabilidade & Confiabilidade
- [ ] Completar painéis Grafana (ingestão, API, frontend).
- [ ] Configurar alertas no PagerDuty/Telegram baseados em SLOs.
- [ ] Realizar _chaos day_ simulando indisponibilidade do GLPI.
- [ ] Documentar runbooks de incidentes e procedimentos de rollback.

**Critérios de saída:** alertas disparam corretamente em testes, runbooks revisados pelo time.

## Fase 7 — Migração & Go-Live
- [ ] Executar backfill histórico controlado.
- [ ] Conduzir testes paralelos (legacy vs refatorado) comparando métricas chave.
- [ ] Treinar usuários finais e atualizar documentação externa.
- [ ] Realizar _canary release_ (5% → 25% → 100%).
- [ ] Arquivar repositório legado e congelar deploys antigos.

**Critérios de saída:** métricas de negócio equivalentes ou melhores que o legado, incidentes zero durante rollout.

## Fase 8 — Pós-Go-Live & Melhoria Contínua
- [ ] Revisão de lições aprendidas e ajustes nos documentos.
- [ ] Planejar incrementos (novos KPIs, automações) com base em feedback.
- [ ] Estabelecer ciclo trimestral de auditoria arquitetural usando estes documentos como baseline.

> Qualquer alteração na ordem ou conteúdo deste roadmap deve ser validada em reunião de arquitetura e registrada em ADR.
