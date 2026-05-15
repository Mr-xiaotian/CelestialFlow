# test_metrics.py Test Documentation

> 📅 Last Updated: 2026/05/15

## Test Objective

Validates all counter logic, deduplication mechanisms, retry exception configuration, and state determination of the `TaskMetrics` task metrics class. `TaskMetrics` is the data source for task status visualization and monitoring within the framework; the accuracy of its counters directly impacts operational decisions.

## Test Scope

| Test Class | Test Count | Coverage |
|------------|-----------|----------|
| `TestTaskMetricsBasic` | 8 | Initial values, each counter, processed/pending formulas, is_finished, reset |
| `TestTaskMetricsDuplicate` | 3 | Deduplication toggle, duplicate detection, reset_state clearing |
| `TestTaskMetricsRetryExceptions` | 2 | Default empty exceptions, dynamic addition |

### Key Test Case Details

#### `test_processed_equals_sum`
- **Objective**: Validate the core accounting formula: `processed = succeeded + failed + duplicated`; `pending = input - processed`.
- **Input**: 10 tasks, 5 succeeded, 2 failed, 1 duplicated
- **Assertions**: `processed == 8`, `pending == 2`

#### `test_is_tasks_finished_true / false`
- **Objective**: Validate that `is_tasks_finished()` determines completion status by comparing `task_counter` with `success + error + duplicate`.
- **Boundary**: Returns `True` when equal, `False` when not equal.

#### `test_duplicate_check_enabled_detects_repeat`
- **Objective**: When deduplication is enabled, the same hash appearing a second time returns `True`.
- **Mechanism**: Internally uses `set[bytes]` to store processed `task_hash` values.

#### `test_duplicate_check_resets_with_reset_state`
- **Objective**: `reset_state()` clears `processed_set`, allowing previously deduplicated tasks to re-enter.
- **Note**: `reset_counter()` only resets counter values, it does **not** reset the deduplication set; `reset_state()` is required for that.

## Dependencies

| Dependency | Description |
|------------|-------------|
| `pytest` | Test framework |
| `celestialflow.runtime.core_metrics.TaskMetrics` | Object under test |

## Potential Issues and Notes

### 1. Thread Safety (Not Covered by Current Tests)
`TaskMetrics` selects different counter implementations based on `execution_mode`:
- `serial`: `ValueWrapper` (no lock)
- `thread`: `ValueWrapper` + `threading.Lock`

Current unit tests run only in `serial` mode and do not cover counter contention in concurrent scenarios. To verify thread safety, the following test should be added:
```python
def test_thread_safe_counter():
    metrics = TaskMetrics(execution_mode="thread")
    # Multi-threaded concurrent add_success_count
```

### 2. Separation of Responsibilities: `reset_counter` vs `reset_state`
| Method | What It Resets |
|--------|---------------|
| `reset_counter()` | Values of `task_counter`, `success_counter`, `error_counter`, `duplicate_counter` |
| `reset_state()` | `processed_set` (deduplication set) |

Common misconception: expecting the deduplication set to be cleared after calling `reset_counter()`. **It is not**; `reset_state()` must be called explicitly.

### 3. Semantics of `add_task_count` and `task_counter`
`add_task_count(5)` accumulates initial values into `task_counter`. In `SumCounter` mode, this value may come from accumulated sub-counters (e.g., `TaskSplitter` split counts). Directly modifying `task_counter.value` may break consistency.

### 4. Timing Issues with `is_tasks_finished`
`is_tasks_finished()` is a non-blocking read operation. In `thread` mode, if a worker thread is between `add_success_count()` and `add_task_count()`, a transient intermediate state may be read (`processed > input` or `processed < input`).

**Recommendation**: In staged scheduling mode, only check this state between layers to avoid calling it during peak task execution.

### 5. Immutability of Retry Exception Tuples
`retry_exceptions` is of type `tuple[type[Exception], ...]`, appended via the `+` operator. This ensures consistency for multi-threaded reads, although the addition operation is not atomic (this is not an issue in current implementation since it is typically configured only during initialization).

## How to Run

```bash
pytest tests/test_metrics.py -v
```

All test cases are pure in-memory operations, execution time `< 100ms`.

## Related Files

- `src/celestialflow/runtime/core_metrics.py`: Implementation under test
- `src/celestialflow/runtime/util_factories.py`: Counter factories (`make_counter`, `SumCounter`)
- `tests/test_executor.py`: Validates metrics counting in end-to-end scenarios
