# GLPI Dashboard — Implementação Refatorada

Este diretório materializa a arquitetura descrita em `refatorado/glpi_dashboard/*.md`, organizando os aplicativos, pacotes de domínio e recursos de plataforma do novo dashboard GLPI. Todo o código aqui contido segue os princípios de [01_Principios_Arquitetura.md](../01_Principios_Arquitetura.md), os contratos de backend e frontend ([03](../03_Contratos_Backend.md), [04](../04_Contratos_Frontend.md)) e os guardrails de governança de [05_Governanca_Qualidade.md](../05_Governanca_Qualidade.md).

## Estrutura

```
glpi_dashboard/
├── apps/
│   ├── api/                 # FastAPI + GraphQL responsáveis por expor REST/GraphQL documentado
│   ├── worker_ingestion/    # Workers assíncronos que consomem o GLPI e alimentam o pipeline de métricas
│   └── frontend/            # Next.js 14 com roteamento por segmentos e design system modularizado
├── packages/
│   ├── core_domain/         # Entidades de domínio, value objects e invariantes (tickets, técnicos, SLA)
│   ├── glpi_contracts/      # Cliente HTTP, builder de criteria, schemas e mapeadores GLPI → domínio
│   ├── data_pipeline/       # Agregadores, repositórios e casos de uso voltados às métricas
│   └── shared/              # Configuração, logging e monitoramento compartilhados
├── platform/                # Artefatos de infraestrutura, CI/CD e runbooks
├── docs/                    # Documentação gerada (OpenAPI, ADRs, diagramas)
└── tests/                   # Testes unitários, de integração e de contrato
```

## Execução rápida

```bash
cd refatorado/glpi_dashboard/glpi_dashboard
poetry install --with dev,worker,contract
poetry run ingest-glpi --use-fixture  # popula dados usando fixtures anonimizadas
poetry run serve-api                  # sobe a API em http://127.0.0.1:8000
```

Para visualizar o dashboard:

```bash
cd apps/frontend
npm install
npm run dev
```

Defina `NEXT_PUBLIC_API_URL=http://127.0.0.1:8000` para que o frontend consuma a API.

## Observabilidade

- Métricas Prometheus expostas em `/metrics` pela API.
- Logs estruturados com `trace_id` e `span_id` configurados em `packages/shared/logging`.
- Métricas de ingestão (`ingestion.lag`, `glpi.retries`) registradas pelos workers.

## Qualidade

- `poetry run pytest` cobre domínio, aggregators e contratos de criteria.
- `poetry run ruff check` e `poetry run mypy` garantem estilo e tipagem.
- `npm run lint` e `npm run test` (frontend) validam componentes e hooks críticos.

Para mais detalhes consulte o [Roadmap](../06_Roadmap_Implementacao.md) e o [Plano de Tarefas](../09_Plano_Tarefas_Roadmap.md).
