# Runtime Type Tests (test_types.py)

> 📅 Last Updated: 2026/07/16

## Purpose
Verifies the value objects, enums, and wrappers in `celestialflow.runtime.util_types`, including termination signals, no-op contexts, optional-locking value wrappers, sum counters, and task event constants.

## Test Coverage Matrix

| Test Class | Case Count | Coverage Goals |
|--------|--------|---------|
| `TestUtilTypes` | 28 | `TerminationSignal` default / custom / partial param construction; `TerminationIdPool` non-empty / empty / single-element construction; `NoOpContext` with statement / exception passthrough / direct enter/exit calls; `ValueWrapper` basic read/write / locked read/write / context manager / `get_lock` returns lock or NoOpContext / negative value boundary; `SumCounter` accumulation / initial value / reset to zero / empty counter / multiple add; `StageStatus` enum values / IntEnum behavior / member count; `CTreeEvent` task constants / termination constants / prefix format |

## Coverage Points
- Construction semantics of `TerminationSignal` / `TerminationIdPool`.
- Context manager behavior and exception passthrough of `NoOpContext`.
- Read/write semantics of `ValueWrapper` in both locked and unlocked modes.
- Accumulation and reset behavior of `SumCounter`.
- Enum values of `StageStatus`, `CTreeEvent`.

## Key Scenarios
- `ValueWrapper.get_lock()` returns a real lock or `NoOpContext` depending on the construction mode.
- `SumCounter.reset()` zeros out both the initial value and sub-counters.

## How to Run

```bash
pytest tests/runtime/test_types.py -v
pytest tests/runtime/test_types.py -k "value_wrapper or sum_counter" -v
pytest tests/runtime/test_types.py -k "termination" -v
```
