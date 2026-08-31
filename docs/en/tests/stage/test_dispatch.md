# Task Dispatch Core Tests (test_dispatch.py)

> 📅 Last Updated: 2026/08/26

## Purpose

Verifies the core behavior of `celestialflow.stage.core_dispatch.TaskDispatch` across three scheduling modes — `serial`, `thread`, and `async`: task execution, exception retry, duplicate deduplication, termination signal handling, and worker crash fallback.

## Core Test Object

- `TaskDispatch`: Responsible for pulling `TaskEnvelope` items from the task queue, dispatching them to workers in the specified mode, and writing results to the result queue.

## Test Coverage Matrix

| Test Class | Case Count | Coverage Goals |
|------------|------------|----------------|
| `TestDispatchSerial` | 7 | Single/multi task, retry success, retry exhaustion, termination signal single/multi ID, success fanout with independent task IDs per downstream node |
| `TestDispatchThread` | 2 | 10-task concurrency, duplicate task dedup count |
| `TestDispatchAsync` | 2 | 10-task coroutine concurrency, async retry success |
| `TestWorkerCrashKeepsTerminationSignal` | 2 | Failure handling chain crash and retry envelope generation crash both still emit the termination signal (parameterized over 3 modes) |
| `TestDispatchCoreBehavior` | 2 | Empty queue + termination signal (parameterized over 3 modes), 5-task result count (parameterized over 3 modes) |
| **Total** | **15** | |

## Key Test Scenarios

### `TestDispatchSerial` — Serial Dispatch
- Single task / multi-task sequential execution
- Retry success (first N calls raise, final call succeeds)
- Retry exhaustion (always raises, ultimately no successful result)
- Termination signal merging (single ID / multi ID)
- success fanout creates independent task IDs for each real downstream node (`get_id()` returns distinct values)

### `TestDispatchThread` — Thread Dispatch
- 10-task concurrency (4 workers), verifies correct result collection
- Duplicate task dedup (same task submitted twice, `metrics.get_duplicate_count()` is 1, and at least one execution result is preserved in the result)

### `TestDispatchAsync` — Async Dispatch
- 10-task coroutine concurrency (4 workers)
- Async retry success (returns correct value after 3 calls)

### `TestWorkerCrashKeepsTerminationSignal` — Worker Crash Fallback (Regression Test)
- Failure handling chain crash (observer raises): the exception is captured by `observer_error`, the termination signal is still emitted, and `worker_crash` is not triggered
- Retry envelope generation crash (logging raises): scheduling is not interrupted, the termination signal is still emitted, and `worker_crash` records the exception
- Both scenarios are parameterized to run under `serial` / `thread` / `async` modes

### `TestDispatchCoreBehavior` — Cross-Mode Parameterized
- Empty queue + termination signal: all three modes exit correctly
- 5-task result count: all three modes produce 5 results + a termination signal

## How to Run

```bash
# Run all
pytest tests/stage/test_dispatch.py -v

# Serial dispatch tests only
pytest tests/stage/test_dispatch.py -k "Serial" -v

# Thread dispatch tests only
pytest tests/stage/test_dispatch.py -k "Thread" -v

# Async dispatch tests only
pytest tests/stage/test_dispatch.py -k "Async" -v

# Worker crash fallback tests only
pytest tests/stage/test_dispatch.py -k "Crash" -v

# Cross-mode parameterized tests only
pytest tests/stage/test_dispatch.py -k "CoreBehavior" -v
```

## Performance Reference

| Test Class | Duration |
|------------|----------|
| `TestDispatchSerial` | ~0.1s |
| `TestDispatchThread` | ~0.2s |
| `TestDispatchAsync` | ~0.2s |
| `TestWorkerCrashKeepsTerminationSignal` | ~0.3s |
| `TestDispatchCoreBehavior` | ~0.3s |

## Important Details

- Tests use `TaskEnvelope` to wrap tasks and inject them into the queue via `_put` and `_put_termination` helper functions.
- Termination signals are injected via the public API `task_queue.put(TerminationSignal(...))` rather than directly manipulating the internal `TerminationIdPool`.
- Async tests use `asyncio.run()` to create an independent event loop, avoiding conflicts with existing loops.
- `_make_executor` registers a result-collection queue for tests via the public `result_queue.add_queue()` API, avoiding injecting test-specific attributes into the executor.
- `TestWorkerCrashKeepsTerminationSignal` uses `_CrashOnFailObserver` and `_CrashRetryLogInlet` to simulate handling-chain crashes and verify the termination-signal fallback mechanism.

## Notes

- The dispatcher is the low-level execution engine for `TaskExecutor` and `TaskStage`; its correctness directly affects task execution across the entire framework.
- The related implementation is located at `src/celestialflow/stage/core_dispatch.py`.
