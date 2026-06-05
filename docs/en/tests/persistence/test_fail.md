# Failure Persistence Tests (test_fail.py)

> Last Updated: 2026/06/05

## Purpose
Validates that when `FailInlet` and `FailSpout` work together, task errors are asynchronously written into JSONL while the total error count and in-memory error pairs are updated at the same time.

## Coverage
- `start_graph()` records graph-structure context.
- `task_error()` serializes task values and exception information into `FailSpout`.
- `FailSpout.total_error_num` and `get_error_pairs()` reflect the actual processed result.

## Key Scenarios
- Start the spout inside a temporary directory.
- Write two kinds of errors in sequence: `ValueError` and `RuntimeError`.
- Wait for the background thread to flush data, then assert that the JSONL file exists and that the number of error records, error types, and task values are all correct.

## How to Run

```bash
pytest tests/persistence/test_fail.py -v
pytest tests/persistence/test_fail.py -k "fail_persistence" -v
```

