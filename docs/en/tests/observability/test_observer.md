# Observer Tests (test_observer.py)

> Last Updated: 2026/05/23

## Purpose
Validates the observer mechanism in `celestialflow.observability`, ensuring callbacks are triggered correctly at key points in the task-execution lifecycle.

## Key Test Objects
- `BaseObserver`: Base observer class.
- `CallbackObserver`: Observer implementation based on callback functions.
- `TaskExecutor`: The observed task executor.

## Key Test Flow
1. **Lifecycle callbacks**: Verifies the full event flow from `on_start` to `on_finish`, including task success, failure, and newly added tasks.
2. **Multiple observers**: Verifies that multiple observers can be attached to the same executor at the same time and receive events independently.
3. **Dynamic management**: Verifies adding and removing observers dynamically.
4. **Functional observation**: Verifies that `CallbackObserver` can implement focused monitoring logic through parameterized lambdas or functions.

## Test Focus
- **Event ordering**: Ensures `on_start` fires first and `on_finish` fires last.
- **Failure capture**: Verifies that `on_task_fail` is called correctly and counted accurately when a task raises an exception.
- **Default behavior**: Verifies that methods not overridden follow the no-op implementation in the base class without raising errors.

## Important Details
- Mock classes such as `RecordingObserver` and `CountObserver` are used to collect and validate events.
- `test_remove_observer` ensures that detached observers no longer produce side effects.

## How to Run

```bash
# Run all tests
pytest tests/observability/test_observer.py -v

# Run lifecycle callback tests only
pytest tests/observability/test_observer.py -k "lifecycle" -v

# Run dynamic management tests only (add / remove observer)
pytest tests/observability/test_observer.py -k "observer_remove" -v

# Run functional observer tests only
pytest tests/observability/test_observer.py -k "callback" -v
```

## Performance Reference

| Test | Duration |
|------|----------|
| `TestExecutorObserver` | ~2s (includes task execution) |

## Notes
- The observer pattern is the foundation for monitoring, logging, and progress reporting in the framework.
- The test code lives in `tests/observability/test_observer.py`.

