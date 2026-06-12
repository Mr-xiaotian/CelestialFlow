# tests Test Package

> 📅 Last Updated: 2026/06/11

## Purpose
The `tests/` directory contains CelestialFlow's pytest test suite. `tests/__init__.py` is an empty file; this page documents the test directory structure.

## Directory Structure
- `tests/funnel/`: Inlet / Spout pipeline basic behavior tests.
- `tests/graph/`: TaskGraph construction and scheduling tests.
- `tests/observability/`: Runtime status reporting tests.
- `tests/persistence/`: Error, log, and success result persistence tests.
- `tests/runtime/`: Envelope, queue, hash, counter, exception, and estimation tests.
- `tests/stage/`: TaskStage / TaskExecutor and built-in Stage tests.
- `tests/utils/`: Clone utility and formatting utility tests.
- `tests/web/`: Web API and service integration tests.
- `tests/conftest.py`: Common test helpers.
- `tests/__init__.py`: Empty file, marks the test package.

## How to Run

```bash
pytest tests -v
pytest tests/runtime -v
pytest tests/stage -k "executor or stage" -v
```
