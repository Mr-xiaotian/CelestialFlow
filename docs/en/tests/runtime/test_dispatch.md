# Task Dispatch Core Tests (test_dispatch.py)

> 📅 Last Updated: 2026/05/28

## Purpose

Validates the core behavior of `celestialflow.runtime.core_dispatch.TaskDispatch` across three scheduling modes (`serial`, `thread`, `async`): task execution, exception retry, duplicate deduplication, and termination signal handling.

## Core Test Target

- `TaskDispatch`: Responsible for pulling `TaskEnvelope` from the task queue, dispatching them to workers in the specified mode, and writing results to the result queue.

## Key Test Scenarios

### `TestDispatchSerial` — Serial Scheduling
- Single task / multi-task sequential execution
- Retry success (first N attempts throw, last succeeds)
- Retry exhaustion (always throws, no success result)
- Termination signal merging (single ID / multiple IDs)

### `TestDispatchThread` — Thread Scheduling
- 10 tasks concurrent (4 workers), verifying correct result collection
- Duplicate task deduplication (same hash submitted twice, executed only once)

### `TestDispatchAsync` — Async Scheduling
- 10 tasks coroutine concurrent (4 workers)
- Async retry success (returns correct value after 3 attempts)

### `TestDispatchCoreBehavior` — Cross-mode Parameterized
- Empty queue + termination signal: all three modes exit correctly
- 5 task result count: all three modes output 5 results + termination signal

## How to Run

```bash
# Run all
pytest tests/runtime/test_dispatch.py -v

# Serial scheduling tests only
pytest tests/runtime/test_dispatch.py -k "Serial" -v

# Thread scheduling tests only
pytest tests/runtime/test_dispatch.py -k "Thread" -v

# Async scheduling tests only
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

## Key Details

- Tests use `TaskEnvelope` to wrap tasks, injected into queues via `_put` and `_put_termination` helper functions.
- Termination signals are injected via the public API `task_queue.put(TerminationSignal(...))` rather than directly manipulating the internal `TerminationIdPool`.
- Async tests use `asyncio.run()` to create an independent event loop, avoiding conflicts with existing loops.

## Notes

- The dispatcher is the underlying execution engine for `TaskExecutor` and `TaskStage`; its correctness directly impacts the entire framework's task execution.
- Related implementation is in `src/celestialflow/runtime/core_dispatch.py`.
