# GLPI Dashboard Refactor – Architecture Overview

This document provides a high‑level overview of the architecture for the
refactored GLPI dashboard project. It is intended to guide contributors
through the main packages, modules and their responsibilities.

## Packages

### `apps`

* `api`: FastAPI application that exposes REST (and eventually GraphQL)
  endpoints. It depends on the data pipeline and domain packages to
  provide aggregated data. It instantiates shared repositories and
  registers routers.
* `worker_ingestion`: Asynchronous workers responsible for ingesting data
  from GLPI (or other sources). Workers poll external APIs, convert
  responses into domain objects via mappers and persist them to
  repositories or publish events.
* `frontend`: Next.js application that consumes the API and presents
  dashboards to the user. It uses React Query and a design system.

### `packages`

* `glpi_contracts`: Contains the `GLPIClient` for interacting with the GLPI
  REST API, a `CriteriaSpec` builder to compose GLPI queries, mappers
  translating GLPI payloads into domain models and Pydantic schemas for
  validating API responses.
* `core_domain`: Pure business objects representing tickets, technicians
  and alerts. These classes are dataclasses with no external dependencies.
  Enumerations for ticket status, priority and alert level live in
  `core_domain.common`.
* `data_pipeline`: Houses aggregators that compute summary metrics and
  repositories that store domain objects. Aggregators take collections of
  domain entities and return high level metrics; repositories provide
  simple persistence mechanisms (currently in‑memory).

### `platform`

* This directory will eventually contain infrastructure definitions, CI/CD
  configuration and observability instrumentation. It is currently
  empty but reserved for future expansion.

## Data Flow

1. **Ingestion** – `apps/worker_ingestion` uses `GLPIClient` to fetch
   tickets from the GLPI API. The raw JSON is converted into
   `core_domain` objects via mappers and persisted via repositories.
2. **Aggregation** – When the API is called, the `data_pipeline`
   aggregators compute metrics over the current repository contents.
3. **Presentation** – The `frontend` uses React Query to call the API
   endpoints and display the metrics in a dashboard.

This modular approach makes it easy to test and evolve each component
independently. For instance, a persistent storage implementation can be
added by implementing the repository interfaces and injecting them into
the API and workers.