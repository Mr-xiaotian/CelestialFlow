# Task Executor Tests (test_executor.py)

> 📅 Last Updated: 2026/06/22

## Purpose
Validates the `TaskExecutor` class in `celestialflow.stage.core_executor`, ensuring accurate task execution, error handling, and support for advanced features (such as retry and deduplication) across various concurrency modes.

## Core Test Target
- `TaskExecutor`: The low-level engine that executes individual task logic.

## Test Coverage Matrix

| Test Class | Case Count | Coverage Goal |
|--------|--------|---------|
| `TestExecutorSerial` | 4 | Serial execution, error handling, retry success, non-matching exceptions not retried |
| `TestExecutorThread` | 1 | Thread-pool parallel execution with correct counting |
| `TestExecutorAsync` | 2 | Async execution and continuous processing logic |
| `TestExecutorDuplicateCheck` | 3 | Behavioral comparison among default disabled, enabled, and explicitly disabled configurations |
| `TestExecutorReplay` | 1 | `start_db` reads failed tasks from sqlite by stage and replays them |
| `TestExecutorSuccessCache` | 1 | Success result caching and `get_success_pairs()` |
| `TestExecutorConfig` | 4 | Zero/multi-parameter function rejection, invalid execution mode validation, `get_summary()` metadata |

## Key Test Scenarios

### Execution Modes
- **Serial**: Sequential execution; verifies result mapping and counting.
- **Thread**: Parallel execution; verifies task distribution under multi-threading (`execution_mode="thread"`).
- **Async**: Async execution; verifies coroutine handling for `start_async` (`execution_mode="async"`).

### Retry Mechanism
- Validates `max_retries` logic: retry is triggered only when the specified `retry_exceptions` are thrown.
- Validates that after a successful retry the final count is marked as success rather than failure.
- Validates that non-matching exceptions (e.g., configuring retry for `RuntimeError` but throwing `ValueError`) immediately trigger failure.

### Deduplication & Caching
- Validates that the default configuration (without specifying `enable_duplicate_check`) does not enable duplicate checking, so identical tasks are executed repeatedly.
- Validates that when `enable_duplicate_check` is on, identical tasks execute only once and duplicates are counted under `tasks_duplicated`.
- Validates that when `enable_duplicate_check` is explicitly off, identical tasks all execute and `tasks_duplicated` is 0.
- Validates that `get_success_pairs()` correctly returns input-output pairs for successfully completed tasks.

### Configuration Validation
- Validates that an invalid `execution_mode` raises `ExecutionModeError` at initialization.
- Validates that `get_summary()` returns key fields such as `name`, `func_name`, and `execution_mode`.

## Test Focus
- **Execution mode consistency**: Ensures that regardless of the execution mode used, the final task counting and result collection logic remains consistent.
- **Retry precision**: Validates that non-matching exceptions immediately trigger failure.
- **Concurrency safety**: Validates that result collection under thread-pool and async modes does not suffer from races or loss.

## How to Run

```bash
# Run all
pytest tests/stage/test_executor.py -v

# Run Serial mode tests only
pytest tests/stage/test_executor.py -k "serial" -v

# Run Thread mode tests only
pytest tests/stage/test_executor.py -k "thread" -v

# Run Async mode tests only
pytest tests/stage/test_executor.py -k "async" -v

# Run retry mechanism tests only
pytest tests/stage/test_executor.py -k "retry" -v

# Run deduplication tests only
pytest tests/stage/test_executor.py -k "duplicate" -v
```

## Performance Reference

| Test Class | Duration |
|------|------|
| `TestExecutorSerial` | ~1s |
| `TestExecutorThread` | ~1s |
| `TestExecutorAsync` | ~2s |
| `TestExecutorDuplicateCheck` / `TestExecutorSuccessCache` / `TestExecutorConfig` | < 0.5s |

## Important Details
- Uses a `flaky` closure to simulate scenarios requiring retry.
- `test_invalid_execution_mode` ensures unsupported modes are rejected at initialization.

## Notes
- `TaskExecutor` is the core component of `TaskStage`, responsible for the actual function call logic.
- Related implementation is in `src/celestialflow/stage/core_executor.py`.
