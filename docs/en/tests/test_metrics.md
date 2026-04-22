# test_metrics.py Test Documentation

## Test Purpose

Validates all counter logic, deduplication mechanisms, retry exception configuration, and state determination of the `TaskMetrics` class. `TaskMetrics` is the data source for task status visualization and monitoring within the framework, and its counting accuracy directly affects operational decision-making.

## Test Scope

| Test Class | Cases | Coverage |
|------------|-------|----------|
| `TestTaskMetricsBasic` | 8 | Initial values, all counters, processed/pending formulas, is_finished, reset |
| `TestTaskMetricsDuplicate` | 3 | Deduplication toggle, duplicate detection, reset_state clearing |
| `TestTaskMetricsRetryExceptions` | 2 | Default empty exceptions, dynamic addition |

### Key Test Case Details

#### `test_processed_equals_sum`
- **Purpose**: Validates the core accounting formula: `processed = succeeded + failed + duplicated`; `pending = input - processed`.
- **Input**: 10 tasks, 5 succeeded, 2 failed, 1 duplicated
- **Assertions**: `processed == 8`, `pending == 2`

#### `test_is_tasks_finished_true / false`
- **Purpose**: Validates that `is_tasks_finished()` determines completion status by comparing `task_counter` against `success + error + duplicate`.
- **Boundary**: Returns `True` when equal, `False` when not equal.

#### `test_duplicate_check_enabled_detects_repeat`
- **Purpose**: With deduplication enabled, the same hash appearing a second time returns `True`.
- **Mechanism**: Internally uses a `set[str]` to store processed `task_hash` values.

#### `test_duplicate_check_resets_with_reset_state`
- **Purpose**: `reset_state()` clears `processed_set`, allowing previously deduplicated tasks to re-enter.
- **Note**: `reset_counter()` only resets counter values; it does **not** reset the deduplication set. `reset_state()` is required to reset the deduplication set.

## Dependencies

| Dependency | Description |
|------------|-------------|
| `pytest` | Test framework |
| `celestialflow.runtime.core_metrics.TaskMetrics` | Object under test |

## Potential Issues and Notes

### 1. Thread/Process Safety (Not Covered by Current Tests)
`TaskMetrics` internally selects different counter implementations based on `execution_mode`:
- `serial`: `ValueWrapper` (no lock)
- `thread`: `ValueWrapper` + `threading.Lock`
- `process`: `multiprocessing.Value`

Current unit tests only run in `serial` mode and do not cover counter races in concurrent scenarios. To verify thread safety, the following test should be added:
```python
def test_thread_safe_counter():
    metrics = TaskMetrics(execution_mode="thread")
    # Multi-threaded concurrent add_success_count
```

### 2. Separation of Responsibilities Between `reset_counter` and `reset_state`
| Method | What It Resets |
|--------|---------------|
| `reset_counter()` | Values of `task_counter`, `success_counter`, `error_counter`, `duplicate_counter` |
| `reset_state()` | `processed_set` (deduplication set) |

Common misconception: expecting the deduplication set to be cleared after calling `reset_counter()`. **It is not**; `reset_state()` must be called explicitly.

### 3. Semantics of `add_task_count` and `task_counter`
`add_task_count(5)` accumulates an initial value to `task_counter`. In `SumCounter` mode, this value may come from the accumulation of multiple sub-counters (such as `TaskSplitter` split counts). Directly modifying `task_counter.value` may break consistency.

### 4. Timing Issues with `is_tasks_finished`
`is_tasks_finished()` is a non-blocking read operation. In `thread` mode, if a worker thread is between `add_success_count()` and `add_task_count()`, a transient intermediate state may be read (`processed > input` or `processed < input`).

**Recommendation**: In staged scheduling mode, check this status only between layers, avoiding calls during peak task execution.

### 5. Immutability of Retry Exception Tuple
`retry_exceptions` is of type `tuple[type[Exception], ...]`, extended via the `+` operator. This ensures consistency during multi-threaded reads, though the addition operation is not atomic (which currently does not matter, as it is typically configured only during initialization).

## How to Run

```bash
pytest tests/test_metrics.py -v
```

All test cases are pure in-memory operations with execution time `< 100ms`.

## Related Files

- `src/celestialflow/runtime/core_metrics.py`: Implementation under test
- `src/celestialflow/runtime/util_factories.py`: Counter factory (`make_counter`, `SumCounter`)
- `tests/test_executor.py`: Validates metrics counting in end-to-end scenarios
