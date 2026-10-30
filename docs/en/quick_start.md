# Quick Start

> 📅 Last Updated: 2026/10/30

This section will guide you through quickly installing and running **TaskGraph**, experiencing its task graph scheduling mechanism through examples.

## Create an Isolated Virtual Environment

It is recommended to use an isolated environment to avoid dependency conflicts with other projects.

```bash
# Create a project virtual environment (generates .venv by default)
uv venv --python 3.12

# Activate environment (Windows)
. .\.venv\Scripts\Activate.ps1

# Activate environment (Linux/macOS)
source .venv/bin/activate
```

Using an isolated virtual environment is recommended. CelestialFlow recommends using `uv` for dependency and environment management.

## Install CelestialFlow

CelestialFlow is published on [PyPI](https://pypi.org/project/celestialflow/) and can be installed directly via `pip` / `uv pip` without cloning the source code.

```bash
# Install the latest version directly
uv pip install celestialflow
```

The installation above only includes CelestialFlow's default runtime dependencies and does not include optional tracing components like `celestialtree`.

If you need to enable CelestialTree event tracing, you can additionally run:

```bash
uv pip install celestialtree
```

However, if you want to run the subsequent test code or use the Go-based `go_worker` program, you will need to clone the project:

```bash
# Clone the project
git clone https://github.com/Mr-xiaotian/CelestialFlow.git
cd CelestialFlow
uv sync --group dev
```

The `dev` dependency group already includes `pytest`, `python-dotenv`, `redis`, `celestialtree`, and other dependencies needed for development and extensions.

## (Optional) Set Up Status Reporting

The main repo no longer includes a built-in Web service. If the example code enables reporting, you can point it to a self-hosted HTTP service or a standalone `celestialflow-web` project; if you only want to experience the core scheduling capabilities of CelestialFlow, this section can be skipped.

Status reporting is configured by explicitly passing a `ReportConfig` instance to the `report` parameter of the run entry point:

```python
from celestialflow import ReportConfig, TaskExecutor, TaskGraph

node = TaskExecutor("process", func=lambda x: x * 2)
graph = TaskGraph(name="demo", graph_mode="thread")
graph.set_nodes([node])

# Omitting report (or passing report=None) disables reporting
graph.run(
    {"process": [1, 2, 3]},
    report=ReportConfig("http://127.0.0.1:5005"),
)
```

`ReportConfig` only accepts `http` / `https` addresses; validation is performed at construction time, and a trailing `/` is stripped. After reporting is enabled, if the target service is not started,
the [logs](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/docs/en/src/persist/core_log.md)
will contain some `WARNING` messages. This indicates that the reporting channel cannot connect to the remote service, but it does not affect the task graph's own operation.

```log
2025-12-10 08:57:13 WARNING [Reporter] Task injection fetch failed: ConnectTimeout
```

## Run Test Examples

The project provides multiple example files in the `tests/` directory for quickly understanding the framework's features.

To ensure tests run properly, it is recommended to run directly from the repository root:

```bash
uv sync --group dev
```

After that, it is recommended to run the following tests first:

```bash
pytest tests/graph/test_graph.py
pytest tests/node/test_node.py
```

- `tests/graph/test_graph.py` contains graph-structure-related tests: DAG construction, layered scheduling, thread mode, loop/grid/complete graph structures, etc.
- `tests/node/test_node.py` contains node-related tests: types, meta information, scheduling and lifecycle, etc.

During code execution, you can inspect the running status through logs, `PrintObserver` (console observer), `MetricsObserver` (metrics observer), or `ReportConfig` remote reporting. `MetricsObserver` must be registered via `graph.add_observer(...)` before running and the instance kept; after running, call `get_node_metrics()` / `get_graph_metrics()` to read the statistics.
