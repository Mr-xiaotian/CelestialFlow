# Task Stage Tests (test_stage.py)

> Last Updated: 2026/05/23

## Purpose
Validates the `TaskStage` class in `celestialflow.stage.core_stage`, ensuring node configuration, runtime mode switching, and identity management match the framework design.

## Key Test Objects
- `TaskStage`: The basic logical unit inside a task graph.

## Key Test Flow
1. **Identity management**: Verifies that the stage identifier is tied to `name` and updates together when `set_name` is called.
2. **Mode validation**:
   - **Stage Mode**: Verifies legal configuration for `serial` (sequential isolation) and `thread` (thread isolation).
   - **Execution Mode**: Verifies legal configuration for `serial`, `thread`, and `async`.
   - **Invalid values**: Verifies that invalid modes raise `StageModeError` or `ExecutionModeError`.
3. **Summary information**: Verifies that `get_summary()` includes important mode markers such as `thread-20` for a thread-pool size of 20.
4. **Lambda support**: Verifies that anonymous functions can be serialized / invoked correctly in `thread` isolation mode with help from the internal executor.

## Test Focus
- **Configuration strictness**: Ensures invalid mode combinations are rejected during initialization.
- **Metadata synchronization**: Verifies the stability of stage names as graph reference keys.
- **Mode semantics**: Distinguishes the roles of stage isolation mode and task execution mode.

## How to Run

```bash
# Run all tests
pytest tests/stage/test_stage.py -v

# Run identity tests only
pytest tests/stage/test_stage.py -k "name" -v

# Run mode-validation tests only
pytest tests/stage/test_stage.py -k "mode" -v

# Run lambda-support tests only
pytest tests/stage/test_stage.py -k "lambda" -v
```

## Performance Reference

| Test | Duration |
|------|----------|
| `TestTaskStage` | ~0.2s (pure configuration validation, no task execution) |

## Important Details
- `TaskStage` does not execute tasks directly. It organizes execution by configuring `TaskExecutor` and managing queues.
- `test_lambda_allowed_in_thread` is an important guard for function flexibility in thread isolation mode.

## Notes
- Task stages are the building blocks of `TaskGraph`.
- Related implementation: `src/celestialflow/stage/core_stage.py`.

