# JSONL Utility Tests (test_jsonl.py)

> Last Updated: 2026/05/23

## Purpose
Validates the helper functions in `celestialflow.persistence.util_jsonl`, ensuring JSONL-based persistence logs can be parsed, filtered, and grouped accurately.

## Key Test Objects
- `parse_jsonl_value`: Intelligently parses string values into native Python types such as numbers, booleans, and tuples.
- `load_jsonl_logs`: Loads and filters JSONL lines in batches.
- `load_jsonl_by_key`: Extracts fields grouped by a single key such as `stage`.
- `load_jsonl_grouped_by_keys`: Groups records by combinations of multiple keys.
- `load_task_error_pairs`: Specialized helper for extracting task/error pairs.

## Key Test Flow
1. **Intelligent parsing**: Verifies that the string `"1"` becomes an integer, `"True"` becomes a boolean, and `"[1, 2]"` becomes a tuple.
2. **Error-string splitting**: Verifies that error type and message are extracted from values such as `ValueError(msg)`.
3. **Structured reading**: Simulates JSONL files containing Meta lines, normal data lines, and complex task lines such as tuple IDs, then verifies completeness of the loaded data.
4. **Multi-level grouping**: Verifies grouping by composite keys such as `(error, stage)`.

## Test Focus
- **Robustness**: Ensures Meta lines or malformed lines are skipped correctly during loading.
- **Type restoration**: Verifies that task data restored from JSONL keeps its original type, such as a tuple `(1, 2)`.
- **Field filtering**: Verifies that the `keys` parameter reduces memory usage by extracting only the needed fields.

## How to Run

```bash
# Run all tests
pytest tests/persistence/test_jsonl.py -v

# Run intelligent parsing tests only
pytest tests/persistence/test_jsonl.py -k "parse" -v

# Run grouped loading tests only
pytest tests/persistence/test_jsonl.py -k "group" -v

# Run error-pair tests only
pytest tests/persistence/test_jsonl.py -k "error_pair" -v
```

## Performance Reference

| Test | Duration |
|------|----------|
| `TestJsonlUtils` | ~0.1s (pure logic, no I/O wait) |

## Important Details
- A temporary `sample_jsonl` file is created with `pytest.fixture`.
- `test_load_task_error_pairs` verifies the `PersistedErrorRecord` data model wrapper.

## Notes
- The test code lives in `tests/persistence/test_jsonl.py`.

