# Pull Routes (GET) — `pull_routes`

> 📅 Last Updated: 2026/06/22

## Purpose

The `pull_routes` module provides all GET endpoints for clients to **pull** data. Most endpoints use a **rev (version number) guard** mechanism: when the client passes a `known_rev` that matches the current version, `data: null` is returned to save bandwidth; the full data body is only returned when the data has actually changed.

## Core Function

### `register(router: APIRouter, server: TaskWebServer) -> None`

Registers all 7 GET endpoints on the given `APIRouter`.

| Parameter | Type | Description |
|-----------|------|-------------|
| `router` | `APIRouter` | FastAPI router instance |
| `server` | `TaskWebServer` | Web server instance holding shared state |

---

## Endpoints

### 1. `GET /api/pull_server_state`

Returns the server-side state needed for reporter synchronization decisions.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `graph_id` | `str` | `""` | Unique identifier of the reporter's current task graph instance |

**Returns:** `dict[str, Any]` — Contains `interval`, `is_current_graph`, `has_structure`, `has_analysis`, `max_event_id_in_fail`.

```json
{
  "interval": 5.0,
  "is_current_graph": true,
  "has_structure": true,
  "has_analysis": false,
  "max_event_id_in_fail": null
}
```

---

### 2. `GET /api/pull_task_injection`

Fetches and clears the current pending injection task queue. This is a **one-shot consumption** endpoint: after returning, the queue is cleared and the same batch of tasks will not be fetched again.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| — | — | — | No parameters |

**Returns:** `dict[str, list[Any]]` — Mapping from node name to task list. Queue is cleared after reading.

```json
{"StageA": [1, 2, 3], "StageB": [{"id": 4, "val": "x"}]}
```

> Note: Although the current implementation uses GET, this endpoint has side effects, clearing the queue after reading; it is closer to a "consumption interface" than a pure query interface.

---

### 3. `GET /api/pull_config`

Fetch the frontend configuration.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| — | — | — | No parameters |

**Returns:** `dict[str, Any]` — The complete `server.config` dictionary, containing `global`, `dashboard`, `errors`, and `injection` groups.

---

### 4. `GET /api/pull_structure`

Fetch graph structure data (nodes and edges), supports rev guard.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `known_rev` | `int` | `-1` | Version number known to the client |

**Returns:** `{"rev": int, "data": dict | None}` — `data` is the structure dictionary (containing `nodes`/`edges`/`source_nodes`); `null` if `known_rev==rev`.

---

### 5. `GET /api/pull_status`

Fetch the runtime status of each node, supports rev guard.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `known_rev` | `int` | `-1` | Version number known to the client |

**Returns:** `{"rev": int, "timestamp": float, "data": dict | None}`

---

### 6. `GET /api/pull_errors`

Fetch paginated error logs, supports node/keyword filtering and rev guard.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `known_rev` | `int` | `-1` | Version number known to the client |
| `page` | `int` | `1` | Page number (1-based) |
| `page_size` | `int` | `10` | Items per page |
| `node` | `str` | `""` | Filter by node name; empty string has no effect |
| `keyword` | `str` | `""` | Filter by keyword; empty string has no effect |
| `sort_order` | `str` | `"newest"` | Sort order, only supports `newest` / `oldest` |

**Returns:** `{"rev": int, "page": int, "page_size": int, "total": int, "total_pages": int, "sort_order": str, "data": list | None}`

---

### 7. `GET /api/pull_analysis`

Fetch graph topology analysis information.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `known_rev` | `int` | `-1` | Version number known to the client (current version always returns full data) |

**Returns:** `{"rev": int, "data": dict | None}` — `data` is `None` when no analysis data has been produced yet.

> **Note**: `pull_analysis` does not check `known_rev` and returns full data every time (if analysis data exists). This behavior differs from `pull_status`/`pull_structure`/`pull_errors`.

## Usage Example

```python
# Poll for structure data, only process when version changes
import requests

# Initial request
resp = requests.get("http://localhost:8000/api/pull_structure")
data = resp.json()
known_rev = data["rev"]
if data["data"] is not None:
    render_structure(data["data"])

# Subsequent polling
while True:
    resp = requests.get(
        "http://localhost:8000/api/pull_structure",
        params={"known_rev": known_rev}
    )
    data = resp.json()
    if data["data"] is not None:
        known_rev = data["rev"]
        render_structure(data["data"])
    time.sleep(5)
```
