# Task Executor Tests (test_executor.py)

> Last Updated: 2026/05/23

## Purpose
Validates the `TaskExecutor` class in `celestialflow.stage.core_executor`, ensuring it executes tasks correctly in different concurrency modes, handles errors, and supports advanced features such as retries and deduplication.

## Key Test Objects
- `TaskExecutor`: The low-level engine that executes one task's logic.

## Key Test Flow
1. **Mode verification**:
   - **Serial**: Sequential execution, verifying result mapping and counters.
   - **Thread**: Parallel execution, verifying task distribution under multithreading.
   - **Async**: Asynchronous execution, verifying coroutine handling in `start_async`.
2. **Retry mechanism**:
   - Verifies `max_retries`: retries happen only when exceptions match the configured `retry_exceptions`.
   - Verifies that a task is counted as success, not failure, when a retry eventually succeeds.
3. **Deduplication and cache**:
   - Verifies that when `enable_duplicate_check` is enabled, identical tasks are executed only once.
   - Verifies that `get_success_pairs()` returns correct input/output pairs for successful tasks.
4. **Error recording**: Verifies that failed-task error type, message, and stage name are recorded correctly in `get_error_pairs()`.

## Test Focus
- **Consistency across execution modes**: Ensures task counts and result collection stay consistent across all execution modes.
- **Retry precision**: Verifies that non-matching exceptions fail immediately, such as configuring retries for `RuntimeError` while raising `ValueError`.
- **Concurrency safety**: Verifies that thread-pool and async modes do not lose or race result collection.

## How to Run

```bash
# Run all tests
pytest tests/stage/test_executor.py -v

# Run Serial mode tests only
pytest tests/stage/test_executor.py -k "serial" -v

# Run Thread mode tests only
pytest tests/stage/test_executor.py -k "thread" -v

# Run Async mode tests only
pytest tests/stage/test_executor.py -k "async" -v

# Run retry tests only
pytest tests/stage/test_executor.py -k "retry" -v

# Run deduplication tests only
pytest tests/stage/test_executor.py -k "duplicate" -v
```

## Performance Reference

| Test | Duration |
|------|----------|
| `TestTaskExecutor` | ~3s (includes multithreaded and async execution) |

## Important Details
- The `flaky` helper simulates scenarios that require retries.
- `test_invalid_execution_mode` ensures unsupported modes fail at initialization time.

## Notes
- `TaskExecutor` is the core component inside `TaskStage` that performs actual function calls.
- Related implementation: `src/celestialflow/stage/core_executor.py`.

