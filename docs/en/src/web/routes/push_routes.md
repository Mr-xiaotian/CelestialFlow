# Push Routes (POST) — `push_routes`

> 📅 Last Updated: 2026/05/28

## Purpose

The `push_routes` module provides all POST endpoints for the **Reporter** to **push** data to the server. Each push updates the corresponding in-memory store and increments the version number (`store_revs`), allowing clients to detect data changes through Pull routes. Error data supports **cache hit** optimization (skips reload if path + rev are unchanged).

## Core Function

### `register(router: APIRouter, server: TaskWebServer, config_path: str) -> None`

Registers all 8 POST endpoints on the given `APIRouter`.

| Parameter | Type | Description |
|-----------|------|-------------|
| `router` | `APIRouter` | FastAPI router instance |
| `server` | `TaskWebServer` | Web server instance holding shared state |
| `config_path` | `str` | Disk path of the configuration file, used for persisting configuration |

---

## Endpoints

### 1. `POST /api/push_config`

Saves frontend configuration and updates the polling interval.

**Request Body:** `WebConfigModel`

```json
{
  "refreshInterval": "5",
  "dashboard": { "left": ["mermaid"], "middle": ["status"], "right": ["progress"] },
  ...
}
```

**Logic:**
1. Deserializes the request body into a dict and updates `server.config`
2. Recalculates `server.report_interval` based on `refreshInterval`
3. Calls `save_config()` to persist the configuration to `config_path`
4. Returns `{"ok": true}` on success, or HTTP 500 on failure

**Returns:**
- Success: `{"ok": true}`
- Failure: `{"ok": false, "error": "Failed to save config"}` (status code 500)

---

### 2. `POST /api/push_structure`

Updates graph structure data.

**Request Body:** `StructureModel` (contains `items` field)

**Logic:**
1. Writes `data.items` to `server.structure_store`
2. `server.store_revs["structure"]` increments by 1

**Returns:** `{"ok": true}`

---

### 3. `POST /api/push_status`

Updates running status of each node.

**Request Body:** `StatusModel` (contains `timestamp` and `status` fields)

**Logic:**
1. Updates `server.status_timestamp`
2. Updates `server.status_store`
3. `server.store_revs["status"]` increments by 1

**Returns:** `{"ok": true}`

---

### 4. `POST /api/push_errors_meta`

Loads error logs via JSONL file path and version number, supports cache hit.

**Request Body:** `ErrorsMetaModel`

```json
{
  "rev": 5,
  "jsonl_path": "/var/log/celestialflow/errors.jsonl"
}
```

**Logic:**

```
┌─────────────────────────────────────────┐
│  Request arrives                         │
│     ↓                                    │
│  Cache hit? (path and rev unchanged)     │
│     ├─ Yes → Return {"cached": true}    │
│     └─ No →                             │
│          try:                            │
│            Call load_jsonl_logs()        │
│            (reads JSONL in separate      │
│             thread)                      │
│            → Update error_store          │
│            → Update cache (rev+path)     │
│            → store_revs["errors"] += 1   │
│            Return {"cached": false}      │
│          except:                         │
│            Return fallback=need_content  │
└─────────────────────────────────────────┘
```

**Returns:**
- Cache hit: `{"ok": true, "cached": true}`
- Load success: `{"ok": true, "cached": false}`
- Load failure: `{"ok": false, "fallback": "need_content", "reason": "...", "msg": "..."}`

> **Note:** On load failure, the caller should fall back to `push_errors_content` to send error content directly.

---

### 5. `POST /api/push_errors_content`

Directly receives and stores error log list, supports cache hit.

**Request Body:** `ErrorsContentModel`

```json
{
  "rev": 5,
  "jsonl_path": "/var/log/celestialflow/errors.jsonl",
  "errors": [{"ts": "2026-05-28T10:00:00", "error_id": "...", ...}, ...]
}
```

**Logic:**
- On cache hit, skips and returns `{"cached": true}`
- Otherwise writes to `server.error_store` and updates cache and version number

**Returns:**
- Cache hit: `{"ok": true, "cached": true}`
- Write success: `{"ok": true, "cached": false}`

---

### 6. `POST /api/push_analysis`

Updates graph topology analysis info.

**Request Body:** `AnalysisModel` (contains `analysis` field)

**Logic:**
1. Updates `server.analysis_store`
2. `server.store_revs["analysis"]` increments by 1

**Returns:** `{"ok": true}`

---

### 7. `POST /api/push_summary`

Updates global task summary data.

**Request Body:** `SummaryModel` (contains `summary` field)

**Logic:**
1. Updates `server.summary_store`
2. `server.store_revs["summary"]` increments by 1

**Returns:** `{"ok": true}`

---

### 8. `POST /api/push_injection_tasks`

Appends frontend-submitted injection tasks to the pending execution queue.

**Request Body:** `TaskInjectionModel`

**Logic:**
1. Acquires `task_injection_lock`
2. Appends `data.model_dump(mode="json")` to `server.injection_tasks`
3. Releases lock

**Returns:**
- Success: `{"ok": true}`
- Failure: `{"ok": false, "msg": "Task injection failed: ..."}` (status code 500)

---

## Usage Example

### Reporter Pushing Status and Errors

```python
import requests

BASE = "http://localhost:8000"

# Push node status
requests.post(f"{BASE}/api/push_status", json={
    "timestamp": 1716883200.5,
    "status": {"node_a": "running", "node_b": "success"}
})

# Push error logs (meta mode: let server read JSONL itself)
resp = requests.post(f"{BASE}/api/push_errors_meta", json={
    "rev": 5,
    "jsonl_path": "/var/log/celestialflow/errors.jsonl"
})

# If server read fails, fall back to sending content directly
data = resp.json()
if not data["ok"] and data.get("fallback") == "need_content":
    requests.post(f"{BASE}/api/push_errors_content", json={
        "rev": 5,
        "jsonl_path": "/var/log/celestialflow/errors.jsonl",
        "errors": [
            {"ts": "2026-05-28T10:00:00", "error_id": "e1", ...}
        ]
    })

# Push structure data
requests.post(f"{BASE}/api/push_structure", json={
    "items": [{"id": "n1", "type": "task", "label": "MyTask"}]
})
```

### Web Frontend Saving Configuration

```javascript
const resp = await fetch("/api/push_config", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ refreshInterval: "10", dashboard: {...} })
});
const result = await resp.json();
console.log(result.ok ? "Save successful" : "Save failed");
```
