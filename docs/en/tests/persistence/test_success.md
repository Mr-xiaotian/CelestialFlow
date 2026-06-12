# Success Result Cache Tests (test_success.py)

> 📅 Last Updated: 2026/06/05

## Purpose
Validates that `SuccessSpout` extracts `prev` and `task` from the `TaskEnvelope` and caches the success result as a `(original_task, result)` pair for subsequent queries.

## Coverage Points
- `TaskEnvelope.prev` is correctly preserved as the original task identifier.
- The `SuccessSpout` background thread converts queued envelopes into success pairs.
- `get_success_pairs()` returns results in the same order as input.

## Key Scenarios
- Construct two `TaskEnvelope` objects with `prev`.
- Enqueue them and wait for `SuccessSpout` to consume.
- Assert that the final result contains the two pairs `('task1', 100)` and `('task2', 200)`.

## How to Run

```bash
pytest tests/persistence/test_success.py -v
pytest tests/persistence/test_success.py -k "success_persistence" -v
```
