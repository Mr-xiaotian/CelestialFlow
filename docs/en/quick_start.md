# Quick Start

> 📅 Last updated: 2026/04/22

This section will guide you through quickly installing and running **TaskGraph**, experiencing its task graph scheduling mechanism through examples.

## Create an Isolated Virtual Environment

It is recommended to use an isolated environment to avoid dependency conflicts with other projects.

```bash
# Create a project virtual environment (generates .venv by default)
uv venv --python 3.10

# Activate the environment (Windows)
. .\.venv\Scripts\Activate.ps1

# Activate the environment (Linux/macOS)
source .venv/bin/activate
```

It is recommended to use an isolated virtual environment. CelestialFlow recommends using `uv` to manage dependencies and environments.

## Install CelestialFlow

CelestialFlow is published on [PyPI](https://pypi.org/project/celestialflow/) and can be installed directly via `pip` / `uv pip` without cloning the source code.

```bash
# Install the latest version directly
uv pip install celestialflow
```

However, if you want to run the test code shown later, or use the Go-based go_worker program, you will still need to clone the project.

```bash
# Clone the project
git clone https://github.com/Mr-xiaotian/CelestialFlow.git
cd CelestialFlow
uv pip install .
```

## (Optional) Set Up .env && Launch Web Visualization

The Web monitoring interface is not required, but it provides additional information about task execution through a web page and is recommended.

First, create a `.env` file in the project root directory with the following content:

```env
# .env
# TaskWeb listening address
REPORT_HOST=127.0.0.1
# TaskWeb listening port
REPORT_PORT=5005
```

Then, you can start the Web service with the following command:

```bash
# If you installed the project via pip, you can use the celestialflow-web command directly in the current virtual environment
celestialflow-web --port 5005

# If you cloned the project and navigated into the project directory, run the task_web.py file
python src/celestialflow/task_web.py --port 5005 
```

The default listening port is `5000`, but to avoid conflicts, the test code uses port `5005`. Visit:

👉 [http://localhost:5005](http://localhost:5005)

You can view the task structure, execution status, error logs, and inject tasks in real time.

The image below shows the Web page when running tests (not the default layout):

![WebUI](https://raw.githubusercontent.com/Mr-xiaotian/CelestialFlow/main/img/web_ui.gif)
<p align="center"><em>The gif has lost too many details due to compression (｡•́︿•̀｡)</em></p>

Note: If you have not started the Web interface but have configured

```python
graph.set_reporter(True, host="127.0.0.1", port=5005)
```

then the [logs](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/docs/reference/persistence/core_log.md) will contain some `WARNING` messages indicating that TaskReporter cannot connect to TaskWeb. This does not affect functionality.

```log
2025-12-10 08:57:13 WARNING [Reporter] Task injection fetch failed: ConnectTimeout
```

## Run Test Examples

The project provides several example files located in the `tests/` directory for quickly understanding the framework's features.

To ensure tests run properly, first install the required testing and dotenv libraries:
```bash
uv pip install pytest pytest-asyncio python-dotenv
```

It is recommended to start by running the following tests:

```bash
pytest tests/test_graph.py
pytest tests/test_stage.py
```

- `tests/test_graph.py` contains graph structure related tests: DAG construction, staged scheduling, thread mode, loop/grid/complete graph structures, etc.
- `tests/test_stage.py` contains Stage node related tests: mode validation, tag generation, serialization checks, etc.

You can monitor the execution through the Web monitoring page while the code is running.
