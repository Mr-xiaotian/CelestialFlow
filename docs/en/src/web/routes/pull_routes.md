# Pull Routes (GET) — `pull_routes`

> 📅 Last Updated: 2026/06/11

## Purpose

The `pull_routes` module provides all GET endpoints for clients to **pull** data. These endpoints use a **rev (version number) guard** mechanism: when the client passes a `known_rev` that matches the current version, `data: null` is returned to save bandwidth; the full data body is only returned when the data has actually changed.

## Core Function

### `register(router: APIRouter, server: TaskWebServer) -> None`

Registers all 7 GET endpoints on the given `APIRouter`.

| Parameter | Type | Description |
|-----------|------|-------------|
| `router` | `APIRouter` | FastAPI router instance |
| `server` | `TaskWebServer` | Web server instance holding shared state |

---

## Endpoints

### 1. `GET /api/pull_config`

Fetch the frontend configuration.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| — | — | — | No parameters |

**Returns:** `dict[str, Any]` — The complete `server.config` dictionary.

```json
{
  "global": {
    "theme": "dark",
    "autoRefreshEnabled": true,
    "refreshInterval": 5000,
    "language": "zh-CN"
  },
  "dashboard": {
    "historyLimit": 20,
    "showStructureEdgeDelta": false,
    "useTotalPendingInStatus": false,
    "layout": { "left": ["mermaid"], "middle": ["status"], "right": ["progress"] }
  },
  "errors": {
    "pageSize": 10,
    "sortOrder": "newest",
    "jumpToInjectionAfterRetry": true
  },
  "injection": {
    "showInjectableOnly": true
  }
}
```

---

### 2. `GET /api/pull_structure`

Fetch graph structure data (nodes and edges), supports rev guard.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `known_rev` | `int` | `-1` | Version number known to the client |

**Returns:**

| Field | Description |
|-------|-------------|
| `rev` | Current version number |
| `data` | Graph structure dictionary; `null` if `known_rev==rev` |

```json
// With update
{"rev": 5, "data": {"nodes": {"n1": {"label": "Task"}}, "edges": {"n1": []}, "source_nodes": ["n1"]}}
// No update
{"rev": 5, "data": null}
```

---

### 3. `GET /api/pull_status`

Fetch the runtime status of each node, supports rev guard.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `known_rev` | `int` | `-1` | Version number known to the client |

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

Fetch paginated error logs, supports node/keyword filtering and rev guard.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `known_rev` | `int` | `-1` | Version number known to the client |
| `page` | `int` | `1` | Page number (1-based) |
| `page_size` | `int` | `10` | Items per page |
| `node` | `str` | `""` | Filter by node name; empty string has no effect |
| `keyword` | `str` | `""` | Filter by keyword; empty string has no effect |
| `sort_order` | `str` | `"newest"` | Sort order, only supports `newest` / `oldest` |

**Returns:**

| Field | Description |
|-------|-------------|
| `rev` | Current version number |
| `page` | Normalized page number |
| `page_size` | Normalized page size |
| `total` | Total filtered count |
| `total_pages` | Total page count |
| `sort_order` | Effectively applied sort order |
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

Fetch graph topology analysis information, supports rev guard.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `known_rev` | `int` | `-1` | Version number known to the client |

**Returns:** `{"rev": int, "data": dict | None}`

```json
{"rev": 2, "data": {"root_count": 3, "max_depth": 5, ...}}
```

---

### 6. `GET /api/pull_interval`

Fetch the current polling interval.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| — | — | — | No parameters |

**Returns:** `{"interval": float}` — Unit is seconds.

```json
{"interval": 5.0}
```

---

### 7. `GET /api/pull_task_injection`

Fetch and clear the current pending injection task queue. This is a **one-shot consumption** endpoint: after returning, the queue is cleared and the same batch of tasks will not be fetched again.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| — | — | — | No parameters |

**Returns:** `dict[str, list[Any]]` — Mapping from node name to task list. Queue is cleared after reading.

```json
{"StageA": [1, 2, 3], "StageB": [{"id": 4, "val": "x"}]}
```

> Note: Although the current implementation uses GET, this endpoint has side effects, clearing the queue after reading; it is closer to a "consumption interface" than a pure query interface.

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
