# Runtime Type Tests (test_types.py)

> 📅 Last Updated: 2026/06/22

## Purpose
Verifies the value objects, enums, and wrappers in `celestialflow.runtime.util_types`, including termination signals, no-op contexts, optional-locking value wrappers, sum counters, and task event constants.

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
