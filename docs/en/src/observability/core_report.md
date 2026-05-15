# TaskReporter

> 📅 Last Updated: 2026/05/15

`TaskReporter` is a background component responsible for collecting task graph runtime status and reporting it to a remote Web server (CelestialFlow Web UI). It is also responsible for pulling control commands (such as task injection) from the server.

## Features

- **Status Reporting**: Periodically pushes task graph structure, topology, runtime status (counters), error information, etc.
- **Task Injection**: Receives user-injected new tasks from the Web UI and dynamically inserts them into the running task graph.
- **Dynamic Parameter Adjustment**: Supports pulling configuration from the server (such as reporting interval).
- **Error Log Synchronization**: Supports incremental error log pushing.

## Usage

Typically, you do not need to instantiate it directly; instead, enable it through `TaskGraph`:

```python
graph = TaskGraph(...)
# Enable Reporter, connecting to local port 5005
graph.set_reporter(True, host="127.0.0.1", port=5005)
```

## API Interactions

The Reporter interacts with the following Web APIs:

- `GET /api/pull_interval`: Get the reporting interval.
- `GET /api/pull_history_limit`: Get the maximum number of history records to retain.
- `GET /api/pull_task_injection`: Get injected tasks.
- `POST /api/push_status`: Push runtime status snapshot.
- `POST /api/push_structure`: Push graph structure information.
- `POST /api/push_analysis`: Push analysis information.
- `POST /api/push_summary`: Push graph summary.
- `POST /api/push_history`: Push node history trend data.
- `POST /api/push_errors_meta` / `push_errors_content`: Push error information.

## NullTaskReporter

When the Reporter is not enabled, `TaskGraph` uses `NullTaskReporter` as a placeholder. Its `start()` and `stop()` methods are no-ops and do not make any network requests.

```python
class NullTaskReporter:
    interval = 1
    history_limit = 20

    def start(self) -> None: ...
    def stop(self) -> None: ...
```
