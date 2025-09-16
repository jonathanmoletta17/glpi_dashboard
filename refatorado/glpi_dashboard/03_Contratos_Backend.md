# 03 — Contratos do Backend

## 1. Visão Geral
O backend refatorado será composto por três subsistemas cooperantes:

1. **Ingestão** (`apps/worker_ingestion` + `packages/glpi_contracts`)
   - Responsável por consumir a API GLPI usando `criteria` determinísticos.
   - Publica eventos normalizados (`TicketCreated`, `TicketUpdated`, `TechnicianAssignmentChanged`, `SLAClockTicked`).

2. **Core de Métricas** (`packages/core_domain` + `packages/data_pipeline`)
   - Processa eventos, mantém projeções (Postgres/ClickHouse) e expõe casos de uso (`GetTicketsBacklog`, `GetTechnicianRanking`, `GetSlaBreaches`).

3. **API Pública** (`apps/api`)
   - Disponibiliza REST e GraphQL, aplica autenticação/autorizações, caching e rate limiting.

```
GLPI API ──> Ingestão (workers) ──> Event Bus ──> Processadores de Métricas ──> Storage Analítico ──> API ──> Frontend/Integradores
```

## 2. Contextos de Domínio e Casos de Uso
| Contexto          | Casos de uso principais                                | Entradas                                                   | Saídas/Contratos                                                                 |
|-------------------|---------------------------------------------------------|------------------------------------------------------------|----------------------------------------------------------------------------------|
| Tickets           | `GetTicketsOverview`, `GetTicketTimeline`, `SyncTicket` | `ServiceDeskID`, `TimeWindow`, filtros (`status`, `queue`) | DTO `TicketSummary`, coleção `TicketTimelineEvent`, projeção `TicketAging`      |
| Técnicos          | `GetTechnicianRanking`, `GetTechnicianProductivity`     | `TeamID`, `Period`, métricas alvo (`handled`, `sla`)        | DTO `TechnicianScorecard`, `RankingEntry`, breakdown por faixa horária          |
| SLA/Alertas       | `GetSlaBreaches`, `GetAlertRules`, `AckAlert`           | `TimeWindow`, `Severity`, `Channel`                        | DTO `SlaBreach`, `AlertRule`, `AckReceipt`                                      |
| Saúde do Sistema  | `GetIngestionLag`, `GetApiUsage`, `GetDataFreshness`    | `None`                                                     | DTO `LagReport`, `UsageStats`, `FreshnessIndicator`                             |

Cada caso de uso segue o contrato:
- **Input DTO** validado (Pydantic) → `UseCase.execute(input: InputDTO) -> OutputDTO`.
- **Output DTO** serializado apenas pela camada de apresentação (REST/GraphQL), nunca pelos casos de uso.

## 3. Integração com o GLPI
### 3.1 Cliente HTTP
- Baseado em `httpx.AsyncClient` com `retry` exponencial e `circuit breaker`.
- Suporta `async with GLPIClient() as client` garantindo _session pooling_.
- Recebe `criteria` já construídos e injeta filtros padronizados (`is_deleted = 0`, `with_tsl = true`, etc.).

### 3.2 Geração de `criteria`
- Builder declarativo localizado em `packages/glpi_contracts/client/criteria_builder.py`.
- Entrada: `CriteriaSpec` (lista de `Filter`, `Sort`, `Limit`).
- Saída: string JSON conforme padrão GLPI, com validação automática contra _fixtures_.
- Biblioteca garante:
  - Escapagem correta de nomes de campos.
  - Combinação de filtros (`AND`/`OR`) por meio de objetos imutáveis.
  - Templates reutilizáveis para `tickets`, `users`, `groups`, `locations`.

### 3.3 Normalização
- Mapeadores convertem respostas GLPI em Value Objects internos.
- Campos opcionais ou inconsistentes são tratados com `Maybe/Option`, evitando `None` propagado.
- Divergências são logadas e enviadas para a fila de _dead letter_ para inspeção manual.

### 3.4 Contratos de Eventos
Todos os eventos publicados pelo worker seguem schema Avro/JSON Schema versionado:
- `TicketCreatedV1`
- `TicketUpdatedV1`
- `TechnicianAssignmentChangedV1`
- `TicketSlaBreachedV1`

Compatibilidade retroativa garantida com versionamento `V{major}` na chave `type`.

## 4. API Pública
### 4.1 REST
| Método | Endpoint                         | Caso de uso                       | Autenticação | Cache TTL | Observações                                   |
|--------|----------------------------------|------------------------------------|--------------|-----------|------------------------------------------------|
| GET    | `/v1/tickets/overview`           | `GetTicketsOverview`               | Bearer (JWT) | 60 s      | Filtros: `queue`, `priority`, `category`       |
| GET    | `/v1/tickets/{id}/timeline`      | `GetTicketTimeline`                | Bearer       | 0 s       | Retorna eventos ordenados + SLAs              |
| GET    | `/v1/technicians/ranking`        | `GetTechnicianRanking`             | Bearer       | 300 s     | Suporte a paginação e agrupamento por equipe  |
| GET    | `/v1/sla/breaches`               | `GetSlaBreaches`                   | Bearer       | 60 s      | Permite `severity`, `timeWindow`              |
| GET    | `/v1/system/health`              | `GetIngestionLag` + `GetDataFreshness` | Bearer   | 30 s      | Usado para _status page_                     |

### 4.2 GraphQL
- _Schema_ hospedado em `/graphql` com _introspection_ desabilitada em produção.
- _Queries_ principais: `ticketsBacklog`, `technicianLeaderboard`, `slaTrends(period: TimeRange)`.
- _Subscriptions_ opcionais para alertas em tempo real (ex.: via WebSocket + Redis Pub/Sub).

### 4.3 Autorização e Rate Limiting
- JWT com _scopes_: `dash.read`, `dash.admin`, `dash.observability`.
- Limite de 100 req/min por chave + _burst_ de 20 req.
- Possibilidade de emitir _API Keys_ para integrações externas com _quotas_ diferenciadas.

## 5. Persistência e Cache
- **Banco transacional (GLPI)**: apenas leitura via API.
- **Banco analítico**: Postgres inicialmente, com plano de migração para ClickHouse quando volume crescer.
- **Cache**: Redis com _namespaces_ (`metrics:tickets`, `metrics:technicians`). TTLs definidos por endpoint.
- **Storage de arquivos**: S3/GCS para exportações ou anexos.
- **Migrations**: `alembic` aplicado somente no banco analítico.

## 6. Observabilidade e Resiliência
- _Tracing_ completo (`trace_id` propagado desde o worker até a API).
- Métricas técnicas: `ingestion.lag`, `api.latency`, `api.error_rate`, `glpi.retries`, `glpi.criteria_failures`.
- Alertas automáticos quando `lag > 5 min` ou `criteria_failures > 0` em 5 minutos.
- _Chaos testing_: cenários simulados de queda do GLPI, _throttling_ e respostas inconsistentes.

## 7. Contratos de Qualidade
1. **Testes de contrato GLPI** executados a cada mudança no `criteria_builder`.
2. **Snapshot tests** para DTOs expostos pelos casos de uso.
3. **Contract tests** REST/GraphQL usando Pact para garantir compatibilidade com o frontend.
4. **Coverage mínima**: 90% em `core_domain`, 80% em `data_pipeline`, 70% no restante.

> Qualquer alteração nos contratos acima exige atualização desta documentação e revisão com o time de arquitetura.
