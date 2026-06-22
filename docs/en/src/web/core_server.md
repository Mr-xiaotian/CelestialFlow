# TaskWebServer (core_server)

> 📅 Last Updated: 2026/06/22

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

### CLI Entry Point

`core_server.py` also provides command-line entry functions:

- `parse_args()` — Parses `--host`, `--port`, `--log-level` arguments; `--log-level` is restricted to `critical` / `error` / `warning` / `info` / `debug` / `trace`.
- `main_entry()` — Constructs a `TaskWebServer` from parsed arguments and calls `start_server()`.

The command-line tool `celestialflow-web` is registered from `main_entry`.

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

Used by the Web UI to fetch the latest data. Most pull endpoints (`pull_status`, `pull_structure`, `pull_errors`, `pull_analysis`) support the `known_rev` mechanism: if the server-side data version hasn't changed, returns `data: null` to save bandwidth. `pull_config`, `pull_task_injection`, and `pull_server_state` do not use the `known_rev` mechanism and return full data every time.

| Endpoint | Return Structure (data field) | Description |
|----------|-------------------------------|-------------|
| `pull_config` | `dict` | Fetch global configuration such as theme, language, refresh interval |
| `pull_structure` | `dict[str, Any]` | Fetch the topology structure of the task graph (including nodes/edges/source_nodes) |
| `pull_status` | `dict[str, dict[str, Any]]` | Fetch real-time runtime metrics and unified timestamp for each node |
| `pull_errors` | `list[dict]` | Paginated pull of error logs, supporting node/keyword filtering and sorting |
| `pull_analysis` | `dict[str, Any]` | Fetch graph topology analysis results |
| `pull_task_injection` | `dict[str, list[Any]]` | For TaskGraph to pull queued injection tasks (grouped by node name, cleared after reading) |
| `pull_server_state` | `dict[str, Any]` | Fetch server-side state needed for Reporter synchronization (interval/is_current_graph/has_structure/max_event_id_in_fail) |

### Push Endpoints (POST /api/push_*)

Primarily called by `TaskReporter` to report backend runtime state.

| Endpoint | Data Model | Description |
|----------|-----------|-------------|
| `push_config` | `WebConfigModel` | Called by frontend, saves user settings |
| `push_status` | `StatusModel` | Reports node status snapshot + current timestamp |
| `push_structure` | `StructureModel` | Reports graph structure |
| `push_analysis` | `AnalysisModel` | Reports analysis data |
| `push_errors` | `ErrorsModel` | Directly receives error content and writes to SQLite |
| `push_injection_tasks` | `TaskInjectionModel` | Frontend submits task injection requests |

## Data Models (Pydantic)

> For complete model definitions, see `util_models.md`. Only core fields are listed here.

### StructureModel

```python
class StructureModel(BaseModel):
    graph_id: str = ""  # Graph instance identifier, used for Reporter-side graph context validation
    structure: dict[str, Any]  # Structure snapshot, containing nodes, edges, source_nodes
```

### StatusModel

```python
class StatusModel(BaseModel):
    graph_id: str = ""                    # Graph instance identifier
    timestamp: float                      # Unified sampling timestamp
    status: dict[str, dict[str, Any]]     # Key is node name, value is node status dictionary
```

### ErrorsModel

```python
class ErrorsModel(BaseModel):
    graph_id: str = ""              # Graph instance identifier
    errors: list[dict[str, Any]]    # Error record list, directly written to SQLite database
```

### AnalysisModel

```python
class AnalysisModel(BaseModel):
    graph_id: str = ""        # Graph instance identifier
    analysis: dict[str, Any]  # Analysis result dictionary
```

### TaskInjectionModel

```python
class TaskInjectionModel(RootModel[dict[str, list[Any]]]):
    """Task injection request model, format: {node_name: [tasklist]}."""
```

> The request body is directly a mapping from node names to task lists. Example:
> `{"StageA": [task1, task2], "StageB": [task3]}`

### WebConfigModel

Configuration uses a nested grouping structure.

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

- `load_config()` — Read at startup and validated via `WebConfigModel`; if `config.json` does not exist, raises `ConfigurationError` directly and does not start with hardcoded defaults.
- `save_config(config, config_path)` — Save configuration to a JSON file, thread-safe (guaranteed by `config_lock` in the upper-level `push_config` route)
- `cal_interval(refresh_interval)` — Convert millisecond refresh interval to seconds, range limited to `[1.0, 60.0]`
- **Sync mechanism**: When the frontend updates `refreshInterval`, the backend `report_interval` is automatically synchronized, thus affecting the `TaskReporter` push frequency.

## Integration with TaskGraph

### Enabling in TaskGraph

```python
from celestialflow import TaskGraph, TaskStage


def process(x: int) -> int:
    return x * 2


stage_a = TaskStage("StageA", process, execution_mode="thread")
graph = TaskGraph(name="DemoGraph")
graph.set_stages(stages=[stage_a])
graph.set_reporter(True, host="127.0.0.1", port=5005)
init_tasks = {stage_a.get_name(): [1, 2, 3]}
graph.start_graph(init_tasks)
```

### Data Flow

```
TaskGraph                         TaskWeb                    Browser
    |                                |                          |
    |--- push_structure ------------>|--- Dashboard ----------->|
    |--- push_status --------------->|                          |
    |--- push_analysis ------------->|                          |
    |                                |                          |
    |--- push_errors --------------->|---- Errors ------------->|
    |                                |                          |
    |<-- pull_task_injection --------|<--- Inject Tasks --------|
    |<-- pull_server_state ----------|<--- Reporter Sync -------|
    |                                |                          |
```

## Error Handling

### SQLite Persistence

Error records are directly written to the SQLite database via `append_records`, supporting efficient querying and pagination.

### Task Injection Concurrency Safety

The `injection_tasks` dictionary is protected by `task_injection_lock`. Both `push_injection_tasks` writes and `pull_task_injection` reads (including clearing) operate within the lock, avoiding race conditions. Injection uses **overwrite** semantics: new tasks for the same node name will overwrite the old task list.

## Notes

1. **Port conflicts**: Ensure the specified port is not already in use.
2. **Firewall**: If remote access is needed, configure firewall rules.
3. **HTTPS**: In production, it is recommended to use a reverse proxy (e.g. Nginx) to add HTTPS.
4. **Authentication**: The current version has no built-in authentication; adding an authentication layer is recommended for production.
