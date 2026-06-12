# TaskWeb

> 📅 Last Updated: 2026/06/11

The TaskWeb module provides a lightweight FastAPI-based web server for real-time monitoring and management of task graph execution. It acts as a relay between `TaskReporter` (backend) and the Web UI (frontend).

## Startup Methods

### CLI Startup

```bash
# Default listen on 0.0.0.0:5000
celestialflow-web

# Specify port
celestialflow-web --port 5005

# Specify host and port
celestialflow-web --host 127.0.0.1 --port 5005

# Specify log level
celestialflow-web --log-level debug
```

### CLI Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--host` | `0.0.0.0` | Listen address |
| `--port` | `5000` | Listen port |
| `--log-level` | `info` | Log level (critical/error/warning/info/debug/trace) |

### Programmatic Startup

```python
from celestialflow import TaskWebServer

server = TaskWebServer(host="127.0.0.1", port=5005, log_level="info")
server.start_server()
```

## Feature Interface

Visit `http://localhost:5000` (or the specified port) to see the Web UI.

### Main Panels

| Panel | Function |
|-------|----------|
| **Dashboard** | Real-time overview of task graph state (structure visualization (Mermaid diagram), node count, success/failure/backlog task counts, line charts) |
| **Errors** | Real-time error log list |
| **Task Injection** | Dynamically inject tasks through the web interface |

### Theme Support

- Supports light/dark theme switching
- Theme settings are persisted to the backend `config.json`

## API Endpoints (RESTful)

TaskWeb provides a series of RESTful APIs for `TaskReporter` calls and frontend use. All endpoints use the `/api/` prefix, with pull endpoints named `pull_*` and push endpoints named `push_*`.

### Pull Endpoints (GET /api/pull_*)

Used by the Web UI to fetch the latest data. Supports the `known_rev` mechanism: if the server-side data version hasn't changed, returns `data: null` to save bandwidth.

| Endpoint | Return Structure (data field) | Description |
|----------|-------------------------------|-------------|
| `pull_config` | `WebConfigModel` | Fetch global configuration such as theme, language, refresh interval |
| `pull_structure`| `list[dict]` | Fetch the topology structure of the task graph |
| `pull_status` | `dict[tag, NodeStatus]` | Fetch real-time runtime metrics and unified timestamp for each node |
| `pull_errors` | `list[dict]` | Paginated pull of error logs |
| `pull_analysis` | `dict` | Fetch graph topology analysis results (DAG, layers, etc.) |
| `pull_task_injection` | `dict[str, list[Any]]` | For TaskGraph to pull queued injection tasks (grouped by node name) |
| `pull_interval` | `{"interval": float}` | Fetch the Reporter push interval |

### Push Endpoints (POST /api/push_*)

Primarily called by `TaskReporter` to report backend runtime state.

| Endpoint | Data Model | Description |
|----------|-----------|-------------|
| `push_config` | `WebConfigModel` | Called by frontend, saves user settings |
| `push_status` | `StatusModel` | Reports node status snapshot + current timestamp |
| `push_structure`| `StructureModel` | Reports graph structure |
| `push_analysis` | `AnalysisModel` | Reports analysis data |
| `push_errors_meta` | `ErrorsMetaModel` | Pushes error metadata (supports caching) |
| `push_errors_content`| `ErrorsContentModel`| Pushes error content (supports caching) |
| `push_injection_tasks` | `TaskInjectionModel` | Frontend submits task injection requests |

## Data Models (Pydantic)

> For complete model definitions, see `util_models.md`. Only core fields are listed here.

### StructureModel

```python
class StructureModel(BaseModel):
    structure: dict[str, Any]  # Structure snapshot, typically containing nodes, edges, source_nodes
```

### StatusModel

```python
class StatusModel(BaseModel):
    timestamp: float                      # Unified sampling timestamp
    status: dict[str, dict[str, Any]]     # Key is node name, value is node status dictionary
```

### ErrorsMetaModel

```python
class ErrorsMetaModel(BaseModel):
    jsonl_path: str  # JSONL file path
    rev: int         # Version number (used for cache judgment)
```

### ErrorsContentModel

```python
class ErrorsContentModel(BaseModel):
    errors: list[dict[str, Any]]
    jsonl_path: str
    rev: int
```

### AnalysisModel

```python
class AnalysisModel(BaseModel):
    analysis: dict[str, Any]
```

### TaskInjectionModel

```python
class TaskInjectionModel(RootModel[dict[str, list[Any]]]):
    """Task injection request model, format: {node_name: [tasklist]}."""
```

> Unlike the old single-node format, the current model uses dictionary keys as node names and values as task lists. Request body example:
> `{"StageA": [task1, task2], "StageB": [task3]}`

### WebConfigModel

Configuration uses a nested grouping structure, no longer flat.

```python
class GlobalConfigModel(BaseModel):
    theme: str
    autoRefreshEnabled: bool = True
    refreshInterval: int
    language: str = "zh-CN"

class DashboardConfigModel(BaseModel):
    left: list[str]
    middle: list[str]
    right: list[str]

class DashboardPageConfigModel(BaseModel):
    historyLimit: int
    showStructureEdgeDelta: bool = False
    useTotalPendingInStatus: bool = False
    layout: DashboardConfigModel

class ErrorsPageConfigModel(BaseModel):
    pageSize: int = 10
    sortOrder: str = "newest"
    jumpToInjectionAfterRetry: bool = True

class InjectionPageConfigModel(BaseModel):
    showInjectableOnly: bool = True

class WebConfigModel(BaseModel):
    global_: GlobalConfigModel = Field(alias="global")
    dashboard: DashboardPageConfigModel
    errors: ErrorsPageConfigModel
    injection: InjectionPageConfigModel = Field(default_factory=InjectionPageConfigModel)
```

## Configuration Management

Web service configuration is persisted in `web/config.json`.

- `load_config()` — Read at startup and validated via `WebConfigModel`
- `save_config(config, config_path)` — Save configuration to a JSON file, thread-safe (guaranteed by `config_lock` in the upper-level `push_config` route)
- `cal_interval(refresh_interval)` — Convert millisecond refresh interval to seconds, range limited to `[1.0, 60.0]`
- **Graceful degradation**: If `config.json` fails to load, the Web service starts with hardcoded defaults, ensuring the monitoring interface is always available.
- **Sync mechanism**: When the frontend updates `refreshInterval`, the backend `report_interval` is automatically synchronized, thus affecting the `TaskReporter` push frequency.

## Integration with TaskGraph

### Enabling in TaskGraph

```python
from celestialflow import TaskGraph

graph = TaskGraph()
graph.set_stages(stages=[stage_a])
graph.set_reporter(True, host="127.0.0.1", port=5005)
graph.start_graph(init_tasks)
```

### Data Flow

```
TaskGraph                    TaskWeb                    Browser
    |                           |                          |
    |--- push_structure ------->|--- Dashboard ----------->|
    |--- push_status ---------->|                          |
    |--- push_analysis -------->|                          |
    |                           |                          |
    |--- push_errors_meta ----->|---- Errors ------------->|
    |--- push_errors_content -->|                          |
    |                           |                          |
    |<-- pull_task_injection ---|<--- Inject Tasks --------|
    |<-- pull_interval ---------|<--- Web Config ----------|
    |                           |                          |
```

## Error Handling

### Caching Mechanism

`push_errors_meta` and `push_errors_content` support caching based on `(jsonl_path, rev)`:

- If both the path and version number are unchanged, returns `{"ok": true, "cached": true}`, without re-reading the file
- Otherwise, reloads the data and updates `_errors_meta_path` / `_errors_meta_rev`

### Graceful Degradation

When the JSONL file cannot be read, `push_errors_meta` returns a fallback indication:

```json
{
    "ok": false,
    "fallback": "need_content",
    "reason": "FileNotFoundError",
    "msg": "File not found"
}
```

Upon receiving this response, the client uses `push_errors_content` to directly pass error content.

### Task Injection Concurrency Safety

The `injection_tasks` list is protected by `_task_injection_lock`. Both `push_injection_tasks` writes and `pull_task_injection` reads (including clearing) operate within the lock, avoiding race conditions.

## Notes

1. **Port conflicts**: Ensure the specified port is not already in use.
2. **Firewall**: If remote access is needed, configure firewall rules.
3. **HTTPS**: In production, it is recommended to use a reverse proxy (e.g. Nginx) to add HTTPS.
4. **Authentication**: The current version has no built-in authentication; adding an authentication layer is recommended for production.
