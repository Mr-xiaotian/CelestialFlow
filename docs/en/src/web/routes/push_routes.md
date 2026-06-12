# Push Routes (POST) — `push_routes`

> 📅 Last Updated: 2026/06/11

## Purpose

The `push_routes` module provides all POST endpoints for the **Reporter** to **push** data to the server. Each push updates the corresponding in-memory store and increments the version number (`store_revs`), allowing clients to detect data changes via Pull routes. Error data supports **cache hit** optimization (skip reloading if path + rev are unchanged).

## Core Function

### `register(router: APIRouter, server: TaskWebServer, config_path: str) -> None`

Registers all 7 POST endpoints on the given `APIRouter`.

| Parameter | Type | Description |
|-----------|------|-------------|
| `router` | `APIRouter` | FastAPI router instance |
| `server` | `TaskWebServer` | Web server instance holding shared state |
| `config_path` | `str` | Disk path of the configuration file, used for persisting configuration |

---

## Endpoints

### 1. `POST /api/push_config`

Save frontend configuration and update the polling interval.

**Request body:** `WebConfigModel`

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

**Logic:**
1. Deserialize the request body into a dict, update `server.config`
2. Recalculate `server.report_interval` based on the `refreshInterval` value
3. Call `save_config()` to persist the configuration to `config_path`
4. Return `{"ok": true}` on success, HTTP 500 on failure

> Note: The current implementation updates in-memory `server.config` and `server.report_interval` first, then attempts to write to disk; if `save_config()` fails, the request returns 500, but the in-process configuration has already changed.

**Returns:**
- Success: `{"ok": true}`
- Failure: `{"ok": false, "error": "Failed to save config"}` (status code 500)

---

### 2. `POST /api/push_structure`

Update graph structure data.

**Request body:** `StructureModel` (contains a `structure` field)

**Logic:**
1. Atomically write `data.structure` into `server.structure_store`
2. Increment `server.store_revs["structure"]` by 1

**Returns:** `{"ok": true}`

---

### 3. `POST /api/push_status`

Update the runtime status of each node.

**Request body:** `StatusModel` (contains `timestamp` and `status` fields)

**Logic:**
1. Update `server.status_timestamp`
2. Update `server.status_store`
3. Increment `server.store_revs["status"]` by 1

**Returns:** `{"ok": true}`

---

### 4. `POST /api/push_errors_meta`

Load error logs via JSONL file path and version number, supports cache hit.

**Request body:** `ErrorsMetaModel`

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
│  Cache hit? (path and rev both unchanged)│
│     ├─ Yes → return {"cached": true}    │
│     └─ No →                             │
│          try:                            │
│            call load_jsonl_logs()       │
│            (read JSONL in a separate    │
│             thread)                     │
│            → update error_store         │
│            → update cache (rev+path)    │
│            → store_revs["errors"] += 1  │
│            return {"cached": false}     │
│          except:                         │
│            return fallback=need_content │
└─────────────────────────────────────────┘
```

**Returns:**
- Cache hit: `{"ok": true, "cached": true}`
- Load success: `{"ok": true, "cached": false}`
- Load failure: `{"ok": false, "fallback": "need_content", "reason": "...", "msg": "..."}`

> **Note:** On load failure, the caller should fall back to `push_errors_content` to directly send error content.

---

### 5. `POST /api/push_errors_content`

Directly receive and store an error log list, supports cache hit.

**Request body:** `ErrorsContentModel`

```json
{
  "rev": 5,
  "jsonl_path": "/var/log/celestialflow/errors.jsonl",
  "errors": [{"ts": "2026-05-28T10:00:00", "error_id": "...", ...}, ...]
}
```

**Logic:**
- On cache hit, skip and directly return `{"cached": true}`
- Otherwise, write into `server.error_store` and update cache and version number

**Returns:**
- Cache hit: `{"ok": true, "cached": true}`
- Write success: `{"ok": true, "cached": false}`

---

### 6. `POST /api/push_analysis`

Update graph topology analysis information.

**Request body:** `AnalysisModel` (contains an `analysis` field)

**Logic:**
1. Update `server.analysis_store`
2. Increment `server.store_revs["analysis"]` by 1

**Returns:** `{"ok": true}`

---

### 7. `POST /api/push_injection_tasks`

Write frontend-submitted injection tasks into the pending execution queue.

**Request body:** `TaskInjectionModel` (`RootModel[dict[str, list[Any]]]`)

```json
{
  "StageA": [1, 2, 3],
  "StageB": [{"id": 4, "val": "x"}]
}
```

**Logic:**
1. Acquire `task_injection_lock`
2. Iterate over `data.root`, write into `server.injection_tasks` in `{node_name: task_list}` format
3. Release the lock

> Note: The request body is directly a `{node_name: [task_list]}` format dictionary, no longer wrapping `node`/`task_datas`/`timestamp` fields. The task list for each node name will **overwrite** that node's existing pending injection tasks (not append).

**Returns:**
- Success: `{"ok": true}`
- Failure: `{"ok": false, "msg": "Task injection failed: ..."}` (status code 500)

---

## Usage Examples

### Reporter Pushing Status and Errors

```python
import requests

BASE = "http://localhost:8000"

# Push node status
requests.post(f"{BASE}/api/push_status", json={
    "timestamp": 1716883200.5,
    "status": {"node_a": "running", "node_b": "success"}
})

# Push error logs (meta mode: let the server read JSONL itself)
resp = requests.post(f"{BASE}/api/push_errors_meta", json={
    "rev": 5,
    "jsonl_path": "/var/log/celestialflow/errors.jsonl"
})

# If server read fails, fall back to direct content delivery
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
    "structure": {
        "nodes": {"n1": {"label": "MyTask"}},
        "edges": {"n1": []},
        "source_nodes": ["n1"],
    }
})
```

### Web Frontend Saving Configuration

```javascript
const resp = await fetch("/api/push_config", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    global: {
      theme: "dark",
      autoRefreshEnabled: true,
      refreshInterval: 10000,
      language: "zh-CN",
    },
    dashboard: {
      historyLimit: 20,
      showStructureEdgeDelta: false,
      useTotalPendingInStatus: false,
      layout: { left: ["mermaid"], middle: ["status"], right: ["progress"] }
    },
    errors: {
      pageSize: 10,
      sortOrder: "newest",
      jumpToInjectionAfterRetry: true,
    },
    injection: {
      showInjectableOnly: true,
    },
  })
});
const result = await resp.json();
console.log(result.ok ? "Save successful" : "Save failed");
```
