# Quick Start

> 📅 Last Updated: 2026/04/22

This section will guide you through quickly installing and running **TaskGraph**, experiencing its task graph scheduling mechanism through examples.

## Create an Independent Virtual Environment

It is recommended to use an independent environment to avoid dependency conflicts with other projects.

```bash
# Create a project virtual environment (generates .venv by default)
uv venv --python 3.10

# Activate the environment (Windows)
. .\.venv\Scripts\Activate.ps1

# Activate the environment (Linux/macOS)
source .venv/bin/activate
```

It is recommended to use an independent virtual environment. CelestialFlow recommends using `uv` to manage dependencies and environments.

## Install CelestialFlow

CelestialFlow has been published to [PyPI](https://pypi.org/project/celestialflow/) and can be installed directly via `pip` / `uv pip` without cloning the source code.

```bash
# Install the latest version directly
uv pip install celestialflow
```

However, if you want to run the test code later, or want to use the Go-based go_worker program, you will still need to clone the project.

```bash
# Clone the project
git clone https://github.com/Mr-xiaotian/CelestialFlow.git
cd CelestialFlow
uv pip install .
```

## (Optional) Set Up .env && Start Web Visualization

The Web monitoring interface is not required, but it provides more information about task execution through a web page and is recommended.

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
# If you pip-installed the project, you can use the celestialflow-web command directly in the current virtual environment
celestialflow-web --port 5005

# If you cloned and cd'd into the project directory, you need to run the task_web.py file
python src/celestialflow/task_web.py --port 5005 
```

The default listening port is `5000`, but to avoid conflicts, the test code uses port `5005`. Access:

👉 [http://localhost:5005](http://localhost:5005)

You can view the task structure, execution status, error logs, and real-time task injection features.

The image below shows the web page display during test execution, not the default appearance:

![WebUI](https://raw.githubusercontent.com/Mr-xiaotian/CelestialFlow/main/img/web_ui.gif)
<p align="center"><em>The gif compressed too many details (｡•́︿•̀｡)</em></p>

Note: If you haven't started the Web window but have set

```python
graph.set_reporter(True, host="127.0.0.1", port=5005)
```

then the [logs](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/docs/reference/persistence/core_log.md) will contain some `WARNING` messages indicating that TaskReporter cannot connect to TaskWeb. This does not affect usage.

```log
2025-12-10 08:57:13 WARNING [Reporter] Task injection fetch failed: ConnectTimeout
```

## Run Test Examples

The project provides multiple example files in the `tests/` directory for quickly understanding framework features.

To ensure tests run properly, please install the necessary test and dotenv libraries first:
```bash
uv pip install pytest pytest-asyncio python-dotenv
```

Then it is recommended to run the following tests first:

```bash
pytest tests/test_graph.py
pytest tests/test_stage.py
```

- `tests/test_graph.py` contains graph structure-related tests: DAG construction, layered scheduling, thread mode, loop/grid/complete graph structures, etc.
- `tests/test_stage.py` contains Stage node-related tests: mode validation, tag generation, serialization checks, etc.

You can monitor the execution through the Web monitoring page while the code is running.
