# Task Metrics Tests (test_metrics.py)

> 📅 Last Updated: 2026/06/11

## Purpose
Verifies the `TaskMetrics` class in `celestialflow.runtime.core_metrics`, ensuring that various statistical metrics (success, failure, duplicate, pending, etc.) accumulated during task execution are calculated accurately.

## Core Test Object
- `TaskMetrics`: Responsible for per-stage or global task counting and status tracking.

## Test Coverage Matrix

| Test Class | Case Count | Coverage Goals |
|------------|------------|----------------|
| `TestTaskMetricsBasic` | 8 | Basic count accumulation, formula verification, completion detection, counter reset |
| `TestTaskMetricsDuplicate` | 3 | Dedup enable/disable, `reset_state()` clearing the hash set |
| `TestTaskMetricsRetryExceptions` | 2 | Default retryable exceptions empty, dynamic addition of exception types |

## Key Test Scenarios
1. **Basic Counting**: Verifies the accumulation logic of `add_task_count`, `add_success_count`, `add_error_count`, `add_duplicate_count`, and similar methods.
2. **Formula Verification**: Verifies `tasks_processed = tasks_succeeded + tasks_failed + tasks_duplicated`, and `tasks_pending = tasks_input - tasks_processed`.
3. **Status Detection**: Verifies the return value of `is_tasks_finished()` under different count combinations (returns `True` when Pending is 0).
4. **Dedup Logic**:
   - Verifies that when dedup is disabled, the same hash always returns `False`.
   - Verifies that when dedup is enabled, a second check of the same hash returns `True`.
   - Verifies that `reset_state()` clears the hash set, allowing the same task to pass through again.
5. **Retry Configuration**: Verifies the logic for dynamically adding retryable exception types.

## Test Focus
- **Metric Conservation**: Ensures `tasks_input` always equals `tasks_processed + tasks_pending`.
- **Dedup Accuracy**: Verifies that the hash set can effectively identify duplicate tasks and prevent redundant computation.
- **Reset Functionality**: Verifies the distinction between `reset_counter()` (resets only values) and `reset_state()` (resets values and the dedup set).

## How to Run

```bash
# Run all
pytest tests/runtime/test_metrics.py -v

# Basic count tests only
pytest tests/runtime/test_metrics.py -k "count" -v

# Dedup logic tests only
pytest tests/runtime/test_metrics.py -k "duplicate" -v

# Reset functionality tests only
pytest tests/runtime/test_metrics.py -k "reset" -v

# Retry configuration tests only
pytest tests/runtime/test_metrics.py -k "retry" -v
```

## Performance Reference

| Test | Duration |
|------|----------|
| `TestTaskMetricsBasic` / `TestTaskMetricsDuplicate` / `TestTaskMetricsRetryExceptions` | ~0.1s (pure logic operations) |

## Important Details
- The metrics are the data source for Dashboard display and graph-run termination detection.
- Tests cover the passing of the `execution_mode` parameter (though it currently mainly affects internal lock usage).

## Notes
- The accuracy of the metrics directly affects the auto-close detection of `TaskGraph`.
- The related implementation is located at `src/celestialflow/runtime/core_metrics.py`.
