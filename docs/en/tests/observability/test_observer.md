# Observer Tests (test_observer.py)

> 📅 Last Updated: 2026/05/23

## Purpose
Validates the Observer mechanism in the `celestialflow.observability` module, ensuring callbacks are correctly triggered at key points in the task execution lifecycle.

## Core Test Targets
- `BaseObserver`: Observer base class.
- `CallbackObserver`: Observer implementation based on callback functions.
- `TaskExecutor`: The task executor being observed.

## Key Test Flow
1. **Lifecycle callbacks**: Validates the complete event flow from `on_start` to `on_finish`, including task success, failure, and new-task events.
2. **Multi-observer support**: Validates that multiple observers can be simultaneously attached to the same executor and receive events independently.
3. **Dynamic management**: Validates the logic for dynamically adding and removing observers.
4. **Functional observation**: Validates that `CallbackObserver` can implement specific monitoring logic via parameterized lambdas or functions.

## Test Focus
- **Event ordering**: Ensures `on_start` fires first and `on_finish` fires last.
- **Failure capture**: Validates that `on_task_fail` is correctly called and the count is accurate when a task throws an exception.
- **Default behavior**: Validates that non-overridden methods fall through to the base class's empty implementation without raising exceptions.

## Important Details
- Uses mock classes such as `RecordingObserver` and `CountObserver` to collect and verify events.
- `test_remove_observer` ensures that unbound observers no longer produce side effects.

## How to Run

```bash
# Run all
pytest tests/observability/test_observer.py -v

# Run lifecycle callback tests only
pytest tests/observability/test_observer.py -k "lifecycle" -v

# Run dynamic management tests only (add/remove observer)
pytest tests/observability/test_observer.py -k "observer_remove" -v

# Run functional observation tests only
pytest tests/observability/test_observer.py -k "callback" -v
```

## Performance Reference

| Test | Duration |
|------|------|
| `TestExecutorObserver` | ~2s (includes task execution) |

## Notes
- The Observer pattern is the foundation for the framework's monitoring, logging, and progress bar features.
- Test code is located at `tests/observability/test_observer.py`.
