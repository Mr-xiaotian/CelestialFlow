# persistence Test Package

> 📅 Last Updated: 2026/06/11

## Purpose
`tests/persistence/` covers the three persistence paths (errors, logs, and success results) as well as JSONL parsing utility functions, verifying that Inlet/Spout paired components can correctly write to disk or cache results in background threads.

## Included Test Files
- `test_fail.py`: Error records written to JSONL.
- `test_jsonl.py`: JSONL file parsing and grouping utility functions.
- `test_log.py`: Log records written to a text file.
- `test_success.py`: Success results cached as `(prev_task, result)` pairs.

## How to Run

```bash
pytest tests/persistence -v
pytest tests/persistence -k "fail or jsonl or log or success" -v
```
