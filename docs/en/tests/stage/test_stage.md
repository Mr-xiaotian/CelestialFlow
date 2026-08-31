# Task Stage Tests (test_stage.py)

> 📅 Last Updated: 2026/08/19

## Purpose
Validates the `TaskStage` class in `celestialflow.stage.core_stage`, ensuring node configuration, execution mode switching, and identity management meet the framework's design requirements.

## Core Test Target
- `TaskStage`: The basic logical unit within a task graph.

## Test Coverage Matrix

### `TestTaskStageConfig` — Node Configuration Validation (8 cases)

| Case | Coverage Goal |
|------|----------|
| `test_stage_name_identity` | `name` is the unique identifier |
| `test_stage_name_changes_with_name` | Identity updates synchronously after `set_name()` |
| `test_valid_execution_mode_serial` | `execution_mode="serial"` is valid |
| `test_valid_execution_mode_thread` | `execution_mode="thread"` is valid |
| `test_valid_execution_mode_async` | `execution_mode="async"` is valid |
| `test_invalid_execution_mode` | Invalid `execution_mode` raises `InvalidOptionError` |
| `test_summary_contains_execution_mode` | `get_summary()` includes `execution_mode` field |
| `test_prev_binding_survives_execution_mode_switch` | Predecessor binding keeps metrics synchronized after switching `execution_mode` |

### `TestTaskStageStartErrors` — Exception Group Collection (2 cases)

| Case | Coverage Goal |
|------|----------|
| `test_start_raises_exception_group_after_finish` | Synchronous `start` raises collected exceptions as a group after `finish` |
| `test_start_async_raises_exception_group_after_finish` | Async `start_async` raises exceptions as a group after `finish` |

## Test Focus
- **Configuration rigor**: Ensures that invalid execution modes are intercepted at initialization, and invalid modes raise `InvalidOptionError`.
- **Metadata synchronization**: Validates the stability of the Stage name as a graph reference key, and that predecessor binding remains synchronized after switching `execution_mode`.
- **Exception group collection**: Pre- and post- exceptions from the synchronous/async `start` lifecycle should be uniformly raised as `ExceptionGroup`.

## How to Run

```bash
# Run all
pytest tests/stage/test_stage.py -v

# Run identity management tests only
pytest tests/stage/test_stage.py -k "name" -v

# Run execution mode validation tests only
pytest tests/stage/test_stage.py -k "mode" -v
```

## Performance Reference

| Test | Duration |
|------|----------|
| `TestTaskStageConfig` | ~0.2s (pure config validation, no task execution) |
| `TestTaskStageStartErrors` | ~0.3s (includes monkeypatch exception injection) |

## Important Details
- `TaskStage` does not directly execute tasks; it orchestrates execution by configuring a `TaskExecutor` and managing a `Queue`.
- `TestTaskStageStartErrors` uses monkeypatch to inject exceptions into `_prepare_start` and `_finish_start` to verify the exception group collection mechanism.

## Notes
- Task stages are the building blocks of `TaskGraph`.
- Related implementation is in `src/celestialflow/stage/core_stage.py`.
