# tests/runtime/test_types.py

> 📅 Last Updated: 2026/09/24

## Purpose
Verifies the value objects, context manager, optional-locking value wrapper, lifecycle status enum, and event constants in `celestialflow.runtime.util_types`, ensuring they are correctly used at runtime by the various nodes/queues.

## Core Test Objects
- `TerminationSignal`: The termination sentinel, carrying `id` and `source`.
- `TerminationIdPool`: The termination signal ID pool.
- `NoOpContext`: An empty context manager, usable to disable locking.
- `ValueWrapper`: A thread-safe counter wrapper that can build its own lock, reuse an external lock, or be passed a `NoOpContext` to disable locking.
- `StageStatus`: A lifecycle status `IntEnum`.
- `CTreeEvent`: A collection of event name constants.

## Test Coverage Matrix

| Test Class | Case Count | Coverage Goals |
|--------|--------|---------|
| `TestUtilTypes` | 23 | `TerminationSignal` default/custom/partial params; `TerminationIdPool` non-empty/empty/single-element; `NoOpContext` with statement / exception passthrough / direct enter, exit calls; `ValueWrapper` read/write / with lock / context manager / `get_lock` returns lock or `NoOpContext` / lock independence / negative value; `StageStatus` enum values / IntEnum behavior / member count; `CTreeEvent` task constants / termination constants / prefix format |

## Coverage Points
- Construction semantics of `TerminationSignal` / `TerminationIdPool`.
- Context manager behavior and exception passthrough of `NoOpContext`.
- Read/write semantics of `ValueWrapper` in the three modes: with lock, reusing a lock, and locking disabled.
- Enum values of `StageStatus` and `CTreeEvent`.

## Key Scenarios
- `TerminationSignal` defaults to `id == -1`, `source == "input"`; supports partial keyword construction with `_id`/`source`.
- `ValueWrapper.get_lock()` returns that lock when a `Lock` is passed; returns a real self-built lock when none is passed; returns that instance when a `NoOpContext` is explicitly passed (read/write without locking).
- Each self-built lock of a `ValueWrapper` is independent and not shared across instances.
- `StageStatus` is an `IntEnum`, comparable with integers, with 3 members.
- `CTreeEvent.TASK_RETRY_PREFIX` ends with a dot.

## How to Run

```bash
pytest tests/runtime/test_types.py -v
pytest tests/runtime/test_types.py -k "value_wrapper or noop" -v
pytest tests/runtime/test_types.py -k "termination" -v
```

## Notes
- The test code is located at `tests/runtime/test_types.py`, and the corresponding implementation is at `src/celestialflow/runtime/util_types.py`.
