# persistence Test Package

> Last Updated: 2026/06/05

## Purpose
`tests/persistence/` covers three persistence paths for errors, logs, and successful results, validating that paired Inlet / Spout components can flush to disk or cache results correctly in background threads.

## Included Test Files
- `test_fail.py`: Writes error records into JSONL.
- `test_log.py`: Writes log records into a text file.
- `test_success.py`: Caches successful results as `(prev_task, result)` pairs.

## How to Run

```bash
pytest tests/persistence -v
pytest tests/persistence -k "fail or log or success" -v
```

