# Success Result Cache Tests (test_success.py)

> Last Updated: 2026/06/05

## Purpose
Validates that `SuccessSpout` extracts `prev` and `task` from `TaskEnvelope` and caches successful results as `(original_task, result)` pairs for later lookup.

## Coverage
- `TaskEnvelope.prev` is preserved correctly as the original task identifier.
- The `SuccessSpout` background thread converts queued envelopes into success pairs.
- `get_success_pairs()` returns results in the same order as the inputs.

## Key Scenarios
- Construct two `TaskEnvelope` objects with `prev`.
- Enqueue them and wait for `SuccessSpout` to consume them.
- Assert that the final results are `('task1', 100)` and `('task2', 200)`.

## How to Run

```bash
pytest tests/persistence/test_success.py -v
pytest tests/persistence/test_success.py -k "success_persistence" -v
```

