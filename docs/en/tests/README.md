# tests/ Test Overview

> 📅 Last Updated: 2026/11/13

## Description

This directory collects documentation for the pytest test suite under `tests/`, designed to help readers quickly locate coverage scopes, execution methods, and regression risk points for different modules.

Unlike `demo/`, the focus here is "functional correctness"; unlike `bench/`, performance is not discussed here. Instead, the focus is on behavioral constraints, edge cases, and protocol consistency.

## Recommended Reading Order

If this is your first time examining the test suite, we recommend reading in the following order:

1. `conftest.md`: Start with test helpers and shared initialization description
2. `runtime/`: Understand coverage of base types, queues, exceptions, and scheduling primitives
3. `graph/`: Understand core tests for graph structures and task topologies
4. `node/`, `funnel/`: Tests for execution scheduling, dispatch, and pipelines
5. `observer/`, `persist/`, `reporter/`, `ticker/`: Observability, persistence, remote reporting, and tickers
6. `assembly/`: Resource assembly and start/stop order
7. `benchmark/`: Benchmark utilities and clone utility tests

## Document Index

### Top-Level Entry Points

| Document | Description |
|------|------|
| `conftest.md` | Global test utilities and shared initialization description (`metrics_of`, `lifecycle_db_of`, `wait_until`, etc.) |

### Subdirectory Descriptions

| Document | Description |
|------|------|
| `assembly/test_run.md` | Resource assembly, observer start/stop, and `db_path` production of `run_graph_resources` / `run_node_resources` |
| `benchmark/test_benchmark.md` / `test_clone.md` | `benchmark_graph` / `benchmark_executor` benchmark tests and clone utility tests |
| `funnel/test_inlet.md` / `test_spout.md` | `BaseInlet.send` / `BaseSpout` start/stop and idempotency-related tests |
| `graph/test_graph.md` etc. | `TaskGraph`, task injection, topological analysis, and structure export tests |
| `node/test_dispatch.md` etc. | `TaskDispatch` retry/termination merging, `TaskExecutor` / `TaskSplitter` / `TaskRouter` related tests |
| `observer/test_observer.md` / `test_metrics.md` | `Event` base class, the unified `on_event` entry, `ObserverHub.find`, and metrics observer tests |
| `persist/test_lifecycle.md` etc. | Tests for lifecycle records (dataclasses), logs, rendering, and sqlite utilities |
| `reporter/test_inject.md` etc. | Remote injection, pushing, and status snapshot tests |
| `runtime/test_envelope.md` etc. | Base runtime tests such as queues, envelopes, exceptions, log levels, and types |
| `ticker/test_ticker.md` etc. | Ticker loop, handler phase, and hub fan-out tests |

## How to Use

You can run tests by module from the project root directory:

```bash
uv run pytest tests -v
uv run pytest tests/runtime -v
uv run pytest tests/graph -v
uv run pytest tests/node -v
uv run pytest tests/observer -v
uv run pytest tests/persist -v
uv run pytest tests/reporter -v
uv run pytest tests/ticker -v
```

You can also filter by keyword:

```bash
uv run pytest tests -k "executor or graph or reporter" -v
```

## How to Read

We recommend using these documents in the following way:

- To know whether a module "is tested": first read the corresponding subdirectory's `test_*.md`
- To know how a specific behavior "is tested": read the corresponding `test_*.md` (subdirectories no longer provide `__init__.md`)
- To assess the impact surface of a protocol change: prioritize the `graph/`, `node/`, `observer/`, `persist/`, and `reporter/` document groups

## Notes

1. Some tests depend on temporary files, sqlite, event queues, or HTTP reporting pipelines. Runtime environment fluctuations may affect execution time but should not affect assertion results.
2. When production protocols change, test documentation typically needs to be synchronized with `src/` and `demo/` updates.
3. If you only want to quickly verify the current change, prioritize running the test subset closest to the changed directory rather than always running the full test suite.
4. Subdirectories in this directory (`assembly/`, `benchmark/`, `funnel/`, `graph/`, `node/`, `observer/`, `persist/`, `reporter/`, `runtime/`, `ticker/`) **do not have `__init__.py`**, so there are no corresponding `__init__.md` files.
