"""Async GLPI API client with retries and circuit breaker.

This client wraps the GLPI REST API and handles authentication, retries,
and circuit breaking logic. Endpoints should pass pre‑built criteria strings
to the request methods. This is a skeleton; implement actual logic per
GLPI API documentation.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional

import httpx


class CircuitBreakerError(Exception):
    """Raised when the circuit breaker is open and requests are blocked."""


class GLPIClient:
    """Asynchronous client for interacting with GLPI API.

    Usage:
        async with GLPIClient(base_url, app_token, user_token) as client:
            response = await client.get("/Ticket", criteria="{}").
    """

    def __init__(self, base_url: str, app_token: str, user_token: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.app_token = app_token
        self.user_token = user_token
        self._client: Optional[httpx.AsyncClient] = None
        self._failure_count: int = 0
        self._circuit_open: bool = False
        self._reset_timeout: float = 30.0

    async def __aenter__(self) -> "GLPIClient":
        self._client = httpx.AsyncClient()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _request(self, method: str, path: str, *, params: Optional[Dict[str, Any]] = None,
                       json: Optional[Any] = None) -> httpx.Response:
        if self._circuit_open:
            raise CircuitBreakerError("Circuit breaker is open; blocking GLPI request")
        assert self._client is not None, "Client not initialized; use async with GLPIClient()"

        headers = {
            "App-Token": self.app_token,
            "Authorization": f"userToken {self.user_token}",
            "Content-Type": "application/json",
        }
        url = f"{self.base_url}{path}"
        for attempt in range(3):
            try:
                response = await self._client.request(method, url, headers=headers, params=params, json=json, timeout=10)
                response.raise_for_status()
                self._failure_count = 0
                return response
            except (httpx.RequestError, httpx.HTTPStatusError) as exc:
                self._failure_count += 1
                # simple backoff
                await asyncio.sleep(2 ** attempt)
                if self._failure_count >= 5:
                    self._circuit_open = True
                    asyncio.create_task(self._reset_circuit())
                    raise CircuitBreakerError("Circuit breaker opened due to repeated failures") from exc
        raise RuntimeError("Exceeded retry attempts")

    async def _reset_circuit(self) -> None:
        """Reset circuit breaker after timeout."""
        await asyncio.sleep(self._reset_timeout)
        self._failure_count = 0
        self._circuit_open = False

    async def get(self, path: str, *, criteria: Optional[str] = None) -> Dict[str, Any]:
        """GET request to GLPI API.

        Args:
            path: API endpoint path (e.g. "/Ticket")
            criteria: JSON criteria string (optional)

        Returns:
            Parsed JSON response from GLPI.
        """
        params: Dict[str, Any] = {}
        if criteria:
            params["criteria"] = criteria
        response = await self._request("GET", path, params=params)
        return response.json()

    async def post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """POST request to GLPI API."""
        response = await self._request("POST", path, json=payload)
        return response.json()