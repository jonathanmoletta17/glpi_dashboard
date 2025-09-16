# GLPI Dashboard Refactor Skeleton

This repository contains the skeleton for the refactored GLPI Dashboard as defined in the architecture documents. It provides the initial folder layout for backend (FastAPI), worker ingestion, and frontend (Next.js).

## How to use

- The Python backend is configured via `pyproject.toml` and uses FastAPI and Uvicorn. Run `poetry install` then `uvicorn glpi_dashboard.apps.api.src.main:app --reload` to start the API.
- The worker ingestion module includes a placeholder for polling GLPI. Implement polling logic in `apps/worker_ingestion/src/consumers/glpi_polling.py`.
- The frontend folder uses Next.js with React and includes a placeholder `fetchMetrics` service. Run `npm install` then `npm run dev` to start the client.

This skeleton is a starting point for further development according to the roadmap.
