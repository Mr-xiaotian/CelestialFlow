# Pull Routes (GET) — `pull_routes`

> 📅 Last Updated: 2026/05/28

## Purpose

The `pull_routes` module provides all GET endpoints for clients to **pull** data. These endpoints use a **rev (version number) guard** mechanism: when the client passes a `known_rev` that matches the current version, the server returns `data: null` to save bandwidth; full data is only returned when changes have occurred.

## Core Function

### `register(router: APIRouter, server: TaskWebServer) -> None`

Registers all 8 GET endpoints on the given `APIRouter`.

| Parameter | Type | Description |
|-----------|------|-------------|
| `router` | `APIRouter` | FastAPI router instance |
| `server` | `TaskWebServer` | Web server instance holding shared state |

---

## Endpoints

### 1. `GET /api/pull_config`

Fetches frontend configuration.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| — | — | — | No parameters |

**Returns:** `dict[str, Any]` — The complete `server.config` dictionary.

```json
{
  "refreshInterval": "5",
  "dashboard": { "left": ["mermaid"], "middle": ["status"], ... },
  ...
}
```

---

### 2. `GET /api/pull_structure`

Fetches graph structure data (nodes and edges), supports rev guard.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `known_rev` | `int` | `-1` | Version number the client already has |

**Returns:**

| Field | Description |
|-------|-------------|
| `rev` | Current version number |
| `data` | Structure data list; `null` if `known_rev==rev` |

```json
// Updated
{"rev": 5, "data": [{"id": "n1", "type": "task", ...}]}
// No update
{"rev": 5, "data": null}
```

---

### 3. `GET /api/pull_status`

Fetches running status of each node, supports rev guard.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `known_rev` | `int` | `-1` | Version number the client already has |

**Returns:**

| Field | Description |
|-------|-------------|
| `rev` | Current version number |
| `timestamp` | Status timestamp (float) |
| `data` | Node status dictionary; `null` if unchanged |

```json
{"rev": 3, "timestamp": 1716883200.5, "data": {"n1": "success", ...}}
```

---

### 4. `GET /api/pull_errors`

Fetches paginated error logs, supports node/keyword filtering and rev guard.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `known_rev` | `int` | `-1` | Version number the client already has |
| `page` | `int` | `1` | Page number (1-based) |
| `page_size` | `int` | `10` | Items per page |
| `node` | `str` | `""` | Filter by node name; empty string is ignored |
| `keyword` | `str` | `""` | Filter by keyword; empty string is ignored |

**Returns:**

| Field | Description |
|-------|-------------|
| `rev` | Current version number |
| `page` | Normalized page number |
| `page_size` | Normalized page size |
| `total` | Total filtered count |
| `total_pages` | Total page count |
| `data` | Current page error list; `null` if unchanged |

```json
{
  "rev": 12, "page": 1, "page_size": 10,
  "total": 47, "total_pages": 5,
  "data": [{"ts": "...", "error_id": "...", "error_repr": "..."}, ...]
}
```

---

### 5. `GET /api/pull_analysis`

Fetches graph topology analysis info, supports rev guard.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `known_rev` | `int` | `-1` | Version number the client already has |

**Returns:** `{"rev": int, "data": dict | None}`

```json
{"rev": 2, "data": {"root_count": 3, "max_depth": 5, ...}}
```

---

### 6. `GET /api/pull_summary`

Fetches global task summary data, supports rev guard.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `known_rev` | `int` | `-1` | Version number the client already has |

**Returns:** `{"rev": int, "data": dict | None}`

```json
{"rev": 1, "data": {"total": 42, "success": 38, "failed": 4, ...}}
```

---

### 7. `GET /api/pull_interval`

Fetches the current polling interval.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| — | — | — | No parameters |

**Returns:** `{"interval": float}` — in seconds.

```json
{"interval": 5.0}
```

---

### 8. `GET /api/pull_task_injection`

Fetches and clears the current pending injection task queue. This is a **one-shot consumption** endpoint: the queue is emptied after the response, and the same batch of tasks will not be fetched again.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| — | — | — | No parameters |

**Returns:** `list[dict[str, Any]]`

```json
[{"task_id": "...", "params": {...}}, ...]
```

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
