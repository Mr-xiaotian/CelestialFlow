# Web Module

> 📅 Last Updated: 2026/06/22

The Web module provides an interactive monitoring and management interface built with FastAPI and native TypeScript, supporting real-time task status visualization, error tracing, dynamic task injection, and global configuration management.

## Module Overview

The Web module serves as a bridge between `TaskReporter` and the end user. On one hand, it acts as a RESTful API server that receives and caches runtime status snapshots; on the other, it provides a high-performance, low-latency single-page application (SPA) that allows developers to intuitively observe task graph execution flow, performance bottlenecks, and error details.

## File Descriptions

### Core Backend Components

1. **core_server.py** (`TaskWebServer`)
   - **Purpose**: Web core server, manages data caching, version control (known_rev), and API routing.
   - **Key Features**: State aggregation, configuration persistence, paginated error queries, task injection relay.

2. **util_error.py**
   - **Purpose**: Provides error log filtering, normalization, and pagination logic.

3. **util_config.py**
   - **Purpose**: Handles `config.json` read/write, supports graceful degradation on startup.

### Core Frontend Components

Frontend TypeScript source files are located in `web/static/ts/`, compiled to JS and loaded by `templates/index.html`:

1. **main.ts** — Global entry and polling coordination
2. **utils.ts** — General utility functions
3. **i18n.ts** — Internationalization support
4. **web_config.ts** — Configuration management logic
5. **dashboard_statuses.ts** — Renders dynamic node cards, displaying real-time performance metrics and progress bars for each stage
6. **dashboard_structure.ts** — Renders task graph topology using Mermaid.js, supporting dynamic node coloring
7. **dashboard_history.ts** — Maintains multi-metric historical series, renders progress line charts using Chart.js
8. **dashboard_summary.ts** — Global statistics dashboard rendering and updates
9. **dashboard_analysis.ts** — Topology analysis information display
10. **errors.ts** — Paginated display and deep filtering of error logs
11. **injection.ts** — Manual task injection UI management, supporting multi-node batch injection
12. **layout_editor.ts** — Card layout editor (depends on CARD_TEMPLATES/PANEL_SELECTOR_MAP in web_config)

## Architectural Highlights

### Client-Side History Accumulation
To significantly reduce frontend-backend communication frequency, historical trend data is no longer fully pushed by the backend. Instead, the frontend accumulates and maintains it in browser memory based on continuous status snapshots.

### Incremental Pull Mechanism
All pull endpoints (`pull_*`) support the `known_rev` mechanism. Actual payload is only transmitted when the backend data version changes; otherwise, only the version number is returned, greatly conserving polling bandwidth.

### Graceful Configuration Degradation
The system has a robust initialization flow: if backend configuration loading fails, the frontend automatically falls back to the built-in `DEFAULT_WEB_CONFIG`, ensuring the monitoring panel can render and display basic data under any circumstances.

## Usage Patterns

### Starting the Server
```bash
# Run the CLI tool directly
celestialflow-web --port 5000
```

### Task Injection Example
```python
import requests

# Inject new tasks into a specified node (format: {node_name: [task_list]})
requests.post("http://localhost:5000/api/push_injection_tasks", json={
    "Stage_A": [{"id": 1, "data": "payload"}]
})
```

## Usage Examples

### Basic Example of Creating and Starting TaskWebServer

```python
from celestialflow import TaskWebServer

# Create server instance
server = TaskWebServer(
    host="127.0.0.1",   # Listen address
    port=5000,            # Listen port
    log_level="info",    # Log level
)

# Start the server (blocking call, runs indefinitely)
server.start_server()
```

After startup, visit `http://127.0.0.1:5000` in a browser to see the Web UI monitoring panel.

### Complete Data Reporting Pipeline Example

```python
from celestialflow import TaskGraph, TaskStage, TaskWebServer
from celestialflow.persistence import LogInlet
from celestialflow.observability import TaskReporter
import asyncio


async def main():
    # 1. Start the Web server first (runs in a background thread)
    server = TaskWebServer(host="127.0.0.1", port=5000, log_level="info")
    # In a real production environment, server.start_server() would block;
    # this demonstrates the reporter-server coordination flow

    # 2. Create a task graph
    def process(x: int) -> int:
        return x * 2

    graph = TaskGraph(name="DemoGraph", schedule_mode="eager")
    stage = TaskStage("Processor", process, execution_mode="thread")
    graph.set_stages([stage])

    # 3. Create and start TaskReporter
    log_inlet = LogInlet()
    reporter = TaskReporter(
        host="127.0.0.1",
        port=5000,
        task_graph=graph,
        log_inlet=log_inlet,
    )
    reporter.start()

    # 4. Execute tasks
    graph.start_graph({stage.get_name(): range(50)})

    # 5. Stop the reporter
    reporter.stop()


asyncio.run(main())
```
