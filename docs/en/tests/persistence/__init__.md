# persistence Test Package

> 📅 Last Updated: 2026/06/22

## Purpose
`tests/persistence/` covers error fallback, log recording, and sqlite utility function persistence paths, verifying that Inlet/Spout paired components can correctly persist to disk or batch-flush logs in background threads.

## Included Test Files
- `test_fallback.py`: Error and success result sqlite persistence (`FallbackInlet` / `FallbackSpout`).
- `test_log.py`: Log record batch writing to text files (`LogInlet` / `LogSpout`).
- `test_splite.py`: sqlite utility functions (table creation, CRUD, state transitions, grouped reads).

## How to Run

```bash
pytest tests/persistence -v
pytest tests/persistence -k "fallback or log or splite" -v
```
