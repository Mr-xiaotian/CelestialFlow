# tests/runtime/test_metrics.py

> 📅 Last Updated: 2026/09/24

## Purpose
Verifies the `TaskMetrics` class in `celestialflow.runtime.core_metrics`, ensuring that various statistical metrics during task execution (input, success, failure, duplicate, pending) are calculated accurately, and covering upstream/downstream bound counters, retryable exception configuration, and the accumulation semantics of busy wall-clock time (busy time).

## Core Test Objects
- `TaskMetrics`: Responsible for a single node's (Stage) task counting, upstream/downstream bound counts, retryable exceptions, and busy-time tracking.
- `ValueWrapper`: A thread-safe wrapper used for upstream/downstream counting; in tests, `ValueWrapper` is used directly to simulate upstream/downstream counters.

## Test Coverage Matrix

| Test Class | Case Count | Coverage Goals |
|------------|------------|----------------|
| `TestTaskMetricsBasic` | 9 | Initial counts, external input accumulation, external/upstream input split, success/failure/duplicate accumulation, `processed`/`pending` formulas, completion detection |
| `TestTaskMetricsBinding` | 5 | Upstream counter counted into the total, `connect_to` shared counter, unregistered downstream raises `KeyError`, upstream/downstream count map query |
| `TestTaskMetricsRetryExceptions` | 2 | Default retryable exceptions empty, dynamic addition of exception types |
| `TestTaskMetricsElapsed` | 3 | Busy time initially 0, accumulates only while executing, concurrent overlap counted once by wall-clock |
| **Total** | **19** | |

## Key Test Scenarios

### Basic Counting (`TestTaskMetricsBasic`)
1. **Initial state** (`test_initial_counts`): When a new `TaskMetrics` is created, `tasks_input/succeeded/failed/duplicated/processed/pending` are all 0, `get_external_input_count()` and `get_upstream_input_count()` are 0, and the upstream/downstream count maps are empty dicts.
2. **External input accumulation** (`test_add_external_input_count`): After `add_external_input_count(5)`, the external input is 5, the upstream input is 0, and both `get_input_count()` and `tasks_input` are 5.
3. **Input split** (`test_input_count_split_external_and_upstream`): Registers two upstreams via `set_upstream_counter`, and after accumulating respectively verifies external 3, upstream 6, total 9.
4. **Success/failure/duplicate accumulation**: `add_success_count`, `add_fail_count`, and `add_duplicate_count` update the corresponding getters and `get_counts()` keys respectively.
5. **Formula verification** (`test_processed_equals_sum`): Verifies `tasks_processed = succeeded + failed + duplicated`, `tasks_pending = input - processed`.
6. **Completion detection** (`test_is_tasks_finished_true` / `_false`): Returns `True` when `pending` is 0, otherwise `False`.

### Upstream/Downstream Binding (`TestTaskMetricsBinding`)
- `test_upstream_counter_adds_to_task_count`: After the upstream `ValueWrapper` increases by 3, the current node's `get_input_count()` and `get_upstream_input_count()` are both 3, and the external input is 0.
- `test_shared_binding_counter`: `prev.set_downstream_counter` and `curr.set_upstream_counter` are passed the same `ValueWrapper`; after `prev.add_downstream_count`, `curr.get_input_count()` reflects that increment.
- `test_add_downstream_count_missing_target_raises`: Calling `add_downstream_count` for an unregistered name raises `KeyError`.
- `test_get_upstream_counts` / `test_get_downstream_counts`: Verifies the returned `{name: count}` maps.

### Retry Configuration (`TestTaskMetricsRetryExceptions`)
- By default `retry_exceptions == ()`.
- After `set_retry_exceptions(ValueError, RuntimeError)`, both exception types appear in the `retry_exceptions` tuple.

### Busy Time (`TestTaskMetricsElapsed`)
Uses a manually advanceable `_FakeClock` to substitute `celestialflow.runtime.core_metrics.time.perf_counter`:
1. **Initially 0** (`test_elapsed_is_zero_without_tasks`): `get_elapsed() == 0.0` when no task is executing.
2. **Accumulates only while busy** (`test_elapsed_accumulates_only_while_busy`): The elapsed slice not yet closed after `begin_task()` is also counted (2.0s); after `end_task()` and 5s idle, it no longer increases.
3. **Concurrent overlap counted once** (`test_elapsed_counts_overlapping_tasks_once`): During the overlap of two `begin_task()` calls, counted once by wall-clock; when the sum of each task's duration is 5s, only 3s is recorded; after finishing, idle time no longer increases.

## Test Focus
- **Metric conservation**: `tasks_input` stays consistent with `tasks_processed + tasks_pending`.
- **Binding sharing**: Upstream and downstream share counts via the same `ValueWrapper` instance, which is how `connect_to` semantics are guaranteed.
- **Elapsed semantics**: Busy time accumulates by the node's wall-clock time, with overlapping intervals of concurrent tasks counted only once.

## How to Run

```bash
# Run all
pytest tests/runtime/test_metrics.py -v

# Basic count tests only
pytest tests/runtime/test_metrics.py -k "count" -v

# Upstream/downstream binding tests only
pytest tests/runtime/test_metrics.py -k "binding or upstream or downstream" -v

# Busy time tests only
pytest tests/runtime/test_metrics.py -k "elapsed" -v
```

## Performance Reference

| Test | Duration |
|------|----------|
| `TestTaskMetricsBasic` / `TestTaskMetricsBinding` / `TestTaskMetricsRetryExceptions` | ~0.1s (pure logic operations) |
| `TestTaskMetricsElapsed` | < 0.1s (fake clock substitute, no real waiting) |

## Important Details
- The metrics are the data source for Dashboard display and graph-run termination detection.
- `get_elapsed()` includes the currently unclosed elapsed slice when `_busy_since` is non-empty.
- `_FakeClock` replaces `core_metrics.time.perf_counter` via `monkeypatch.setattr`, so tests produce no real waiting.

## Notes
- The accuracy of the metrics directly affects the auto-close detection of `TaskGraph`.
- The related implementation is located at `src/celestialflow/runtime/core_metrics.py`.
