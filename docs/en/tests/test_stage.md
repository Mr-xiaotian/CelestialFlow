# test_stage.py Test Documentation

## Test Purpose

Validates the configuration layer behavior of `TaskStage`, including: tag generation and invalidation mechanism, stage_mode / execution_mode legality validation, and pickle guard in process mode. These tests cover `TaskStage` as a graph node's metadata management layer, not its execution capabilities (which are covered in `test_executor.py`).

## Test Scope

| Test Class | Cases | Coverage |
|------------|-------|----------|
| `TestTaskStageConfig` | 8 | Tag generation, tag change, valid stage_mode values, valid execution_mode values, invalid value interception, summary fields |
| `TestTaskStagePickleGuard` | 2 | Lambda interception, regular function pass-through |

### Key Test Case Details

#### `test_stage_tag_auto_generation`
- **Purpose**: When no tag is specified, an auto-generated tag containing `name` and `func_name` is created.
- **Format**: `Stage[{func_name}]` or custom name.

#### `test_stage_tag_changes_with_name`
- **Purpose**: After modifying `stage_name`, the old tag should be invalidated and the new tag should reflect the new name.
- **Implementation**: `set_stage_name()` deletes the cached tag via `delattr(self, "_tag")`; the next `get_tag()` call recomputes it.
- **Risk**: In multiprocessing scenarios, if a child process has already serialized the old tag before the parent process modifies the name, tag inconsistency may occur.

#### `test_invalid_stage_mode`
- **Purpose**: Invalid `stage_mode` (not `"serial"` / `"process"`) should raise `StageModeError`.

#### `test_invalid_execution_mode`
- **Purpose**: Invalid `execution_mode` (not `"serial"` / `"thread"` / `"async"`) should raise `ExecutionModeError`.

#### `test_summary_contains_stage_mode`
- **Purpose**: The dictionary returned by `get_summary()` should contain `stage_mode` and `execution_mode` fields for monitoring dashboard display.
- **Note**: In non-serial mode, `execution_mode` appends the worker count, e.g., `"thread-20"`.

#### `test_unpickleable_lambda_raises`
- **Purpose**: In `stage_mode="process"`, lambda functions cannot be pickled and should be intercepted at construction time.
- **Exception**: `PickleError`
- **Significance**: Avoids discovering serialization failures at runtime, which would crash child processes.

## Dependencies

| Dependency | Description |
|------------|-------------|
| `pytest` | Test framework |
| `celestialflow.TaskStage` | Object under test |
| `celestialflow.runtime.util_errors` | `ExecutionModeError`, `StageModeError`, `PickleError` |

## Potential Issues and Notes

### 1. Thread Safety of `get_tag()`
`get_tag()` uses a `hasattr` + dynamic attribute setting pattern for lazy-loading cache:
```python
if hasattr(self, "_tag"):
    return str(self._tag)
self._tag = f"{self.get_name()}[{self.get_func_name()}]"
```

In multi-threaded environments, the following may occur:
- Thread A checks `hasattr` and gets `False`
- Thread B checks simultaneously and also gets `False`
- Both threads create `_tag`; although the results are identical, a race condition exists

**Recommendation**: If thread safety is needed in the future, consider using `@functools.cached_property` or computing the value in `__init__`.

### 2. Limitations of Pickle Check
`find_unpickleable(func)` checks at construction time whether the function can be pickled, but **does not check variables in closures**. For example:
```python
def make_func():
    huge_data = [0] * 1000000
    def func(x):
        return x + len(huge_data)
    return func

TaskStage(make_func(), stage_mode="process")  # Passes construction, fails at serialization
```

This scenario is not covered by current tests.

### 3. Combination of `stage_mode="process"` and `execution_mode="async"`
`TaskStage`'s `set_execution_mode()` only allows `"serial"` / `"thread"`, but `TaskExecutor` allows `"async"`. If `"async"` is set through inheritance or by bypassing validation, unpredictable behavior may occur in a `stage_mode="process"` multiprocessing context.

**Current protection**: `set_execution_mode()` raises `ExecutionModeError`, but direct attribute modification can still bypass it.

### 4. `PickleError` Test Only Triggers in `stage_mode="process"`
In `stage_mode="serial"`, no pickle check is performed since tasks execute within the same process. This means the following code will not raise an error:
```python
TaskStage(lambda x: x, stage_mode="serial")  # Passes
```

This is expected behavior, but users may mistakenly believe the framework completely prohibits lambdas.

### 5. `test_valid_execution_mode_thread` Does Not Verify `max_workers`
The test only verifies that `execution_mode` is set to `"thread"`, but does not verify whether the default `max_workers` value (20) takes effect, nor does it test interception of invalid values (such as 0 or -1).

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

All test cases are pure configuration validation with no process/thread startup; execution time `< 50ms`.

## Related Files

- `src/celestialflow/stage/core_stage.py`: Implementation under test
- `src/celestialflow/stage/core_executor.py`: Parent class `TaskExecutor`
- `src/celestialflow/utils/util_debug.py`: `find_unpickleable`
- `tests/test_graph.py`: Uses `TaskStage` in graph integration scenarios
