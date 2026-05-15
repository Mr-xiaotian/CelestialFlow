# test_stage.py Test Documentation

> 📅 Last Updated: 2026/05/15

## Test Objective

Validates the configuration-layer behavior of `TaskStage`, including: tag generation and invalidation mechanisms, stage_mode / execution_mode legality validation. These tests cover `TaskStage`'s metadata management layer as a graph node, rather than its execution capabilities (which are covered in `test_executor.py`).

## Test Scope

| Test Class | Test Count | Coverage |
|------------|-----------|----------|
| `TestTaskStageConfig` | 9 | Tag generation, tag change, stage_mode valid values, execution_mode valid values, illegal value interception, summary fields, lambda thread mode |

### Key Test Case Details

#### `test_stage_tag_auto_generation`
- **Objective**: When no tag is specified, an auto-generated tag containing `name` and `func_name` is produced.
- **Format**: `Stage[{func_name}]` or custom name.

#### `test_stage_tag_changes_with_name`
- **Objective**: After modifying `name`, the old tag should be invalidated and the new tag should reflect the new name.
- **Implementation mechanism**: `set_name()` uses `delattr(self, "_tag")` to delete the cached tag; the next `get_tag()` call recomputes it.
- **Risk point**: In multi-threaded scenarios, if other threads have cached the old tag before the main thread modifies the name, tag inconsistency may occur.

#### `test_invalid_stage_mode`
- **Objective**: Illegal `stage_mode` (not `"serial"` / `"thread"`) should raise `StageModeError`.

#### `test_invalid_execution_mode`
- **Objective**: Illegal `execution_mode` (not `"serial"` / `"thread"` / `"async"`) should raise `ExecutionModeError`.

#### `test_summary_contains_stage_mode`
- **Objective**: The dictionary returned by `get_summary()` should contain `stage_mode` and `execution_mode` fields for monitoring dashboard display.
- **Note**: `execution_mode` in non-serial mode appends the worker count, e.g., `"thread-20"`.

#### `test_lambda_allowed_in_thread`
- **Objective**: Validate that lambda functions can be created normally under `stage_mode="thread"` (not rejected due to pickle limitations).
- **Assertions**: `get_stage_mode()` returns `"thread"`.

## Dependencies

| Dependency | Description |
|------------|-------------|
| `pytest` | Test framework |
| `celestialflow.TaskStage` | Object under test |
| `celestialflow.runtime.util_errors` | `ExecutionModeError`, `StageModeError` |

## Potential Issues and Notes

### 1. Thread Safety of `get_tag()`
`get_tag()` implements lazy-loading caching via the `hasattr` + dynamic attribute setting pattern:
```python
if hasattr(self, "_tag"):
    return str(self._tag)
self._tag = f"{self.get_name()}[{self.get_func_name()}]"
```

In a multi-threaded environment, the following may occur:
- Thread A checks `hasattr` and gets `False`
- Thread B simultaneously checks and also gets `False`
- Both threads create `_tag`; although the result is the same, a race condition exists

**Recommendation**: If thread safety is needed in the future, switch to `@functools.cached_property` or solidify in `__init__`.

### 2. `test_valid_execution_mode_thread` Does Not Verify `max_workers`
The test only verifies that `execution_mode` is set to `"thread"`, but does not verify whether the default `max_workers` value (20) takes effect, nor does it test illegal values (e.g., 0, -1).

**Suggested addition**:
```python
def test_invalid_max_workers():
    with pytest.raises(ValueError):
        TaskStage(add_one, execution_mode="thread", max_workers=0)
```

## How to Run

```bash
pytest tests/test_stage.py -v
```

All test cases are pure configuration validation with no thread startup, execution time `< 50ms`.

## Related Files

- `src/celestialflow/stage/core_stage.py`: Implementation under test
- `src/celestialflow/stage/core_executor.py`: Parent class `TaskExecutor`
- `src/celestialflow/utils/util_debug.py`: `find_unpickleable`
- `tests/test_graph.py`: Uses `TaskStage` in graph integration scenarios
