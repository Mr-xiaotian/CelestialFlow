# Runtime Type Tests (test_types.py)

> 📅 Last Updated: 2026/05/28

## Purpose

Validates the correctness of all runtime helper types in `celestialflow.runtime.util_types`, including termination signals, counters, context managers, event constants, and error records.

## Core Test Targets

| Type | Description |
|------|-------------|
| `TerminationSignal` | Termination signal carrying `id` and `source` |
| `TerminationIdPool` | Multi-termination-signal ID pool for merge propagation |
| `NoOpContext` | No-op context manager, placeholder implementation for lock-free scenarios |
| `ValueWrapper` | Locked value wrapper supporting thread-safe read/write |
| `SumCounter` | Multi-counter aggregation accumulator with `init_value` and reset |
| `StageStatus` | Stage lifecycle enum (NOT_STARTED / RUNNING / STOPPED) |
| `CTreeEvent` | CTree event name constants |
| `PersistedErrorRecord` | Persisted error record (frozen dataclass) |

## Key Test Scenarios

### `TerminationSignal`
- Default construction: `id=-1`, `source="input"`
- Custom arguments: `_id=42`, `source="queue"`
- Partial argument skipping

### `TerminationIdPool`
- Non-empty list, empty list, single-element list construction

### `NoOpContext`
- `with` statement enters and exits normally, variable state preserved
- Exceptions are not suppressed (`__exit__` returns `None`)
- Direct calls to `__enter__` / `__exit__`

### `ValueWrapper`
- Basic read/write: `value` property works correctly
- Default value is 0
- Locked read/write behavior is consistent
- `get_lock()` returns the provided `Lock` or `NoOpContext`
- Negative value boundary

### `SumCounter`
- Single counter / multi-counter accumulation
- `init_value` affects the total
- `reset()` zeroes all counters (including `init_value`)
- Empty counter: `value=0`
- `thread` mode accumulation works correctly

### `StageStatus`
- Enum values are correct (0 / 1 / 2)
- `IntEnum` comparable to integers
- Member count is 3

### `CTreeEvent`
- Task constants are correct (`task.input`, `task.success`, `task.error`, `task.duplicate`)
- Termination constants are correct (`termination.input`, `termination.merge`)
- Retry prefix ends with `"."`

### `PersistedErrorRecord`
- Basic / full-field construction
- Frozen dataclass — cannot be modified
- `__str__` returns `error_repr`
- `get_group_key()` returns `(error_type, error_message)` tuple

## How to Run

```bash
# Run all
pytest tests/utils/test_types.py -v

# Termination signal tests only
pytest tests/utils/test_types.py -k "termination" -v

# Counter tests only
pytest tests/utils/test_types.py -k "counter or Sum or Value" -v

# Enum and event tests only
pytest tests/utils/test_types.py -k "status or event or Stage or CTree" -v

# Error record tests only
pytest tests/utils/test_types.py -k "error" -v
```

## Performance Reference

| Test Class | Duration |
|------------|----------|
| `TestUtilTypes` | ~0.1s |

## Key Details

- `NoOpContext` is a Null Object pattern implementation, providing a unified interface for `ValueWrapper.get_lock()` in lock-free scenarios.
- `ValueWrapper`'s `get_lock()` returns a context manager (`Lock` or `NoOpContext`); callers uniformly use the `with` statement.
- `PersistedErrorRecord` is a frozen dataclass, ensuring error records cannot be tampered with after persistence.
- `StageStatus` is an `IntEnum` and can be directly compared to integers (e.g., `status > StageStatus.NOT_STARTED`).

## Notes

- These types are widely used by the framework's core code; their correctness directly impacts critical paths such as scheduling, deduplication, and reporting.
- Related implementation is in `src/celestialflow/runtime/util_types.py`.
