# Task Metrics Tests (test_metrics.py)

> Last Updated: 2026/05/23

## Purpose
Validates the `TaskMetrics` class in `celestialflow.runtime.core_metrics`, ensuring execution statistics such as success, failure, duplication, and pending counts are computed accurately.

## Key Test Objects
- `TaskMetrics`: Tracks task counts and state for a single stage or globally.

## Key Test Flow
1. **Basic counters**: Verifies the accumulation logic of methods such as `add_task_count`, `add_success_count`, `add_error_count`, and `add_duplicate_count`.
2. **Formula verification**: Verifies the core conservation formula `processed = succeeded + failed + duplicated`.
3. **State checks**: Verifies the return value of `is_tasks_finished()` under different counter combinations, where Pending being 0 means `True`.
4. **Deduplication logic**:
   - Verifies behavior when deduplication is disabled.
   - Verifies that with deduplication enabled, a second check for the same hash returns `True`.
   - Verifies that `reset_state()` clears the hash set so the same task can pass again.
5. **Retry configuration**: Verifies the logic for dynamically adding retryable exception types.

## Test Focus
- **Metric conservation**: Ensures `tasks_input` always stays consistent with `tasks_processed + tasks_pending`.
- **Deduplication accuracy**: Verifies the hash set identifies duplicate tasks correctly and prevents redundant work.
- **Reset behavior**: Verifies the difference between `reset_counter()` for numeric counters only and `reset_state()` for counters plus the dedupe set.

## How to Run

```bash
# Run all tests
pytest tests/runtime/test_metrics.py -v

# Run basic counter tests only
pytest tests/runtime/test_metrics.py -k "count" -v

# Run deduplication tests only
pytest tests/runtime/test_metrics.py -k "duplicate" -v

# Run reset tests only
pytest tests/runtime/test_metrics.py -k "reset" -v

# Run retry configuration tests only
pytest tests/runtime/test_metrics.py -k "retry" -v
```

## Performance Reference

| Test | Duration |
|------|----------|
| `TestTaskMetrics` | ~0.1s (pure logic) |

## Important Details
- These metrics power both dashboard display and graph-shutdown decisions.
- The tests also cover passing the `execution_mode` parameter, even though it currently mainly affects internal locking.

## Notes
- Metrics accuracy directly affects the automatic shutdown decision of `TaskGraph`.
- Related implementation: `src/celestialflow/runtime/core_metrics.py`.

