# tests/observability/test_observer.py

> 📅 Last Updated: 2026/09/09

## Purpose
Validates the callback contract between `BaseObserver` and `TaskExecutor` exported by the `celestialflow` package, ensuring that key points in the task execution lifecycle correctly trigger the override methods of `BaseObserver`.

## Core Test Objects
- `BaseObserver`: From `celestialflow.observability`, the observer base class providing callback hooks such as `on_start` / `on_task_success` / `on_task_fail` / `on_task_duplicate` / `on_tasks_added` / `on_finish`.
- `TaskExecutor`: From `celestialflow.node`, the observed task executor (in tests it is imported through the top-level `celestialflow` package).

## Test Coverage Matrix

| Test Class | Case | Coverage Target |
|--------|------|----------|
| `TestExecutorObserver` | `test_observer_lifecycle` | Full lifecycle callbacks: `on_start` appears, `on_task_success` callback count equals the task count (3), `on_finish` is the last to fire |
| `TestExecutorObserver` | `test_observer_with_errors` | Failure callbacks: out of 3 tasks, 2 succeed and 1 fails; success/failure counts are accurate |
| `TestExecutorObserver` | `test_no_observer_works` | Without an attached observer, the executor runs normally and counts are unaffected |
| `TestExecutorObserver` | `test_multiple_observers` | Multiple observers are attached simultaneously, and each independently receives the same callbacks |
| `TestExecutorObserver` | `test_remove_observer` | After `remove_observer()`, the unbound observer no longer receives any callbacks |

## Test Focus
- **Event ordering**: Ensures `on_start` fires first and `on_finish` fires last.
- **Failure capture**: Validates that `on_task_fail` is correctly called and the count is accurate when a task throws an exception.
- **Observer composition**: Validates multi-observer attachment and detachment (no side effects after removal).

## Important Details
- Uses mock classes such as `RecordingObserver`, `CountObserver`, and `Counter` to collect and verify events.
- `RecordingObserver` overrides `on_start` / `on_task_success` / `on_task_fail` / `on_task_duplicate` / `on_tasks_added` / `on_finish`, where `on_task_success` and `on_task_fail` explicitly declare a default `count=1` parameter.
- `CountObserver` only overrides `on_task_success` / `on_task_fail`, accumulating the `count` field for aggregate statistics.
- `test_remove_observer` calls `executor.remove_observer(observer)` to unbind, then runs again, asserting `observer.count == 0`.
- All cases use the `execution_mode="serial"` mode to facilitate sequential event assertions.

## How to Run

```bash
# Run all
pytest tests/observability/test_observer.py -v

# Run lifecycle callback tests only
pytest tests/observability/test_observer.py -k "lifecycle" -v

# Run dynamic management tests only (add/remove observer)
pytest tests/observability/test_observer.py -k "observer_remove" -v
```

## Performance Reference

| Test | Duration |
|------|------|
| `TestExecutorObserver` | ~2s (includes task execution) |

## Notes
- The Observer pattern is the foundation for the framework's monitoring, logging, and progress bar features.
- Test code is located at `tests/observability/test_observer.py`.
