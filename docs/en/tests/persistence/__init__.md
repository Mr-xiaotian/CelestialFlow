# persistence Test Package

> 📅 Last Updated: 2026/08/26

## Purpose
`tests/persistence/` covers three persistence paths: lifecycle persistence, log recording, and sqlite utility functions, verifying that Inlet / Spout paired components can correctly persist to disk or batch-flush logs in background threads.

## Included Test Files
- `test_lifecycle.py`: Task lifecycle event sqlite persistence (`LifecycleInlet` / `LifecycleSpout`).
- `test_log.py`: Log record batch writing to text files (`LogInlet` / `LogSpout`).
- `test_splite.py`: sqlite utility functions (table creation, CRUD, state transitions, grouped reads).
- `test_scope.py`: `funnel_scope()` context manager for managing global spout lifecycles.

## How to Run

```bash
pytest tests/persistence -v
pytest tests/persistence -k "lifecycle or log or splite" -v
```
