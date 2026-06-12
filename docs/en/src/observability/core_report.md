# TaskReporter

> 📅 Last Updated: 2026/06/11

`TaskReporter` is a background component responsible for collecting task graph runtime status and reporting it to a remote Web server (CelestialFlow Web UI). It is also responsible for pulling control commands (such as task injection) from the server.

## Features

- **Status Reporting**: Periodically pushes task graph structure, topology, runtime status (counters), analysis data, etc.
- **Task Injection**: Receives user-injected new tasks from the Web UI and dynamically inserts them into the running task graph.
- **Dynamic Parameter Adjustment**: Supports pulling configuration from the server (such as reporting interval `interval`).
- **Error Log Syncing**: Supports incremental error log pushing (metadata mode / content mode).

## Initialization

```python
class TaskReporter:
    def __init__(
        self,
        host: str,
        port: int,
        task_graph: "TaskGraph",
        log_inlet: LogInlet,
    ) -> None:
        """
        :param host: Remote service host address
        :param port: Remote service port
        :param task_graph: Task graph instance
        :param log_inlet: Log collector instance
        """
```

After initialization, `base_url = f"http://{host}:{port}"` is set, with defaults `interval = 5` seconds and `history_limit = 20`.

## API Interaction

The Reporter interacts with the following Web APIs via HTTP:

### Pull Endpoints

| Method | Endpoint | Description |
|------|------|------|
| `GET` | `/api/pull_interval` | Retrieve reporting interval configuration |
| `GET` | `/api/pull_task_injection` | Retrieve injected tasks |

### Push Endpoints

| Method | Endpoint | Description |
|------|------|------|
| `POST` | `/api/push_errors_meta` | Push error metadata (version number and JSONL path) |
| `POST` | `/api/push_errors_content` | Push error content (incremental, including specific error entries) |
| `POST` | `/api/push_status` | Push runtime status snapshot |
| `POST` | `/api/push_structure` | Push graph structure information |
| `POST` | `/api/push_analysis` | Push graph analysis data |

> **Changed**: Previous documentation listed the `/api/push_summary` endpoint, but `TaskReporter._refresh_all()` does not include a push call for summary (`LogInlet` retains the `push_summary_failed` log method but it is not called by the Reporter).

### Interaction Flow

```mermaid
sequenceDiagram
    participant R as TaskReporter
    participant S as Web Server

    loop Every interval seconds
        R->>S: GET /api/pull_interval
        S-->>R: {interval: 5}

        R->>S: GET /api/pull_task_injection
        S-->>R: {target_stage: [task_datas]}

        R->>R: collect_runtime_snapshot()

        alt error mode = meta
            R->>S: POST /api/push_errors_meta {rev, jsonl_path}
            S-->>R: {ok: true}
        else error mode = content (fallback)
            R->>S: POST /api/push_errors_content {rev, errors}
            S-->>R: {ok: true}
        end

        R->>S: POST /api/push_status {status_snapshot}
        R->>S: POST /api/push_structure {structure}
        R->>S: POST /api/push_analysis {analysis}
    end
```

## _refresh_all Execution Order

```python
def _refresh_all(self) -> None:
    # 1. Pull
    self._pull_interval()          # GET /api/pull_interval
    self._pull_and_inject_tasks()  # GET /api/pull_task_injection → inject tasks

    # 2. Collect snapshot
    self.task_graph.collect_runtime_snapshot()

    # 3. Push
    self._push_errors()      # Meta mode first, fallback to content mode on failure
    self._push_status()      # POST /api/push_status
    self._push_structure()   # POST /api/push_structure
    self._push_analysis()    # POST /api/push_analysis
```

## Lifecycle

```python
reporter.start()  # Clear stop flag, create daemon thread executing _loop()
reporter.stop()   # Set stop flag, join thread (timeout=2), final refresh
```

In `_loop()`, each cycle executes `_refresh_all()`. Exceptions are caught and recorded via `log_inlet.loop_failed()`, without terminating the thread.

## NullTaskReporter

When the Reporter is not enabled, `NullTaskReporter` is used as a placeholder. Its `start()` and `stop()` are no-ops and will not make any network requests.

```python
class NullTaskReporter:
    interval: int = 1
    history_limit: int = 20

    def start(self) -> None: ...
    def stop(self) -> None: ...
```
