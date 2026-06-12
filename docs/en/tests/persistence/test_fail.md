# Failure Persistence Tests (test_fail.py)

> 📅 Last Updated: 2026/06/05

## Purpose
Validates that when `FailInlet` and `FailSpout` work together, task errors are asynchronously written to JSONL, and the total error count and in-memory error pair list are synchronously accumulated.

## Coverage Points
- `start_graph()` records the graph structure context.
- `task_error()` serializes the task value and exception information to `FailSpout`.
- `FailSpout.total_error_num` and `get_error_pairs()` reflect actual processing results.

## Key Scenarios
- Start a spout in a temporary directory.
- Write two types of errors consecutively: `ValueError` and `RuntimeError`.
- After waiting for the background thread to flush, assert that the JSONL file exists and that the error record count, types, and task values are all correct.

## How to Run

```bash
pytest tests/persistence/test_fail.py -v
pytest tests/persistence/test_fail.py -k "fail_persistence" -v
```
