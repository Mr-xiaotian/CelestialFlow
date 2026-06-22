# Push Routes (POST) — `push_routes`

> 📅 Last Updated: 2026/06/22

## Purpose

The `push_routes` module provides all POST endpoints for the **Reporter** to **push** data to the server. Each push updates the corresponding in-memory store and increments the version number (`store_revs`), allowing clients to detect data changes via Pull routes. All reporter-side pushes must carry `graph_id`, and the server verifies whether it is the current graph instance.

## Core Function

### `register(router: APIRouter, server: TaskWebServer, config_path: str) -> None`

Registers all 6 POST endpoints on the given `APIRouter`.

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

**Request body:** `StructureModel` (contains `graph_id` and `structure` fields)

```json
{
  "graph_id": "graph-001",
  "structure": {
    "nodes": {"n1": {"label": "MyTask"}},
    "edges": {"n1": []},
    "source_nodes": ["n1"]
  }
}
```

**Logic:**
1. Verify whether `data.graph_id` matches the current graph context; if not, return `{"ok": false}`
2. Atomically write `data.structure` into `server.structure_store`
3. Increment `server.store_revs["structure"]` by 1

**Returns:** `{"ok": true}` or `{"ok": false}`

---

### 3. `POST /api/push_status`

Update the runtime status of each node.

**Request body:** `StatusModel` (contains `graph_id`, `timestamp`, and `status` fields)

```json
{
  "graph_id": "graph-001",
  "timestamp": 1716883200.5,
  "status": {"node_a": "running", "node_b": "success"}
}
```

**Logic:**
1. Verify whether `data.graph_id` matches the current graph context
2. Update `server.status_timestamp` and `server.status_store`
3. Increment `server.store_revs["status"]` by 1

**Returns:** `{"ok": true}` or `{"ok": false}`

---

### 4. `POST /api/push_errors`

Directly receives an error log list and writes it to SQLite.

**Request body:** `ErrorsModel` (contains `graph_id` and `errors` fields)

```json
{
  "graph_id": "graph-001",
  "errors": [
    {"ts": "2026-06-18T10:00:00", "error_id": "e1", "error_type": "ValueError", "error_message": "..."}
  ]
}
```

**Logic:**
1. Verify whether `data.graph_id` matches the current graph context
2. Call `append_records` to write errors to the SQLite database
3. Increment `server.store_revs["errors"]` by 1

**Returns:** `{"ok": true}` or `{"ok": false}`

---

### 5. `POST /api/push_analysis`

Update graph topology analysis information.

**Request body:** `AnalysisModel` (contains `graph_id` and `analysis` fields)

```json
{
  "graph_id": "graph-001",
  "analysis": {"root_count": 3, "max_depth": 5}
}
```

**Logic:**
1. Verify whether `data.graph_id` matches the current graph context
2. Update `server.analysis_store`
3. Increment `server.store_revs["analysis"]` by 1

**Returns:** `{"ok": true}` or `{"ok": false}`

---

### 6. `POST /api/push_injection_tasks`

Write frontend-submitted injection tasks into the pending execution queue.

**Request body:** `TaskInjectionModel` (`RootModel[dict[str, list[Any]]]`)

```json
{
  "StageA": [1, 2, 3],
  "StageB": [{"id": 4, "val": "x"}]
}
```

**Logic:**
1. Hold the `task_injection_lock`
2. Iterate over `data.root`, writing into `server.injection_tasks` in `{node_name: task_list}` format
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
    "graph_id": "graph-001",
    "timestamp": 1716883200.5,
    "status": {
        "node_a": {"state": "running", "pending": 0},
        "node_b": {"state": "success", "pending": 0}
    }
})

# Push error logs
requests.post(f"{BASE}/api/push_errors", json={
    "graph_id": "graph-001",
    "errors": [
        {"ts": "2026-06-18T10:00:00", "error_id": "e1", "error_type": "ValueError", "error_message": "Invalid input"}
    ]
})

# Push structure data
requests.post(f"{BASE}/api/push_structure", json={
    "graph_id": "graph-001",
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
