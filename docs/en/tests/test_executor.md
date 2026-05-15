# test_executor.py Test Documentation

> 📅 Last Updated: 2026/05/08

## Test Objective

Validates the core capabilities of `TaskExecutor` across three execution modes (`serial` / `thread` / `async`): task scheduling, result correctness, exception handling, retry mechanisms, deduplication checking, success caching, configuration validation, and Observer callbacks. `TaskExecutor` is the most fundamental task execution unit in CelestialFlow; its stability is the foundation of the entire framework.

## Test Scope

| Test Class | Test Count | Coverage |
|------------|-----------|----------|
| `TestExecutorSerial` | 4 | Serial mode basic functionality, error handling, retry, exception filtering |
| `TestExecutorThread` | 1 | Thread mode concurrency correctness |
| `TestExecutorAsync` | 2 | Async mode basic functionality, concurrent batch tasks |
| `TestExecutorDuplicateCheck` | 2 | Deduplication enabled/disabled |
| `TestExecutorSuccessCache` | 1 | Success result caching |
| `TestExecutorConfig` | 2 | Illegal configuration interception, summary field completeness |
| `TestExecutorObserver` | 7 | Lifecycle callbacks, error callbacks, no observer, multiple observers, observer removal, CallbackObserver, partial callbacks |

### Key Test Case Details

#### `test_serial_basic`
- **Objective**: Validate that tasks execute sequentially in serial mode with correct result dictionary and counter statistics.
- **Input**: `[1, 2, 3, 4, 5]`, function `add_one`
- **Assertions**: `result_dict[x] == x + 1`; `tasks_succeeded == 5`

#### `test_serial_with_errors`
- **Objective**: Validate that when some tasks fail, successful tasks continue executing and error information is correctly recorded.
- **Input**: `[1, -1, 2, -2, 3]`, function `raise_on_negative`
- **Assertions**: 3 succeeded, 2 failed; failure results contain exception text.

#### `test_serial_retry`
- **Objective**: Validate that the retry mechanism works for configured exception types, and ultimately successful tasks are not counted as failures.
- **Design**: `flaky` function throws `RuntimeError` on the first 2 calls, succeeds on the 3rd.
- **Assertions**: `call_count == 3` (1 initial + 2 retries); `tasks_failed == 0`

#### `test_observer_lifecycle`
- **Objective**: Validate that observers receive complete lifecycle callbacks during execution (start -> success x N -> finish).
- **Design**: `RecordingObserver` records all events; verifies event types and order.

#### `test_callback_observer`
- **Objective**: Validate that `CallbackObserver` receives events through callback functions.
- **Design**: Passes `on_task_success` and `on_finish` callbacks; verifies call counts.

#### `test_multiple_observers`
- **Objective**: Validate that multiple observers simultaneously receive callbacks.

#### `test_remove_observer`
- **Objective**: Validate that a removed observer no longer receives callbacks.

## Dependencies

| Dependency | Description |
|------------|-------------|
| `pytest` | Test framework |
| `pytest-asyncio` | Async test support |
| `celestialflow.TaskExecutor` | Object under test |
| `celestialflow.BaseObserver` | Observer base class |
| `celestialflow.CallbackObserver` | Callback-based Observer |

## How to Run

```bash
# Run all tests
pytest tests/test_executor.py -v

# Serial tests only
pytest tests/test_executor.py::TestExecutorSerial -v

# Observer tests only
pytest tests/test_executor.py::TestExecutorObserver -v
```

## Related Files

- `src/celestialflow/stage/core_executor.py`: Implementation under test
- `src/celestialflow/runtime/core_dispatch.py`: Scheduling logic
- `src/celestialflow/observability/core_observer.py`: Observer base class
- `demo/demo_executor.py`: TaskExecutor demo script
