# tests Test Package

> 📅 Last Updated: 2026/08/26

## Purpose
The `tests/` directory contains CelestialFlow's pytest test suite. `tests/__init__.py` is an empty file; this page documents the test directory structure.

## Directory Structure
- `tests/funnel/`: Inlet / Spout pipeline basic behavior tests.
- `tests/graph/`: TaskGraph construction and scheduling tests.
- `tests/observability/`: Runtime status reporting and injection tests.
- `tests/persistence/`: Lifecycle sqlite persistence, log persistence, `funnel_scope` context, and sqlite utility tests.
- `tests/runtime/`: Envelope, queue, hash, counter, exception, and estimation tests.
- `tests/stage/`: TaskStage / TaskExecutor / TaskDispatch and built-in Stage tests.
- `tests/benchmark/`: Clone utility and performance benchmark tests.
- `tests/conftest.py`: Common test helpers.
- `tests/__init__.py`: Empty file, marks the test package.

## How to Run

```bash
pytest tests -v
pytest tests/runtime -v
pytest tests/stage -k "executor or stage" -v
```
