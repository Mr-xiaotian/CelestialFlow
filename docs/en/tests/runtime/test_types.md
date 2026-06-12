# Runtime Type Tests (test_types.py)

> 📅 Last Updated: 2026/06/05

## Purpose
Verifies the value objects, enums, and wrappers in `celestialflow.runtime.util_types`, including termination signals, no-op contexts, optional-locking value wrappers, sum counters, and persisted error records.

## Coverage Points
- Construction semantics of `TerminationSignal` / `TerminationIdPool`.
- Context manager behavior and exception passthrough of `NoOpContext`.
- Read/write semantics of `ValueWrapper` in both locked and unlocked modes.
- Accumulation, reset, and thread-mode behavior of `SumCounter`.
- Enum values and immutability constraints of `StageStatus`, `CTreeEvent`, and `PersistedErrorRecord`.

## Key Scenarios
- `ValueWrapper.get_lock()` returns a real lock or `NoOpContext` depending on the construction mode.
- `SumCounter.reset()` zeros out both the initial value and sub-counters.
- `PersistedErrorRecord` is a frozen dataclass; modifying a field should raise `FrozenInstanceError`.

## How to Run

```bash
pytest tests/runtime/test_types.py -v
pytest tests/runtime/test_types.py -k "value_wrapper or sum_counter" -v
pytest tests/runtime/test_types.py -k "termination or persisted_error" -v
```
