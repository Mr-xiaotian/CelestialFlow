# Task Dispatch Core Tests (test_dispatch.py)

> 📅 Last Updated: 2026/06/11

## Purpose

Verifies the core behavior of `celestialflow.runtime.core_dispatch.TaskDispatch` across three scheduling modes — `serial`, `thread`, and `async`: task execution, exception retry, duplicate deduplication, and termination signal handling.

## Core Test Object

- `TaskDispatch`: Responsible for pulling `TaskEnvelope` items from the task queue, dispatching them to workers in the specified mode, and writing results to the result queue.

## Test Coverage Matrix

| Test Class | Case Count | Coverage Goals |
|------------|------------|----------------|
| `TestDispatchSerial` | 6 | Single/multi task, retry success, retry exhaustion, termination signal single/multi ID |
| `TestDispatchThread` | 2 | 10-task concurrency, duplicate task dedup count |
| `TestDispatchAsync` | 2 | 10-task coroutine concurrency, async retry success |
| `TestDispatchCoreBehavior` | 2 | Empty queue + termination signal (3-mode parameterized), 5-task result count (3-mode parameterized) |
| **Total** | **12** | |

## Key Test Scenarios

### `TestDispatchSerial` — Serial Dispatch
- Single task / multi-task sequential execution
- Retry success (first N calls raise, final call succeeds)
- Retry exhaustion (always raises, ultimately no successful result)
- Termination signal merging (single ID / multi ID)

### `TestDispatchThread` — Thread Dispatch
- 10-task concurrency (4 workers), verifies correct result collection
- Duplicate task dedup (same hash submitted twice, executed only once, `duplicate_count` equals 1)

### `TestDispatchAsync` — Async Dispatch
- 10-task coroutine concurrency (4 workers)
- Async retry success (returns correct value after 3 calls)

### `TestDispatchCoreBehavior` — Cross-Mode Parameterized
- Empty queue + termination signal: all three modes exit correctly
- 5-task result count: all three modes produce 5 results + termination signal

## How to Run

```bash
# Run all
pytest tests/runtime/test_dispatch.py -v

# Serial dispatch tests only
pytest tests/runtime/test_dispatch.py -k "Serial" -v

# Thread dispatch tests only
pytest tests/runtime/test_dispatch.py -k "Thread" -v

# Async dispatch tests only
pytest tests/runtime/test_dispatch.py -k "Async" -v

# Cross-mode parameterized tests only
pytest tests/runtime/test_dispatch.py -k "CoreBehavior" -v
```

## Performance Reference

| Test Class | Duration |
|------------|----------|
| `TestDispatchSerial` | ~0.1s |
| `TestDispatchThread` | ~0.2s |
| `TestDispatchAsync` | ~0.2s |
| `TestDispatchCoreBehavior` | ~0.3s |

## Important Details

- Tests use `TaskEnvelope` to wrap tasks and inject them into the queue via `_put` and `_put_termination` helper functions.
- Termination signals are injected via the public API `task_queue.put(TerminationSignal(...))` rather than directly manipulating the internal `TerminationIdPool`.
- Async tests use `asyncio.run()` to create an independent event loop, avoiding conflicts with existing loops.
- `_make_executor` registers a result-collection queue for tests via the public `result_queue.add_queue()` API, avoiding injecting test-specific attributes into the executor.

## Notes

- The dispatcher is the low-level execution engine for `TaskExecutor` and `TaskStage`; its correctness directly affects task execution across the entire framework.
- The related implementation is located at `src/celestialflow/runtime/core_dispatch.py`.
