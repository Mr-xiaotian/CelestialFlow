# TaskWeb

> 📅 Last Updated: 2026/04/24

The TaskWeb module provides a lightweight FastAPI-based web server for real-time monitoring and management of task graph execution.

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

## API Endpoints

TaskWeb provides a set of RESTful APIs for `TaskReporter` and the frontend. All endpoints are prefixed with `/api/`. Pull endpoints use the `pull_` naming convention, and push endpoints use the `push_` naming convention.

### Pull Data (GET)

| Endpoint | Description |
|----------|-------------|
| `GET /api/pull_config` | Get frontend configuration (theme, refresh interval, dashboard layout, etc.) |
| `GET /api/pull_structure` | Get graph structure |
| `GET /api/pull_status` | Get node runtime status |
| `GET /api/pull_errors` | Get error logs |
| `GET /api/pull_analysis` | Get analysis data |
| `GET /api/pull_summary` | Get summary statistics |
| `GET /api/pull_history` | Get task processing history for each node (used for line charts) |
| `GET /api/pull_interval` | Get Reporter push interval |
| `GET /api/pull_history_limit` | Get maximum history record retention count |
| `GET /api/pull_task_injection` | Get tasks pending injection (pulled by TaskGraph) |

### Push Data (POST)

| Endpoint | Description |
|----------|-------------|
| `POST /api/push_config` | Save frontend configuration |
| `POST /api/push_structure` | Push graph structure |
| `POST /api/push_status` | Push node status |
| `POST /api/push_errors_meta` | Push error metadata (supports caching) |
| `POST /api/push_errors_content` | Push error content (supports caching) |
| `POST /api/push_analysis` | Push analysis data |
| `POST /api/push_summary` | Push summary statistics |
| `POST /api/push_history` | Push history data for each node |
| `POST /api/push_injection_tasks` | Inject tasks (pushed by frontend, pulled by TaskGraph) |

## Data Models

### StructureModel

```python
class StructureModel(BaseModel):
    items: list[dict[str, Any]]
```

### StatusModel

```python
class StatusModel(BaseModel):
    status: dict[str, dict]
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
    errors: list[dict]
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

### HistoryModel

```python
class HistoryModel(BaseModel):
    history: dict[str, list[dict]]
    # key: node tag; value: [{timestamp, tasks_processed}, ...]
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
    theme: str                        # "light" or "dark"
    refreshInterval: int              # Refresh interval (milliseconds)
    historyLimit: int                 # Maximum history record retention count
    dashboard: DashboardConfigModel   # Dashboard layout configuration
    cards: dict[str, CardConfigModel] # Card title configuration

class DashboardConfigModel(BaseModel):
    left: list[str]    # Left column card key list
    middle: list[str]  # Middle column card key list
    right: list[str]   # Right column card key list

class CardConfigModel(BaseModel):
    title: str         # Card title
```

## Configuration Management

Web service configuration is persisted in `web/config.json`.

- `load_config()` -- Reads and validates via `WebConfigModel` at startup
- `save_config(config)` -- Saves configuration to JSON file, thread-safe (uses `_config_lock`)
- `cal_interval(refresh_interval)` -- Converts millisecond refresh interval to seconds, clamped to the range `[1.0, 60.0]`

When the frontend updates the configuration via `push_config`, `report_interval` is also updated accordingly.

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
    |--- push_history --------->|                          |
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
