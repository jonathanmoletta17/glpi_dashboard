"""
Worker for polling the GLPI API.

This module defines an asynchronous function that polls the GLPI API for
tickets, converts them into domain objects and stores them in a repository.
It demonstrates how to use the GLPI client, criteria builder and mappers
together. In a production environment this worker might run on a schedule
and publish events to a message bus.
"""

from typing import Iterable, List

from .....packages.glpi_contracts.client.glpi_client import GLPIClient
from .....packages.glpi_contracts.client.criteria_builder import CriteriaSpec, FilterOperator
from .....packages.glpi_contracts.mappers.ticket_mapper import glpi_ticket_to_domain
from .....packages.data_pipeline.repositories.in_memory import TicketRepository


async def poll_glpi(
    base_url: str,
    app_token: str,
    user_token: str,
    repository: TicketRepository,
    *,
    batch_size: int = 100,
) -> None:
    """Poll the GLPI Ticket endpoint and store results in the repository.

    Args:
        base_url: Base URL of the GLPI API (e.g. "https://glpi.example.com/apirest.php").
        app_token: GLPI application token.
        user_token: GLPI user token.
        repository: TicketRepository for persisting domain objects.
        batch_size: Number of tickets to fetch per request.

    Notes:
        This function requests tickets without any filters; in a real
        application you might filter by update date to avoid re-ingesting
        previously processed tickets. Use CriteriaSpec to build complex
        queries.
    """
    # Build criteria to limit results
    criteria = CriteriaSpec().set_limit(batch_size)
    criteria_json = criteria.to_json()
    async with GLPIClient(base_url, app_token, user_token) as client:
        # GLPI endpoints typically start with "/Ticket"
        response_data = await client.get("/Ticket", criteria=criteria_json)
        # GLPI returns a list of ticket dicts under the "data" key in some versions
        items: Iterable[dict]
        if isinstance(response_data, dict) and "data" in response_data:
            items = response_data["data"]
        elif isinstance(response_data, list):
            items = response_data
        else:
            items = []
        tickets: List = []
        for item in items:
            try:
                ticket = glpi_ticket_to_domain(item)
            except Exception:
                # Skip invalid tickets silently; optionally log
                continue
            tickets.append(ticket)
        # Persist tickets
        repository.add_many(tickets)
        # In a real system, publish an event or trigger downstream aggregation here
