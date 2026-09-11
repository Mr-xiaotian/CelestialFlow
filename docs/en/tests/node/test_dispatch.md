# Task Dispatch Core Tests (test_dispatch.py)

> 📅 Last Updated: 2026/09/10

## Purpose

Verifies the core behavior of `celestialflow.node.core_dispatch.TaskDispatch` across three scheduling modes — `serial`, `thread`, and `async`: normal task execution, exception retry, duplicate task deduplication, termination signal merge exit, and fallback logic when the worker itself crashes.

## Core Test Objects

| Class / Function | Role | Description |
|-----------|------|-------------|
| `TaskDispatch` | Class under test | Task dispatcher, pulls `TaskEnvelope` / termination signals from the input queue, executes them by mode, and writes results back to the result queue |
| `TaskExecutor` | Host | Constructs the minimal runnable `BaseTaskNode` subclass used as the dispatch host |
| `_CtreeStub` | Mock | Replaces `ctree_client.emit` with an incrementing integer to avoid conflicts with the sqlite unique constraint |
| `MockSpout` / `LogSpout` / `LifecycleSpout` | Global handles | `start()` / `stop()` on demand in the `autouse` fixture to avoid background threads and persistence state cross-contamination |
| `_RecordingLogInlet` / `_CrashRetryLogInlet` | Mock LogInlet | Records or raises exceptions to trigger the worker crash fallback |
| `_CrashOnFailObserver` | Mock Observer | Raises inside the failure callback to verify the `observer_error` fallback |

## Key Test Scenarios

### `TestDispatchSerial` — Serial Dispatch

| Case | Coverage Goal |
|------|----------|
| `test_single_task` | Serial mode processes a single task, result is 9 |
| `test_multiple_tasks` | Serial mode processes 5 tasks, result count + termination signal = 6 |
| `test_retry_then_succeed` | The first 2 calls raise `ValueError`, the 3rd succeeds; final `func.calls == 3` |
| `test_retry_exhausted` | When errors persist continuously, only the termination signal is output |
| `test_termination_single_id` | A single termination ID is correctly passed to the result queue |
| `test_termination_multi_id` | Multiple termination IDs are merged into 1 termination signal output |
| `test_success_fanout_creates_distinct_downstream_ids` | On success fanout, each real downstream node is given an independent `TaskEnvelope.get_id()`, and the persisted `get_success_pairs()` can read the results back |

### `TestDispatchThread` — Thread Dispatch

| Case | Coverage Goal |
|------|----------|
| `test_basic_parallel` | 10 tasks, 4 threads in parallel, result count = 10 |
| `test_thread_duplicate` | When the same task is enqueued twice, `metrics.get_duplicate_count() == 1`, and at least 1 result is preserved |

### `TestDispatchAsync` — Async Dispatch

| Case | Coverage Goal |
|------|----------|
| `test_basic_async` | 10 tasks, 4 coroutines concurrently, result count = 10 |
| `test_async_retry_then_succeed` | Async retry: the first 2 calls raise, the 3rd succeeds, `func.calls == 3` |

### `TestWorkerCrashKeepsTerminationSignal` — Worker Crash Fallback (parameterized over three modes)

| Case | Coverage Goal |
|------|----------|
| `test_fail_handler_crash_keeps_termination` | Observer's failure callback raises `RuntimeError`, caught by the `observer_error` fallback, `worker_crash` is **not** triggered, the termination signal is still emitted |
| `test_retry_handler_crash_keeps_termination` | When `LogInlet.task_retry` raises, scheduling is not interrupted, the termination signal is still emitted, and `worker_crash` records the exception |

### `TestDispatchCoreBehavior` — Cross-Mode Parameterized

| Case | Coverage Goal |
|------|----------|
| `test_empty_queue_with_termination` | All three modes exit correctly with empty queue + termination signal |
| `test_result_count` | 5-task result count: all three modes produce 5 results + a termination signal |

## Key Data Flow

```mermaid
flowchart LR
    In[TaskInQueue] --> Get[task_queue.get]
    Get --> Sig{is TerminationIdPool?}
    Sig -- yes --> Merge[_process_termination_signal]
    Merge --> Break[break loop]
    Sig -- no --> Dup{metrics.is_duplicate?}
    Dup -- yes --> DupDeal[deal_duplicate]
    Dup -- no --> Worker[_worker / _async_worker]
    Worker --> Out[TaskOutQueue]
    Break --> Put[result_queue.put signal]
```

## Test Coverage Matrix

| Test Class | Case Count | Coverage Goals |
|-----------|------------|----------------|
| `TestDispatchSerial` | 7 | Single/multi task, retry success, retry exhaustion, single/multi ID termination signal, success fanout with independent downstream IDs |
| `TestDispatchThread` | 2 | 10-task concurrency, duplicate task dedup count |
| `TestDispatchAsync` | 2 | 10-task coroutine concurrency, async retry success |
| `TestWorkerCrashKeepsTerminationSignal` | 2 | Failure handling chain crash, retry log crash (parameterized over 3 modes) |
| `TestDispatchCoreBehavior` | 2 | Empty queue + termination signal (parameterized over 3 modes), 5-task result count (parameterized over 3 modes) |
| **Total** | **15** | |

## How to Run

```bash
# Run all
pytest tests/node/test_dispatch.py -v

# Serial dispatch tests only
pytest tests/node/test_dispatch.py -k "Serial" -v

# Thread dispatch tests only
pytest tests/node/test_dispatch.py -k "Thread" -v

# Async dispatch tests only
pytest tests/node/test_dispatch.py -k "Async" -v

# Worker crash fallback tests only
pytest tests/node/test_dispatch.py -k "Crash" -v

# Cross-mode parameterized tests only
pytest tests/node/test_dispatch.py -k "CoreBehavior" -v
```

## Performance Reference

| Test Class | Duration |
|------------|----------|
| `TestDispatchSerial` | < 0.5s |
| `TestDispatchThread` | < 0.5s |
| `TestDispatchAsync` | < 0.5s |
| `TestWorkerCrashKeepsTerminationSignal` | < 1.0s (6 cases = 2 scenarios × 3 modes) |
| `TestDispatchCoreBehavior` | < 1.0s (6 cases = 2 scenarios × 3 modes) |

## Notes

- Each case has an `autouse` fixture `_cleanup_global_spouts` that ensures `LogSpout` / `LifecycleSpout` are `stop()`-ed before and after the case, avoiding background thread leaks or persistence state cross-contamination.
- `_CtreeStub` starts with a default ID of 42, avoiding conflicts with the sqlite unique constraint; if you need `ctree_client` to start at 0, instantiate it yourself.
- Test fixtures are injected through the public API (`task_queue.put` / `result_queue.add_queue`), avoiding direct modification of `executor` internal state.
- `_RecordingLogInlet._log` is a no-op, avoiding dependency on the real spout queue.
- When using `monkeypatch.setattr` to replace `get_log_inlet`, you must cover both `celestialflow.node.core_node` and `celestialflow.node.core_dispatch` because both call it.
- The related implementation is at `src/celestialflow/node/core_dispatch.py` and `src/celestialflow/node/core_node.py`.
