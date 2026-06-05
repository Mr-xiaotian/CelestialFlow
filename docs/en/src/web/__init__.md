# Web Module

> 📅 Last Updated: 2026/05/23

The Web module provides an interactive monitoring and management interface, built on FastAPI and native TypeScript, supporting real-time task status visualization, error tracing, dynamic task injection, and global configuration management.

## Module Overview

The Web module acts as a bridge between `TaskReporter` and end users. On one hand, it serves as a RESTful API Server that receives and caches status snapshots from the runtime; on the other, it provides a high-performance, low-latency single-page application (SPA) that allows developers to intuitively observe the execution flow of graph tasks, performance bottlenecks, and exception details.

## File Descriptions

### Core Backend Components

1. **core_server.py** (`TaskWebServer`)
   - **Purpose**: Core web server that manages data caching, version control (known_rev), and API routes.
   - **Key Features**: Status aggregation, configuration persistence, error pagination queries, task injection relay.

2. **util_error.py**
   - **Purpose**: Provides error log filtering, normalization, and pagination logic.

3. **util_config.py**
   - **Purpose**: Handles reading and writing of `config.json`, supporting degraded startup.

### Core Frontend Components

1. **dashboard_history.ts**
   - **Purpose**: Maintains multi-metric historical series, renders progress line charts using Chart.js. Supports real-time metric switching.

2. **dashboard_statuses.ts**
   - **Purpose**: Renders dynamic node cards, displaying real-time performance metrics and progress bars for each stage.

3. **dashboard_structure.ts**
   - **Purpose**: Renders task graph topology structure based on Mermaid.js, supporting dynamic node coloring.

4. **injection.ts**
   - **Purpose**: Manages the task manual injection UI, supporting multi-node batch injection and file uploads.

5. **errors.ts**
   - **Purpose**: Handles paginated display and deep filtering of error logs.

## Architecture Features

### Client-Side History Accumulation
To significantly reduce frontend-backend communication frequency, historical trend data is no longer fully pushed by the backend. Instead, the frontend accumulates and maintains it in browser memory based on continuous status snapshots.

### Incremental Pull Mechanism
All pull endpoints (`pull_*`) support the `known_rev` mechanism. The actual payload is transmitted only when the backend data version has changed; otherwise, only the version number is returned, greatly saving polling bandwidth.

### Degraded Configuration Startup
The system is designed with a robust initialization flow: if backend configuration loading fails, the frontend automatically falls back to the built-in `DEFAULT_WEB_CONFIG`, ensuring the monitoring dashboard renders and displays basic data under any circumstances.

## Usage Patterns

### Starting the Server
```bash
# Run the CLI tool directly
celestialflow-web --port 5000
```

### Task Injection Example
```python
import requests

# Inject new tasks into a specified node
requests.post("http://localhost:5000/api/push_injection_tasks", json={
    "node": "Stage_A",
    "task_datas": [{"id": 1, "data": "payload"}],
    "timestamp": "2026-05-23T10:00:00"
})
```

## Usage Examples

### Basic Example of Creating and Starting TaskWebServer

```python
from celestialflow import TaskWebServer

# Create a server instance
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
    # this example illustrates the reporter-server coordination flow

    # 2. Create a task graph
    def process(x: int) -> int:
        return x * 2

    graph = TaskGraph(schedule_mode="eager")
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
    await graph.start_graph({stage.get_tag(): range(50)})

    # 5. Stop the reporter
    reporter.stop()


asyncio.run(main())
```
