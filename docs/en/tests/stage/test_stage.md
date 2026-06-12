# Task Stage Tests (test_stage.py)

> 📅 Last Updated: 2026/06/11

## Purpose
Validates the `TaskStage` class in `celestialflow.stage.core_stage`, ensuring node configuration, execution mode switching, and identity management meet the framework's design requirements.

## Core Test Target
- `TaskStage`: The basic logical unit within a task graph.

## Test Coverage Matrix

| Case | Coverage Goal |
|------|----------|
| `test_stage_name_identity` | `name` is the unique identifier |
| `test_stage_name_changes_with_name` | Identity updates synchronously after `set_name()` |
| `test_valid_stage_mode_serial` | `stage_mode="serial"` is valid |
| `test_valid_stage_mode_thread` | `stage_mode="thread"` is valid |
| `test_invalid_stage_mode` | Invalid `stage_mode` raises `StageModeError` |
| `test_valid_execution_mode_serial` | `execution_mode="serial"` is valid |
| `test_valid_execution_mode_thread` | `execution_mode="thread"` is valid |
| `test_valid_execution_mode_async` | `execution_mode="async"` is valid |
| `test_invalid_execution_mode` | Invalid `execution_mode` raises `ExecutionModeError` |
| `test_summary_contains_stage_mode` | `get_summary()` includes `stage_mode` and `execution_mode` |
| `test_lambda_allowed_in_thread` | Lambda functions are allowed in thread mode |

## Test Focus
- **Configuration rigor**: Ensures invalid mode combinations are caught at initialization.
- **Metadata synchronization**: Validates the stability of the Stage name as a graph reference key.
- **Mode semantics**: Distinguishes between the responsibilities of "Node Isolation Mode (Stage Mode)" and "Task Execution Mode (Execution Mode)".

## How to Run

```bash
# Run all
pytest tests/stage/test_stage.py -v

# Run identity management tests only
pytest tests/stage/test_stage.py -k "name" -v

# Run mode validation tests only
pytest tests/stage/test_stage.py -k "mode" -v

# Run Lambda support tests only
pytest tests/stage/test_stage.py -k "lambda" -v
```

## Performance Reference

| Test | Duration |
|------|------|
| `TestTaskStageConfig` | ~0.2s (pure config validation, no task execution) |

## Important Details
- `TaskStage` does not directly execute tasks; it orchestrates execution by configuring a `TaskExecutor` and managing a `Queue`.
- `test_lambda_allowed_in_thread` is an important validation of task function flexibility under thread-isolation mode.

## Notes
- Task stages are the building blocks of `TaskGraph`.
- Related implementation is in `src/celestialflow/stage/core_stage.py`.
