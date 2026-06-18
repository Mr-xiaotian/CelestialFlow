# tests/ Test Overview

> 📅 Last Updated: 2026/06/18

## Description

This directory collects Chinese documentation for the pytest test suite under `tests/`, designed to help readers quickly locate coverage scopes, execution methods, and regression risk points for different modules.

Unlike `demo/`, the focus here is "functional correctness"; unlike `bench/`, performance is not discussed here. Instead, the focus is on behavioral constraints, edge cases, and protocol consistency.

## Recommended Reading Order

If this is your first time examining the test suite, we recommend reading in the following order:

1. `tests/__init__.md`: Start with the overall test directory structure
2. `runtime/__init__.md`: Understand coverage of base types, queues, exceptions, and scheduling primitives
3. `stage/__init__.md` and `graph/__init__.md`: Understand core tests for executors, stages, and task graphs
4. `web/__init__.md` and `observability/__init__.md`: Finally, review integration tests for Web and reporting pipelines

## Document Index

### Top-Level Entry Points

| Document | Description |
|------|------|
| `__init__.md` | Overall `tests/` directory structure and execution instructions |
| `conftest.md` | Global fixtures, test utility helpers, and shared initialization description |

### Subdirectory Descriptions

| Document | Description |
|------|------|
| `funnel/__init__.md` | Inlet / Spout pipeline tests |
| `graph/__init__.md` | `TaskGraph`, topological analysis, and structure export tests |
| `observability/__init__.md` | Observer, Reporter, injection, and reporting tests |
| `persistence/__init__.md` | sqlite / JSONL / success / fail / log persistence tests |
| `runtime/__init__.md` | Queue, envelope, exception, estimator, counter, and other base runtime tests |
| `stage/__init__.md` | `TaskExecutor`, `TaskStage`, and built-in stage tests |
| `utils/__init__.md` | clone / format and other utility layer tests |
| `web/__init__.md` | Web service, routing, and interface behavior tests |

## How to Use

You can run tests by module from the project root directory:

```bash
pytest tests -v
pytest tests/runtime -v
pytest tests/stage -v
pytest tests/graph -v
pytest tests/web -v
```

You can also filter by keyword:

```bash
pytest tests -k "executor or graph or reporter" -v
```

## How to Read

We recommend using these documents in the following way:

- To know whether a module "is tested": first read the corresponding subdirectory's `__init__.md`
- To know how a specific behavior "is tested": then read the corresponding `test_*.md`
- To assess the impact surface of a protocol change: prioritize `graph/`, `stage/`, `persistence/`, and `web/` document groups

## Notes

1. Some tests depend on temporary files, sqlite, event queues, or web test clients. Runtime environment fluctuations may affect execution time but should not affect assertion results.
2. When production protocols change, test documentation typically needs to be synchronized with `src/`, `web/`, and `demo/` updates.
3. If you only want to quickly verify the current change, prioritize running the test subset closest to the changed directory rather than always running the full test suite.
