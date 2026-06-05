# tests Package

> Last Updated: 2026/06/05

## Purpose
The `tests/` directory stores the CelestialFlow pytest suite. `tests/__init__.py` is an empty file, and this page documents the test directory structure.

## Directory Structure
- `tests/funnel/`: Base behavior tests for Inlet / Spout pipelines.
- `tests/graph/`: Graph construction and scheduling tests for `TaskGraph`.
- `tests/observability/`: Runtime status reporting tests.
- `tests/persistence/`: Persistence tests for errors, logs, and successful results.
- `tests/runtime/`: Tests for envelopes, queues, hashes, counters, exceptions, and estimators.
- `tests/stage/`: Tests for `TaskStage`, `TaskExecutor`, and built-in stages.
- `tests/web/`: Web API and service integration tests.
- `tests/conftest.py`: Shared test helpers.

## How to Run

```bash
pytest tests -v
pytest tests/runtime -v
pytest tests/stage -k "executor or stage" -v
```

