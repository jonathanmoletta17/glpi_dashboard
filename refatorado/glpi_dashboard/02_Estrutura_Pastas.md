# 02 — Estrutura de Pastas Planejada

A estrutura proposta evita sobreposição de responsabilidades, elimina dependências cíclicas e isola código legado. O nível superior da aplicação refatorada ficará assim:

```
glpi_dashboard/
├── apps/
│   ├── api/                 # FastAPI (ou equivalente) expondo REST + GraphQL
│   ├── worker_ingestion/    # Workers assíncronos responsáveis por consumir GLPI e publicar eventos internos
│   └── frontend/            # Dashboard React/Next.js consumindo métricas normalizadas
├── packages/
│   ├── core_domain/         # Entidades, value objects, casos de uso e regras de negócio puras
│   ├── glpi_contracts/      # Clientes, DTOs e mapeadores específicos da API GLPI (criteria inclusos)
│   ├── data_pipeline/       # Agregadores, cálculos de métricas, serviços de cache e normalização
│   └── shared/              # Utilidades (logger, config, autenticação, feature flags)
├── platform/
│   ├── infrastructure/      # Helm, Terraform, Docker, templates de observabilidade, secrets
│   ├── ci_cd/               # Pipelines, workflows, templates de qualidade
│   └── docs/                # Runbooks operacionais e SLOs
├── docs/                    # Documentação técnica gerada automaticamente (OpenAPI, ADRs, relatórios)
└── tests/
    ├── unit/
    ├── integration/
    └── contract/
```

## 1. `apps/`
- **api**
  - `/src/main.py`: ponto de entrada da aplicação.
  - `/src/interfaces/rest/`: controladores REST agrupados por contexto (tickets, técnicos, SLA).
  - `/src/interfaces/graphql/`: _resolvers_ para consultas agregadas.
  - `/src/config/`: carregamento tipado de environment.
  - Depende apenas de pacotes internos (`core_domain`, `data_pipeline`, `shared`).

- **worker_ingestion**
  - `/src/consumers/glpi_polling.py`: fallback de polling usando `criteria` pré-configurados.
  - `/src/consumers/webhook.py`: entrada para _webhooks_ caso o GLPI suporte.
  - `/src/publishers/event_bus.py`: envia mensagens para Kafka/Rabbit/Redis Streams.
  - `/src/schedulers/`: _cron jobs_ para sincronizações completas e _refresh_ de tokens.

- **frontend**
  - `/app/` (Next.js) ou `/src/` (React Vite) com Atomic Design.
  - `/app/services/metricsClient.ts`: gateway único para a API.
  - `/app/state/`: store (Zustand/Redux) com _slices_ por domínio.
  - `/app/components/`: `atoms`, `molecules`, `organisms`, `layouts`.

## 2. `packages/`
- **core_domain**
  - `/tickets/`: entidades, agregados (TicketAggregate), políticas de SLA.
  - `/technicians/`: ranking, produtividade, disponibilidade.
  - `/alerts/`: regras de notificação e thresholds.
  - `/common/`: tipos compartilhados (ServiceDeskID, TimeWindow, SLAStatus).

- **glpi_contracts**
  - `/client/`: wrappers HTTP com _retry_, _circuit breaker_, paginação e geração de `criteria`.
  - `/schemas/`: objetos de transporte validados (Pydantic) espelhando respostas GLPI.
  - `/mappers/`: transforma payloads GLPI → domínio.
  - `/fixtures/`: exemplos versionados para testes de contrato.

- **data_pipeline**
  - `/aggregators/`: cálculos de backlog, SLA, funil.
  - `/repositories/`: abstração sobre bancos analíticos (Postgres, ClickHouse) e caches.
  - `/services/`: composição de agregadores em casos de uso.

- **shared**
  - `/config/`: carregamento de `.env`, _feature flags_, _secrets_.
  - `/logging/`: padrão estruturado com _trace id_.
  - `/monitoring/`: exporters de métricas Prometheus, tracing OpenTelemetry.

## 3. `platform/`
Centraliza tópicos que hoje estão dispersos ou ausentes:
- **infrastructure**: manifests de deploy, módulos Terraform, scripts de bootstrap.
- **ci_cd**: pipelines com lint, testes, _contract tests_, _security scans_ e promoção controlada.
- **docs**: manuais operacionais, playbooks de incidentes, SLO/SLA.

## 4. `docs/`
Documentação gerada automaticamente e artefatos que acompanham o código (ex.: OpenAPI, diagramas). O diretório atual `docs/` será migrado gradualmente para cá, respeitando uma taxonomia única.

## 5. `tests/`
Estrutura padronizada:
- `unit/` alinhado com módulos de `packages/`.
- `integration/` focado em orquestrações (API ↔ cache ↔ GLPI mock).
- `contract/` validando compatibilidade com GLPI (`criteria`, esquemas) e frontend (Pact ou MSW). Nenhum teste unitário toca rede externa.

## 6. Isolamento do Código Legado
- **`legacy/` removido**: qualquer necessidade de referência ficará em um repositório arquivado ou em anexos de documentação.
- **Migração assistida**: componentes que forem reaproveitados precisam passar por reescrita para se adequarem aos padrões anteriores. Copiar e colar é proibido.

## 7. Convenções Transversais
- Nomenclatura consistente (`snake_case` para Python, `camelCase`/`PascalCase` para TypeScript/React).
- Imports absolutos baseados em módulos (`from packages.core_domain.tickets import ...`).
- _Lint_ padronizado (`ruff`, `mypy`, `eslint`, `stylelint`).
- Arquivos `__init__.py` apenas quando necessário, com exportações explícitas.

> Qualquer novo diretório deve ser registrado aqui antes de existir no código-fonte.
