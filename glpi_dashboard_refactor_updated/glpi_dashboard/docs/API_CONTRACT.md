# API Contract

This document describes the REST endpoints exposed by the GLPI Dashboard
API. The API returns JSON responses and follows conventional HTTP
semantics (2xx for success, 4xx for client errors, 5xx for server
errors).

## Base URL

The API is served at `/` by the FastAPI application. Endpoints are
prefixed by their resource name.

## Endpoints

### `GET /`

Health check endpoint. Returns a simple JSON with a message.

Response body:

```json
{ "message": "GLPI Dashboard API is up" }
```

### `GET /tickets/metrics`

Returns aggregated metrics over all tickets currently stored in the
repository.

Response body:

```json
{
  "total_count": 42,
  "new_count": 5,
  "in_progress_count": 10,
  "resolved_count": 20,
  "closed_count": 7,
  "pending_count": 0,
  "average_resolution_time_hours": 3.5
}
```

### `GET /tickets/technicians/performance`

Returns performance metrics for each technician. The keys of the
top‑level object are technician IDs and the values are metric objects.

Response body:

```json
{
  "1": {
    "technician_id": 1,
    "ticket_count": 10,
    "resolved_ticket_count": 8,
    "average_resolution_time_hours": 2.7,
    "satisfaction_score": null
  },
  "2": {
    "technician_id": 2,
    "ticket_count": 5,
    "resolved_ticket_count": 3,
    "average_resolution_time_hours": 4.0,
    "satisfaction_score": null
  }
}
```

## Error Responses

If an error occurs, the API returns an appropriate HTTP status code and
body. For example, if the repository is unavailable, the API may return
HTTP 503 with a JSON body containing an error description.