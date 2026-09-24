# tests/observability/test_observer.py

> 📅 Last Updated: 2026/09/24

## Purpose

Validates the callback contract between the `BaseObserver` and built-in `PrintObserver` exported by the `celestialflow` package and `TaskExecutor`, ensuring that key points in the task execution lifecycle correctly trigger the observer's override methods, and that `PrintObserver` prefixes its output with the node name.

## Core Test Objects

- `BaseObserver`: From `celestialflow.observability`, the observer base class providing callback hooks such as `on_start` / `on_task_success` / `on_task_fail` / `on_task_duplicate` / `on_task_added` / `on_finish`.
- `PrintObserver`: From `celestialflow.observability`, a built-in observer whose constructor argument is `name`; it outputs logs such as `[<name>] start` / `[<name>] finish` and maintains `total` / `succeeded` / `failed` counts.
- `TaskExecutor`: From `celestialflow.node`, the observed task executor (in tests it is imported through the top-level `celestialflow` package).

## Test Coverage Matrix

| Test Class | Case | Coverage Target |
|--------|------|----------|
| `TestExecutorObserver` | `test_observer_lifecycle` | Full lifecycle callbacks: `on_start` appears, `on_task_success` callback count equals the task count (3), `on_finish` is the last to fire, `on_task_added` accumulates to 3 |
| `TestExecutorObserver` | `test_print_observer` | `PrintObserver("PrintObserverTest")` outputs `start` / `finish` with the `[PrintObserverTest]` prefix, `total=3` / `succeeded=2` / `failed=1` |
| `TestExecutorObserver` | `test_observer_with_errors` | Failure callbacks: out of 3 tasks, 2 succeed and 1 fails; success/failure counts are accurate |
| `TestExecutorObserver` | `test_no_observer_works` | Without an attached observer, the executor runs normally and counts are unaffected |
| `TestExecutorObserver` | `test_multiple_observers` | Multiple observers are attached simultaneously, and each independently receives the same callbacks |
| `TestExecutorObserver` | `test_remove_observer` | After `remove_observer()` unbinds an observer, it no longer receives any callbacks |

## Test Focus
- **Event ordering**: Ensures `on_start` fires first and `on_finish` fires last.
- **Failure capture**: Validates that `on_task_fail` is correctly called and the count is accurate when a task throws an exception.
- **Built-in observer**: Validates `PrintObserver`'s `name`-prefixed output and accumulated counts.
- **Observer composition**: Validates multi-observer attachment and detachment (no side effects after removal).

## Important Details
- Uses mock classes such as `RecordingObserver`, `CountObserver`, and `Counter` to collect and verify events.
- `RecordingObserver` overrides `on_start` / `on_task_success` / `on_task_fail` / `on_task_duplicate` / `on_task_added` / `on_finish`, where `on_task_success` and `on_task_fail` explicitly declare a default `count=1` parameter.
- `test_print_observer` captures standard output via `redirect_stdout(io.StringIO())`, asserts that the output contains `[PrintObserverTest] start` / `[PrintObserverTest] finish`, and reads the observer's `total` / `succeeded` / `failed` counters.
- `CountObserver` only overrides `on_task_success` / `on_task_fail`, accumulating the `count` field for aggregate statistics.
- `test_remove_observer` calls `executor.remove_observer(observer)` to unbind, then runs again, asserting `observer.count == 0`.
- All cases use the `execution_mode="serial"` mode to facilitate sequential event assertions.

## How to Run

```bash
# Run all
pytest tests/observability/test_observer.py -v

# Run lifecycle callback tests only
pytest tests/observability/test_observer.py -k "lifecycle" -v

# Run PrintObserver tests only
pytest tests/observability/test_observer.py -k "print_observer" -v

# Run dynamic management tests only (add/remove observer)
pytest tests/observability/test_observer.py -k "observer" -v
```

## Performance Reference

| Test | Duration |
|------|------|
| `TestExecutorObserver` | ~2s (includes task execution) |

## Notes
- The Observer pattern is the foundation for the framework's monitoring, logging, and progress bar features.
- `PrintObserver.__init__(name)` requires a node name to prefix all output with `[name]`, avoiding confusion between multiple nodes' logs.
- Test code is located at `tests/observability/test_observer.py`.
