# TaskWeb

> 📅 Last Updated: 2026/05/23

The TaskWeb module provides a lightweight FastAPI-based web server for real-time monitoring and management of task graph execution. It acts as a relay between `TaskReporter` (backend) and the Web UI (frontend).

## Starting the Server

### Command Line

```bash
# Default: listen on 0.0.0.0:5000
celestialflow-web

# Specify port
celestialflow-web --port 5005

# Specify host and port
celestialflow-web --host 127.0.0.1 --port 5005

# Specify log level
celestialflow-web --log-level debug
```

### Command Line Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--host` | `0.0.0.0` | Listen address |
| `--port` | `5000` | Listen port |
| `--log-level` | `info` | Log level (critical/error/warning/info/debug/trace) |

### Starting from Code

```python
from celestialflow import TaskWebServer

server = TaskWebServer(host="127.0.0.1", port=5005, log_level="info")
server.start_server()
```

## UI Panels

Visit `http://localhost:5000` (or the specified port) to access the Web UI.

### Main Panels

| Panel | Functionality |
|-------|---------------|
| **Dashboard** | Real-time status overview of the task graph (structure visualization (Mermaid diagram), node count, success/failure/backlog task counts, line charts) |
| **Errors** | Real-time error log list |
| **Task Injection** | Dynamically inject tasks via the web interface |

### Theme Support

- Supports light/dark theme switching
- Theme settings are persisted to the backend `config.json`

## API Endpoints (RESTful)

TaskWeb provides a set of RESTful APIs for `TaskReporter` and frontend usage. All endpoints are prefixed with `/api/`. Pull endpoints use the `pull_` naming convention, and push endpoints use the `push_` naming convention.

### Pull Endpoints (GET /api/pull_*)

Used by the Web UI to fetch the latest data. Supports the `known_rev` mechanism: if the server-side data version is unchanged, `data: null` is returned to save bandwidth.

| Endpoint | Return Structure (data field) | Description |
|----------|-------------------------------|-------------|
| `pull_config` | `WebConfigModel` | Fetch global configuration such as theme, language, and refresh interval |
| `pull_structure`| `list[dict]` | Fetch the topological structure of the task graph |
| `pull_status` | `dict[tag, NodeStatus]` | Fetch real-time runtime metrics and unified timestamps for each node |
| `pull_errors` | `list[dict]` | Fetch paginated error logs |
| `pull_analysis` | `dict` | Fetch graph topology analysis results (DAG, levels, etc.) |
| `pull_summary` | `{"total_remain": float}` | Fetch graph-level total remaining time estimate |
| `pull_task_injection` | `list[dict]` | For TaskGraph to fetch the pending injection task queue |
| `pull_interval` | `{"interval": float}` | Fetch the Reporter push interval |

### Push Endpoints (POST /api/push_*)

Primarily called by `TaskReporter` to report backend runtime status.

| Endpoint | Data Model | Description |
|----------|-----------|-------------|
| `push_config` | `WebConfigModel` | Called by the frontend to save user settings |
| `push_status` | `StatusModel` | Report node status snapshot + current timestamp |
| `push_structure`| `StructureModel` | Report graph structure |
| `push_analysis` | `AnalysisModel` | Report analysis data |
| `push_summary` | `SummaryModel` | Report graph-level summary information |
| `push_errors_meta` | `ErrorsMetaModel` | Push error metadata (supports caching) |
| `push_errors_content`| `ErrorsContentModel`| Push error content (supports caching) |
| `push_injection_tasks` | `TaskInjectionModel` | Frontend submits task injection requests |

## Data Models (Pydantic)

### StructureModel
```python
class StructureModel(BaseModel):
    items: list[dict[str, Any]]
```

### StatusModel
```python
class StatusModel(BaseModel):
    timestamp: float                 # Unified sampling timestamp
    status: dict[str, dict[str, Any]] # Key: node tag, Value: NodeStatus
```

### ErrorsMetaModel
```python
class ErrorsMetaModel(BaseModel):
    jsonl_path: str  # JSONL file path
    rev: int         # Version number (used for cache validation)
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

### SummaryModel
```python
class SummaryModel(BaseModel):
    summary: dict[str, Any]
```

### TaskInjectionModel
```python
class TaskInjectionModel(BaseModel):
    node: str             # Target node tag
    task_datas: list[Any] # Task data list
    timestamp: datetime   # Timestamp
```

### WebConfigModel
```python
class WebConfigModel(BaseModel):
    theme: str                        # "light" | "dark"
    refreshInterval: int              # Polling interval (ms)
    historyLimit: int                 # Frontend history retention length
    language: str = "zh-CN"           # Interface language
    errorPageSize: int = 10           # Error log page size
    showStructureEdgeDelta: bool = True # Structure diagram edge delta toggle
    dashboard: DashboardConfigModel   # Dashboard three-column layout definition

class DashboardConfigModel(BaseModel):
    left: list[str]    # Left column card key list
    middle: list[str]  # Middle column card key list
    right: list[str]   # Right column card key list
```

## Configuration Management

Web service configuration is persisted in `web/config.json`.

- `load_config()` — Reads at startup and validates via `WebConfigModel`
- `save_config(config)` — Saves configuration to JSON file, thread-safe (uses `_config_lock`)
- `cal_interval(refresh_interval)` — Converts millisecond refresh interval to seconds, clamped to `[1.0, 60.0]`
- **Degraded Startup**: If `config.json` fails to load, the Web service starts with hardcoded defaults, ensuring the monitoring interface is always available.
- **Sync Mechanism**: When the frontend updates `refreshInterval`, the backend's `report_interval` is automatically synchronized, thereby affecting the `TaskReporter` push frequency.

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
    |--- push_summary --------->|                          |
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

- If both the path and version number are unchanged, returns `{"ok": true, "cached": true}` without re-reading the file
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

Upon receiving this response, the client falls back to using `push_errors_content` to transmit error content directly.

### Task Injection Concurrency Safety

The `injection_tasks` list is protected by `_task_injection_lock`. Both `push_injection_tasks` (write) and `pull_task_injection` (read with clear) operate within the lock to avoid race conditions.

## Notes

1. **Port Conflicts**: Ensure the specified port is not already in use.
2. **Firewall**: Configure firewall rules if remote access is needed.
3. **HTTPS**: For production environments, it is recommended to add HTTPS via a reverse proxy (e.g., Nginx).
4. **Authentication**: The current version has no built-in authentication; adding an authentication layer is recommended for production environments.
