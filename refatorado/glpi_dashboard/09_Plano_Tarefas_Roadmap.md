# 09 — Plano de Tarefas por Fase do Roadmap

Este plano traduz o prompt do **GLPIRefactorOrchestrator** em um backlog executável, cobrindo as fases `0` a `8` do roadmap definido em [06_Roadmap_Implementacao.md](06_Roadmap_Implementacao.md). Cada subtarefa referencia os princípios, contratos e guardrails estabelecidos nos documentos `01` a `07`, garantindo coerência ponta a ponta.

> Antes de iniciar qualquer subtarefa, o responsável deve reavaliar premissas e dependências à luz de novas informações e registrar eventuais ajustes via RFC conforme [05_Governanca_Qualidade.md](05_Governanca_Qualidade.md).

## Convenções Gerais
- **Responsáveis**: agentes definidos no prompt (`GLPIRefactorOrchestrator`, `GLPIDataIngestor`, `MetricsCoreEngineer`, `APIArchitect`, `DashboardDesigner`, `DevOpsGuard`).
- **Referências normativas**: [01_Principios_Arquitetura.md](01_Principios_Arquitetura.md), [02_Estrutura_Pastas.md](02_Estrutura_Pastas.md), [03_Contratos_Backend.md](03_Contratos_Backend.md), [04_Contratos_Frontend.md](04_Contratos_Frontend.md), [05_Governanca_Qualidade.md](05_Governanca_Qualidade.md), [07_Validacao_Completude.md](07_Validacao_Completude.md) e auditoria [docs/AUDITORIA_ARQUITETURA_CONSISTENCIA.md](../docs/AUDITORIA_ARQUITETURA_CONSISTENCIA.md).
- **Evidências**: cada fase exige checklist assinada, relatório de decisões, métricas de qualidade e anexos técnicos (OpenAPI, diagramas, testes, _playbooks_).
- **Guardrails automáticos**: as etapas de lint, testes, observabilidade e segurança listadas em [05_Governanca_Qualidade.md](05_Governanca_Qualidade.md) são obrigatórias e devem ser parametrizadas na pipeline desde a Fase 1.

## Fase 0 — Alinhamento & Preparação
**Objetivo**: estabelecer fundação documental, comunicação e infraestrutura mínima antes da escrita de código.

| ID | Subtarefa | Responsável | Dependências | Riscos & Mitigações | Evidências / Artefatos |
|----|-----------|-------------|--------------|---------------------|------------------------|
| F0-01 | Validar e obter aprovação formal dos documentos `01` a `05` com stakeholders chave. | GLPIRefactorOrchestrator | Nenhuma | Falta de consenso → marcar workshop revisando princípios e estrutura ([01_Principios_Arquitetura.md](01_Principios_Arquitetura.md), [02_Estrutura_Pastas.md](02_Estrutura_Pastas.md)). | Ata da reunião + checklist de aprovação assinada. |
| F0-02 | Elaborar RFC de migração descrevendo escopo, riscos e plano de comunicação. | GLPIRefactorOrchestrator | F0-01 | Escopo mal definido → usar seções da auditoria para contextualizar dívidas atuais. | RFC registrada em `docs/adrs/` com _diff_ de assinatura. |
| F0-03 | Provisionar repositório limpo `glpi_dashboard_refactor` aplicando estrutura inicial de pastas (sem código). | DevOpsGuard | F0-01 | Estrutura divergente → seguir taxonomia descrita em [02_Estrutura_Pastas.md](02_Estrutura_Pastas.md). | Repositório com árvore inicial + _screenshot_ da pipeline vazia. |
| F0-04 | Definir papéis e capacidade de cada agente/squad para fases futuras, alinhando comunicação. | GLPIRefactorOrchestrator | F0-02 | Responsabilidades difusas → publicar matriz RACI referenciando agentes do prompt. | Matriz RACI anexada ao RFC. |

**Qualidade e Observabilidade**
- Habilitar _checklist_ de aderência arquitetação (Import Linter, Deptry, Madge) previsto em [05_Governanca_Qualidade.md](05_Governanca_Qualidade.md).
- Configurar monitoramento básico do repositório (branch protection, templates de PR).

**Critérios de saída**: conforme [06_Roadmap_Implementacao.md](06_Roadmap_Implementacao.md), todos os itens acima concluídos e comunicados.

## Fase 1 — Fundações Técnicas
**Objetivo**: montar esqueleto do monorepo, toolchain e observabilidade básica, sem lógica de negócio.

| ID | Subtarefa | Responsável | Dependências | Riscos & Mitigações | Evidências / Artefatos |
|----|-----------|-------------|--------------|---------------------|------------------------|
| F1-01 | Criar _skeleton_ da estrutura de pastas `apps/`, `packages/`, `platform/`, `docs/`, `tests/`. | DevOpsGuard | F0-03 | Divergência estrutural → aplicar convenções de [02_Estrutura_Pastas.md](02_Estrutura_Pastas.md). | Commit inicial com estrutura vazia revisado por arquitetura. |
| F1-02 | Configurar toolchain (`poetry`/`uv`, `npm`/`pnpm`, `pre-commit`) conforme padrões de [05_Governanca_Qualidade.md](05_Governanca_Qualidade.md). | DevOpsGuard | F1-01 | Hooks bloqueando produtividade → documentar overrides temporários com aprovação. | Arquivo `CONTRIBUTING.md` + pipeline `lint` executando com sucesso. |
| F1-03 | Implementar pipeline CI (`lint`, `tests` placeholder, `build`) e storage de artefatos. | DevOpsGuard | F1-02 | Falta de runners → preparar _self-hosted_ temporário ou usar cloud. | Execução verde em CI com logs arquivados. |
| F1-04 | Configurar observabilidade básica (logging estruturado, tracing stub, métricas dummy) em `shared/monitoring`. | MetricsCoreEngineer | F1-01 | Falta de padrões → seguir princípios de rastreabilidade do [01_Principios_Arquitetura.md](01_Principios_Arquitetura.md). | Pacote `shared.monitoring` com testes unitários e exemplos de uso. |
| F1-05 | Registrar ADRs iniciais para stack (FastAPI, Redis, Next.js, Postgres, ferramentas de tracing). | GLPIRefactorOrchestrator | F1-02 | Escolhas controversas → anexar comparativos e requisitos de compliance. | ADRs publicados em `docs/adrs/`. |

**Qualidade e Observabilidade**
- Executar `ruff`, `mypy`, `eslint`, `stylelint`, `pytest -k smoke` placeholders nas pipelines.
- Publicar métricas dummy (`ingestion.lag = 0`) no endpoint de saúde para garantir instrumentação inicial.

**Critérios de saída**: build vazio gerado, pipelines verdes, documentação atualizada ([06_Roadmap_Implementacao.md](06_Roadmap_Implementacao.md)).

## Fase 2 — Ingestão GLPI
**Objetivo**: construir clientes GLPI, workers de ingestão e garantir domínio sobre `criteria`.

| ID | Subtarefa | Responsável | Dependências | Riscos & Mitigações | Evidências / Artefatos |
|----|-----------|-------------|--------------|---------------------|------------------------|
| F2-01 | Implementar `packages/glpi_contracts` (cliente HTTP com retry/circuit breaker, builder de `criteria`). | GLPIDataIngestor | F1-04 | Quebra de compatibilidade GLPI → reutilizar critérios validados na auditoria (`metrics_service`). | Pacote publicado com testes unitários para `criteria_builder`. |
| F2-02 | Criar _fixtures_ e mocks do GLPI (`respx`, dados anonimizados) para testes automatizados. | GLPIDataIngestor | F2-01 | Dados sensíveis → anonimizar seguindo políticas de segurança (Doc 05). | Diretório `tests/contract/glpi` com _fixtures_ versionadas. |
| F2-03 | Desenvolver workers de polling e agendamento (`worker_ingestion`) com paginação e retries. | GLPIDataIngestor | F2-01 | Lags altos → aplicar métricas `ingestion.lag`, `glpi.retries` conforme [03_Contratos_Backend.md](03_Contratos_Backend.md). | Código do worker + dashboard de métricas dummy. |
| F2-04 | Definir e registrar schemas de eventos (`TicketCreatedV1` etc.) em registry versionado. | MetricsCoreEngineer | F2-02 | Evolução de schema quebrando consumidores → aplicar versionamento `V{major}` documentado. | Schemas publicados + testes de compatibilidade. |
| F2-05 | Documentar latência/lag esperado, limites e _playbook_ de incidentes. | GLPIRefactorOrchestrator | F2-03 | Falta de dados históricos → executar _dry-run_ com mocks e extrapolar cenários. | Relatório em `docs/ingestion/latency.md`. |

**Qualidade e Observabilidade**
- Adicionar testes de contrato GLPI a cada alteração (`pytest` com `respx`).
- Instrumentar métricas `criteria_failures`, `ingestion.lag` e logs com `trace_id`.

**Critérios de saída**: eventos publicados em ambiente de teste, contratos de `criteria` cobertos por testes ([06_Roadmap_Implementacao.md](06_Roadmap_Implementacao.md)).

## Fase 3 — Núcleo de Métricas
**Objetivo**: modelar domínio, agregadores e casos de uso coerentes com eventos ingestados.

| ID | Subtarefa | Responsável | Dependências | Riscos & Mitigações | Evidências / Artefatos |
|----|-----------|-------------|--------------|---------------------|------------------------|
| F3-01 | Modelar entidades e value objects (`Ticket`, `Technician`, `SLA`) em `packages/core_domain`. | MetricsCoreEngineer | F2-04 | Modelagem desalinhada → seguir princípios de domínio do [01_Principios_Arquitetura.md](01_Principios_Arquitetura.md). | Diagramas + testes de invariantes. |
| F3-02 | Implementar agregadores e repositórios (`data_pipeline`) usando Postgres em memória. | MetricsCoreEngineer | F3-01 | Queries lentas → medir `aggregation.duration` e otimizar índices. | Scripts de migração + testes de integração. |
| F3-03 | Codificar casos de uso (`GetTicketsOverview`, `GetTechnicianRanking`, `GetSlaBreaches`, `GetSystemHealth`). | MetricsCoreEngineer | F3-02 | Divergência com contratos → mapear DTOs conforme [03_Contratos_Backend.md](03_Contratos_Backend.md). | Casos de uso com testes unitários/integração. |
| F3-04 | Integrar ingestão com núcleo, garantindo reprocessamento idempotente e _dead-letter_ queue. | GLPIDataIngestor | F3-02 | Perda de eventos → validar idempotência e alertas `dead_letter.count`. | Pipeline E2E com _fixtures_ e métricas. |
| F3-05 | Instrumentar métricas técnicas (`ingestion.lag`, `aggregation.duration`) e dashboards de diagnóstico. | DevOpsGuard | F3-03 | Falta de observabilidade → seguir guardrails de [05_Governanca_Qualidade.md](05_Governanca_Qualidade.md). | Dashboard Grafana inicial + alertas básicos. |

**Qualidade e Observabilidade**
- `pytest` com cobertura mínima (90% domínio, 80% data pipeline) conforme [03_Contratos_Backend.md](03_Contratos_Backend.md).
- Testes de mutação (`mutmut`) nos casos de uso críticos.

**Critérios de saída**: casos de uso retornam dados coerentes a partir de eventos simulados, cobertura mínima atingida ([06_Roadmap_Implementacao.md](06_Roadmap_Implementacao.md)).

## Fase 4 — API Pública
**Objetivo**: expor REST/GraphQL alinhados aos contratos e mecanismos de segurança/caching.

| ID | Subtarefa | Responsável | Dependências | Riscos & Mitigações | Evidências / Artefatos |
|----|-----------|-------------|--------------|---------------------|------------------------|
| F4-01 | Implementar endpoints REST (`/v1/...`) com FastAPI conforme [03_Contratos_Backend.md](03_Contratos_Backend.md). | APIArchitect | F3-03 | Contratos divergentes → gerar OpenAPI e validar com Pact. | Código FastAPI + testes de integração. |
| F4-02 | Configurar gateway GraphQL (Strawberry/Ariadne) com resolvers e _schema stitching_. | APIArchitect | F4-01 | Overfetching → aplicar _projections_ alinhadas aos casos de uso. | Schema GraphQL + testes automatizados. |
| F4-03 | Implementar autenticação JWT, rate limiting e caching (Redis) usando `shared`. | DevOpsGuard | F4-01 | Falhas de segurança → seguir políticas de [05_Governanca_Qualidade.md](05_Governanca_Qualidade.md). | Middleware de auth + testes de segurança. |
| F4-04 | Automatizar documentação OpenAPI/GraphQL e publicar portal de referência. | GLPIRefactorOrchestrator | F4-02 | Documentação desatualizada → pipeline gera docs em cada PR. | Portal de docs hospedado + _artifact_ versionado. |
| F4-05 | Criar testes de contrato (Pact), smoke tests e validações de performance. | APIArchitect | F4-03 | Falta de ambientes → usar ambientes efêmeros via CI. | Relatórios Pact + Playwright API. |

**Qualidade e Observabilidade**
- Pipeline executa `pytest`, `pact-verifier`, análise de segurança (`bandit`, `pip-audit`).
- Monitorar métricas `api.latency`, `api.error_rate`, `cache.hit_ratio`.

**Critérios de saída**: API em staging com documentação disponível e testes verdes ([06_Roadmap_Implementacao.md](06_Roadmap_Implementacao.md)).

## Fase 5 — Frontend
**Objetivo**: construir dashboard Next.js alinhado aos contratos REST/GraphQL e design system.

| ID | Subtarefa | Responsável | Dependências | Riscos & Mitigações | Evidências / Artefatos |
|----|-----------|-------------|--------------|---------------------|------------------------|
| F5-01 | Criar estrutura Next.js (app router) seguindo [02_Estrutura_Pastas.md](02_Estrutura_Pastas.md) e design system conforme [04_Contratos_Frontend.md](04_Contratos_Frontend.md). | DashboardDesigner | F4-01 | Divergência de módulos → mapear `feature modules` como especificado. | Projeto Next.js inicial + Storybook configurado. |
| F5-02 | Implementar componentes principais (`TicketsOverviewPanel`, `TechnicianRankingBoard`, `SlaTrendChart`, `SystemHealthPanel`). | DashboardDesigner | F5-01 | UI inconsistente → usar tokens do design system e contratos de dados [04_Contratos_Frontend.md](04_Contratos_Frontend.md). | Componentes com histórias no Storybook. |
| F5-03 | Integrar serviços de dados (`metricsClient`, React Query, Zustand) com contratos gerados do backend. | DashboardDesigner | F5-02 | Contratos desatualizados → pipeline de codegen roda em cada PR. | Hooks + testes Vitest garantindo filtros. |
| F5-04 | Configurar telemetria (PostHog/Sentry) propagando `trace_id`. | DevOpsGuard | F5-03 | Vazamento de dados → seguir políticas de privacidade (Doc 05). | Configuração validada em ambiente de staging. |
| F5-05 | Executar testes Storybook (Chromatic), Vitest, Playwright E2E e publicar relatórios. | DashboardDesigner | F5-03 | Falta de cobertura → garantir cenários de filtros, ranking e health. | Relatórios de testes + _artifacts_ CI. |

**Qualidade e Observabilidade**
- `eslint`, `stylelint`, `tsc --noEmit`, `vitest`, `playwright` obrigatórios.
- Capturar métricas de uso (`filtros aplicados`, `tempo em página`).

**Critérios de saída**: dashboard funcional em staging, Storybook publicado, testes E2E cobrindo fluxos principais ([06_Roadmap_Implementacao.md](06_Roadmap_Implementacao.md)).

## Fase 6 — Observabilidade & Confiabilidade
**Objetivo**: garantir monitoramento ponta a ponta, alertas e runbooks.

| ID | Subtarefa | Responsável | Dependências | Riscos & Mitigações | Evidências / Artefatos |
|----|-----------|-------------|--------------|---------------------|------------------------|
| F6-01 | Construir painéis Grafana para ingestão, API e frontend com métricas definidas em Docs 03 e 05. | DevOpsGuard | F5-05 | Métricas incompletas → validar cobertura contra lista de métricas obrigatórias. | Dashboards Grafana exportados. |
| F6-02 | Configurar alertas PagerDuty/Telegram baseados em SLOs. | DevOpsGuard | F6-01 | Alertas ruidosos → usar thresholds definidos em `platform/docs/slo.md`. | Alertas testados com simulação. |
| F6-03 | Realizar _chaos day_ simulando indisponibilidades do GLPI e medir recuperação. | GLPIDataIngestor | F6-02 | Falha de rollback → aplicar playbooks criados nas fases anteriores. | Relatório de caos com métricas de MTTR. |
| F6-04 | Documentar runbooks de incidentes e rollback detalhados. | GLPIRefactorOrchestrator | F6-03 | Falta de clareza → incluir _checklists_ passo a passo e contatos. | Runbooks em `platform/docs/`. |

**Qualidade e Observabilidade**
- Validar métricas `ingestion.lag`, `api.error_rate`, `frontend.latency` e alertas correspondentes.
- Rodar smoke tests automáticos pós-alerta para confirmar estabilidade.

**Critérios de saída**: alertas disparando corretamente em testes, runbooks revisados ([06_Roadmap_Implementacao.md](06_Roadmap_Implementacao.md)).

## Fase 7 — Migração & Go-Live
**Objetivo**: executar migração segura, comparação com legado e rollout controlado.

| ID | Subtarefa | Responsável | Dependências | Riscos & Mitigações | Evidências / Artefatos |
|----|-----------|-------------|--------------|---------------------|------------------------|
| F7-01 | Executar backfill histórico com monitoramento de performance e integridade. | GLPIDataIngestor | F6-04 | Carga excessiva → usar _dry-run_ e _feature flag_ de enable/disable. | Relatórios de backfill + métricas. |
| F7-02 | Conduzir testes paralelos (legacy vs refatorado) comparando métricas chave. | MetricsCoreEngineer | F7-01 | Divergências → criar dashboards comparativos e ajustar agregadores. | Relatório de paridade com anexos. |
| F7-03 | Treinar usuários finais e atualizar documentação externa. | GLPIRefactorOrchestrator | F7-02 | Resistência dos usuários → incluir material interativo e FAQ. | Material de treinamento + feedback registrado. |
| F7-04 | Realizar _canary release_ (5% → 25% → 100%) com monitoramento contínuo. | DevOpsGuard | F7-02 | Incidentes → aplicar automatismos de rollback e alertas do Doc 05. | Logs de rollout + métricas de estabilidade. |
| F7-05 | Arquivar repositório legado e congelar deploys antigos. | DevOpsGuard | F7-04 | Necessidade de fallback → manter tag final e instruções de restauração rápida. | Repositório legado arquivado + comunicado oficial. |

**Qualidade e Observabilidade**
- Monitorar SLOs críticos durante rollout (`error_rate`, `lag`, `frontend.core_web_vitals`).
- Validar dados com testes automatizados comparando endpoints (`pytest -m parity`).

**Critérios de saída**: métricas equivalentes ou melhores ao legado, incidentes zero no rollout ([06_Roadmap_Implementacao.md](06_Roadmap_Implementacao.md)).

## Fase 8 — Pós-Go-Live & Melhoria Contínua
**Objetivo**: capturar lições aprendidas, planejar evoluções e institucionalizar auditorias.

| ID | Subtarefa | Responsável | Dependências | Riscos & Mitigações | Evidências / Artefatos |
|----|-----------|-------------|--------------|---------------------|------------------------|
| F8-01 | Conduzir retrospectiva e documentar lições aprendidas. | GLPIRefactorOrchestrator | F7-05 | Ações não priorizadas → vincular _action items_ a backlog com prazos. | Ata + plano de ação. |
| F8-02 | Planejar incrementos (novos KPIs, automações) com base em feedback e métricas. | MetricsCoreEngineer | F8-01 | Escopo inflado → priorizar via RFC e _capacity planning_. | Roadmap trimestral publicado. |
| F8-03 | Estabelecer ciclo trimestral de auditoria arquitetural utilizando os documentos `01` a `08`. | DevOpsGuard | F8-01 | Auditoria negligenciada → criar _calendar_ automatizado e responsáveis fixos. | Checklist de auditoria + lembretes automáticos. |

**Qualidade e Observabilidade**
- Atualizar métricas de arquitetura (`cycle time`, `deploy frequency`, `MTTR`) e comparar com metas do Doc 01.
- Garantir que novas RFCs continuem seguindo governança do Doc 05.

**Critérios de saída**: documentação revisada, melhorias priorizadas, auditorias agendadas ([06_Roadmap_Implementacao.md](06_Roadmap_Implementacao.md)).

## Checklist de Encerramento por Fase
Para cada fase concluída, registrar no mínimo:
1. **Resumo das decisões** com referências às seções relevantes dos documentos `01` a `07`.
2. **Entregáveis** anexados (código, diagramas, testes, dashboards, relatórios).
3. **Riscos emergentes** e ações mitigadoras atualizadas.
4. **Próximos passos** aprovados pelo GLPIRefactorOrchestrator.

> Este documento deve ser atualizado sempre que o prompt ou o roadmap forem ajustados, mantendo rastreabilidade completa das tarefas planejadas.
