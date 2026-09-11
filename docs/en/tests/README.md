# tests/ Test Overview

> 📅 Last Updated: 2026/09/09

## Description

This directory collects documentation for the pytest test suite under `tests/`, designed to help readers quickly locate coverage scopes, execution methods, and regression risk points for different modules.

Unlike `demo/`, the focus here is "functional correctness"; unlike `bench/`, performance is not discussed here. Instead, the focus is on behavioral constraints, edge cases, and protocol consistency.

## Recommended Reading Order

If this is your first time examining the test suite, we recommend reading in the following order:

1. `conftest.md`: Start with test helpers and shared initialization description
2. `runtime/`: Understand coverage of base types, queues, exceptions, and scheduling primitives
3. `graph/`: Understand core tests for graph structures and task topologies
4. `observability/`: Finally, review integration tests for Reporter and reporting pipelines

## Document Index

### Top-Level Entry Points

| Document | Description |
|------|------|
| `conftest.md` | Global fixtures, test utility helpers, and shared initialization description |

### Subdirectory Descriptions

| Document | Description |
|------|------|
| `funnel/test_inlet.md` / `test_spout.md` | Inlet / Spout pipeline tests |
| `graph/test_graph.md` etc. | `TaskGraph`, topological analysis, and structure export tests |
| `observability/test_observer.md` / `test_reporter.md` | Observer, Reporter, injection, and reporting tests |
| `persistence/test_lifecycle.md` etc. | Lifecycle / log / sqlite utility persistence tests |
| `runtime/test_envelope.md` etc. | Queue, envelope, exception, estimator, counter, and other base runtime tests |
| `benchmark/test_benchmark.md` / `test_clone.md` | `benchmark_graph` / `benchmark_executor` benchmark tests and clone utility tests |

## How to Use

You can run tests by module from the project root directory:

```bash
pytest tests -v
pytest tests/runtime -v
pytest tests/graph -v
pytest tests/observability -v
```

You can also filter by keyword:

```bash
pytest tests -k "executor or graph or reporter" -v
```

## How to Read

We recommend using these documents in the following way:

- To know whether a module "is tested": first read the corresponding subdirectory's `test_*.md`
- To know how a specific behavior "is tested": read the corresponding `test_*.md` (subdirectories no longer provide `__init__.md`)
- To assess the impact surface of a protocol change: prioritize `graph/`, `runtime/`, `persistence/`, and `observability/` document groups

## Notes

1. Some tests depend on temporary files, sqlite, event queues, or HTTP reporting pipelines. Runtime environment fluctuations may affect execution time but should not affect assertion results.
2. When production protocols change, test documentation typically needs to be synchronized with `src/` and `demo/` updates.
3. If you only want to quickly verify the current change, prioritize running the test subset closest to the changed directory rather than always running the full test suite.
4. Subdirectories in this directory (`runtime/`, `graph/`, `funnel/`, `observability/`, `persistence/`, `benchmark/`) **do not have `__init__.py`**, so there are no corresponding `__init__.md` files.
