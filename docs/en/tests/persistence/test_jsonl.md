# JSONL Utility Tests (test_jsonl.py)

> 📅 Last Updated: 2026/05/23

## Purpose
Validates the utility functions in `celestialflow.persistence.util_jsonl`, ensuring accurate parsing, filtering, and grouping of JSONL-format persistence logs.

## Core Test Targets
- `parse_jsonl_value`: Intelligently parses string values into Python native types (numbers, booleans, tuples, etc.).
- `load_jsonl_logs`: Batch-loads and filters log lines.
- `load_jsonl_by_key`: Groups and extracts fields by a single key (e.g., stage).
- `load_jsonl_grouped_by_keys`: Groups by a combination of multiple keys.
- `load_task_error_pairs`: Specialized function for extracting task-error record pairs.

## Key Test Flow
1. **Intelligent parsing**: Validates that the string `"1"` becomes an integer, `"True"` becomes a boolean, and `"[1, 2]"` becomes a tuple.
2. **Error string splitting**: Validates extracting the error type and message content from `ValueError(msg)` format.
3. **Structured reading**: Simulates a JSONL file containing Meta lines, regular data lines, and complex task lines (such as tuple IDs), and validates reading completeness.
4. **Multi-level grouping**: Validates the logic for grouping by composite keys such as `(error, stage)`.

## Test Focus
- **Robustness**: Ensures Meta lines or lines with inconsistent formats are correctly skipped during reading.
- **Type restoration**: Validates that task data recovered from JSONL retains its original type (e.g., `(1, 2)` tuples).
- **Field filtering**: Validates that the `keys` parameter effectively reduces memory usage by extracting only needed fields.

## How to Run

```bash
# Run all
pytest tests/persistence/test_jsonl.py -v

# Run intelligent parsing tests only
pytest tests/persistence/test_jsonl.py -k "parse" -v

# Run grouping read tests only
pytest tests/persistence/test_jsonl.py -k "group" -v

# Run error pair tests only
pytest tests/persistence/test_jsonl.py -k "error_pair" -v
```

## Performance Reference

| Test | Duration |
|------|------|
| `TestJsonlUtils` | ~0.1s (pure logic, no I/O wait) |

## Important Details
- Uses `pytest.fixture` to create a temporary `sample_jsonl` file for testing.
- `test_load_task_error_pairs` validates the encapsulation of the `PersistedErrorRecord` data model.

## Notes
- Test code is located at `tests/persistence/test_jsonl.py`.
