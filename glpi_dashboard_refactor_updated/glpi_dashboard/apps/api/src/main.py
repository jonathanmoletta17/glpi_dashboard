"""
Main entrypoint for the GLPI Dashboard API.

This module instantiates the FastAPI application, registers routers and
provides shared dependencies such as the in-memory ticket repository.
"""

from fastapi import FastAPI

from .....packages.data_pipeline.repositories.in_memory import TicketRepository
from .interfaces.rest import tickets as tickets_router


# Shared repository instance; in a real deployment this would be replaced
# by a persistent datastore or injected via dependency management.
ticket_repository = TicketRepository()

# Create FastAPI app
app = FastAPI(title="GLPI Dashboard API", version="0.1.0")

@app.get("/")
def root() -> dict:
    """Health check endpoint."""
    return {"message": "GLPI Dashboard API is up"}

# Include routers
app.include_router(tickets_router.router)
