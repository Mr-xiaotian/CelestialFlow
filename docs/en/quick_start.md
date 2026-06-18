# Quick Start

> 📅 Last Updated: 2026/06/18

This section will guide you through quickly installing and running **TaskGraph**, experiencing its task graph scheduling mechanism through examples.

## Create an Isolated Virtual Environment

It is recommended to use an isolated environment to avoid dependency conflicts with other projects.

```bash
# Create a project virtual environment (generates .venv by default)
uv venv --python 3.10

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

## (Optional) Set Up .env && Start Web Visualization

The Web monitoring interface is not mandatory, but it provides more information about task execution through a web page and is recommended.

First, create a `.env` file in the project root directory and fill in the following:

```env
# .env
# TaskWeb listening address
REPORT_HOST=127.0.0.1
# TaskWeb listening port
REPORT_PORT=5005
```

After that, you can start the Web service with the following command:

```bash
# If you pip-installed the project, you can directly use the celestialflow-web command in the current virtual environment
celestialflow-web --port 5005

# If you cloned and cd'd into the project directory, you need to run core_server.py
python -m celestialflow.web.core_server --port 5005 
```

The default listening port is `5000`, but to avoid conflicts, the test code uses port `5005`. Visit:

👉 [http://localhost:5005](http://localhost:5005)

to view task structure, execution status, error logs, and features like real-time task injection.

Below is the Web page display during test execution (not the default layout):

![WebUI](https://raw.githubusercontent.com/Mr-xiaotian/CelestialFlow/main/img/web_ui.gif)
<p align="center"><em>The gif compression loses too much detail (｡•́︿•̀｡)</em></p>

Note: If you have not started the Web window but have set:

```python
graph.set_reporter(True, host="127.0.0.1", port=5005)
```

then the [logs](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/docs/en/src/persistence/core_log.md) will contain some `WARNING` messages. This is TaskReporter indicating that it cannot connect to TaskWeb, but it does not affect usage.

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
pytest tests/stage/test_stage.py
```

- `tests/graph/test_graph.py` contains graph-structure-related tests: DAG construction, layered scheduling, thread mode, loop/grid/complete graph structures, etc.
- `tests/stage/test_stage.py` contains Stage-node-related tests: mode validation, tag generation, serialization checks, etc.

During execution, you can monitor the running status through the Web monitoring page.

