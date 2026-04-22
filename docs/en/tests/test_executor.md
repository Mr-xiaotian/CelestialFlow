# test_executor.py Test Documentation

> 📅 Last updated: 2026/04/22

## Test Purpose

Validates the core capabilities of `TaskExecutor` across three execution modes (`serial` / `thread` / `async`): task scheduling, result correctness, exception handling, retry mechanism, deduplication checks, success caching, and configuration validation. `TaskExecutor` is the most fundamental task execution unit in CelestialFlow, and its stability is the cornerstone of the entire framework.

## Test Scope

| Test Class | Cases | Coverage |
|------------|-------|----------|
| `TestExecutorSerial` | 4 | Serial mode basic functionality, error handling, retry, exception filtering |
| `TestExecutorThread` | 1 | Thread mode concurrency correctness |
| `TestExecutorAsync` | 2 | Async mode basic functionality, concurrent batch tasks |
| `TestExecutorDuplicateCheck` | 2 | Deduplication enabled/disabled |
| `TestExecutorSuccessCache` | 1 | Successful result caching |
| `TestExecutorConfig` | 2 | Invalid configuration interception, summary field completeness |

### Key Test Case Details

#### `test_serial_basic`
- **Purpose**: Verifies tasks execute sequentially in serial mode, with correct result dictionary and counter statistics.
- **Input**: `[1, 2, 3, 4, 5]`, function `add_one`
- **Assertions**: `result_dict[x] == x + 1`; `tasks_succeeded == 5`

#### `test_serial_with_errors`
- **Purpose**: Verifies that when some tasks fail, successful tasks continue executing and error information is correctly recorded.
- **Input**: `[1, -1, 2, -2, 3]`, function `raise_on_negative`
- **Assertions**: 3 successes, 2 failures; failure results contain exception text.

#### `test_serial_retry`
- **Purpose**: Verifies the retry mechanism works for configured exception types, and eventual success is not counted as failure.
- **Design**: `flaky` function raises `RuntimeError` on the first 2 calls, succeeds on the 3rd.
- **Assertions**: `call_count == 3` (1 initial + 2 retries); `tasks_failed == 0`

#### `test_serial_no_retry_for_unmatched_exception`
- **Purpose**: Verifies that unconfigured exception types do not trigger retry and are directly counted as failures.
- **Design**: Retry is configured for `RuntimeError`, but the function raises `ValueError`.

#### `test_duplicate_check_enabled`
- **Purpose**: With deduplication enabled, duplicate inputs are executed only once.
- **Input**: `[1, 1, 2, 2, 2, 3]`
- **Assertions**: `tasks_succeeded == 3`, `tasks_duplicated == 3`

## Dependencies

| Dependency | Description |
|------------|-------------|
| `pytest` | Test framework |
| `pytest-asyncio` | Async test support |
| `celestialflow.TaskExecutor` | Object under test |

## Potential Issues and Notes

### 1. Result Order in Thread Mode
`test_thread_basic` only verifies result correctness, **not execution order**. In multi-threaded environments, task completion order may differ from input order. If business logic depends on order, it should be handled explicitly in `process_result()`.

### 2. Event Loop Strategy for Async Tests
`pytest-asyncio` uses a `function`-scoped event loop by default. Running a large number of async tests simultaneously (>100) may exhaust event loop resources. The current 2 async test cases have no such risk.

### 3. Key Conflicts in `process_result_dict`
`process_result_dict()` uses the original task as a dictionary key. If the task is an unhashable type (such as `list` or `dict`), it will raise `TypeError`. Current tests use integers only, so this is not an issue.

**Recommendation**: In production, if tasks are unhashable objects, use a custom `process_result()` or `get_success_pairs()`.

### 4. Closure State During Retry
`test_serial_retry` uses `nonlocal call_count` to track invocation count. In `thread` mode, if `call_count` does not use a thread-safe mechanism (such as `threading.Lock`), it may cause count races. The current serial test has no such issue, but if `flaky` is used in `thread` mode, `Value` or `Lock` should be used instead.

### 5. Necessity of `show_progress=False`
All test cases explicitly set `show_progress=False`. If this parameter is omitted, `tqdm` may produce garbled output or block in CI/CD environments without a TTY.

### 6. Exception Type in Invalid Mode Test
`test_invalid_execution_mode` uses `pytest.raises(Exception)` rather than a precise exception type. Although the current implementation raises `ExecutionModeError`, the test is loosely written. Consider changing to:
```python
with pytest.raises(ExecutionModeError):
    ...
```

## How to Run

```bash
# Run all tests
pytest tests/test_executor.py -v

# Serial tests only
pytest tests/test_executor.py::TestExecutorSerial -v

# Async tests only
pytest tests/test_executor.py::TestExecutorAsync -v
```

## Performance Reference

On a typical development machine:
- Serial, 5 tasks: `< 10ms`
- Thread, 5 tasks: `< 20ms`
- Async, 20 tasks: `< 10ms`

## Related Files

- `src/celestialflow/stage/core_executor.py`: Implementation under test
- `src/celestialflow/runtime/core_dispatch.py`: Scheduling logic
- `tests/demo_executor.py`: TaskExecutor demo/integration test (no assertions)
