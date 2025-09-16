# Implementation Roadmap

This roadmap outlines the major phases and tasks for building the
refactored GLPI dashboard. It is based on the high‑level roadmap
documents in `refatorado/glpi_dashboard/` and adapted to the
implementation in this repository.

## Phase 1: Skeleton & Setup

- [x] Establish repository structure with `apps/`, `packages/`,
  `platform/`, `docs/` and `tests/` directories.
- [x] Create basic Python project using Poetry and TypeScript project
  using pnpm (see `pyproject.toml` and `package.json`).
- [x] Add `GLPIClient` and `CriteriaSpec` builder to interact with
  GLPI API.

## Phase 2: Domain & Data Pipeline

- [x] Define domain models for tickets, technicians and alerts using
  Python dataclasses.
- [x] Implement enumerations for ticket statuses and priorities.
- [x] Develop aggregators for ticket metrics and technician performance.
- [x] Provide in‑memory repositories for storing domain objects.
- [ ] Design domain events and event bus (future work).

## Phase 3: Data Ingestion

- [x] Implement a polling worker that uses `GLPIClient` to fetch
  tickets from the GLPI API, maps them to domain objects and stores
  them in the repository.
- [ ] Add pagination and date‑based filtering to avoid duplicate
  ingestion.
- [ ] Publish events to a message bus or queue for downstream
  processing.

## Phase 4: API Layer

- [x] Build a FastAPI application with a health check endpoint.
- [x] Add REST endpoints for aggregated ticket metrics and technician
  performance.
- [ ] Expose additional endpoints (e.g. individual ticket CRUD) and
  GraphQL interface.
- [ ] Implement proper dependency injection for repositories and
  services.

## Phase 5: Front‑End

- [x] Set up Next.js with React and tanstack/react‑query.
- [x] Provide service functions and hooks to fetch ticket metrics and
  technician performance from the API.
- [ ] Implement dashboard pages and components using the design system.
- [ ] Add state management with Zustand and integrate with React Query.

## Phase 6: Testing & Observability

- [x] Write unit tests for aggregator functions.
- [ ] Add tests for API routes using `pytest` and `httpx` test client.
- [ ] Configure logging and instrumentation for observability.
- [ ] Write contract tests to ensure API and front‑end stay in sync.

## Phase 7: Documentation & Governance

- [x] Create architecture and API contract documentation.
- [ ] Write ADRs (Architecture Decision Records) to document design
  choices.
- [ ] Set up CI/CD pipelines with linting, tests and automatic
  deployment.
- [ ] Establish coding standards, code review guidelines and merge
  policies.